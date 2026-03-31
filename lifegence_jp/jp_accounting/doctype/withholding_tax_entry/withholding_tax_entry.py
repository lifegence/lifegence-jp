import frappe
from frappe.model.document import Document


class WithholdingTaxEntry(Document):
	def validate(self):
		self.calculate_tax()

	def calculate_tax(self):
		if self.withholding_tax_rule and self.gross_amount:
			rule = frappe.get_doc("Withholding Tax Rule", self.withholding_tax_rule)
			self.tax_amount = self.gross_amount * (rule.tax_rate / 100)
			self.net_amount = self.gross_amount - self.tax_amount
		elif self.gross_amount:
			self.net_amount = self.gross_amount
