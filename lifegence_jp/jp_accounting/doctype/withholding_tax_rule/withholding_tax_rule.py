import frappe
from frappe.model.document import Document


class WithholdingTaxRule(Document):
    def validate(self):
        if self.tax_rate and (self.tax_rate < 0 or self.tax_rate > 100):
            frappe.throw("Tax rate must be between 0 and 100")
