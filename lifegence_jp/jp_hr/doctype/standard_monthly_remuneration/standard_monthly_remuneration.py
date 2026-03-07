# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StandardMonthlyRemuneration(Document):
	def validate(self):
		if self.insurance_rate and self.standard_monthly_amount:
			self._calculate_premiums()

	def _calculate_premiums(self):
		"""Calculate insurance premiums from standard monthly amount and rate table."""
		rate = frappe.get_doc("Social Insurance Rate", self.insurance_rate)
		amount = self.standard_monthly_amount

		# Health insurance (employee portion)
		self.health_insurance_premium = round(amount * (rate.health_insurance_employee or 0) / 100)

		# Nursing care insurance (40-64 years old)
		self.nursing_care_premium = round(amount * (rate.nursing_care_rate or 0) / 100 / 2)

		# Pension (employee portion)
		self.pension_premium = round(amount * (rate.pension_employee or 0) / 100)

		# Totals
		self.total_employee_premium = (
			self.health_insurance_premium
			+ self.nursing_care_premium
			+ self.pension_premium
		)

		# Employer portion
		health_employer = round(amount * ((rate.health_insurance_rate or 0) - (rate.health_insurance_employee or 0)) / 100)
		nursing_employer = round(amount * (rate.nursing_care_rate or 0) / 100 / 2)
		pension_employer = round(amount * ((rate.pension_rate or 0) - (rate.pension_employee or 0)) / 100)
		self.total_employer_premium = health_employer + nursing_employer + pension_employer
