# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

"""
Tests for bpm/automation/handlers.py — action execution, retry logic.

Covers:
  1. _get_handler — handler selection by action type
  2. _render_body — Jinja template rendering and default body
  3. _build_headers — header construction with auth
  4. _build_auth — Basic Auth tuple construction
  5. _handle_webhook — HTTP request execution
  6. _handle_n8n_workflow — n8n trigger
  7. _handle_custom_script — sandboxed script execution
  8. execute_action — happy path with mocked handler
  9. execute_action — retry with exponential backoff
  10. _truncate — text truncation
"""

import json
import time

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock, call


class TestGetHandler(FrappeTestCase):
    """Tests for _get_handler — handler dispatch by action type."""

    def test_webhook_handler(self):
        from lifegence_jp.bpm.automation.handlers import _get_handler, _handle_webhook
        self.assertEqual(_get_handler("Webhook"), _handle_webhook)

    def test_n8n_handler(self):
        from lifegence_jp.bpm.automation.handlers import _get_handler, _handle_n8n_workflow
        self.assertEqual(_get_handler("n8n Workflow"), _handle_n8n_workflow)

    def test_frappe_api_handler(self):
        from lifegence_jp.bpm.automation.handlers import _get_handler, _handle_frappe_api
        self.assertEqual(_get_handler("Frappe API"), _handle_frappe_api)

    def test_custom_script_handler(self):
        from lifegence_jp.bpm.automation.handlers import _get_handler, _handle_custom_script
        self.assertEqual(_get_handler("Custom Script"), _handle_custom_script)

    def test_unknown_type_raises(self):
        from lifegence_jp.bpm.automation.handlers import _get_handler
        with self.assertRaises(ValueError):
            _get_handler("Unknown Type")


class TestRenderBody(FrappeTestCase):
    """Tests for _render_body — Jinja template rendering."""

    def test_default_body_without_template(self):
        from lifegence_jp.bpm.automation.handlers import _render_body

        action = MagicMock()
        action.request_body_template = None

        doc = MagicMock()
        doc.doctype = "Sales Order"
        doc.name = "SO-0001"
        doc.workflow_state = "Approved"

        result = json.loads(_render_body(action, doc))
        self.assertEqual(result["doctype"], "Sales Order")
        self.assertEqual(result["name"], "SO-0001")
        self.assertEqual(result["workflow_state"], "Approved")

    def test_jinja_template_rendering(self):
        from lifegence_jp.bpm.automation.handlers import _render_body

        action = MagicMock()
        action.request_body_template = '{"order": "{{ doc.name }}", "status": "{{ doc.workflow_state }}"}'

        doc = MagicMock()
        doc.name = "SO-0002"
        doc.workflow_state = "Submitted"

        with patch("lifegence_jp.bpm.automation.handlers.frappe.render_template") as mock_render:
            mock_render.return_value = '{"order": "SO-0002", "status": "Submitted"}'
            result = _render_body(action, doc)

        self.assertIn("SO-0002", result)


class TestBuildHeaders(FrappeTestCase):
    """Tests for _build_headers — header construction with auth."""

    def test_default_content_type(self):
        from lifegence_jp.bpm.automation.handlers import _build_headers

        action = MagicMock()
        action.headers = None
        action.auth_type = None
        action.auth_credentials = None

        headers = _build_headers(action)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_custom_headers_merged(self):
        from lifegence_jp.bpm.automation.handlers import _build_headers

        action = MagicMock()
        action.headers = '{"X-Custom": "value"}'
        action.auth_type = None
        action.auth_credentials = None

        headers = _build_headers(action)
        self.assertEqual(headers["X-Custom"], "value")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_bearer_token_auth(self):
        from lifegence_jp.bpm.automation.handlers import _build_headers

        action = MagicMock()
        action.headers = None
        action.auth_type = "Bearer Token"
        action.auth_credentials = "token123"
        action.get_password.return_value = "secret_token"

        headers = _build_headers(action)
        self.assertEqual(headers["Authorization"], "Bearer secret_token")

    def test_api_key_auth(self):
        from lifegence_jp.bpm.automation.handlers import _build_headers

        action = MagicMock()
        action.headers = None
        action.auth_type = "API Key"
        action.auth_credentials = "key123"
        action.get_password.return_value = "my_api_key"

        headers = _build_headers(action)
        self.assertEqual(headers["X-API-Key"], "my_api_key")

    def test_invalid_headers_json(self):
        from lifegence_jp.bpm.automation.handlers import _build_headers

        action = MagicMock()
        action.headers = "not valid json"
        action.auth_type = None
        action.auth_credentials = None

        # Should not raise, just log error
        headers = _build_headers(action)
        self.assertIn("Content-Type", headers)


class TestBuildAuth(FrappeTestCase):
    """Tests for _build_auth — Basic Auth tuple."""

    def test_basic_auth(self):
        from lifegence_jp.bpm.automation.handlers import _build_auth

        action = MagicMock()
        action.auth_type = "Basic Auth"
        action.auth_credentials = "user:pass"
        action.get_password.return_value = "user:pass"

        result = _build_auth(action)
        self.assertEqual(result, ("user", "pass"))

    def test_non_basic_auth_returns_none(self):
        from lifegence_jp.bpm.automation.handlers import _build_auth

        action = MagicMock()
        action.auth_type = "Bearer Token"
        action.auth_credentials = "token"

        self.assertIsNone(_build_auth(action))

    def test_no_credentials_returns_none(self):
        from lifegence_jp.bpm.automation.handlers import _build_auth

        action = MagicMock()
        action.auth_type = "Basic Auth"
        action.auth_credentials = None

        self.assertIsNone(_build_auth(action))


class TestHandleWebhook(FrappeTestCase):
    """Tests for _handle_webhook."""

    @patch("lifegence_jp.bpm.automation.handlers.requests.request")
    def test_successful_request(self, mock_request):
        from lifegence_jp.bpm.automation.handlers import _handle_webhook

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"ok": true}'
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        action = MagicMock()
        action.url = "https://example.com/webhook"
        action.http_method = "POST"
        action.request_body_template = None
        action.headers = None
        action.auth_type = None
        action.auth_credentials = None

        doc = MagicMock()
        doc.doctype = "Sales Order"
        doc.name = "SO-001"
        doc.workflow_state = "Approved"

        result = _handle_webhook(action, doc, timeout=30)
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["url"], "https://example.com/webhook")

    @patch("lifegence_jp.bpm.automation.handlers.requests.request")
    def test_http_error_raises(self, mock_request):
        from lifegence_jp.bpm.automation.handlers import _handle_webhook
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_request.return_value = mock_response

        action = MagicMock()
        action.url = "https://example.com/webhook"
        action.http_method = "POST"
        action.request_body_template = None
        action.headers = None
        action.auth_type = None
        action.auth_credentials = None

        doc = MagicMock()
        doc.doctype = "Test"
        doc.name = "T-1"
        doc.workflow_state = "Done"

        with self.assertRaises(requests.HTTPError):
            _handle_webhook(action, doc, timeout=30)


class TestHandleN8nWorkflow(FrappeTestCase):
    """Tests for _handle_n8n_workflow."""

    @patch("lifegence_jp.bpm.automation.handlers.requests.post")
    def test_uses_action_url(self, mock_post):
        from lifegence_jp.bpm.automation.handlers import _handle_n8n_workflow

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"ok": true}'
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        action = MagicMock()
        action.url = "https://n8n.example.com/webhook/my-flow"
        action.action_name = "test_flow"
        action.request_body_template = None
        action.auth_credentials = None

        settings = MagicMock()
        settings.n8n_base_url = "https://n8n.example.com"
        settings.n8n_api_key = "key123"
        settings.get_password.return_value = "key123"

        doc = MagicMock()
        doc.doctype = "Test"
        doc.name = "T-1"
        doc.workflow_state = "Done"

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
            result = _handle_n8n_workflow(action, doc, timeout=30)

        self.assertEqual(result["status_code"], 200)

    @patch("lifegence_jp.bpm.automation.handlers.requests.post")
    def test_builds_url_from_settings(self, mock_post):
        from lifegence_jp.bpm.automation.handlers import _handle_n8n_workflow

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        action = MagicMock()
        action.url = None  # No URL on action
        action.action_name = "my_flow"
        action.request_body_template = None
        action.auth_credentials = None

        settings = MagicMock()
        settings.n8n_base_url = "https://n8n.example.com"
        settings.n8n_api_key = "key123"
        settings.get_password.return_value = "key123"

        doc = MagicMock()
        doc.doctype = "Test"
        doc.name = "T-1"
        doc.workflow_state = "Done"

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
            result = _handle_n8n_workflow(action, doc, timeout=30)

        # URL should be constructed from settings
        call_url = mock_post.call_args[0][0]
        self.assertIn("n8n.example.com", call_url)
        self.assertIn("webhook/my_flow", call_url)

    def test_no_url_raises(self):
        from lifegence_jp.bpm.automation.handlers import _handle_n8n_workflow

        action = MagicMock()
        action.url = None
        action.action_name = "test"
        action.request_body_template = None
        action.auth_credentials = None

        settings = MagicMock()
        settings.n8n_base_url = None
        settings.n8n_api_key = None

        doc = MagicMock()

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
            with self.assertRaises(ValueError):
                _handle_n8n_workflow(action, doc, timeout=30)


class TestHandleCustomScript(FrappeTestCase):
    """Tests for _handle_custom_script."""

    def test_no_script_raises(self):
        from lifegence_jp.bpm.automation.handlers import _handle_custom_script

        action = MagicMock()
        action.request_body_template = None

        with self.assertRaises(ValueError):
            _handle_custom_script(action, MagicMock(), timeout=30)

    def test_executes_script(self):
        from lifegence_jp.bpm.automation.handlers import _handle_custom_script

        action = MagicMock()
        action.request_body_template = "doc.name"

        doc = MagicMock()
        doc.name = "SO-001"

        with patch("lifegence_jp.bpm.automation.handlers.frappe.safe_eval", return_value="SO-001"):
            result = _handle_custom_script(action, doc, timeout=30)
        self.assertEqual(result["status_code"], 200)
        self.assertIn("SO-001", result["response_body"])


class TestTruncate(FrappeTestCase):
    """Tests for _truncate utility."""

    def test_short_text(self):
        from lifegence_jp.bpm.automation.handlers import _truncate
        self.assertEqual(_truncate("short", 100), "short")

    def test_long_text(self):
        from lifegence_jp.bpm.automation.handlers import _truncate
        result = _truncate("x" * 200, 50)
        self.assertEqual(len(result), 50 + len("... [truncated]"))
        self.assertTrue(result.endswith("... [truncated]"))

    def test_empty_text(self):
        from lifegence_jp.bpm.automation.handlers import _truncate
        self.assertEqual(_truncate("", 100), "")

    def test_none_text(self):
        from lifegence_jp.bpm.automation.handlers import _truncate
        self.assertEqual(_truncate(None, 100), "")


class TestExecuteAction(FrappeTestCase):
    """Tests for execute_action — full flow with retry."""

    def _make_mocks(self):
        action = MagicMock()
        action.action_type = "Webhook"
        action.retry_count = 2
        action.timeout = 30
        action.action_name = "test_action"

        doc = MagicMock()
        doc.doctype = "Sales Order"
        doc.name = "SO-001"

        settings = MagicMock()
        settings.max_retry_count = 3
        settings.default_timeout = 30

        log = MagicMock()
        log.name = "LOG-001"

        return action, doc, settings, log

    @patch("lifegence_jp.bpm.automation.handlers.time.sleep")
    @patch("lifegence_jp.bpm.automation.handlers._handle_webhook")
    def test_success_on_first_attempt(self, mock_handler, mock_sleep):
        from lifegence_jp.bpm.automation.handlers import execute_action

        action, doc, settings, log = self._make_mocks()
        mock_handler.return_value = {
            "url": "https://example.com",
            "request_body": "{}",
            "status_code": 200,
            "response_body": "ok",
        }

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_doc", side_effect=[action, doc]):
            with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
                with patch("lifegence_jp.bpm.automation.handlers.frappe.new_doc", return_value=log):
                    with patch("lifegence_jp.bpm.automation.handlers.frappe.db"):
                        result = execute_action("test_action", "Sales Order", "SO-001", "Approved")

        self.assertEqual(log.status, "Success")
        mock_sleep.assert_not_called()

    @patch("lifegence_jp.bpm.automation.handlers.time.sleep")
    @patch("lifegence_jp.bpm.automation.handlers._handle_webhook")
    def test_retry_then_success(self, mock_handler, mock_sleep):
        from lifegence_jp.bpm.automation.handlers import execute_action

        action, doc, settings, log = self._make_mocks()

        # First call fails, second succeeds
        mock_handler.side_effect = [
            Exception("Connection refused"),
            {
                "url": "https://example.com",
                "request_body": "{}",
                "status_code": 200,
                "response_body": "ok",
            },
        ]

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_doc", side_effect=[action, doc]):
            with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
                with patch("lifegence_jp.bpm.automation.handlers.frappe.new_doc", return_value=log):
                    with patch("lifegence_jp.bpm.automation.handlers.frappe.db"):
                        with patch("lifegence_jp.bpm.automation.handlers.frappe.log_error"):
                            result = execute_action("test_action", "Sales Order", "SO-001", "Approved")

        self.assertEqual(log.status, "Success")
        # Should have slept once (exponential backoff)
        mock_sleep.assert_called_once()

    @patch("lifegence_jp.bpm.automation.handlers.time.sleep")
    @patch("lifegence_jp.bpm.automation.handlers._handle_webhook")
    def test_all_retries_fail(self, mock_handler, mock_sleep):
        from lifegence_jp.bpm.automation.handlers import execute_action

        action, doc, settings, log = self._make_mocks()
        mock_handler.side_effect = Exception("Always fails")

        with patch("lifegence_jp.bpm.automation.handlers.frappe.get_doc", side_effect=[action, doc]):
            with patch("lifegence_jp.bpm.automation.handlers.frappe.get_cached_doc", return_value=settings):
                with patch("lifegence_jp.bpm.automation.handlers.frappe.new_doc", return_value=log):
                    with patch("lifegence_jp.bpm.automation.handlers.frappe.db"):
                        with patch("lifegence_jp.bpm.automation.handlers.frappe.log_error"):
                            result = execute_action("test_action", "Sales Order", "SO-001", "Approved")

        self.assertEqual(log.status, "Failed")
        # retry_count=2, so 3 attempts total, 2 sleeps
        self.assertEqual(mock_sleep.call_count, 2)
