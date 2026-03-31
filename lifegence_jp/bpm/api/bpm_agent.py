# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from typing import Dict, Any, Optional


@frappe.whitelist()
def list_active_processes(
	limit: int = 20,
	reference_doctype: Optional[str] = None,
) -> Dict[str, Any]:
	"""List active BPM action logs."""
	filters = {"status": ["in", ["Pending", "Retrying"]]}
	if reference_doctype:
		filters["reference_doctype"] = reference_doctype

	logs = frappe.get_all(
		"BPM Action Log",
		filters=filters,
		fields=[
			"name", "bpm_action", "reference_doctype", "reference_name",
			"workflow_state", "previous_state", "status",
			"retry_attempt", "executed_at", "executed_by",
		],
		order_by="creation desc",
		limit_page_length=limit,
	)

	return {
		"success": True,
		"count": len(logs),
		"action_logs": logs,
	}


@frappe.whitelist()
def get_process_status(log_name: str) -> Dict[str, Any]:
	"""Get detailed BPM action log status."""
	if not frappe.db.exists("BPM Action Log", log_name):
		frappe.throw(f"BPM Action Log '{log_name}' does not exist", frappe.DoesNotExistError)

	if not frappe.has_permission("BPM Action Log", "read", log_name):
		frappe.throw(f"No read permission for BPM Action Log '{log_name}'", frappe.PermissionError)

	log = frappe.get_doc("BPM Action Log", log_name)
	return {
		"success": True,
		"log_name": log_name,
		"bpm_action": log.bpm_action,
		"reference_doctype": log.reference_doctype,
		"reference_name": log.reference_name,
		"workflow_state": log.workflow_state,
		"previous_state": log.previous_state,
		"status": log.status,
		"error_message": log.error_message or "",
		"response_code": log.response_code,
		"retry_attempt": log.retry_attempt,
		"executed_at": str(log.executed_at) if log.executed_at else "",
		"executed_by": log.executed_by or "",
	}


@frappe.whitelist()
def draft_ringi(
	title: str,
	category: str,
	amount: Optional[float] = None,
	description: Optional[str] = None,
) -> Dict[str, Any]:
	"""Create a draft Ringi document from chat instructions."""
	ringi = frappe.new_doc("Ringi")
	ringi.ringi_title = title
	ringi.ringi_category = category
	if amount:
		ringi.amount = amount
	if description:
		ringi.description = description
	ringi.application_date = frappe.utils.today()

	# Auto-set applicant
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "department"],
		as_dict=True,
	)
	if employee:
		ringi.applicant = employee.name
		ringi.department = employee.department

	ringi.insert()

	return {
		"success": True,
		"ringi_name": ringi.name,
		"ringi_title": ringi.ringi_title,
		"message": f"稟議書 '{ringi.name}' をドラフトとして作成しました。",
	}


@frappe.whitelist()
def check_approval_status(
	ringi_name: Optional[str] = None,
	applicant: Optional[str] = None,
) -> Dict[str, Any]:
	"""Check approval status of Ringi documents."""
	if ringi_name:
		if not frappe.db.exists("Ringi", ringi_name):
			frappe.throw(f"稟議書 '{ringi_name}' は存在しません", frappe.DoesNotExistError)

		ringi = frappe.get_doc("Ringi", ringi_name)
		approvers = []
		for a in ringi.approvers:
			approvers.append({
				"approver_name": a.approver_name,
				"role": a.role,
				"status": a.status,
				"comment": a.comment or "",
			})

		return {
			"success": True,
			"ringi_name": ringi.name,
			"ringi_title": ringi.ringi_title,
			"workflow_state": ringi.workflow_state,
			"approvers": approvers,
		}

	# List pending ringis
	filters = {
		"docstatus": 0,
		"workflow_state": ["in", [
			"Pending Supervisor Approval",
			"Pending Department Head Approval",
			"Pending Executive Approval",
		]],
	}
	if applicant:
		filters["applicant"] = applicant

	ringis = frappe.get_all(
		"Ringi",
		filters=filters,
		fields=["name", "ringi_title", "ringi_category", "amount", "workflow_state", "applicant"],
		order_by="creation desc",
		limit_page_length=20,
	)

	return {
		"success": True,
		"count": len(ringis),
		"ringis": ringis,
	}


@frappe.whitelist()
def find_ringi_template(
	keyword: Optional[str] = None,
	category: Optional[str] = None,
) -> Dict[str, Any]:
	"""Find suitable Ringi templates based on keyword or category."""
	filters = {}
	if category:
		filters["ringi_category"] = category

	or_filters = {}
	if keyword:
		or_filters = {
			"template_name": ["like", f"%{keyword}%"],
			"description": ["like", f"%{keyword}%"],
		}

	templates = frappe.get_all(
		"Ringi Template",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=["name", "template_name", "ringi_category", "description", "amount_threshold"],
		order_by="creation desc",
		limit_page_length=10,
	)

	return {
		"success": True,
		"count": len(templates),
		"templates": templates,
	}
