# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeAgreement(Document):
	def validate(self):
		self._validate_dates()
		self._validate_special_limits()

	def _validate_dates(self):
		"""Ensure effective_to > effective_from."""
		if self.effective_from and self.effective_to:
			if self.effective_to <= self.effective_from:
				frappe.throw(_("有効終了日は有効開始日より後でなければなりません"))

	def _validate_special_limits(self):
		"""Validate special clause limits against legal maximums."""
		if self.special_monthly_limit and self.special_monthly_limit > 100:
			frappe.throw(_("特別条項の月間上限は100時間を超えることはできません（法定上限）"))
		if self.special_annual_limit and self.special_annual_limit > 720:
			frappe.throw(_("特別条項の年間上限は720時間を超えることはできません（法定上限）"))
		if self.special_months_limit and self.special_months_limit > 6:
			frappe.throw(_("特別条項の適用月数は年6回を超えることはできません"))
