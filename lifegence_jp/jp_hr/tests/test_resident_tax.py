# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from lifegence_jp.jp_hr.tests.test_helpers import ensure_test_employee
from frappe.tests.utils import FrappeTestCase


MONTHS_CYCLE = ["6月", "7月", "8月", "9月", "10月", "11月", "12月", "1月", "2月", "3月", "4月", "5月"]


class TestResidentTax(FrappeTestCase):
	"""Test cases for Resident Tax DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_test_employee(cls)

	# ─── TC-RT01: Create Resident Tax with 12 monthly entries ───────────────

	def test_create_resident_tax(self):
		"""TC-RT01: Create resident tax with 12 monthly amounts."""
		monthly = []
		for month in MONTHS_CYCLE:
			amount = 25000 if month == "6月" else 20000
			monthly.append({"month": month, "amount": amount})

		doc = frappe.get_doc({
			"doctype": "Resident Tax",
			"employee": self.test_employee,
			"fiscal_year": 2026,
			"municipality": "東京都渋谷区",
			"monthly_amounts": monthly,
		})
		doc.insert(ignore_permissions=True)

		self.assertTrue(doc.name.startswith("RES-TAX-"))
		self.assertEqual(len(doc.monthly_amounts), 12)

	# ─── TC-RT02: Annual amount auto-sum ────────────────────────────────────

	def test_annual_amount_auto_sum(self):
		"""TC-RT02: Annual amount should equal sum of monthly amounts."""
		monthly = []
		for month in MONTHS_CYCLE:
			amount = 25000 if month == "6月" else 20000
			monthly.append({"month": month, "amount": amount})

		doc = frappe.get_doc({
			"doctype": "Resident Tax",
			"employee": self.test_employee,
			"fiscal_year": 2026,
			"municipality": "東京都港区",
			"monthly_amounts": monthly,
		})
		doc.insert(ignore_permissions=True)

		# 25000 (June) + 20000 * 11 = 245000
		expected_annual = 25000 + 20000 * 11
		self.assertEqual(doc.annual_amount, expected_annual)

	# ─── TC-RT03: Monthly months cycle ──────────────────────────────────────

	def test_monthly_months_cycle(self):
		"""TC-RT03: Verify all 12 months (June-May) are represented."""
		monthly = [{"month": m, "amount": 20000} for m in MONTHS_CYCLE]

		doc = frappe.get_doc({
			"doctype": "Resident Tax",
			"employee": self.test_employee,
			"fiscal_year": 2026,
			"municipality": "東京都新宿区",
			"monthly_amounts": monthly,
		})
		doc.insert(ignore_permissions=True)

		inserted_months = [row.month for row in doc.monthly_amounts]
		self.assertEqual(inserted_months, MONTHS_CYCLE)
		self.assertEqual(len(inserted_months), 12)
