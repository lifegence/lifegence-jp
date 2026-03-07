# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password


def _create_access_log(employee, access_type, purpose, my_number_record=None):
	"""Create an access log entry for My Number operations."""
	log = frappe.get_doc({
		"doctype": "My Number Access Log",
		"employee": employee,
		"accessed_by": frappe.session.user,
		"accessed_at": frappe.utils.now_datetime(),
		"access_type": access_type,
		"purpose": purpose,
		"ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "",
		"my_number_record": my_number_record,
	})
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return log.name


@frappe.whitelist()
def get_my_number_masked(employee):
	"""Get masked My Number display with access log recording.

	Requires HR Manager or System Manager role.
	"""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	record = frappe.db.get_value(
		"My Number Record",
		{"employee": employee, "status": ["not in", ["削除済"]]},
		["name", "my_number_masked", "status", "collection_date", "valid_until"],
		as_dict=True,
		order_by="creation desc",
	)

	if not record:
		return {"success": False, "error": _("マイナンバーが登録されていません。")}

	# Record access log
	_create_access_log(employee, "閲覧", "マスク表示取得", record.name)

	return {
		"success": True,
		"employee": employee,
		"my_number_masked": record.my_number_masked,
		"status": record.status,
		"collection_date": str(record.collection_date) if record.collection_date else None,
		"valid_until": str(record.valid_until) if record.valid_until else None,
	}


@frappe.whitelist()
def access_my_number(employee, purpose):
	"""Access decrypted My Number (System Manager only).

	Always creates an access log entry.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("マイナンバーの復号にはSystem Manager権限が必要です"), frappe.PermissionError)

	if not purpose:
		frappe.throw(_("利用目的を指定してください"))

	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	record = frappe.db.get_value(
		"My Number Record",
		{"employee": employee, "status": ["not in", ["削除済"]]},
		["name", "status"],
		as_dict=True,
		order_by="creation desc",
	)

	if not record:
		return {"success": False, "error": _("マイナンバーが登録されていません。")}

	# Decrypt the My Number from __Auth table
	decrypted = get_decrypted_password("My Number Record", record.name, "my_number")

	# Record access log
	_create_access_log(employee, "閲覧", purpose, record.name)

	return {
		"success": True,
		"employee": employee,
		"my_number": decrypted,
		"record_name": record.name,
	}


@frappe.whitelist()
def check_my_number_status(employee):
	"""Check My Number registration status (no access log).

	Requires HR Manager or System Manager role.
	"""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	record = frappe.db.get_value(
		"My Number Record",
		{"employee": employee, "status": ["not in", ["削除済"]]},
		["name", "status", "collection_date", "valid_until", "verified_by", "verified_date"],
		as_dict=True,
		order_by="creation desc",
	)

	if not record:
		return {
			"success": True,
			"registered": False,
			"employee": employee,
		}

	# Check expiration
	is_expired = False
	if record.valid_until:
		is_expired = frappe.utils.getdate(record.valid_until) < frappe.utils.getdate()

	return {
		"success": True,
		"registered": True,
		"employee": employee,
		"status": record.status,
		"collection_date": str(record.collection_date) if record.collection_date else None,
		"valid_until": str(record.valid_until) if record.valid_until else None,
		"is_expired": is_expired,
		"verified": bool(record.verified_by),
	}
