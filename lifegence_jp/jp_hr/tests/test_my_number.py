# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMyNumber(FrappeTestCase):
	"""Test cases for My Number Record and Access Log."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_employee()

	@classmethod
	def _ensure_employee(cls):
		"""Ensure test employee exists (reuse pattern from test_social_insurance)."""
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

	def _create_my_number_record(self, my_number="123456789012", **kwargs):
		"""Helper to create a My Number Record."""
		doc = frappe.get_doc({
			"doctype": "My Number Record",
			"employee": self.test_employee,
			"my_number": my_number,
			"purpose": "社会保障・税の手続き",
			**kwargs,
		})
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-MN01: Create My Number Record ──────────────────────────────────

	def test_create_my_number_record(self):
		"""TC-MN01: Create a My Number Record with encryption and naming series."""
		record = self._create_my_number_record()

		self.assertTrue(record.name.startswith("MN-"))
		self.assertEqual(record.status, "収集済")
		self.assertEqual(record.employee, self.test_employee)

	# ─── TC-MN02: Masked display ───────────────────────────────────────────

	def test_masked_display(self):
		"""TC-MN02: Verify my_number_masked is in ****-****-XXXX format."""
		record = self._create_my_number_record(my_number="123456789012")

		self.assertEqual(record.my_number_masked, "****-****-9012")

	# ─── TC-MN03: Access log on masked read ────────────────────────────────

	def test_access_log_on_masked_read(self):
		"""TC-MN03: get_my_number_masked() creates an access log."""
		self._create_my_number_record()

		from lifegence_jp.jp_hr.api.my_number import get_my_number_masked
		result = get_my_number_masked(employee=self.test_employee)

		self.assertTrue(result["success"])
		self.assertIn("****", result["my_number_masked"])

		# Verify access log was created
		logs = frappe.get_all(
			"My Number Access Log",
			filters={"employee": self.test_employee, "access_type": "閲覧"},
			limit=1,
		)
		self.assertGreater(len(logs), 0)

	# ─── TC-MN04: Full access decryption ───────────────────────────────────

	def test_full_access_decryption(self):
		"""TC-MN04: access_my_number() returns decrypted value and logs access."""
		self._create_my_number_record(my_number="111122223333")

		from lifegence_jp.jp_hr.api.my_number import access_my_number
		result = access_my_number(employee=self.test_employee, purpose="年末調整処理")

		self.assertTrue(result["success"])
		self.assertEqual(result["my_number"], "111122223333")

		# Verify access log was created with correct purpose
		logs = frappe.get_all(
			"My Number Access Log",
			filters={"employee": self.test_employee, "purpose": ["like", "%年末調整%"]},
			limit=1,
		)
		self.assertGreater(len(logs), 0)

	# ─── TC-MN05: Access log append-only ────────────────────────────────────

	def test_access_log_append_only(self):
		"""TC-MN05: Access Log cannot be updated or deleted."""
		log = frappe.get_doc({
			"doctype": "My Number Access Log",
			"employee": self.test_employee,
			"accessed_by": frappe.session.user,
			"accessed_at": frappe.utils.now_datetime(),
			"access_type": "閲覧",
			"purpose": "テスト",
		})
		log.insert(ignore_permissions=True)
		frappe.db.commit()

		# Try to update → should fail
		log.purpose = "変更テスト"
		self.assertRaises(frappe.ValidationError, log.save, ignore_permissions=True)

		# Try to delete → should fail
		self.assertRaises(frappe.ValidationError, log.delete, ignore_permissions=True)

	# ─── TC-MN06: Status check no log ──────────────────────────────────────

	def test_status_check_no_log(self):
		"""TC-MN06: check_my_number_status() does not create access log."""
		self._create_my_number_record()

		# Count logs before
		before_count = frappe.db.count("My Number Access Log", {"employee": self.test_employee})

		from lifegence_jp.jp_hr.api.my_number import check_my_number_status
		result = check_my_number_status(employee=self.test_employee)

		self.assertTrue(result["success"])
		self.assertTrue(result["registered"])

		# Count logs after - should be same
		after_count = frappe.db.count("My Number Access Log", {"employee": self.test_employee})
		self.assertEqual(before_count, after_count)

	# ─── TC-MN07: Expired detection ────────────────────────────────────────

	def test_expired_detection(self):
		"""TC-MN07: Detect expired My Number when valid_until is in the past."""
		self._create_my_number_record(valid_until="2020-01-01")

		from lifegence_jp.jp_hr.api.my_number import check_my_number_status
		result = check_my_number_status(employee=self.test_employee)

		self.assertTrue(result["success"])
		self.assertTrue(result["is_expired"])

	# ─── TC-MN08: Encryption in __Auth table ────────────────────────────────

	def test_encryption_in_auth_table(self):
		"""TC-MN08: Verify My Number is stored encrypted in __Auth table."""
		record = self._create_my_number_record(my_number="999988887777")

		# The Password field stores the value in __Auth table, not in the main table
		# Verify the raw value is not in the DocType table
		raw_in_table = frappe.db.get_value("My Number Record", record.name, "my_number")
		# Password fields return '***' or empty from the main table
		self.assertNotEqual(raw_in_table, "999988887777")

		# But decryption should work
		from frappe.utils.password import get_decrypted_password
		decrypted = get_decrypted_password("My Number Record", record.name, "my_number")
		self.assertEqual(decrypted, "999988887777")
