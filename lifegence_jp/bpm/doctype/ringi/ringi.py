# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from lifegence_jp.bpm.utils import get_current_employee


class Ringi(Document):
	def validate(self):
		self._set_applicant_info()
		self._apply_template()

	def _set_applicant_info(self):
		"""Auto-set applicant from current user's employee record."""
		if not self.applicant:
			employee = get_current_employee()
			if employee:
				self.applicant = employee

	def _apply_template(self):
		"""Apply template approvers if template is set and approvers list is empty."""
		if self.ringi_template and not self.approvers:
			template = frappe.get_doc("Ringi Template", self.ringi_template)
			for ta in template.approvers:
				self.append("approvers", {
					"approver": ta.approver,
					"approver_name": ta.approver_name,
					"role": ta.role,
					"sequence": ta.sequence,
					"status": "Pending",
				})
