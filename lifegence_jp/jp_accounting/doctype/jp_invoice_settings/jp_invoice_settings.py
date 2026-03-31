import frappe
from frappe.model.document import Document


class JPInvoiceSettings(Document):
	def validate(self):
		if self.qualified_invoice_issuer_number:
			num = self.qualified_invoice_issuer_number.strip()
			if not (num.startswith("T") and len(num) == 14 and num[1:].isdigit()):
				frappe.throw("Qualified Invoice Issuer Number must be T followed by 13 digits")
