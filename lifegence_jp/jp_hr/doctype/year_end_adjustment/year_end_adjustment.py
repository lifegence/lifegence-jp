# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


def calc_salary_income_deduction(income):
	"""Calculate salary income deduction (給与所得控除).

	Based on NTA tax table for FY2024+.
	"""
	income = int(income or 0)
	if income <= 1625000:
		return 550000
	elif income <= 1800000:
		return int(income * 0.4 - 100000)
	elif income <= 3600000:
		return int(income * 0.3 + 80000)
	elif income <= 6600000:
		return int(income * 0.2 + 440000)
	elif income <= 8500000:
		return int(income * 0.1 + 1100000)
	else:
		return 1950000


def calc_income_tax(taxable_income):
	"""Calculate income tax amount (所得税額).

	Based on NTA progressive tax rates.
	"""
	taxable = int(taxable_income or 0)
	if taxable <= 0:
		return 0
	elif taxable <= 1950000:
		return int(taxable * 0.05)
	elif taxable <= 3300000:
		return int(taxable * 0.10 - 97500)
	elif taxable <= 6950000:
		return int(taxable * 0.20 - 427500)
	elif taxable <= 9000000:
		return int(taxable * 0.23 - 636000)
	elif taxable <= 18000000:
		return int(taxable * 0.33 - 1536000)
	elif taxable <= 40000000:
		return int(taxable * 0.40 - 2796000)
	else:
		return int(taxable * 0.45 - 4796000)


class YearEndAdjustment(Document):
	@frappe.whitelist()
	def calculate(self):
		"""Execute full year-end adjustment calculation."""
		income = int(self.total_salary_income or 0)

		# 1. Salary income deduction
		self.salary_income_deduction = calc_salary_income_deduction(income)

		# 2. Salary income amount
		self.salary_income_amount = max(0, income - self.salary_income_deduction)

		# 3. Total income
		total_income = self.salary_income_amount + int(self.other_income or 0)

		# 4. Total deductions from child table + social insurance + small enterprise
		deduction_sum = sum(int(d.amount or 0) for d in (self.deductions or []))
		social_ins = int(self.social_insurance_total or 0)
		small_ent = int(self.small_enterprise_mutual or 0)
		self.total_deductions = deduction_sum + social_ins + small_ent

		# 5. Taxable income (1000 yen truncation)
		taxable_raw = max(0, total_income - self.total_deductions)
		self.taxable_income = (taxable_raw // 1000) * 1000

		# 6. Calculated tax
		self.calculated_tax = calc_income_tax(self.taxable_income)

		# 7. Tax after housing loan deduction (100 yen truncation)
		housing = int(self.housing_loan_deduction or 0)
		tax_after_housing = max(0, self.calculated_tax - housing)
		tax_after_housing = (tax_after_housing // 100) * 100

		# 8. Reconstruction special income tax (復興特別所得税 2.1%)
		reconstruction_tax = int(tax_after_housing * 0.021)
		reconstruction_tax = (reconstruction_tax // 100) * 100

		# 9. Final tax
		self.final_tax = tax_after_housing + reconstruction_tax

		# 10. Adjustment amount
		withheld = int(self.withheld_total or 0)
		self.adjustment_amount = withheld - self.final_tax

		# 11. Adjustment type
		if self.adjustment_amount > 0:
			self.adjustment_type = "還付"
		elif self.adjustment_amount < 0:
			self.adjustment_type = "徴収"
		else:
			self.adjustment_type = ""

		self.status = "Calculated"
		self.save()

		return {
			"salary_income_deduction": self.salary_income_deduction,
			"taxable_income": self.taxable_income,
			"calculated_tax": self.calculated_tax,
			"final_tax": self.final_tax,
			"adjustment_amount": self.adjustment_amount,
			"adjustment_type": self.adjustment_type,
		}
