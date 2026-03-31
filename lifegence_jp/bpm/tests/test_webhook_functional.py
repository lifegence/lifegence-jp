# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

"""
Functional tests for bpm/api/webhook.py — webhook receiver.

Security tests exist in test_webhook_security.py. These cover functional flow:
  1. receive — missing required fields in payload
  2. receive — happy path with valid signature
  3. receive — user validation (nonexistent, disabled)
  4. receive — workflow action failure
  5. _validate_user — existence and enabled checks
  6. _verify_signature — HMAC verification
"""

import hashlib
import hmac
import json

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock


class TestWebhookReceive(FrappeTestCase):
    """Functional tests for the receive endpoint."""

    def _sign(self, body, secret="test_secret"):
        return hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _mock_request(self, payload_dict, secret="test_secret"):
        body = json.dumps(payload_dict)
        sig = self._sign(body, secret)
        mock_req = MagicMock()
        mock_req.get_data.return_value = body
        mock_req.headers = {"X-Webhook-Signature": sig}
        return mock_req

    def _mock_settings(self, secret="test_secret"):
        settings = MagicMock()
        settings.n8n_api_key = secret
        settings.get_password.return_value = secret
        return settings

    def test_missing_doctype(self):
        """Payload without doctype should be rejected."""
        from lifegence_jp.bpm.api.webhook import receive

        payload = {"docname": "SO-001", "action": "Approve"}
        mock_req = self._mock_request(payload)
        mock_settings = self._mock_settings()

        with patch.object(frappe, "request", mock_req):
            with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
                with self.assertRaises(Exception) as ctx:
                    receive()
                self.assertIn("doctype", str(ctx.exception).lower())

    def test_missing_action(self):
        """Payload without action should be rejected."""
        from lifegence_jp.bpm.api.webhook import receive

        payload = {"doctype": "Sales Order", "docname": "SO-001"}
        mock_req = self._mock_request(payload)
        mock_settings = self._mock_settings()

        with patch.object(frappe, "request", mock_req):
            with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
                with self.assertRaises(Exception) as ctx:
                    receive()
                self.assertIn("action", str(ctx.exception).lower())

    @patch("lifegence_jp.bpm.api.webhook.apply_workflow")
    def test_happy_path(self, mock_apply):
        """Valid payload with correct signature should process successfully."""
        from lifegence_jp.bpm.api.webhook import receive

        payload = {
            "doctype": "Sales Order",
            "docname": "SO-001",
            "action": "Approve",
        }
        mock_req = self._mock_request(payload)
        mock_settings = self._mock_settings()

        mock_doc = MagicMock()
        mock_doc.workflow_state = "Approved"

        with patch.object(frappe, "request", mock_req):
            with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
                with patch("lifegence_jp.bpm.api.webhook.frappe.get_doc", return_value=mock_doc):
                    result = receive(source="test")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action_applied"], "Approve")
        self.assertEqual(result["source"], "test")
        mock_apply.assert_called_once()

    @patch("lifegence_jp.bpm.api.webhook.apply_workflow")
    def test_with_user_context(self, mock_apply):
        """Providing a user should set_user before applying workflow."""
        from lifegence_jp.bpm.api.webhook import receive

        payload = {
            "doctype": "Sales Order",
            "docname": "SO-001",
            "action": "Approve",
            "user": "admin@example.com",
        }
        mock_req = self._mock_request(payload)
        mock_settings = self._mock_settings()

        mock_doc = MagicMock()
        mock_doc.workflow_state = "Approved"

        with patch.object(frappe, "request", mock_req):
            with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
                with patch("lifegence_jp.bpm.api.webhook.frappe.db.exists", return_value=True):
                    with patch("lifegence_jp.bpm.api.webhook.frappe.db.get_value", return_value=1):
                        with patch("lifegence_jp.bpm.api.webhook.frappe.set_user") as mock_set_user:
                            with patch("lifegence_jp.bpm.api.webhook.frappe.get_doc", return_value=mock_doc):
                                result = receive()

        mock_set_user.assert_called_with("admin@example.com")

    @patch("lifegence_jp.bpm.api.webhook.apply_workflow", side_effect=Exception("Transition not allowed"))
    def test_workflow_failure(self, mock_apply):
        """Workflow action failures should raise an error."""
        from lifegence_jp.bpm.api.webhook import receive

        payload = {
            "doctype": "Sales Order",
            "docname": "SO-001",
            "action": "InvalidAction",
        }
        mock_req = self._mock_request(payload)
        mock_settings = self._mock_settings()

        mock_doc = MagicMock()
        mock_doc.workflow_state = "Draft"

        with patch.object(frappe, "request", mock_req):
            with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=mock_settings):
                with patch("lifegence_jp.bpm.api.webhook.frappe.get_doc", return_value=mock_doc):
                    with patch("lifegence_jp.bpm.api.webhook.frappe.log_error"):
                        with self.assertRaises(Exception):
                            receive()


class TestValidateUser(FrappeTestCase):
    """Tests for _validate_user."""

    def test_nonexistent_user(self):
        from lifegence_jp.bpm.api.webhook import _validate_user
        with patch("lifegence_jp.bpm.api.webhook.frappe.db.exists", return_value=False):
            with self.assertRaises(frappe.ValidationError):
                _validate_user("nonexistent@example.com")

    def test_disabled_user(self):
        from lifegence_jp.bpm.api.webhook import _validate_user
        with patch("lifegence_jp.bpm.api.webhook.frappe.db.exists", return_value=True):
            with patch("lifegence_jp.bpm.api.webhook.frappe.db.get_value", return_value=0):
                with self.assertRaises(frappe.ValidationError):
                    _validate_user("disabled@example.com")

    def test_valid_user(self):
        from lifegence_jp.bpm.api.webhook import _validate_user
        with patch("lifegence_jp.bpm.api.webhook.frappe.db.exists", return_value=True):
            with patch("lifegence_jp.bpm.api.webhook.frappe.db.get_value", return_value=1):
                # Should not raise
                _validate_user("valid@example.com")


class TestVerifySignature(FrappeTestCase):
    """Tests for _verify_signature."""

    def test_valid_signature(self):
        from lifegence_jp.bpm.api.webhook import _verify_signature

        secret = "my_secret"
        body = '{"test": true}'
        sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

        settings = MagicMock()
        settings.n8n_api_key = secret
        settings.get_password.return_value = secret

        with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=settings):
            # Should not raise
            _verify_signature(body, sig)

    def test_invalid_signature(self):
        from lifegence_jp.bpm.api.webhook import _verify_signature

        settings = MagicMock()
        settings.n8n_api_key = "secret"
        settings.get_password.return_value = "secret"

        with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=settings):
            with self.assertRaises(frappe.AuthenticationError):
                _verify_signature('{"test": true}', "wrong_signature")

    def test_no_secret_configured(self):
        from lifegence_jp.bpm.api.webhook import _verify_signature

        settings = MagicMock()
        settings.n8n_api_key = None

        with patch("lifegence_jp.bpm.api.webhook.frappe.get_cached_doc", return_value=settings):
            with self.assertRaises(frappe.AuthenticationError):
                _verify_signature('{"test": true}', "some_sig")
