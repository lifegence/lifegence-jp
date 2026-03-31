# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from lifegence_jp.jp_hr.tests.test_helpers import ensure_test_employee
from frappe.tests.utils import FrappeTestCase


class TestSocialInsurance(FrappeTestCase):
	"""Test cases for Social Insurance DocTypes and calculation logic."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_insurance_rate()
		ensure_test_employee(cls)

	@classmethod
	def _ensure_insurance_rate(cls):
		"""Ensure test insurance rate exists."""
		if not frappe.db.exists("Social Insurance Rate", "テスト料率_東京"):
			frappe.get_doc({
				"doctype": "Social Insurance Rate",
				"rate_name": "テスト料率_東京",
				"effective_from": "2024-04-01",
				"prefecture": "東京都",
				"health_insurance_rate": 9.98,
				"health_insurance_employee": 4.99,
				"nursing_care_rate": 1.60,
				"pension_rate": 18.3,
				"pension_employee": 9.15,
				"employment_insurance_employee": 0.6,
				"employment_insurance_employer": 0.95,
			}).insert(ignore_permissions=True)
			frappe.db.commit()

	# ─── TC-SI01: Create Social Insurance Rate ──────────────────────────────

	def test_create_insurance_rate(self):
		"""TC-SI01: Create a social insurance rate record."""
		rate_name = f"テスト料率_{frappe.utils.now_datetime()}"
		rate = frappe.get_doc({
			"doctype": "Social Insurance Rate",
			"rate_name": rate_name,
			"effective_from": "2024-04-01",
			"prefecture": "テスト県",
			"health_insurance_rate": 10.0,
			"health_insurance_employee": 5.0,
			"nursing_care_rate": 1.60,
			"pension_rate": 18.3,
			"pension_employee": 9.15,
			"employment_insurance_employee": 0.6,
			"employment_insurance_employer": 0.95,
		})
		rate.insert(ignore_permissions=True)

		self.assertEqual(rate.name, rate_name)
		self.assertEqual(rate.health_insurance_rate, 10.0)
		self.assertEqual(rate.pension_rate, 18.3)

	# ─── TC-SI02: Rate date validation ──────────────────────────────────────

	def test_rate_date_validation(self):
		"""TC-SI02: Verify effective_to must be after effective_from."""
		rate = frappe.get_doc({
			"doctype": "Social Insurance Rate",
			"rate_name": f"日付テスト_{frappe.utils.now_datetime()}",
			"effective_from": "2024-04-01",
			"effective_to": "2024-03-01",  # Before effective_from
			"health_insurance_rate": 10.0,
			"health_insurance_employee": 5.0,
		})

		self.assertRaises(frappe.ValidationError, rate.insert, ignore_permissions=True)

	# ─── TC-SI03: Create Social Insurance Record ────────────────────────────

	def test_create_insurance_record(self):
		"""TC-SI03: Create a social insurance record."""
		record = frappe.get_doc({
			"doctype": "Social Insurance Record",
			"employee": self.test_employee,
			"record_type": "資格取得",
			"effective_date": "2024-04-01",
			"health_insurance_number": "12345678",
			"health_insurance_status": "加入",
			"pension_number": "1234-567890",
			"pension_status": "加入",
		})
		record.insert(ignore_permissions=True)

		self.assertTrue(record.name.startswith("SI-REC-"))
		self.assertEqual(record.record_type, "資格取得")

	# ─── TC-SI04: Create Standard Monthly Remuneration ──────────────────────

	def test_create_standard_monthly_remuneration(self):
		"""TC-SI04: Create standard monthly remuneration record."""
		smr = frappe.get_doc({
			"doctype": "Standard Monthly Remuneration",
			"employee": self.test_employee,
			"effective_from": "2024-09-01",
			"total_remuneration": 300000,
			"remuneration_grade": 22,
			"standard_monthly_amount": 300000,
			"insurance_rate": "テスト料率_東京",
			"calculation_type": "算定基礎",
		})
		smr.insert(ignore_permissions=True)

		self.assertTrue(smr.name.startswith("SMR-"))
		self.assertEqual(smr.standard_monthly_amount, 300000)

	# ─── TC-SI05: Premium auto-calculation ──────────────────────────────────

	def test_premium_calculation(self):
		"""TC-SI05: Verify insurance premiums are auto-calculated correctly."""
		smr = frappe.get_doc({
			"doctype": "Standard Monthly Remuneration",
			"employee": self.test_employee,
			"effective_from": "2024-09-01",
			"total_remuneration": 300000,
			"remuneration_grade": 22,
			"standard_monthly_amount": 300000,
			"insurance_rate": "テスト料率_東京",
			"calculation_type": "算定基礎",
		})
		smr.insert(ignore_permissions=True)

		# Health insurance: 300000 * 4.99% = 14970
		self.assertEqual(smr.health_insurance_premium, 14970)

		# Nursing care: 300000 * 1.60% / 2 = 2400
		self.assertEqual(smr.nursing_care_premium, 2400)

		# Pension: 300000 * 9.15% = 27450
		self.assertEqual(smr.pension_premium, 27450)

		# Total employee: 14970 + 2400 + 27450 = 44820
		self.assertEqual(smr.total_employee_premium, 44820)

		# Employer portion should also be calculated
		self.assertGreater(smr.total_employer_premium, 0)

	# ─── TC-SI06: Create Remuneration Calculation ───────────────────────────

	def test_create_remuneration_calculation(self):
		"""TC-SI06: Create a remuneration calculation record."""
		calc = frappe.get_doc({
			"doctype": "Remuneration Calculation",
			"employee": self.test_employee,
			"calculation_type": "算定基礎",
			"target_year": 2024,
			"period_from": "2024-04-01",
			"period_to": "2024-06-30",
			"month1_days": 20,
			"month1_amount": 280000,
			"month2_days": 21,
			"month2_amount": 300000,
			"month3_days": 20,
			"month3_amount": 290000,
		})
		calc.insert(ignore_permissions=True)

		self.assertTrue(calc.name.startswith("REM-CALC-"))
		self.assertEqual(calc.calculation_type, "算定基礎")
		self.assertEqual(calc.status, "Draft")

	# ─── TC-SI07: Remuneration calculation logic ────────────────────────────

	def test_remuneration_calculation_logic(self):
		"""TC-SI07: Verify average remuneration and grade calculation."""
		calc = frappe.get_doc({
			"doctype": "Remuneration Calculation",
			"employee": self.test_employee,
			"calculation_type": "算定基礎",
			"target_year": 2024,
			"period_from": "2024-04-01",
			"period_to": "2024-06-30",
			"month1_days": 20,
			"month1_amount": 280000,
			"month2_days": 21,
			"month2_amount": 300000,
			"month3_days": 20,
			"month3_amount": 290000,
		})
		calc.insert(ignore_permissions=True)

		result = calc.calculate()

		# Average: (280000 + 300000 + 290000) / 3 = 290000
		self.assertEqual(calc.average_remuneration, 290000)
		self.assertEqual(calc.status, "Calculated")

		# Grade 22: 290000 >= 290000 → standard monthly = 300000
		self.assertEqual(calc.new_grade, 22)
		self.assertEqual(calc.new_standard_monthly, 300000)

	# ─── TC-SI08: Calculation with low-days month ───────────────────────────

	def test_calculation_excludes_low_days(self):
		"""TC-SI08: Months with < 17 base days should be excluded."""
		calc = frappe.get_doc({
			"doctype": "Remuneration Calculation",
			"employee": self.test_employee,
			"calculation_type": "算定基礎",
			"target_year": 2024,
			"period_from": "2024-04-01",
			"period_to": "2024-06-30",
			"month1_days": 10,  # < 17, should be excluded
			"month1_amount": 150000,
			"month2_days": 21,
			"month2_amount": 300000,
			"month3_days": 20,
			"month3_amount": 290000,
		})
		calc.insert(ignore_permissions=True)

		result = calc.calculate()

		# Only month2 and month3 should be included
		# Average: (300000 + 290000) / 2 = 295000
		self.assertEqual(calc.average_remuneration, 295000)

	# ─── TC-SI09: Period date validation ────────────────────────────────────

	def test_period_date_validation(self):
		"""TC-SI09: period_to must be after period_from."""
		calc = frappe.get_doc({
			"doctype": "Remuneration Calculation",
			"employee": self.test_employee,
			"calculation_type": "算定基礎",
			"target_year": 2024,
			"period_from": "2024-06-30",
			"period_to": "2024-04-01",  # Before period_from
		})

		self.assertRaises(frappe.ValidationError, calc.insert, ignore_permissions=True)

	# ─── TC-SI10: JP HR Settings defaults ───────────────────────────────────

	def test_jp_hr_settings_defaults(self):
		"""TC-SI10: Verify JP HR Settings can be saved with defaults."""
		# JP HR Settings is a Single DocType
		settings = frappe.get_doc("JP HR Settings")
		settings.employment_insurance_rate_type = "一般"
		settings.auto_calculate_premiums = 1
		settings.fiscal_year_start = "4月"
		settings.save(ignore_permissions=True)

		reloaded = frappe.get_doc("JP HR Settings")
		self.assertEqual(reloaded.employment_insurance_rate_type, "一般")
		self.assertEqual(reloaded.auto_calculate_premiums, 1)
