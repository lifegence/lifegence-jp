# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from lifegence_jp_hr.jp_hr.doctype.year_end_adjustment.year_end_adjustment import (
	calc_salary_income_deduction,
	calc_income_tax,
)


class TestYearEndAdjustment(FrappeTestCase):
	"""Test cases for Year End Adjustment calculation logic."""

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

	# ─── TC-YEA01: Create Year End Adjustment ───────────────────────────────

	def test_create_year_end_adjustment(self):
		"""TC-YEA01: Create and verify naming series."""
		doc = frappe.get_doc({
			"doctype": "Year End Adjustment",
			"employee": self.test_employee,
			"fiscal_year": 2025,
			"total_salary_income": 5000000,
		})
		doc.insert(ignore_permissions=True)

		self.assertTrue(doc.name.startswith("YEA-"))
		self.assertEqual(doc.status, "Draft")

	# ─── TC-YEA02: Salary income deduction - low income ────────────────────

	def test_salary_income_deduction_low(self):
		"""TC-YEA02: income ≤ 1,625,000 → deduction 550,000."""
		self.assertEqual(calc_salary_income_deduction(1500000), 550000)
		self.assertEqual(calc_salary_income_deduction(1625000), 550000)

	# ─── TC-YEA03: Salary income deduction - mid income ────────────────────

	def test_salary_income_deduction_mid(self):
		"""TC-YEA03: income = 5,000,000 → deduction 1,440,000."""
		# 5,000,000 * 20% + 440,000 = 1,440,000
		self.assertEqual(calc_salary_income_deduction(5000000), 1440000)

	# ─── TC-YEA04: Salary income deduction - cap ───────────────────────────

	def test_salary_income_deduction_cap(self):
		"""TC-YEA04: income > 8,500,000 → deduction cap 1,950,000."""
		self.assertEqual(calc_salary_income_deduction(10000000), 1950000)
		self.assertEqual(calc_salary_income_deduction(20000000), 1950000)

	# ─── TC-YEA05: Full calculation flow ───────────────────────────────────

	def test_full_calculation(self):
		"""TC-YEA05: Full year-end adjustment calculation with income 5M + basic deduction."""
		doc = frappe.get_doc({
			"doctype": "Year End Adjustment",
			"employee": self.test_employee,
			"fiscal_year": 2025,
			"total_salary_income": 5000000,
			"deductions": [
				{
					"deduction_type": "基礎控除",
					"amount": 480000,
				},
			],
			"withheld_total": 200000,
		})
		doc.insert(ignore_permissions=True)

		result = doc.calculate()

		# Salary income deduction: 5,000,000 * 20% + 440,000 = 1,440,000
		self.assertEqual(doc.salary_income_deduction, 1440000)

		# Salary income amount: 5,000,000 - 1,440,000 = 3,560,000
		self.assertEqual(doc.salary_income_amount, 3560000)

		# Total deductions: 480,000 (basic)
		self.assertEqual(doc.total_deductions, 480000)

		# Taxable income: 3,560,000 - 480,000 = 3,080,000 (1000 yen truncation)
		self.assertEqual(doc.taxable_income, 3080000)

		# Calculated tax: 3,080,000 * 10% - 97,500 = 210,500
		self.assertEqual(doc.calculated_tax, 210500)

		self.assertEqual(doc.status, "Calculated")

	# ─── TC-YEA06: Refund case ─────────────────────────────────────────────

	def test_refund_case(self):
		"""TC-YEA06: withheld > final_tax → 還付 (refund)."""
		doc = frappe.get_doc({
			"doctype": "Year End Adjustment",
			"employee": self.test_employee,
			"fiscal_year": 2025,
			"total_salary_income": 3000000,
			"deductions": [
				{"deduction_type": "基礎控除", "amount": 480000},
			],
			"withheld_total": 100000,  # Higher than expected tax
		})
		doc.insert(ignore_permissions=True)
		doc.calculate()

		# Low income → low tax, withheld 100K should be more than final tax
		self.assertEqual(doc.adjustment_type, "還付")
		self.assertGreater(doc.adjustment_amount, 0)

	# ─── TC-YEA07: Additional collection case ──────────────────────────────

	def test_additional_collection(self):
		"""TC-YEA07: withheld < final_tax → 徴収 (additional collection)."""
		doc = frappe.get_doc({
			"doctype": "Year End Adjustment",
			"employee": self.test_employee,
			"fiscal_year": 2025,
			"total_salary_income": 8000000,
			"deductions": [
				{"deduction_type": "基礎控除", "amount": 480000},
			],
			"withheld_total": 10000,  # Very low withheld amount
		})
		doc.insert(ignore_permissions=True)
		doc.calculate()

		# High income, low withheld → additional collection
		self.assertEqual(doc.adjustment_type, "徴収")
		self.assertLess(doc.adjustment_amount, 0)
