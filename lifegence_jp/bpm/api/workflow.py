import frappe
from frappe.model.workflow import apply_workflow


@frappe.whitelist()
def get_pending_approvals(doctype=None, user=None):
	"""Get list of documents pending approval.

	Args:
		doctype: Filter by document type (optional)
		user: Filter by user who can approve (optional, defaults to current user)
	"""
	user = user or frappe.session.user

	filters = {
		"status": "Open",
		"user": user,
	}
	if doctype:
		filters["reference_doctype"] = doctype

	actions = frappe.get_all(
		"Workflow Action",
		filters=filters,
		fields=[
			"name",
			"reference_doctype",
			"reference_name",
			"workflow_state",
			"status",
			"user",
			"creation",
		],
		order_by="creation desc",
	)

	# Enrich with document details
	results = []
	for action in actions:
		try:
			doc = frappe.get_doc(action.reference_doctype, action.reference_name)
			results.append({
				"workflow_action": action.name,
				"doctype": action.reference_doctype,
				"name": action.reference_name,
				"workflow_state": action.workflow_state,
				"title": doc.get_title() if hasattr(doc, "get_title") else action.reference_name,
				"creation": str(action.creation),
				"modified": str(doc.modified),
			})
		except frappe.DoesNotExistError:
			continue

	return results


@frappe.whitelist()
def apply_action(doctype, docname, action):
	"""Apply a workflow action to a document.

	Args:
		doctype: Document type (e.g. "Sales Order")
		docname: Document name (e.g. "SO-0001")
		action: Workflow action to apply (e.g. "Approve")
	"""
	if not doctype or not docname or not action:
		frappe.throw("doctype, docname, and action are required")

	doc = frappe.get_doc(doctype, docname)
	apply_workflow(doc, action)
	doc.save(ignore_permissions=False)

	return {
		"doctype": doctype,
		"name": docname,
		"workflow_state": doc.workflow_state,
		"action_applied": action,
		"modified": str(doc.modified),
	}


@frappe.whitelist()
def get_workflow_status(doctype, docname):
	"""Get the current workflow status of a document.

	Args:
		doctype: Document type
		docname: Document name
	"""
	if not doctype or not docname:
		frappe.throw("doctype and docname are required")

	doc = frappe.get_doc(doctype, docname)

	# Get available transitions for current user
	from frappe.model.workflow import get_transitions

	transitions = get_transitions(doc)
	available_actions = [
		{
			"action": t.get("action"),
			"next_state": t.get("next_state"),
			"allowed": t.get("allowed"),
		}
		for t in transitions
	]

	return {
		"doctype": doctype,
		"name": docname,
		"workflow_state": doc.workflow_state,
		"docstatus": doc.docstatus,
		"available_actions": available_actions,
	}


@frappe.whitelist()
def get_workflow_history(doctype, docname):
	"""Get the workflow transition history of a document.

	Args:
		doctype: Document type
		docname: Document name
	"""
	if not doctype or not docname:
		frappe.throw("doctype and docname are required")

	# Get version history for workflow_state changes
	versions = frappe.get_all(
		"Version",
		filters={
			"ref_doctype": doctype,
			"docname": docname,
		},
		fields=["name", "owner", "creation", "data"],
		order_by="creation asc",
	)

	history = []
	for version in versions:
		try:
			import json

			data = json.loads(version.data) if version.data else {}
			changed = data.get("changed", [])

			for change in changed:
				if len(change) >= 3 and change[0] == "workflow_state":
					history.append({
						"from_state": change[1] or "None",
						"to_state": change[2],
						"changed_by": version.owner,
						"changed_at": str(version.creation),
					})
		except (json.JSONDecodeError, IndexError):
			continue

	# Also get comments related to workflow
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": docname,
			"comment_type": "Workflow",
		},
		fields=["content", "owner", "creation"],
		order_by="creation asc",
	)

	return {
		"doctype": doctype,
		"name": docname,
		"transitions": history,
		"comments": [
			{
				"content": c.content,
				"by": c.owner,
				"at": str(c.creation),
			}
			for c in comments
		],
	}
