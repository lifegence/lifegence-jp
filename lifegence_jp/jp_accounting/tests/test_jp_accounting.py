# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Tests for lifegence_jp_accounting: JP Invoice Settings validation,
Withholding Tax Rule, Withholding Tax Entry tax calculation,
and tax report API.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestJPInvoiceSettings(FrappeTestCase):
    """Test JP Invoice Settings (Single DocType)."""

    def test_settings_exists(self):
        """JP Invoice Settings single should exist."""
        settings = frappe.get_single("JP Invoice Settings")
        self.assertIsNotNone(settings)

    def test_valid_issuer_number(self):
        """Valid T+13 digit issuer number should pass validation."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.qualified_invoice_issuer_number = "T1234567890123"
        settings.save(ignore_permissions=True)

        reloaded = frappe.get_single("JP Invoice Settings")
        self.assertEqual(reloaded.qualified_invoice_issuer_number, "T1234567890123")

    def test_invalid_issuer_number_no_t_prefix(self):
        """Issuer number without T prefix should fail validation."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.qualified_invoice_issuer_number = "1234567890123"

        with self.assertRaises(frappe.ValidationError):
            settings.save(ignore_permissions=True)

    def test_invalid_issuer_number_wrong_length(self):
        """Issuer number with wrong length should fail validation."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.qualified_invoice_issuer_number = "T12345"

        with self.assertRaises(frappe.ValidationError):
            settings.save(ignore_permissions=True)

    def test_invalid_issuer_number_non_digits(self):
        """Issuer number with non-digit characters should fail validation."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.qualified_invoice_issuer_number = "T123456789ABCD"

        with self.assertRaises(frappe.ValidationError):
            settings.save(ignore_permissions=True)

    def test_empty_issuer_number_allowed(self):
        """Empty issuer number should be allowed (optional field)."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.qualified_invoice_issuer_number = ""
        settings.save(ignore_permissions=True)
        # No error means pass

    def test_default_tax_rates(self):
        """Should be able to set default and reduced tax rates."""
        settings = frappe.get_single("JP Invoice Settings")
        settings.default_tax_rate = 10
        settings.reduced_tax_rate = 8
        settings.save(ignore_permissions=True)

        reloaded = frappe.get_single("JP Invoice Settings")
        self.assertEqual(float(reloaded.default_tax_rate), 10.0)
        self.assertEqual(float(reloaded.reduced_tax_rate), 8.0)


class TestWithholdingTaxRule(FrappeTestCase):
    """Test Withholding Tax Rule DocType."""

    def tearDown(self):
        for name in frappe.get_all("Withholding Tax Rule",
                                    filters={"rule_name": ["like", "Test WHT Rule%"]},
                                    pluck="name"):
            frappe.delete_doc("Withholding Tax Rule", name, force=True)
        frappe.db.commit()

    def test_create_rule(self):
        """Should create a withholding tax rule."""
        doc = frappe.get_doc({
            "doctype": "Withholding Tax Rule",
            "rule_name": "Test WHT Rule Basic",
            "income_type": "報酬・料金等",
            "tax_rate": 10.21,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(frappe.db.exists("Withholding Tax Rule", doc.name))

    def test_rule_name_unique(self):
        """rule_name should be unique."""
        frappe.get_doc({
            "doctype": "Withholding Tax Rule",
            "rule_name": "Test WHT Rule Unique",
            "income_type": "報酬・料金等",
            "tax_rate": 10.21,
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        with self.assertRaises(frappe.DuplicateEntryError):
            frappe.get_doc({
                "doctype": "Withholding Tax Rule",
                "rule_name": "Test WHT Rule Unique",
                "income_type": "給与所得",
                "tax_rate": 20,
            }).insert(ignore_permissions=True)


class TestWithholdingTaxEntry(FrappeTestCase):
    """Test Withholding Tax Entry DocType with tax calculation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test rule for tax calculation
        if not frappe.db.exists("Withholding Tax Rule", "Test WHT Rule Calc"):
            frappe.get_doc({
                "doctype": "Withholding Tax Rule",
                "rule_name": "Test WHT Rule Calc",
                "income_type": "報酬・料金等",
                "tax_rate": 10.21,
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def tearDown(self):
        frappe.db.delete("Withholding Tax Entry",
                         {"payee_name": ["like", "Test Payee%"]})
        frappe.db.commit()

    @classmethod
    def tearDownClass(cls):
        if frappe.db.exists("Withholding Tax Rule", "Test WHT Rule Calc"):
            frappe.delete_doc("Withholding Tax Rule", "Test WHT Rule Calc", force=True)
            frappe.db.commit()
        super().tearDownClass()

    def test_tax_calculation(self):
        """Tax amount should be calculated from rule's tax_rate."""
        doc = frappe.get_doc({
            "doctype": "Withholding Tax Entry",
            "payee_name": "Test Payee Calc",
            "withholding_tax_rule": "Test WHT Rule Calc",
            "gross_amount": 100000,
            "payment_date": "2026-01-15",
        })
        doc.insert(ignore_permissions=True)

        self.assertAlmostEqual(float(doc.tax_amount), 10210.0)
        self.assertAlmostEqual(float(doc.net_amount), 89790.0)

    def test_no_rule_no_tax(self):
        """Without a rule, tax_amount should not be set and net = gross."""
        doc = frappe.get_doc({
            "doctype": "Withholding Tax Entry",
            "payee_name": "Test Payee NoRule",
            "gross_amount": 50000,
            "payment_date": "2026-01-15",
        })
        doc.insert(ignore_permissions=True)

        self.assertAlmostEqual(float(doc.net_amount), 50000.0)

    def test_zero_gross_amount(self):
        """Zero gross amount should not cause errors."""
        doc = frappe.get_doc({
            "doctype": "Withholding Tax Entry",
            "payee_name": "Test Payee Zero",
            "withholding_tax_rule": "Test WHT Rule Calc",
            "gross_amount": 0,
            "payment_date": "2026-01-15",
        })
        doc.insert(ignore_permissions=True)
        # No error means pass


class TestTaxReportAPI(FrappeTestCase):
    """Test tax_report API."""

    def test_summary_returns_dict(self):
        """get_withholding_tax_summary should return expected structure."""
        from lifegence_jp_accounting.api.tax_report import get_withholding_tax_summary

        result = get_withholding_tax_summary(year=2026)
        self.assertIsInstance(result, dict)
        self.assertIn("entries", result)
        self.assertIn("total_gross", result)
        self.assertIn("total_tax", result)
        self.assertIn("total_net", result)
        self.assertIn("count", result)

    def test_summary_empty_period(self):
        """Summary should return zeros for period with no submitted entries."""
        from lifegence_jp_accounting.api.tax_report import get_withholding_tax_summary

        result = get_withholding_tax_summary(year=2099)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["total_gross"], 0)
