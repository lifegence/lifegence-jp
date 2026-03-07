import frappe
from lifegence_jp.bpm.setup.setup_workflow import setup_workflows
from lifegence_jp.bpm.setup.setup_authorization import setup_authorization_rules


def after_install():
	"""Run after app installation to set up BPM workflows and JP HR defaults."""
	try:
		# BPM setup
		setup_workflows()
		setup_authorization_rules()

		# JP HR setup
		_setup_jp_hr_settings()

		frappe.db.commit()
		frappe.msgprint("Lifegence JP: Installation complete.")
	except Exception:
		frappe.log_error("Lifegence JP: Error during post-install setup")
		raise


def _setup_jp_hr_settings():
	"""Create default JP HR Settings if not exists."""
	if frappe.db.exists("JP HR Settings"):
		return

	settings = frappe.new_doc("JP HR Settings")
	settings.employment_insurance_rate_type = "一般"
	settings.auto_calculate_premiums = 1
	settings.fiscal_year_start = "4月"
	settings.save(ignore_permissions=True)
	frappe.logger().info("JP HR: Default settings created")
