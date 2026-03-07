# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_employee_labor_insurance(employee):
	"""Get labor insurance summary for an employee."""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	employee_name = frappe.db.get_value("Employee", employee, "employee_name")

	# Latest labor insurance record
	record = frappe.db.get_value(
		"Labor Insurance Record",
		{"employee": employee},
		[
			"name", "record_type", "effective_date",
			"employment_insurance_number", "employment_insurance_status",
			"employment_insurance_type",
			"workers_comp_status", "insurance_category", "workers_comp_rate",
		],
		as_dict=True,
		order_by="effective_date desc",
	)

	return {
		"success": True,
		"employee": employee,
		"employee_name": employee_name,
		"labor_insurance": record or {},
		"has_record": bool(record),
	}
