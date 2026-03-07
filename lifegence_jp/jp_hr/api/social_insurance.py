# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_active_rate(prefecture=None, date=None):
	"""Get the currently active social insurance rate table."""
	date = date or frappe.utils.today()

	filters = {
		"effective_from": ["<=", date],
	}
	or_filters = [
		["effective_to", ">=", date],
		["effective_to", "is", "not set"],
	]

	if prefecture:
		filters["prefecture"] = prefecture

	rates = frappe.get_all(
		"Social Insurance Rate",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "rate_name", "prefecture", "effective_from", "effective_to",
			"health_insurance_rate", "health_insurance_employee",
			"nursing_care_rate", "pension_rate", "pension_employee",
			"employment_insurance_employee", "employment_insurance_employer",
		],
		order_by="effective_from desc",
		limit_page_length=1,
	)

	if not rates:
		return {"success": False, "error": _("有効な社会保険料率が見つかりません。")}

	return {"success": True, "rate": rates[0]}


@frappe.whitelist()
def calculate_premiums(standard_monthly_amount, rate_name=None, include_nursing_care=True):
	"""Calculate social insurance premiums from standard monthly amount."""
	standard_monthly_amount = float(standard_monthly_amount)
	include_nursing_care = frappe.utils.sbool(include_nursing_care)

	if rate_name:
		rate = frappe.get_doc("Social Insurance Rate", rate_name)
	else:
		# Get latest active rate
		result = get_active_rate()
		if not result.get("success"):
			return result
		rate = frappe.get_doc("Social Insurance Rate", result["rate"]["name"])

	health_employee = round(standard_monthly_amount * (rate.health_insurance_employee or 0) / 100)
	health_employer = round(
		standard_monthly_amount * ((rate.health_insurance_rate or 0) - (rate.health_insurance_employee or 0)) / 100
	)

	nursing_employee = 0
	nursing_employer = 0
	if include_nursing_care:
		nursing_employee = round(standard_monthly_amount * (rate.nursing_care_rate or 0) / 100 / 2)
		nursing_employer = round(standard_monthly_amount * (rate.nursing_care_rate or 0) / 100 / 2)

	pension_employee = round(standard_monthly_amount * (rate.pension_employee or 0) / 100)
	pension_employer = round(
		standard_monthly_amount * ((rate.pension_rate or 0) - (rate.pension_employee or 0)) / 100
	)

	total_employee = health_employee + nursing_employee + pension_employee
	total_employer = health_employer + nursing_employer + pension_employer

	return {
		"success": True,
		"standard_monthly_amount": standard_monthly_amount,
		"rate_name": rate.name,
		"health_insurance": {"employee": health_employee, "employer": health_employer},
		"nursing_care": {"employee": nursing_employee, "employer": nursing_employer},
		"pension": {"employee": pension_employee, "employer": pension_employer},
		"total_employee": total_employee,
		"total_employer": total_employer,
		"total": total_employee + total_employer,
	}


@frappe.whitelist()
def get_employee_insurance_summary(employee):
	"""Get social insurance summary for an employee."""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	# Latest standard monthly remuneration
	smr = frappe.db.get_value(
		"Standard Monthly Remuneration",
		{"employee": employee},
		[
			"name", "standard_monthly_amount", "remuneration_grade",
			"effective_from", "total_employee_premium", "total_employer_premium",
		],
		as_dict=True,
		order_by="effective_from desc",
	)

	# Latest insurance record
	record = frappe.db.get_value(
		"Social Insurance Record",
		{"employee": employee},
		["name", "record_type", "effective_date", "health_insurance_status", "pension_status"],
		as_dict=True,
		order_by="effective_date desc",
	)

	return {
		"success": True,
		"employee": employee,
		"standard_monthly_remuneration": smr or {},
		"insurance_record": record or {},
	}
