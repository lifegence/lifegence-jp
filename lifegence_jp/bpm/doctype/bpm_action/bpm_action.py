import frappe
from frappe.model.document import Document


class BPMAction(Document):
	def validate(self):
		self._validate_action_type_fields()
		self._validate_condition()

	def _validate_action_type_fields(self):
		if self.action_type in ("Webhook", "Frappe API"):
			if not self.url:
				frappe.throw("URL is required for action type: " + self.action_type)
		if self.action_type == "n8n Workflow" and not self.url:
			settings = frappe.get_cached_doc("BPM Settings")
			if not settings.n8n_base_url:
				frappe.throw("URL is required, or set n8n Base URL in BPM Settings")

	def _validate_condition(self):
		if self.condition:
			try:
				# Validate syntax only (compile, don't execute)
				compile(self.condition, "<condition>", "eval")
			except SyntaxError as e:
				frappe.throw(f"Invalid condition syntax: {e}")
