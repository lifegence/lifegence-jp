# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from lifegence_jp.bpm.utils import get_current_employee


class GeneralApplication(Document):
	def validate(self):
		if not self.applicant:
			employee = get_current_employee()
			if employee:
				self.applicant = employee
