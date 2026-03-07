# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document


# Workers' compensation insurance rates by industry category (‰, FY2024 basis)
WORKERS_COMP_RATES = {
	"一般": 3.0,       # Other businesses
	"建設": 9.5,       # Construction (average)
	"農林水産": 13.0,  # Agriculture/Forestry/Fishery (average)
	"清酒製造": 6.5,   # Sake manufacturing
}


class LaborInsuranceRecord(Document):
	def before_save(self):
		self._set_workers_comp_rate()

	def _set_workers_comp_rate(self):
		"""Auto-set workers' compensation rate based on insurance category."""
		if self.insurance_category:
			self.workers_comp_rate = WORKERS_COMP_RATES.get(self.insurance_category, 3.0)
