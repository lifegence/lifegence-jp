# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MyNumberRecord(Document):
	def before_save(self):
		self._set_masked_number()

	def _set_masked_number(self):
		"""Generate masked display: ****-****-XXXX format."""
		# Password field stores encrypted value; we generate mask from raw input
		# On first save, self.my_number contains the raw value
		raw = self.my_number
		if raw and len(raw) >= 4:
			last4 = raw[-4:]
			self.my_number_masked = f"****-****-{last4}"
		elif raw:
			self.my_number_masked = "****-****-****"
