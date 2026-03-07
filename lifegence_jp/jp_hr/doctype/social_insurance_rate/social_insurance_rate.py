# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SocialInsuranceRate(Document):
	def validate(self):
		if self.effective_to and self.effective_from > self.effective_to:
			frappe.throw("適用終了日は適用開始日より後の日付を指定してください。")
