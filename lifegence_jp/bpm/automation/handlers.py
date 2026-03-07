import json
import time

import frappe
import requests
from frappe.utils import now_datetime


def execute_action(action_name, reference_doctype, reference_name, workflow_state, previous_state=None):
	"""Execute a BPM Action and log the result."""
	action = frappe.get_doc("BPM Action", action_name)
	doc = frappe.get_doc(reference_doctype, reference_name)
	settings = frappe.get_cached_doc("BPM Settings")

	max_retries = action.retry_count or settings.max_retry_count or 3
	timeout = action.timeout or settings.default_timeout or 30

	log = frappe.new_doc("BPM Action Log")
	log.bpm_action = action_name
	log.reference_doctype = reference_doctype
	log.reference_name = reference_name
	log.workflow_state = workflow_state
	log.previous_state = previous_state or ""
	log.status = "Pending"
	log.executed_at = now_datetime()
	log.executed_by = frappe.session.user

	handler = _get_handler(action.action_type)

	for attempt in range(max_retries + 1):
		log.retry_attempt = attempt
		start_time = time.time()

		try:
			result = handler(action, doc, timeout)
			log.status = "Success"
			log.request_url = result.get("url", "")
			log.request_body = result.get("request_body", "")
			log.response_code = result.get("status_code", 0)
			log.response_body = _truncate(result.get("response_body", ""), 10000)
			log.execution_time = time.time() - start_time
			break

		except Exception as e:
			log.execution_time = time.time() - start_time
			log.error_message = str(e)

			if attempt < max_retries:
				log.status = "Retrying"
				frappe.log_error(
					f"BPM Action '{action_name}' attempt {attempt + 1} failed: {e}",
					"BPM Action Retry",
				)
				time.sleep(min(2 ** attempt, 30))  # Exponential backoff capped at 30s
			else:
				log.status = "Failed"
				frappe.log_error(
					f"BPM Action '{action_name}' failed after {max_retries + 1} attempts: {e}",
					"BPM Action Failed",
				)

	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return log


def _get_handler(action_type):
	"""Return the appropriate handler function for the action type."""
	handlers = {
		"Webhook": _handle_webhook,
		"n8n Workflow": _handle_n8n_workflow,
		"Frappe API": _handle_frappe_api,
		"Custom Script": _handle_custom_script,
	}
	handler = handlers.get(action_type)
	if not handler:
		raise ValueError(f"Unknown action type: {action_type}")
	return handler


def _render_body(action, doc):
	"""Render the request body template with Jinja."""
	if not action.request_body_template:
		# Default: send basic document info
		return json.dumps({
			"doctype": doc.doctype,
			"name": doc.name,
			"workflow_state": doc.workflow_state,
		})

	return frappe.render_template(action.request_body_template, {"doc": doc})


def _build_headers(action):
	"""Build request headers from action configuration."""
	headers = {"Content-Type": "application/json"}

	if action.headers:
		try:
			custom_headers = json.loads(action.headers)
			headers.update(custom_headers)
		except json.JSONDecodeError:
			frappe.log_error("Invalid JSON in BPM Action headers", "BPM Headers Error")

	# Add authentication headers
	if action.auth_type == "Bearer Token" and action.auth_credentials:
		credentials = action.get_password("auth_credentials")
		headers["Authorization"] = f"Bearer {credentials}"
	elif action.auth_type == "API Key" and action.auth_credentials:
		credentials = action.get_password("auth_credentials")
		headers["X-API-Key"] = credentials

	return headers


def _build_auth(action):
	"""Build auth tuple for Basic Auth."""
	if action.auth_type == "Basic Auth" and action.auth_credentials:
		credentials = action.get_password("auth_credentials")
		# Expect format "username:password"
		if ":" in credentials:
			parts = credentials.split(":", 1)
			return (parts[0], parts[1])
	return None


def _handle_webhook(action, doc, timeout):
	"""Send an HTTP request to a webhook URL."""
	body = _render_body(action, doc)
	headers = _build_headers(action)
	auth = _build_auth(action)
	method = (action.http_method or "POST").upper()

	response = requests.request(
		method=method,
		url=action.url,
		data=body,
		headers=headers,
		auth=auth,
		timeout=timeout,
	)
	response.raise_for_status()

	return {
		"url": action.url,
		"request_body": body,
		"status_code": response.status_code,
		"response_body": response.text,
	}


def _handle_n8n_workflow(action, doc, timeout):
	"""Trigger an n8n workflow via webhook."""
	settings = frappe.get_cached_doc("BPM Settings")

	url = action.url
	if not url and settings.n8n_base_url:
		url = settings.n8n_base_url.rstrip("/") + "/webhook/" + frappe.scrub(action.action_name)

	if not url:
		raise ValueError("No URL configured for n8n workflow trigger")

	body = _render_body(action, doc)
	headers = {"Content-Type": "application/json"}

	# Use n8n API key from settings if action doesn't have its own
	if action.auth_credentials:
		credentials = action.get_password("auth_credentials")
		headers["X-N8N-API-KEY"] = credentials
	elif settings.n8n_api_key:
		headers["X-N8N-API-KEY"] = settings.get_password("n8n_api_key")

	response = requests.post(url, data=body, headers=headers, timeout=timeout)
	response.raise_for_status()

	return {
		"url": url,
		"request_body": body,
		"status_code": response.status_code,
		"response_body": response.text,
	}


def _handle_frappe_api(action, doc, timeout):
	"""Call a Frappe internal API method."""
	body = _render_body(action, doc)
	headers = _build_headers(action)
	auth = _build_auth(action)
	method = (action.http_method or "POST").upper()

	response = requests.request(
		method=method,
		url=action.url,
		data=body,
		headers=headers,
		auth=auth,
		timeout=timeout,
	)
	response.raise_for_status()

	return {
		"url": action.url,
		"request_body": body,
		"status_code": response.status_code,
		"response_body": response.text,
	}


def _handle_custom_script(action, doc, timeout):
	"""Execute a custom Python script in a sandboxed environment."""
	if not action.request_body_template:
		raise ValueError("Custom Script action requires code in Request Body Template field")

	script = action.request_body_template
	local_vars = {"doc": doc, "frappe": frappe}
	result = frappe.safe_eval(script, eval_globals=None, eval_locals=local_vars)

	return {
		"url": "",
		"request_body": script,
		"status_code": 200,
		"response_body": str(result) if result else "",
	}


def _truncate(text, max_length):
	"""Truncate text to max_length."""
	if not text:
		return ""
	if len(text) <= max_length:
		return text
	return text[:max_length] + "... [truncated]"
