# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from lifegence_jp.jp_hr.jp_hr.doctype.withholding_tax_table.withholding_tax_data import (
	get_withholding_tax,
)


class TestWithholdingTax(FrappeTestCase):
	"""Test cases for Withholding Tax Table and tax lookup logic."""

	# ─── TC-WT01: Create Withholding Tax Table ──────────────────────────────

	def test_create_withholding_tax_table(self):
		"""TC-WT01: Create a withholding tax table record with autoname."""
		table_name = f"テスト税額表_{frappe.utils.now_datetime()}"
		doc = frappe.get_doc({
			"doctype": "Withholding Tax Table",
			"table_name": table_name,
			"effective_from": "2025-01-01",
			"tax_table_type": "月額表",
			"kou_enabled": 1,
			"otsu_enabled": 1,
		})
		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.name, table_name)
		self.assertEqual(doc.tax_table_type, "月額表")

	# ─── TC-WT02: Date validation ───────────────────────────────────────────

	def test_date_validation(self):
		"""TC-WT02: Verify effective_to must be after effective_from."""
		doc = frappe.get_doc({
			"doctype": "Withholding Tax Table",
			"table_name": f"日付テスト_{frappe.utils.now_datetime()}",
			"effective_from": "2025-01-01",
			"effective_to": "2024-12-31",  # Before effective_from
			"tax_table_type": "月額表",
		})

		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	# ─── TC-WT03: 甲欄 basic lookup ────────────────────────────────────────

	def test_kou_tax_lookup_basic(self):
		"""TC-WT03: 甲欄 300,000円・扶養0人 → tax amount check."""
		tax = get_withholding_tax(300000, dependents=0, table_type="甲")

		# 299,000-302,000 range, dep_0 = 12280
		self.assertEqual(tax, 12280)

	# ─── TC-WT04: 甲欄 with dependents ──────────────────────────────────────

	def test_kou_tax_lookup_with_dependents(self):
		"""TC-WT04: 甲欄 300,000円・扶養2人 → lower tax than dep_0."""
		tax_0 = get_withholding_tax(300000, dependents=0, table_type="甲")
		tax_2 = get_withholding_tax(300000, dependents=2, table_type="甲")

		# With 2 dependents, tax should be 0 (in 299,000-302,000 range, dep_2 = 0)
		self.assertEqual(tax_2, 0)
		self.assertGreater(tax_0, tax_2)

	# ─── TC-WT05: 乙欄 lookup ──────────────────────────────────────────────

	def test_otsu_tax_lookup(self):
		"""TC-WT05: 乙欄 300,000円 → higher tax than 甲欄."""
		tax_kou = get_withholding_tax(300000, dependents=0, table_type="甲")
		tax_otsu = get_withholding_tax(300000, dependents=0, table_type="乙")

		# 乙欄 should always be higher than 甲欄
		# 299,000-302,000 range: otsu = 33700
		self.assertEqual(tax_otsu, 33700)
		self.assertGreater(tax_otsu, tax_kou)
