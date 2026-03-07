# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WithholdingTaxTable(Document):
	def validate(self):
		if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
			frappe.throw(_("適用終了日は適用開始日より後の日付を指定してください。"))
