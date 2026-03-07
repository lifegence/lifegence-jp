import frappe
from frappe.utils import now_datetime


def on_document_update(doc, method):
	"""Hook called on every document update. Dispatches BPM actions on workflow state change."""
	if not getattr(doc, "workflow_state", None):
		return

	old_state = doc.get_db_value("workflow_state") if not doc.is_new() else None
	new_state = doc.workflow_state

	if old_state == new_state:
		return

	# Check if automation is enabled
	try:
		settings = frappe.get_cached_doc("BPM Settings")
		if not settings.enable_automation:
			return
	except frappe.DoesNotExistError:
		# BPM Settings not yet created (first run), skip
		return

	# Find matching BPM Actions
	filters = {
		"enabled": 1,
		"document_type": doc.doctype,
		"workflow_state": new_state,
	}

	actions = frappe.get_all(
		"BPM Action",
		filters=filters,
		fields=["name", "previous_state", "condition", "run_in_background"],
	)

	for action_ref in actions:
		# Check previous state filter
		if action_ref.previous_state and action_ref.previous_state != old_state:
			continue

		# Evaluate condition
		if action_ref.condition:
			try:
				if not frappe.safe_eval(action_ref.condition, eval_globals=None, eval_locals={"doc": doc}):
					continue
			except Exception as e:
				frappe.log_error(
					f"BPM Action condition evaluation failed for {action_ref.name}: {e}",
					"BPM Condition Error",
				)
				continue

		# Execute action
		if action_ref.run_in_background:
			frappe.enqueue(
				"lifegence_jp.bpm.automation.handlers.execute_action",
				action_name=action_ref.name,
				reference_doctype=doc.doctype,
				reference_name=doc.name,
				workflow_state=new_state,
				previous_state=old_state,
				queue="default",
			)
		else:
			from lifegence_jp.bpm.automation.handlers import execute_action

			execute_action(
				action_name=action_ref.name,
				reference_doctype=doc.doctype,
				reference_name=doc.name,
				workflow_state=new_state,
				previous_state=old_state,
			)
