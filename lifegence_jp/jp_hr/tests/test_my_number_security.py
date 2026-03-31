# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMyNumberSecurity(FrappeTestCase):
	"""Security tests for My Number API role checks."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_employee()
		cls._ensure_test_users()

	@classmethod
	def _ensure_employee(cls):
		"""Ensure test employee exists."""
		if not frappe.db.exists("Employee", {"employee_name": "セキュリティテスト太郎"}):
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
				"employee_name": "セキュリティテスト太郎",
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
				"Employee", {"employee_name": "セキュリティテスト太郎"}, "name"
			)

	@classmethod
	def _ensure_test_users(cls):
		"""Ensure test users with specific roles exist."""
		# Unprivileged user (no HR Manager or System Manager)
		cls.unprivileged_user = "unprivileged-mn-test@example.com"
		if not frappe.db.exists("User", cls.unprivileged_user):
			user = frappe.get_doc({
				"doctype": "User",
				"email": cls.unprivileged_user,
				"first_name": "Unprivileged",
				"enabled": 1,
				"roles": [{"role": "Employee"}],
			})
			user.insert(ignore_permissions=True)
			frappe.db.commit()

		# HR Manager user
		cls.hr_manager_user = "hr-manager-mn-test@example.com"
		if not frappe.db.exists("User", cls.hr_manager_user):
			user = frappe.get_doc({
				"doctype": "User",
				"email": cls.hr_manager_user,
				"first_name": "HRManager",
				"enabled": 1,
				"roles": [{"role": "HR Manager"}, {"role": "Employee"}],
			})
			user.insert(ignore_permissions=True)
			frappe.db.commit()

	# --- TC-MN-S01: get_my_number_masked rejects unprivileged user ---

	def test_get_my_number_masked_rejects_unprivileged(self):
		"""TC-MN-S01: Unprivileged user cannot call get_my_number_masked."""
		from lifegence_jp.jp_hr.api.my_number import get_my_number_masked

		frappe.set_user(self.unprivileged_user)
		try:
			with self.assertRaises(frappe.PermissionError):
				get_my_number_masked(employee=self.test_employee)
		finally:
			frappe.set_user("Administrator")

	# --- TC-MN-S02: check_my_number_status rejects unprivileged user ---

	def test_check_my_number_status_rejects_unprivileged(self):
		"""TC-MN-S02: Unprivileged user cannot call check_my_number_status."""
		from lifegence_jp.jp_hr.api.my_number import check_my_number_status

		frappe.set_user(self.unprivileged_user)
		try:
			with self.assertRaises(frappe.PermissionError):
				check_my_number_status(employee=self.test_employee)
		finally:
			frappe.set_user("Administrator")

	# --- TC-MN-S03: get_my_number_masked allows HR Manager ---

	def test_get_my_number_masked_allows_hr_manager(self):
		"""TC-MN-S03: HR Manager can call get_my_number_masked."""
		# Create a My Number Record first
		if not frappe.db.exists("My Number Record", {"employee": self.test_employee, "status": ["not in", ["削除済"]]}):
			frappe.get_doc({
				"doctype": "My Number Record",
				"employee": self.test_employee,
				"my_number": "123456789012",
				"purpose": "テスト",
			}).insert(ignore_permissions=True)
			frappe.db.commit()

		from lifegence_jp.jp_hr.api.my_number import get_my_number_masked

		frappe.set_user(self.hr_manager_user)
		try:
			result = get_my_number_masked(employee=self.test_employee)
			self.assertTrue(result["success"])
		finally:
			frappe.set_user("Administrator")

	# --- TC-MN-S04: check_my_number_status allows HR Manager ---

	def test_check_my_number_status_allows_hr_manager(self):
		"""TC-MN-S04: HR Manager can call check_my_number_status."""
		from lifegence_jp.jp_hr.api.my_number import check_my_number_status

		frappe.set_user(self.hr_manager_user)
		try:
			result = check_my_number_status(employee=self.test_employee)
			self.assertTrue(result["success"])
		finally:
			frappe.set_user("Administrator")

	# --- TC-MN-S05: Administrator can still access ---

	def test_administrator_can_access(self):
		"""TC-MN-S05: Administrator (System Manager) can access both endpoints."""
		from lifegence_jp.jp_hr.api.my_number import (
			check_my_number_status,
			get_my_number_masked,
		)

		frappe.set_user("Administrator")
		# Should not raise
		result1 = get_my_number_masked(employee=self.test_employee)
		result2 = check_my_number_status(employee=self.test_employee)
		# Just verify no exception was thrown
		self.assertIsNotNone(result1)
		self.assertIsNotNone(result2)
