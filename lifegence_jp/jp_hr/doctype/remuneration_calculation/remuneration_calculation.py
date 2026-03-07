# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


# Standard Monthly Remuneration grade table (厚生年金・健康保険 等級表)
# Grade: (lower_bound, standard_monthly_amount)
GRADE_TABLE = [
	(1, 0, 58000),
	(2, 63000, 68000),
	(3, 73000, 78000),
	(4, 83000, 88000),
	(5, 93000, 98000),
	(6, 101000, 104000),
	(7, 107000, 110000),
	(8, 114000, 118000),
	(9, 122000, 126000),
	(10, 130000, 134000),
	(11, 138000, 142000),
	(12, 146000, 150000),
	(13, 155000, 160000),
	(14, 165000, 170000),
	(15, 175000, 180000),
	(16, 185000, 190000),
	(17, 195000, 200000),
	(18, 210000, 220000),
	(19, 230000, 240000),
	(20, 250000, 260000),
	(21, 270000, 280000),
	(22, 290000, 300000),
	(23, 310000, 320000),
	(24, 330000, 340000),
	(25, 350000, 360000),
	(26, 370000, 380000),
	(27, 395000, 410000),
	(28, 425000, 440000),
	(29, 455000, 470000),
	(30, 485000, 500000),
	(31, 515000, 530000),
	(32, 545000, 560000),
	(33, 575000, 590000),
	(34, 605000, 620000),
	(35, 635000, 650000),
	(36, 665000, 680000),
	(37, 695000, 710000),
	(38, 730000, 750000),
	(39, 770000, 790000),
	(40, 810000, 830000),
	(41, 855000, 880000),
	(42, 905000, 930000),
	(43, 955000, 980000),
	(44, 1005000, 1030000),
	(45, 1055000, 1090000),
	(46, 1115000, 1150000),
	(47, 1175000, 1210000),
	(48, 1235000, 1270000),
	(49, 1295000, 1330000),
	(50, 1355000, 1390000),
]


def get_grade_and_amount(average_remuneration):
	"""Determine the grade and standard monthly amount from average remuneration."""
	for grade, lower, standard in reversed(GRADE_TABLE):
		if average_remuneration >= lower:
			return grade, standard
	return 1, 58000


class RemunerationCalculation(Document):
	def validate(self):
		if self.period_from and self.period_to and self.period_from > self.period_to:
			frappe.throw(_("対象期間終了は対象期間開始より後の日付を指定してください。"))

	@frappe.whitelist()
	def calculate(self):
		"""Calculate average remuneration and determine new grade."""
		months = []
		min_days = 17  # Minimum payment base days for inclusion

		for i in range(1, 4):
			days = getattr(self, f"month{i}_days", 0) or 0
			amount = getattr(self, f"month{i}_amount", 0) or 0
			if days >= min_days:
				months.append(amount)

		if not months:
			frappe.throw(_("支払基礎日数が17日以上の月がありません。"))

		self.average_remuneration = round(sum(months) / len(months))
		self.new_grade, self.new_standard_monthly = get_grade_and_amount(self.average_remuneration)

		# Get current standard monthly if employee has one
		current = frappe.db.get_value(
			"Standard Monthly Remuneration",
			{"employee": self.employee},
			"standard_monthly_amount",
			order_by="effective_from desc",
		)
		self.current_standard_monthly = current or 0
		self.status = "Calculated"
		self.save()

		return {
			"average_remuneration": self.average_remuneration,
			"new_grade": self.new_grade,
			"new_standard_monthly": self.new_standard_monthly,
			"current_standard_monthly": self.current_standard_monthly,
		}
