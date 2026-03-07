# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ResidentTax(Document):
	def validate(self):
		self._calculate_annual_amount()

	def _calculate_annual_amount(self):
		"""Auto-sum monthly amounts to annual total."""
		self.annual_amount = sum(
			int(row.amount or 0) for row in (self.monthly_amounts or [])
		)
