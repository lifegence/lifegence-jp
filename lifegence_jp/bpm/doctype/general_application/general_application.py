# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GeneralApplication(Document):
	def validate(self):
		if not self.applicant:
			employee = frappe.db.get_value(
				"Employee",
				{"user_id": frappe.session.user, "status": "Active"},
				"name",
			)
			if employee:
				self.applicant = employee
