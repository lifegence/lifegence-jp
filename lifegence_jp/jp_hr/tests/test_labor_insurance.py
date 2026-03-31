# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from lifegence_jp.jp_hr.tests.test_helpers import ensure_test_employee
from frappe.tests.utils import FrappeTestCase


class TestLaborInsurance(FrappeTestCase):
	"""Test cases for Labor Insurance Record."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_test_employee(cls)

	# ─── TC-LI01: Create Labor Insurance Record ────────────────────────────

	def test_create_labor_insurance_record(self):
		"""TC-LI01: Create a Labor Insurance Record with naming series."""
		record = frappe.get_doc({
			"doctype": "Labor Insurance Record",
			"employee": self.test_employee,
			"record_type": "資格取得",
			"effective_date": "2024-04-01",
			"employment_insurance_number": "1234-567890-1",
			"employment_insurance_status": "加入",
			"employment_insurance_type": "一般被保険者",
			"workers_comp_status": "適用",
			"insurance_category": "一般",
		})
		record.insert(ignore_permissions=True)

		self.assertTrue(record.name.startswith("LI-REC-"))
		self.assertEqual(record.record_type, "資格取得")

	# ─── TC-LI02: Employment insurance enrollment ──────────────────────────

	def test_employment_insurance_enrollment(self):
		"""TC-LI02: Verify employment insurance enrollment fields."""
		record = frappe.get_doc({
			"doctype": "Labor Insurance Record",
			"employee": self.test_employee,
			"record_type": "資格取得",
			"effective_date": "2024-04-01",
			"employment_insurance_number": "9876-543210-2",
			"employment_insurance_status": "加入",
			"employment_insurance_type": "高年齢被保険者",
		})
		record.insert(ignore_permissions=True)

		self.assertEqual(record.employment_insurance_number, "9876-543210-2")
		self.assertEqual(record.employment_insurance_status, "加入")
		self.assertEqual(record.employment_insurance_type, "高年齢被保険者")

	# ─── TC-LI03: Workers' comp rate by category ───────────────────────────

	def test_workers_comp_rate_by_category(self):
		"""TC-LI03: Verify auto-set workers' compensation rate by category."""
		from lifegence_jp.jp_hr.doctype.labor_insurance_record.labor_insurance_record import WORKERS_COMP_RATES

		for category, expected_rate in [("一般", 3.0), ("建設", 9.5), ("農林水産", 13.0), ("清酒製造", 6.5)]:
			record = frappe.get_doc({
				"doctype": "Labor Insurance Record",
				"employee": self.test_employee,
				"record_type": "資格取得",
				"effective_date": "2024-04-01",
				"workers_comp_status": "適用",
				"insurance_category": category,
			})
			record.insert(ignore_permissions=True)

			self.assertEqual(
				record.workers_comp_rate, expected_rate,
				f"Rate for {category}: expected {expected_rate}, got {record.workers_comp_rate}"
			)

	# ─── TC-LI04: Get employee labor insurance API ─────────────────────────

	def test_get_employee_labor_insurance_api(self):
		"""TC-LI04: Verify API response format."""
		# Create a record first
		frappe.get_doc({
			"doctype": "Labor Insurance Record",
			"employee": self.test_employee,
			"record_type": "資格取得",
			"effective_date": "2024-04-01",
			"employment_insurance_number": "API-TEST-001",
			"employment_insurance_status": "加入",
			"workers_comp_status": "適用",
			"insurance_category": "一般",
		}).insert(ignore_permissions=True)

		from lifegence_jp.jp_hr.api.labor_insurance import get_employee_labor_insurance
		result = get_employee_labor_insurance(employee=self.test_employee)

		self.assertTrue(result["success"])
		self.assertEqual(result["employee"], self.test_employee)
		self.assertTrue(result["has_record"])
		self.assertIn("labor_insurance", result)
		self.assertEqual(result["labor_insurance"]["employment_insurance_status"], "加入")
