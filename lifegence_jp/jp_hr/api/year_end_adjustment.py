# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_employee_year_end_summary(employee, fiscal_year):
	"""Get year-end adjustment summary for an employee."""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	fiscal_year = int(fiscal_year)

	yea = frappe.db.get_value(
		"Year End Adjustment",
		{"employee": employee, "fiscal_year": fiscal_year},
		[
			"name", "status", "total_salary_income", "taxable_income",
			"final_tax", "withheld_total", "adjustment_amount", "adjustment_type",
		],
		as_dict=True,
	)

	if not yea:
		return {
			"success": True,
			"employee": employee,
			"fiscal_year": fiscal_year,
			"year_end_adjustment": None,
			"message": _("年末調整データが見つかりません。"),
		}

	return {
		"success": True,
		"employee": employee,
		"fiscal_year": fiscal_year,
		"year_end_adjustment": yea,
	}


@frappe.whitelist()
def auto_populate_year_end_data(employee, fiscal_year):
	"""Auto-populate salary and social insurance data for year-end adjustment.

	Fetches from Standard Monthly Remuneration records.
	Future HRMS integration will also pull from Salary Slips.
	"""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	fiscal_year = int(fiscal_year)

	# Get latest standard monthly remuneration for social insurance total
	smr = frappe.db.get_value(
		"Standard Monthly Remuneration",
		{"employee": employee},
		["total_employee_premium"],
		as_dict=True,
		order_by="effective_from desc",
	)

	# Estimate annual social insurance from monthly premium * 12
	annual_social_insurance = 0
	if smr and smr.total_employee_premium:
		annual_social_insurance = int(smr.total_employee_premium) * 12

	return {
		"success": True,
		"employee": employee,
		"fiscal_year": fiscal_year,
		"social_insurance_total": annual_social_insurance,
	}
