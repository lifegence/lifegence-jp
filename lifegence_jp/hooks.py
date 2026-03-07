app_name = "lifegence_jp"
app_title = "Lifegence JP"
app_publisher = "Lifegence"
app_description = "Japanese Business Processes - Workflow, HR, Accounting"
app_email = "masakazu@lifegence.co.jp"
app_license = "mit"

required_apps = ["frappe", "erpnext"]

export_python_type_annotations = True

add_to_apps_screen = [
	{
		"name": "lifegence_bpm",
		"logo": "/assets/lifegence_jp/images/logo_bpm.svg",
		"title": "ワークフロー",
		"route": "/app/bpm",
	},
	{
		"name": "lifegence_jp_hr",
		"logo": "/assets/lifegence_jp/images/logo_jp_hr.svg",
		"title": "人事労務",
		"route": "/app/jp-hr",
	},
	{
		"name": "lifegence_jp_accounting",
		"logo": "/assets/lifegence_jp/images/logo_jp_accounting.svg",
		"title": "会計",
		"route": "/app/jp-accounting",
	},
]

# Lifecycle Hooks
after_install = "lifegence_jp.install.after_install"

# DocType Events
doc_events = {
	"*": {
		"on_update": "lifegence_jp.bpm.automation.dispatcher.on_document_update",
	}
}

# Fixtures
fixtures = [
	# --- BPM fixtures ---
	{
		"dt": "Workflow",
		"filters": [["name", "in", [
			"Lead Approval",
			"Opportunity Approval",
			"Quotation Approval",
			"Sales Order Approval",
			"Purchase Order Approval",
			"Ringi Approval",
			"Seal Request Approval",
			"General Application Approval",
		]]],
	},
	{
		"dt": "Role",
		"filters": [["name", "in", [
			"CRM Approver",
			"Approval Manager",
			"Approval Director",
			"Approval Executive",
			"Budget Controller",
			"Ringi Approver",
			"General Affairs",
			"Legal Reviewer",
		]]],
	},
	{
		"dt": "Workflow State",
		"filters": [["name", "in", [
			"Draft", "Pending Review", "Pending Manager Approval",
			"Pending Director Approval", "Pending Executive Approval",
			"Pending Budget Check", "Approved", "Rejected", "Cancelled",
			"Qualified", "Unqualified", "Converted", "Lost", "Confirmed", "Submitted",
			"Pending Supervisor Approval", "Pending Department Head Approval",
			"Pending Legal Review", "Pending General Affairs",
			"Pending HR Review", "Completed",
		]]],
	},
	{
		"dt": "Workflow Action Master",
		"filters": [["name", "in", [
			"Submit for Review", "Approve", "Reject", "Request Changes",
			"Escalate to Director", "Escalate to Executive",
			"Qualify", "Disqualify", "Mark as Lost", "Convert",
			"Confirm", "Submit for Budget Check", "Pass Budget Check", "Cancel",
			"Submit for Approval", "Return", "Complete",
		]]],
	},
	{
		"dt": "Authorization Rule",
		"filters": [["approving_role", "in", [
			"Sales Manager", "Approval Manager", "Approval Director", "Approval Executive",
		]]],
	},
	"BPM Settings",
	"BPM Action",
	"Ringi Template",
	"Application Template",
	# --- JP HR fixtures ---
	"JP HR Settings",
	{
		"dt": "Social Insurance Rate",
		"filters": [["rate_name", "like", "令和%"]],
	},
	{
		"dt": "Withholding Tax Table",
		"filters": [["table_name", "like", "令和%"]],
	},
	{
		"dt": "Overtime Agreement",
		"filters": [["agreement_name", "like", "%"]],
	},
	# --- JP Accounting fixtures ---
	"JP Invoice Settings",
]
