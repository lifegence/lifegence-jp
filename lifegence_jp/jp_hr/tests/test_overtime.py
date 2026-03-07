# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestOvertime(FrappeTestCase):
	"""Test cases for Overtime Agreement and Alert Log."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_employee()

	@classmethod
	def _ensure_employee(cls):
		"""Ensure test employee exists."""
		if not frappe.db.exists("Employee", {"employee_name": "テスト太郎"}):
			if not frappe.db.exists("Company", "テスト株式会社"):
				frappe.get_doc({
					"doctype": "Company",
					"company_name": "テスト株式会社",
					"abbr": "TST",
					"country": "Japan",
					"default_currency": "JPY",
				}).insert(ignore_permissions=True)

			emp = frappe.get_doc({
				"doctype": "Employee",
				"employee_name": "テスト太郎",
				"first_name": "太郎",
				"company": "テスト株式会社",
				"status": "Active",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-04-01",
			})
			emp.insert(ignore_permissions=True)
			cls.test_employee = emp.name
			frappe.db.commit()
		else:
			cls.test_employee = frappe.db.get_value(
				"Employee", {"employee_name": "テスト太郎"}, "name"
			)

	def setUp(self):
		"""Clean up test agreements before each test to avoid conflicts."""
		# Delete all test agreements to ensure a clean state
		for name in frappe.get_all("Overtime Agreement", filters={"agreement_name": ["like", "テスト協定_%"]}, pluck="name"):
			frappe.delete_doc("Overtime Agreement", name, force=True)
		frappe.db.commit()

	def _create_agreement(self, **kwargs):
		"""Helper to create a test Overtime Agreement."""
		defaults = {
			"doctype": "Overtime Agreement",
			"agreement_name": f"テスト協定_{frappe.utils.now_datetime().isoformat()}",
			"company": "テスト株式会社",
			"fiscal_year": 2026,
			"effective_from": "2026-01-01",
			"effective_to": "2026-12-31",
			"monthly_limit": 45,
			"annual_limit": 360,
			"special_monthly_limit": 80,
			"special_annual_limit": 720,
			"special_months_limit": 6,
			"alert_threshold_pct": 80,
			"enable_alerts": 1,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _create_attendance(self, date, working_hours=8):
		"""Helper to create attendance record."""
		if frappe.db.exists("Attendance", {"employee": self.test_employee, "attendance_date": date}):
			frappe.db.delete("Attendance", {"employee": self.test_employee, "attendance_date": date})

		att = frappe.get_doc({
			"doctype": "Attendance",
			"employee": self.test_employee,
			"attendance_date": date,
			"status": "Present",
			"working_hours": working_hours,
		})
		att.insert(ignore_permissions=True)
		return att

	# ─── TC-OT01: Create Overtime Agreement ─────────────────────────────────

	def test_create_overtime_agreement(self):
		"""TC-OT01: Create an Overtime Agreement with autoname."""
		agreement = self._create_agreement(
			agreement_name="テスト協定_OT01",
		)

		self.assertEqual(agreement.name, "テスト協定_OT01")
		self.assertEqual(agreement.monthly_limit, 45)
		self.assertEqual(agreement.annual_limit, 360)

	# ─── TC-OT02: Date validation ───────────────────────────────────────────

	def test_date_validation(self):
		"""TC-OT02: effective_to must be after effective_from."""
		self.assertRaises(
			frappe.ValidationError,
			self._create_agreement,
			agreement_name="テスト協定_OT02",
			effective_from="2026-12-31",
			effective_to="2026-01-01",
		)

	# ─── TC-OT03: Special limit validation ──────────────────────────────────

	def test_special_limit_validation(self):
		"""TC-OT03: special_monthly_limit must not exceed 100."""
		self.assertRaises(
			frappe.ValidationError,
			self._create_agreement,
			agreement_name="テスト協定_OT03",
			special_monthly_limit=101,
		)

	# ─── TC-OT04: No alert under threshold ──────────────────────────────────

	def test_no_alert_under_threshold(self):
		"""TC-OT04: 20h overtime should not trigger any alert."""
		self._create_agreement(agreement_name="テスト協定_OT04")

		# Create attendance with 20h overtime (20 days * 9h = 20h overtime)
		for day in range(1, 21):
			self._create_attendance(f"2026-03-{day:02d}", working_hours=9)

		from lifegence_jp.jp_hr.api.overtime import check_overtime_against_agreement
		result = check_overtime_against_agreement(
			employee=self.test_employee, month="2026-03",
		)

		self.assertTrue(result["success"])
		self.assertEqual(result["monthly_overtime"], 20.0)
		self.assertEqual(len(result["alerts_created"]), 0)

	# ─── TC-OT05: Warning at threshold ──────────────────────────────────────

	def test_warning_at_threshold(self):
		"""TC-OT05: Overtime exceeding 80% threshold triggers warning."""
		self._create_agreement(
			agreement_name="テスト協定_OT05",
			monthly_limit=45,
			alert_threshold_pct=80,
		)

		# 20 days at 9.85h each = 20*(9.85-8) = 37h overtime (> 45*0.8=36)
		for day in range(1, 21):
			self._create_attendance(f"2026-04-{day:02d}", working_hours=9.85)

		from lifegence_jp.jp_hr.api.overtime import check_overtime_against_agreement
		result = check_overtime_against_agreement(
			employee=self.test_employee, month="2026-04",
		)

		self.assertTrue(result["success"])
		self.assertGreater(result["monthly_overtime"], 36)
		self.assertGreater(len(result["warnings"]), 0)
		self.assertGreater(len(result["alerts_created"]), 0)

	# ─── TC-OT06: Exceeded alert ────────────────────────────────────────────

	def test_exceeded_alert(self):
		"""TC-OT06: Overtime exceeding monthly limit triggers exceeded alert."""
		self._create_agreement(
			agreement_name="テスト協定_OT06",
			monthly_limit=45,
		)

		# 20 days * 10.5h = 50h overtime (> 45h limit)
		for day in range(1, 21):
			self._create_attendance(f"2026-05-{day:02d}", working_hours=10.5)

		from lifegence_jp.jp_hr.api.overtime import check_overtime_against_agreement
		result = check_overtime_against_agreement(
			employee=self.test_employee, month="2026-05",
		)

		self.assertTrue(result["success"])
		self.assertGreater(result["monthly_overtime"], 45)
		self.assertGreater(len(result["alerts_created"]), 0)
		has_exceeded = any("超えています" in w for w in result["warnings"])
		self.assertTrue(has_exceeded)

	# ─── TC-OT07: Alert log fields ──────────────────────────────────────────

	def test_alert_log_fields(self):
		"""TC-OT07: Verify alert log fields are correctly populated."""
		alert = frappe.get_doc({
			"doctype": "Overtime Alert Log",
			"employee": self.test_employee,
			"alert_type": "月間警告",
			"overtime_hours": 38.5,
			"limit_hours": 45,
			"target_month": "2026-03",
			"target_year": 2026,
		})
		alert.insert(ignore_permissions=True)

		self.assertTrue(alert.name.startswith("OT-ALERT-"))
		self.assertEqual(alert.status, "Open")
		self.assertEqual(alert.alert_type, "月間警告")
		self.assertEqual(alert.overtime_hours, 38.5)
		self.assertEqual(alert.limit_hours, 45)

	# ─── TC-OT08: Fallback without agreement ────────────────────────────────

	def test_fallback_without_agreement(self):
		"""TC-OT08: Without agreement, defaults to 45h/360h."""
		# Ensure no active agreement for a different company
		if not frappe.db.exists("Company", "別会社テスト"):
			frappe.get_doc({
				"doctype": "Company",
				"company_name": "別会社テスト",
				"abbr": "BTS",
				"country": "Japan",
				"default_currency": "JPY",
			}).insert(ignore_permissions=True)

		# Create employee with no agreement
		if not frappe.db.exists("Employee", {"employee_name": "テスト次郎"}):
			emp = frappe.get_doc({
				"doctype": "Employee",
				"employee_name": "テスト次郎",
				"first_name": "次郎",
				"company": "別会社テスト",
				"status": "Active",
				"gender": "Male",
				"date_of_birth": "1992-05-15",
				"date_of_joining": "2021-04-01",
			})
			emp.insert(ignore_permissions=True)
			test_emp2 = emp.name
		else:
			test_emp2 = frappe.db.get_value(
				"Employee", {"employee_name": "テスト次郎"}, "name"
			)

		from lifegence_jp.jp_hr.api.overtime import check_overtime_against_agreement
		result = check_overtime_against_agreement(
			employee=test_emp2, month="2026-06",
		)

		self.assertTrue(result["success"])
		self.assertTrue(result["using_defaults"])
		self.assertEqual(result["monthly_limit"], 45)
		self.assertEqual(result["annual_limit"], 360)
