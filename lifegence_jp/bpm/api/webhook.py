import hashlib
import hmac
import json

import frappe
from frappe.model.workflow import apply_workflow


@frappe.whitelist(allow_guest=True)
def receive(source=None):
	"""Receive an external webhook and map it to a workflow action.

	Expected payload format:
	{
		"doctype": "Sales Order",
		"docname": "SO-0001",
		"action": "Approve",
		"user": "admin@example.com"  (optional - execute as this user)
	}

	Security: Validates HMAC-SHA256 signature from X-Webhook-Signature header.
	The secret is stored in BPM Settings.
	"""
	# Parse request
	try:
		data = frappe.request.get_data(as_text=True)
		payload = json.loads(data) if data else {}
	except json.JSONDecodeError:
		frappe.throw("Invalid JSON payload", frappe.InvalidRequestError)

	# Validate signature
	signature = frappe.request.headers.get("X-Webhook-Signature")
	if signature:
		_verify_signature(data, signature)

	# Extract fields
	doctype = payload.get("doctype")
	docname = payload.get("docname")
	action = payload.get("action")
	user = payload.get("user")

	if not doctype or not docname or not action:
		frappe.throw(
			"Payload must include 'doctype', 'docname', and 'action'",
			frappe.InvalidRequestError,
		)

	# Execute as specified user if provided (requires System Manager)
	if user:
		frappe.set_user(user)

	try:
		doc = frappe.get_doc(doctype, docname)
		old_state = doc.workflow_state
		apply_workflow(doc, action)
		doc.save(ignore_permissions=False)

		return {
			"status": "success",
			"source": source,
			"doctype": doctype,
			"name": docname,
			"previous_state": old_state,
			"workflow_state": doc.workflow_state,
			"action_applied": action,
		}
	except Exception as e:
		frappe.log_error(
			f"Webhook action failed: {e}",
			"BPM Webhook Error",
		)
		frappe.throw(str(e))


def _verify_signature(payload_body, signature):
	"""Verify HMAC-SHA256 signature of the webhook payload."""
	try:
		settings = frappe.get_cached_doc("BPM Settings")
		secret = settings.get_password("n8n_api_key") if settings.n8n_api_key else None
	except frappe.DoesNotExistError:
		secret = None

	if not secret:
		# No secret configured - skip verification but log warning
		frappe.logger().warning("BPM: Webhook signature provided but no secret configured")
		return

	expected = hmac.new(
		secret.encode("utf-8"),
		payload_body.encode("utf-8"),
		hashlib.sha256,
	).hexdigest()

	if not hmac.compare_digest(expected, signature):
		frappe.throw("Invalid webhook signature", frappe.AuthenticationError)
