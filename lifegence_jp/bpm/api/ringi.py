# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_pending_ringis(user=None):
	"""Get pending Ringi documents waiting for the current user's approval."""
	user = user or frappe.session.user

	ringis = frappe.get_all(
		"Ringi",
		filters={
			"docstatus": 0,
			"workflow_state": ["in", [
				"Pending Supervisor Approval",
				"Pending Department Head Approval",
				"Pending Executive Approval",
			]],
		},
		fields=[
			"name", "ringi_title", "ringi_category", "amount",
			"applicant", "application_date", "department",
			"workflow_state",
		],
		order_by="creation desc",
	)

	# Filter to only show ringis where user is in the approvers list
	result = []
	for ringi in ringis:
		approvers = frappe.get_all(
			"Ringi Approver",
			filters={"parent": ringi.name, "approver": user, "status": "Pending"},
			fields=["name"],
		)
		if approvers:
			result.append(ringi)

	return {"success": True, "count": len(result), "ringis": result}


@frappe.whitelist()
def approve_ringi(ringi_name, comment=None):
	"""Approve a Ringi document and update the approver record."""
	if not frappe.db.exists("Ringi", ringi_name):
		frappe.throw(_("Ringi {0} does not exist").format(ringi_name))

	ringi = frappe.get_doc("Ringi", ringi_name)

	# Update approver status
	user = frappe.session.user
	for approver in ringi.approvers:
		if approver.approver == user and approver.status == "Pending":
			approver.status = "Approved"
			approver.comment = comment or ""
			approver.action_date = frappe.utils.now_datetime()
			break

	ringi.add_comment("Comment", _("Approved by {0}. {1}").format(
		frappe.utils.get_fullname(user),
		comment or "",
	))
	ringi.save(ignore_permissions=True)

	return {"success": True, "message": _("Ringi approved successfully")}


@frappe.whitelist()
def return_ringi(ringi_name, comment=None):
	"""Return a Ringi document for revision."""
	if not frappe.db.exists("Ringi", ringi_name):
		frappe.throw(_("Ringi {0} does not exist").format(ringi_name))

	ringi = frappe.get_doc("Ringi", ringi_name)

	# Update approver status
	user = frappe.session.user
	for approver in ringi.approvers:
		if approver.approver == user and approver.status == "Pending":
			approver.status = "Returned"
			approver.comment = comment or ""
			approver.action_date = frappe.utils.now_datetime()
			break

	ringi.add_comment("Comment", _("Returned by {0}. {1}").format(
		frappe.utils.get_fullname(user),
		comment or "",
	))
	ringi.save(ignore_permissions=True)

	return {"success": True, "message": _("Ringi returned for revision")}


@frappe.whitelist()
def get_ringi_summary(ringi_name):
	"""Get summary of a Ringi including approval status."""
	if not frappe.db.exists("Ringi", ringi_name):
		frappe.throw(_("Ringi {0} does not exist").format(ringi_name))

	ringi = frappe.get_doc("Ringi", ringi_name)

	approvers = []
	for a in ringi.approvers:
		approvers.append({
			"approver": a.approver,
			"approver_name": a.approver_name,
			"role": a.role,
			"sequence": a.sequence,
			"status": a.status,
			"comment": a.comment,
			"action_date": str(a.action_date) if a.action_date else "",
		})

	return {
		"success": True,
		"ringi_title": ringi.ringi_title,
		"ringi_category": ringi.ringi_category,
		"amount": ringi.amount,
		"workflow_state": ringi.workflow_state,
		"applicant": ringi.applicant,
		"department": ringi.department,
		"approvers": approvers,
	}
