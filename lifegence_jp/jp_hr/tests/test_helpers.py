# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


def ensure_test_employee(cls):
	"""Ensure test employee exists and set cls.test_employee.

	Use as a classmethod helper in test setUpClass:
		from lifegence_jp.jp_hr.tests.test_helpers import ensure_test_employee

		@classmethod
		def setUpClass(cls):
			super().setUpClass()
			ensure_test_employee(cls)
	"""
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
