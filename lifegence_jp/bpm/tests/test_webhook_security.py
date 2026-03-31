# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestWebhookSecurity(FrappeTestCase):
	"""Security tests for BPM Webhook endpoint."""

	def _make_payload(self, **overrides):
		"""Create a standard webhook payload."""
		payload = {
			"doctype": "Sales Order",
			"docname": "SO-0001",
			"action": "Approve",
		}
		payload.update(overrides)
		return json.dumps(payload)

	def _sign_payload(self, payload_body, secret):
		"""Generate HMAC-SHA256 signature for a payload."""
		return hmac.new(
			secret.encode("utf-8"),
			payload_body.encode("utf-8"),
			hashlib.sha256,
		).hexdigest()

	def _mock_request(self, payload, headers=None):
		"""Create a mock request object."""
		mock = MagicMock()
		mock.get_data.return_value = payload  # as_text=True returns str
		mock.headers = headers or {}
		return mock

	# --- TC-WH-S01: Reject request with no signature header ---

	def test_reject_missing_signature(self):
		"""TC-WH-S01: Requests without X-Webhook-Signature must be rejected."""
		payload = self._make_payload()
		mock_request = self._mock_request(payload, headers={})

		with patch.object(frappe, "request", mock_request):
			with self.assertRaises(frappe.AuthenticationError):
				from lifegence_jp.bpm.api.webhook import receive
				receive()

	# --- TC-WH-S02: Reject request with invalid signature ---

	def test_reject_invalid_signature(self):
		"""TC-WH-S02: Requests with wrong signature must be rejected."""
		payload = self._make_payload()
		mock_request = self._mock_request(
			payload, headers={"X-Webhook-Signature": "invalid_signature_value"}
		)

		mock_settings = MagicMock()
		mock_settings.n8n_api_key = "test_secret"
		mock_settings.get_password.return_value = "test_secret"

		with patch.object(frappe, "request", mock_request):
			with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
				with self.assertRaises(frappe.AuthenticationError):
					from lifegence_jp.bpm.api.webhook import receive
					receive()

	# --- TC-WH-S03: Reject when no secret is configured ---

	def test_reject_when_no_secret_configured(self):
		"""TC-WH-S03: If no webhook secret is configured, all requests must be rejected."""
		payload = self._make_payload()
		mock_request = self._mock_request(
			payload, headers={"X-Webhook-Signature": "some_signature"}
		)

		mock_settings = MagicMock()
		mock_settings.n8n_api_key = None
		mock_settings.get_password.return_value = None

		with patch.object(frappe, "request", mock_request):
			with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
				with self.assertRaises(frappe.AuthenticationError):
					from lifegence_jp.bpm.api.webhook import receive
					receive()

	# --- TC-WH-S04: Reject user impersonation with invalid user ---

	def test_reject_invalid_user_in_payload(self):
		"""TC-WH-S04: Payload with non-existent user must be rejected."""
		payload = self._make_payload(user="nonexistent@example.com")
		secret = "test_secret"
		signature = self._sign_payload(payload, secret)
		mock_request = self._mock_request(
			payload, headers={"X-Webhook-Signature": signature}
		)

		mock_settings = MagicMock()
		mock_settings.n8n_api_key = "test_secret"
		mock_settings.get_password.return_value = secret

		with patch.object(frappe, "request", mock_request):
			with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
				with self.assertRaises(frappe.ValidationError):
					from lifegence_jp.bpm.api.webhook import receive
					receive()

	# --- TC-WH-S05: Reject disabled user in payload ---

	def test_reject_disabled_user_in_payload(self):
		"""TC-WH-S05: Payload with disabled user must be rejected."""
		test_email = "disabled-webhook-test@example.com"
		if not frappe.db.exists("User", test_email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": test_email,
				"first_name": "Disabled",
				"enabled": 0,
			})
			user.insert(ignore_permissions=True)
			frappe.db.commit()
		else:
			frappe.db.set_value("User", test_email, "enabled", 0)
			frappe.db.commit()

		payload = self._make_payload(user=test_email)
		secret = "test_secret"
		signature = self._sign_payload(payload, secret)
		mock_request = self._mock_request(
			payload, headers={"X-Webhook-Signature": signature}
		)

		mock_settings = MagicMock()
		mock_settings.n8n_api_key = "test_secret"
		mock_settings.get_password.return_value = secret

		with patch.object(frappe, "request", mock_request):
			with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
				with self.assertRaises(frappe.ValidationError):
					from lifegence_jp.bpm.api.webhook import receive
					receive()

	# --- TC-WH-S06: Accept valid signed request ---

	def test_accept_valid_signature(self):
		"""TC-WH-S06: Valid HMAC signature must pass verification."""
		from lifegence_jp.bpm.api.webhook import _verify_signature

		payload = self._make_payload()
		secret = "test_secret_key"
		signature = self._sign_payload(payload, secret)

		mock_settings = MagicMock()
		mock_settings.n8n_api_key = "test_secret_key"
		mock_settings.get_password.return_value = secret

		with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
			# Should not raise
			_verify_signature(payload, signature)
