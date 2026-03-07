# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# Default 36 Agreement limits (legal defaults)
DEFAULT_MONTHLY_LIMIT = 45.0
DEFAULT_ANNUAL_LIMIT = 360.0
DEFAULT_ALERT_THRESHOLD_PCT = 80.0


@frappe.whitelist()
def get_active_overtime_agreement(company):
	"""Get the currently active Overtime Agreement for a company."""
	if not company:
		return {"success": False, "error": _("会社を指定してください")}

	today = frappe.utils.today()
	agreement = frappe.db.get_value(
		"Overtime Agreement",
		{
			"company": company,
			"effective_from": ["<=", today],
			"effective_to": [">=", today],
		},
		[
			"name", "agreement_name", "company", "fiscal_year",
			"effective_from", "effective_to",
			"monthly_limit", "annual_limit",
			"special_monthly_limit", "special_annual_limit", "special_months_limit",
			"alert_threshold_pct", "enable_alerts",
		],
		as_dict=True,
		order_by="effective_from desc",
	)

	if not agreement:
		return {
			"success": True,
			"found": False,
			"message": _("有効な36協定が見つかりません。法定デフォルトが適用されます。"),
			"defaults": {
				"monthly_limit": DEFAULT_MONTHLY_LIMIT,
				"annual_limit": DEFAULT_ANNUAL_LIMIT,
			},
		}

	return {
		"success": True,
		"found": True,
		"agreement": agreement,
	}


def _get_overtime_hours(employee, month):
	"""Calculate overtime hours from HRMS attendance data."""
	year, m = month.split("-")
	from_date = f"{year}-{m}-01"
	to_date = str(frappe.utils.get_last_day(from_date))

	attendance = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [from_date, to_date]],
			"status": "Present",
		},
		fields=["attendance_date", "working_hours"],
		order_by="attendance_date asc",
	)

	total_days = len(attendance)
	total_hours = sum(a.working_hours or 0 for a in attendance)
	standard_hours = total_days * 8  # Legal working hours: 8h/day
	overtime_hours = max(0, total_hours - standard_hours)

	return round(overtime_hours, 1)


def _get_annual_overtime_hours(employee, year):
	"""Calculate annual overtime hours from HRMS attendance data."""
	from_date = f"{year}-01-01"
	to_date = f"{year}-12-31"

	attendance = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [from_date, to_date]],
			"status": "Present",
		},
		fields=["attendance_date", "working_hours"],
		order_by="attendance_date asc",
	)

	total_days = len(attendance)
	total_hours = sum(a.working_hours or 0 for a in attendance)
	standard_hours = total_days * 8
	overtime_hours = max(0, total_hours - standard_hours)

	return round(overtime_hours, 1)


def _create_alert(employee, alert_type, overtime_hours, limit_hours, agreement_name=None, month=None, year=None):
	"""Create an Overtime Alert Log entry."""
	alert = frappe.get_doc({
		"doctype": "Overtime Alert Log",
		"employee": employee,
		"alert_type": alert_type,
		"overtime_hours": overtime_hours,
		"limit_hours": limit_hours,
		"overtime_agreement": agreement_name,
		"target_month": month,
		"target_year": year,
	})
	alert.insert(ignore_permissions=True)
	frappe.db.commit()
	return alert.name


@frappe.whitelist()
def check_overtime_against_agreement(employee, month=None):
	"""Check overtime against 36 Agreement limits and generate alerts.

	Falls back to legal defaults (45h/month, 360h/year) if no agreement exists.
	"""
	if not frappe.db.exists("Employee", employee):
		return {"success": False, "error": _("従業員 {0} は存在しません。").format(employee)}

	if not month:
		month = frappe.utils.today()[:7]

	year = int(month.split("-")[0])

	# Get employee's company
	company = frappe.db.get_value("Employee", employee, "company")
	employee_name = frappe.db.get_value("Employee", employee, "employee_name")

	# Get active agreement or use defaults
	monthly_limit = DEFAULT_MONTHLY_LIMIT
	annual_limit = DEFAULT_ANNUAL_LIMIT
	threshold_pct = DEFAULT_ALERT_THRESHOLD_PCT
	enable_alerts = True
	agreement_name = None

	if company:
		today = frappe.utils.today()
		agreement = frappe.db.get_value(
			"Overtime Agreement",
			{
				"company": company,
				"effective_from": ["<=", today],
				"effective_to": [">=", today],
			},
			["name", "monthly_limit", "annual_limit", "alert_threshold_pct", "enable_alerts"],
			as_dict=True,
			order_by="effective_from desc",
		)
		if agreement:
			monthly_limit = agreement.monthly_limit
			annual_limit = agreement.annual_limit
			threshold_pct = agreement.alert_threshold_pct or DEFAULT_ALERT_THRESHOLD_PCT
			enable_alerts = bool(agreement.enable_alerts)
			agreement_name = agreement.name

	# Calculate overtime
	monthly_overtime = _get_overtime_hours(employee, month)
	annual_overtime = _get_annual_overtime_hours(employee, year)

	# Check thresholds and create alerts
	alerts = []
	warnings = []

	if enable_alerts:
		threshold_hours = monthly_limit * (threshold_pct / 100)

		# Monthly checks
		if monthly_overtime > monthly_limit:
			alert_name = _create_alert(
				employee, "月間上限超過", monthly_overtime, monthly_limit,
				agreement_name, month, year,
			)
			alerts.append(alert_name)
			warnings.append(f"月間時間外労働が上限（{monthly_limit}時間）を超えています: {monthly_overtime}時間")
		elif monthly_overtime > threshold_hours:
			alert_name = _create_alert(
				employee, "月間警告", monthly_overtime, monthly_limit,
				agreement_name, month, year,
			)
			alerts.append(alert_name)
			warnings.append(f"月間時間外労働が上限の{threshold_pct}%を超えています: {monthly_overtime}時間")

		# Annual checks
		annual_threshold = annual_limit * (threshold_pct / 100)
		if annual_overtime > annual_limit:
			alert_name = _create_alert(
				employee, "年間上限超過", annual_overtime, annual_limit,
				agreement_name, None, year,
			)
			alerts.append(alert_name)
			warnings.append(f"年間時間外労働が上限（{annual_limit}時間）を超えています: {annual_overtime}時間")
		elif annual_overtime > annual_threshold:
			alert_name = _create_alert(
				employee, "年間警告", annual_overtime, annual_limit,
				agreement_name, None, year,
			)
			alerts.append(alert_name)
			warnings.append(f"年間時間外労働が上限の{threshold_pct}%を超えています: {annual_overtime}時間")

	return {
		"success": True,
		"employee": employee,
		"employee_name": employee_name,
		"month": month,
		"monthly_overtime": monthly_overtime,
		"monthly_limit": monthly_limit,
		"annual_overtime": annual_overtime,
		"annual_limit": annual_limit,
		"agreement": agreement_name,
		"using_defaults": agreement_name is None,
		"warnings": warnings,
		"alerts_created": alerts,
	}


@frappe.whitelist()
def get_overtime_alerts(employee=None, status=None):
	"""Query overtime alert logs with optional filters."""
	filters = {}
	if employee:
		filters["employee"] = employee
	if status:
		filters["status"] = status

	alerts = frappe.get_all(
		"Overtime Alert Log",
		filters=filters,
		fields=[
			"name", "employee", "employee_name", "alert_date", "status",
			"alert_type", "overtime_hours", "limit_hours",
			"overtime_agreement", "target_month", "target_year",
		],
		order_by="alert_date desc",
		limit_page_length=50,
	)

	return {"success": True, "alerts": alerts, "count": len(alerts)}
