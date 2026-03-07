import frappe
from frappe.model.document import Document


class BPMSettings(Document):
	def validate(self):
		if self.default_timeout and self.default_timeout < 1:
			frappe.throw("Default timeout must be at least 1 second")
		if self.max_retry_count and self.max_retry_count < 0:
			frappe.throw("Max retry count cannot be negative")
		if self.log_retention_days and self.log_retention_days < 1:
			frappe.throw("Log retention days must be at least 1")
