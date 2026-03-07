# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def calculate_monthly_withholding(monthly_salary, dependents=0, table_type="甲"):
	"""Calculate monthly withholding tax amount.

	Args:
		monthly_salary: Monthly salary (yen)
		dependents: Number of dependents (0-7)
		table_type: "甲" or "乙"

	Returns:
		dict with tax amount and calculation details
	"""
	from lifegence_jp.jp_hr.jp_hr.doctype.withholding_tax_table.withholding_tax_data import (
		get_withholding_tax,
	)

	monthly_salary = float(monthly_salary)
	dependents = int(dependents)

	tax = get_withholding_tax(monthly_salary, dependents, table_type)

	return {
		"success": True,
		"monthly_salary": int(monthly_salary),
		"dependents": dependents,
		"table_type": table_type,
		"withholding_tax": tax,
	}


@frappe.whitelist()
def get_employee_annual_withholding(employee, fiscal_year):
	"""Get total withholding tax already deducted for an employee in a fiscal year.

	This is a placeholder that returns manually-entered data from Year End Adjustment.
	Future HRMS integration will pull from Salary Slips.
	"""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	fiscal_year = int(fiscal_year)

	# Check if Year End Adjustment exists
	yea = frappe.db.get_value(
		"Year End Adjustment",
		{"employee": employee, "fiscal_year": fiscal_year},
		["name", "withheld_total", "status"],
		as_dict=True,
	)

	return {
		"success": True,
		"employee": employee,
		"fiscal_year": fiscal_year,
		"year_end_adjustment": yea or {},
	}
