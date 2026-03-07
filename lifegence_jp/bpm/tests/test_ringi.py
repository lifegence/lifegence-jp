# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestRingi(FrappeTestCase):
	"""Test cases for Ringi (稟議) DocType and related functionality."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_ringi_template()

	@classmethod
	def _ensure_roles(cls):
		"""Ensure required roles exist."""
		for role_name in ["Ringi Approver", "General Affairs", "Legal Reviewer"]:
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
					"is_custom": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_ringi_template(cls):
		"""Ensure a test Ringi Template exists."""
		if not frappe.db.exists("Ringi Template", "テスト購入テンプレート"):
			template = frappe.get_doc({
				"doctype": "Ringi Template",
				"template_name": "テスト購入テンプレート",
				"ringi_category": "購入",
				"description": "テスト用購入稟議テンプレート",
				"amount_threshold": 1000000,
				"approvers": [
					{
						"approver": "Administrator",
						"approver_name": "Administrator",
						"role": "上長",
						"sequence": 1,
					},
				],
			})
			template.insert(ignore_permissions=True)
		frappe.db.commit()

	# ─── TC-R01: Create basic Ringi ─────────────────────────────────────────

	def test_create_ringi(self):
		"""TC-R01: Create a basic Ringi document."""
		ringi = frappe.get_doc({
			"doctype": "Ringi",
			"ringi_title": "テスト稟議 - 備品購入",
			"ringi_category": "購入",
			"amount": 50000,
			"description": "テスト用の稟議書です。",
			"application_date": frappe.utils.today(),
		})
		ringi.insert(ignore_permissions=True)

		self.assertTrue(ringi.name)
		self.assertEqual(ringi.ringi_title, "テスト稟議 - 備品購入")
		self.assertEqual(ringi.ringi_category, "購入")
		self.assertEqual(ringi.amount, 50000)

	# ─── TC-R02: Ringi naming series ────────────────────────────────────────

	def test_ringi_naming_series(self):
		"""TC-R02: Verify Ringi auto-naming with RINGI-.##### pattern."""
		ringi = frappe.get_doc({
			"doctype": "Ringi",
			"ringi_title": "命名テスト稟議",
			"ringi_category": "その他",
			"application_date": frappe.utils.today(),
		})
		ringi.insert(ignore_permissions=True)

		self.assertTrue(ringi.name.startswith("RINGI-"))

	# ─── TC-R03: Template application ───────────────────────────────────────

	def test_template_application(self):
		"""TC-R03: Verify template approvers are applied on validate."""
		ringi = frappe.get_doc({
			"doctype": "Ringi",
			"ringi_title": "テンプレートテスト稟議",
			"ringi_category": "購入",
			"ringi_template": "テスト購入テンプレート",
			"application_date": frappe.utils.today(),
		})
		ringi.insert(ignore_permissions=True)

		self.assertTrue(len(ringi.approvers) > 0)
		self.assertEqual(ringi.approvers[0].approver, "Administrator")
		self.assertEqual(ringi.approvers[0].role, "上長")
		self.assertEqual(ringi.approvers[0].status, "Pending")

	# ─── TC-R04: Create Ringi Template ──────────────────────────────────────

	def test_create_ringi_template(self):
		"""TC-R04: Create a Ringi Template with approvers."""
		template_name = f"テスト契約テンプレート_{frappe.utils.now_datetime()}"
		template = frappe.get_doc({
			"doctype": "Ringi Template",
			"template_name": template_name,
			"ringi_category": "契約",
			"description": "テスト用契約稟議テンプレート",
			"amount_threshold": 5000000,
			"approvers": [
				{
					"approver": "Administrator",
					"approver_name": "Administrator",
					"role": "部門長",
					"sequence": 1,
				},
			],
		})
		template.insert(ignore_permissions=True)

		self.assertEqual(template.template_name, template_name)
		self.assertEqual(template.ringi_category, "契約")
		self.assertEqual(len(template.approvers), 1)

	# ─── TC-R05: Create General Application ─────────────────────────────────

	def test_create_general_application(self):
		"""TC-R05: Create a General Application document."""
		app = frappe.get_doc({
			"doctype": "General Application",
			"application_title": "住所変更届",
			"application_type": "住所変更",
			"description": "テスト用住所変更届です。",
			"application_date": frappe.utils.today(),
		})
		app.insert(ignore_permissions=True)

		self.assertTrue(app.name.startswith("APP-"))
		self.assertEqual(app.application_title, "住所変更届")
		self.assertEqual(app.application_type, "住所変更")

	# ─── TC-R06: Create Seal Request ────────────────────────────────────────

	def test_create_seal_request(self):
		"""TC-R06: Create a Seal Request document."""
		seal = frappe.get_doc({
			"doctype": "Seal Request",
			"seal_type": "社印",
			"purpose": "テスト契約書への押印",
			"document_type": "契約書",
			"document_reference": "CONTRACT-001",
			"description": "テスト用押印申請です。",
			"request_date": frappe.utils.today(),
		})
		seal.insert(ignore_permissions=True)

		self.assertTrue(seal.name.startswith("SEAL-"))
		self.assertEqual(seal.seal_type, "社印")
		self.assertEqual(seal.purpose, "テスト契約書への押印")

	# ─── TC-R07: Create Application Template ────────────────────────────────

	def test_create_application_template(self):
		"""TC-R07: Create an Application Template."""
		template_name = f"住所変更テンプレート_{frappe.utils.now_datetime()}"
		template = frappe.get_doc({
			"doctype": "Application Template",
			"template_name": template_name,
			"application_type": "住所変更",
			"description": "住所変更届のテンプレート",
			"default_content": "<p>新住所：</p><p>転居日：</p>",
		})
		template.insert(ignore_permissions=True)

		self.assertEqual(template.template_name, template_name)
		self.assertEqual(template.application_type, "住所変更")

	# ─── TC-R08: Ringi approver child table ─────────────────────────────────

	def test_ringi_with_manual_approvers(self):
		"""TC-R08: Create Ringi with manually set approvers."""
		ringi = frappe.get_doc({
			"doctype": "Ringi",
			"ringi_title": "手動承認者テスト",
			"ringi_category": "人事",
			"application_date": frappe.utils.today(),
			"approvers": [
				{
					"approver": "Administrator",
					"approver_name": "Administrator",
					"role": "上長",
					"sequence": 1,
					"status": "Pending",
				},
				{
					"approver": "Administrator",
					"approver_name": "Administrator",
					"role": "部門長",
					"sequence": 2,
					"status": "Pending",
				},
			],
		})
		ringi.insert(ignore_permissions=True)

		self.assertEqual(len(ringi.approvers), 2)
		self.assertEqual(ringi.approvers[0].sequence, 1)
		self.assertEqual(ringi.approvers[1].sequence, 2)

	# ─── TC-R09: Ringi category validation ──────────────────────────────────

	def test_ringi_categories(self):
		"""TC-R09: Verify all Ringi categories are accepted."""
		for category in ["購入", "契約", "人事", "その他"]:
			ringi = frappe.get_doc({
				"doctype": "Ringi",
				"ringi_title": f"カテゴリテスト - {category}",
				"ringi_category": category,
				"application_date": frappe.utils.today(),
			})
			ringi.insert(ignore_permissions=True)
			self.assertEqual(ringi.ringi_category, category)

	# ─── TC-R10: Seal type validation ───────────────────────────────────────

	def test_seal_types(self):
		"""TC-R10: Verify all seal types are accepted."""
		for seal_type in ["社印", "代表印", "角印"]:
			seal = frappe.get_doc({
				"doctype": "Seal Request",
				"seal_type": seal_type,
				"purpose": f"テスト - {seal_type}",
				"request_date": frappe.utils.today(),
			})
			seal.insert(ignore_permissions=True)
			self.assertEqual(seal.seal_type, seal_type)
