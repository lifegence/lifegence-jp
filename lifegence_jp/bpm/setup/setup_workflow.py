import frappe


# ─── Custom Roles ────────────────────────────────────────────────────────────
CUSTOM_ROLES = [
	"CRM Approver",
	"Approval Manager",
	"Approval Director",
	"Approval Executive",
	"Budget Controller",
	"Ringi Approver",
	"General Affairs",
	"Legal Reviewer",
	"HR Manager",
	"HR User",
]


# ─── Workflow States ─────────────────────────────────────────────────────────
WORKFLOW_STATES = [
	{"state": "Draft", "style": ""},
	{"state": "Pending Review", "style": "Warning"},
	{"state": "Pending Manager Approval", "style": "Warning"},
	{"state": "Pending Director Approval", "style": "Warning"},
	{"state": "Pending Executive Approval", "style": "Warning"},
	{"state": "Pending Budget Check", "style": "Warning"},
	{"state": "Approved", "style": "Success"},
	{"state": "Rejected", "style": "Danger"},
	{"state": "Cancelled", "style": "Danger"},
	{"state": "Qualified", "style": "Success"},
	{"state": "Unqualified", "style": "Inverse"},
	{"state": "Converted", "style": "Primary"},
	{"state": "Lost", "style": "Inverse"},
	{"state": "Confirmed", "style": "Success"},
	{"state": "Submitted", "style": "Primary"},
	{"state": "Pending Supervisor Approval", "style": "Warning"},
	{"state": "Pending Department Head Approval", "style": "Warning"},
	{"state": "Pending Legal Review", "style": "Warning"},
	{"state": "Pending General Affairs", "style": "Warning"},
	{"state": "Pending HR Review", "style": "Warning"},
	{"state": "Completed", "style": "Success"},
]


# ─── Workflow Action Masters ─────────────────────────────────────────────────
WORKFLOW_ACTIONS = [
	"Submit for Review",
	"Approve",
	"Reject",
	"Request Changes",
	"Escalate to Director",
	"Escalate to Executive",
	"Qualify",
	"Disqualify",
	"Mark as Lost",
	"Convert",
	"Confirm",
	"Submit for Budget Check",
	"Pass Budget Check",
	"Cancel",
	"Submit for Approval",
	"Return",
	"Complete",
]


# ─── Workflow Definitions ────────────────────────────────────────────────────

LEAD_WORKFLOW = {
	"workflow_name": "Lead Approval",
	"document_type": "Lead",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{
			"state": "Draft",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Review",
			"doc_status": 0,
			"allow_edit": "CRM Approver",
			"is_optional_state": 0,
		},
		{
			"state": "Qualified",
			"doc_status": 0,
			"allow_edit": "CRM Approver",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Interested",
		},
		{
			"state": "Unqualified",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Do Not Contact",
		},
		{
			"state": "Converted",
			"doc_status": 0,
			"allow_edit": "CRM Approver",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Converted",
		},
	],
	"transitions": [
		{
			"state": "Draft",
			"action": "Submit for Review",
			"next_state": "Pending Review",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Review",
			"action": "Qualify",
			"next_state": "Qualified",
			"allowed": "CRM Approver",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Review",
			"action": "Disqualify",
			"next_state": "Unqualified",
			"allowed": "CRM Approver",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Review",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "CRM Approver",
			"allow_self_approval": 0,
		},
		{
			"state": "Qualified",
			"action": "Convert",
			"next_state": "Converted",
			"allowed": "CRM Approver",
			"allow_self_approval": 0,
		},
		{
			"state": "Unqualified",
			"action": "Submit for Review",
			"next_state": "Pending Review",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
	],
}


OPPORTUNITY_WORKFLOW = {
	"workflow_name": "Opportunity Approval",
	"document_type": "Opportunity",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{
			"state": "Draft",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Manager Approval",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Approved",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Open",
		},
		{
			"state": "Rejected",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Closed",
		},
		{
			"state": "Converted",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Converted",
		},
		{
			"state": "Lost",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
			"update_field": "status",
			"update_value": "Lost",
		},
	],
	"transitions": [
		{
			"state": "Draft",
			"action": "Submit for Review",
			"next_state": "Pending Manager Approval",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Approved",
			"action": "Convert",
			"next_state": "Converted",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Approved",
			"action": "Mark as Lost",
			"next_state": "Lost",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Rejected",
			"action": "Submit for Review",
			"next_state": "Pending Manager Approval",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
	],
}


QUOTATION_WORKFLOW = {
	"workflow_name": "Quotation Approval",
	"document_type": "Quotation",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{
			"state": "Draft",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Review",
			"doc_status": 0,
			"allow_edit": "Sales Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Manager Approval",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Director Approval",
			"doc_status": 0,
			"allow_edit": "Approval Director",
			"is_optional_state": 0,
		},
		{
			"state": "Approved",
			"doc_status": 0,
			"allow_edit": "Sales Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Rejected",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Submitted",
			"doc_status": 1,
			"allow_edit": "Sales Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Cancelled",
			"doc_status": 2,
			"allow_edit": "Sales Manager",
			"is_optional_state": 0,
		},
	],
	"transitions": [
		{
			"state": "Draft",
			"action": "Submit for Review",
			"next_state": "Pending Review",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Review",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 5000000",
		},
		{
			"state": "Pending Review",
			"action": "Escalate to Director",
			"next_state": "Pending Manager Approval",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 5000000",
		},
		{
			"state": "Pending Review",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Review",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 20000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Escalate to Director",
			"next_state": "Pending Director Approval",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 20000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Approved",
			"action": "Confirm",
			"next_state": "Submitted",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Rejected",
			"action": "Submit for Review",
			"next_state": "Pending Review",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Submitted",
			"action": "Cancel",
			"next_state": "Cancelled",
			"allowed": "Sales Manager",
			"allow_self_approval": 0,
		},
	],
}


SALES_ORDER_WORKFLOW = {
	"workflow_name": "Sales Order Approval",
	"document_type": "Sales Order",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{
			"state": "Draft",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Manager Approval",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Director Approval",
			"doc_status": 0,
			"allow_edit": "Approval Director",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Executive Approval",
			"doc_status": 0,
			"allow_edit": "Approval Executive",
			"is_optional_state": 0,
		},
		{
			"state": "Approved",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Rejected",
			"doc_status": 0,
			"allow_edit": "Sales User",
			"is_optional_state": 0,
		},
		{
			"state": "Confirmed",
			"doc_status": 1,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Cancelled",
			"doc_status": 2,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
	],
	"transitions": [
		{
			"state": "Draft",
			"action": "Submit for Review",
			"next_state": "Pending Manager Approval",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 20000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Escalate to Director",
			"next_state": "Pending Director Approval",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 20000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 100000000",
		},
		{
			"state": "Pending Director Approval",
			"action": "Escalate to Executive",
			"next_state": "Pending Executive Approval",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 100000000",
		},
		{
			"state": "Pending Director Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Approved",
			"action": "Confirm",
			"next_state": "Confirmed",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Rejected",
			"action": "Submit for Review",
			"next_state": "Pending Manager Approval",
			"allowed": "Sales User",
			"allow_self_approval": 0,
		},
		{
			"state": "Confirmed",
			"action": "Cancel",
			"next_state": "Cancelled",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
	],
}


PURCHASE_ORDER_WORKFLOW = {
	"workflow_name": "Purchase Order Approval",
	"document_type": "Purchase Order",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{
			"state": "Draft",
			"doc_status": 0,
			"allow_edit": "Purchase User",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Budget Check",
			"doc_status": 0,
			"allow_edit": "Budget Controller",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Manager Approval",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Director Approval",
			"doc_status": 0,
			"allow_edit": "Approval Director",
			"is_optional_state": 0,
		},
		{
			"state": "Pending Executive Approval",
			"doc_status": 0,
			"allow_edit": "Approval Executive",
			"is_optional_state": 0,
		},
		{
			"state": "Approved",
			"doc_status": 0,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Rejected",
			"doc_status": 0,
			"allow_edit": "Purchase User",
			"is_optional_state": 0,
		},
		{
			"state": "Confirmed",
			"doc_status": 1,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
		{
			"state": "Cancelled",
			"doc_status": 2,
			"allow_edit": "Approval Manager",
			"is_optional_state": 0,
		},
	],
	"transitions": [
		{
			"state": "Draft",
			"action": "Submit for Budget Check",
			"next_state": "Pending Budget Check",
			"allowed": "Purchase User",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Budget Check",
			"action": "Pass Budget Check",
			"next_state": "Pending Manager Approval",
			"allowed": "Budget Controller",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Budget Check",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Budget Controller",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 10000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Escalate to Director",
			"next_state": "Pending Director Approval",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 10000000",
		},
		{
			"state": "Pending Manager Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Manager Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
			"condition": "doc.grand_total <= 50000000",
		},
		{
			"state": "Pending Director Approval",
			"action": "Escalate to Executive",
			"next_state": "Pending Executive Approval",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
			"condition": "doc.grand_total > 50000000",
		},
		{
			"state": "Pending Director Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Director Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Director",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Executive Approval",
			"action": "Request Changes",
			"next_state": "Draft",
			"allowed": "Approval Executive",
			"allow_self_approval": 0,
		},
		{
			"state": "Approved",
			"action": "Confirm",
			"next_state": "Confirmed",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
		{
			"state": "Rejected",
			"action": "Submit for Budget Check",
			"next_state": "Pending Budget Check",
			"allowed": "Purchase User",
			"allow_self_approval": 0,
		},
		{
			"state": "Confirmed",
			"action": "Cancel",
			"next_state": "Cancelled",
			"allowed": "Approval Manager",
			"allow_self_approval": 0,
		},
	],
}


RINGI_WORKFLOW = {
	"workflow_name": "Ringi Approval",
	"document_type": "Ringi",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{"state": "Draft", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
		{"state": "Pending Supervisor Approval", "doc_status": 0, "allow_edit": "Ringi Approver", "is_optional_state": 0},
		{"state": "Pending Department Head Approval", "doc_status": 0, "allow_edit": "Ringi Approver", "is_optional_state": 0},
		{"state": "Pending Executive Approval", "doc_status": 0, "allow_edit": "Approval Executive", "is_optional_state": 0},
		{"state": "Approved", "doc_status": 1, "allow_edit": "Ringi Approver", "is_optional_state": 0},
		{"state": "Rejected", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
		{"state": "Cancelled", "doc_status": 2, "allow_edit": "Ringi Approver", "is_optional_state": 0},
	],
	"transitions": [
		{"state": "Draft", "action": "Submit for Approval", "next_state": "Pending Supervisor Approval", "allowed": "Employee", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Approve", "next_state": "Pending Department Head Approval", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Return", "next_state": "Draft", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Department Head Approval", "action": "Approve", "next_state": "Approved", "allowed": "Ringi Approver", "allow_self_approval": 0, "condition": "doc.amount <= 1000000 or not doc.amount"},
		{"state": "Pending Department Head Approval", "action": "Escalate to Executive", "next_state": "Pending Executive Approval", "allowed": "Ringi Approver", "allow_self_approval": 0, "condition": "doc.amount > 1000000"},
		{"state": "Pending Department Head Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Department Head Approval", "action": "Return", "next_state": "Draft", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Executive Approval", "action": "Approve", "next_state": "Approved", "allowed": "Approval Executive", "allow_self_approval": 0},
		{"state": "Pending Executive Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Approval Executive", "allow_self_approval": 0},
		{"state": "Pending Executive Approval", "action": "Return", "next_state": "Draft", "allowed": "Approval Executive", "allow_self_approval": 0},
		{"state": "Rejected", "action": "Submit for Approval", "next_state": "Pending Supervisor Approval", "allowed": "Employee", "allow_self_approval": 0},
		{"state": "Approved", "action": "Cancel", "next_state": "Cancelled", "allowed": "Ringi Approver", "allow_self_approval": 0},
	],
}


SEAL_REQUEST_WORKFLOW = {
	"workflow_name": "Seal Request Approval",
	"document_type": "Seal Request",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{"state": "Draft", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
		{"state": "Pending Legal Review", "doc_status": 0, "allow_edit": "Legal Reviewer", "is_optional_state": 0},
		{"state": "Pending General Affairs", "doc_status": 0, "allow_edit": "General Affairs", "is_optional_state": 0},
		{"state": "Completed", "doc_status": 0, "allow_edit": "General Affairs", "is_optional_state": 0},
		{"state": "Rejected", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
	],
	"transitions": [
		{"state": "Draft", "action": "Submit for Approval", "next_state": "Pending Legal Review", "allowed": "Employee", "allow_self_approval": 0},
		{"state": "Pending Legal Review", "action": "Approve", "next_state": "Pending General Affairs", "allowed": "Legal Reviewer", "allow_self_approval": 0},
		{"state": "Pending Legal Review", "action": "Reject", "next_state": "Rejected", "allowed": "Legal Reviewer", "allow_self_approval": 0},
		{"state": "Pending Legal Review", "action": "Return", "next_state": "Draft", "allowed": "Legal Reviewer", "allow_self_approval": 0},
		{"state": "Pending General Affairs", "action": "Complete", "next_state": "Completed", "allowed": "General Affairs", "allow_self_approval": 0},
		{"state": "Pending General Affairs", "action": "Return", "next_state": "Draft", "allowed": "General Affairs", "allow_self_approval": 0},
		{"state": "Rejected", "action": "Submit for Approval", "next_state": "Pending Legal Review", "allowed": "Employee", "allow_self_approval": 0},
	],
}


GENERAL_APPLICATION_WORKFLOW = {
	"workflow_name": "General Application Approval",
	"document_type": "General Application",
	"is_active": 1,
	"send_email_alert": 0,
	"workflow_state_field": "workflow_state",
	"states": [
		{"state": "Draft", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
		{"state": "Pending Supervisor Approval", "doc_status": 0, "allow_edit": "Ringi Approver", "is_optional_state": 0},
		{"state": "Pending HR Review", "doc_status": 0, "allow_edit": "HR Manager", "is_optional_state": 0},
		{"state": "Approved", "doc_status": 0, "allow_edit": "HR Manager", "is_optional_state": 0},
		{"state": "Rejected", "doc_status": 0, "allow_edit": "Employee", "is_optional_state": 0},
	],
	"transitions": [
		{"state": "Draft", "action": "Submit for Approval", "next_state": "Pending Supervisor Approval", "allowed": "Employee", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Approve", "next_state": "Pending HR Review", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Reject", "next_state": "Rejected", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending Supervisor Approval", "action": "Return", "next_state": "Draft", "allowed": "Ringi Approver", "allow_self_approval": 0},
		{"state": "Pending HR Review", "action": "Approve", "next_state": "Approved", "allowed": "HR Manager", "allow_self_approval": 0},
		{"state": "Pending HR Review", "action": "Reject", "next_state": "Rejected", "allowed": "HR Manager", "allow_self_approval": 0},
		{"state": "Pending HR Review", "action": "Return", "next_state": "Draft", "allowed": "HR Manager", "allow_self_approval": 0},
		{"state": "Rejected", "action": "Submit for Approval", "next_state": "Pending Supervisor Approval", "allowed": "Employee", "allow_self_approval": 0},
	],
}


ALL_WORKFLOWS = [
	LEAD_WORKFLOW,
	OPPORTUNITY_WORKFLOW,
	QUOTATION_WORKFLOW,
	SALES_ORDER_WORKFLOW,
	PURCHASE_ORDER_WORKFLOW,
	RINGI_WORKFLOW,
	SEAL_REQUEST_WORKFLOW,
	GENERAL_APPLICATION_WORKFLOW,
]


def setup_workflows():
	"""Create all BPM workflow definitions. Idempotent - safe to re-run."""
	_create_roles()
	_create_workflow_states()
	_create_workflow_actions()
	_create_workflows()


def _create_roles():
	for role_name in CUSTOM_ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
				"is_custom": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"BPM: Created role '{role_name}'")


def _create_workflow_states():
	for ws in WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", ws["state"]):
			frappe.get_doc({
				"doctype": "Workflow State",
				"workflow_state_name": ws["state"],
				"style": ws["style"],
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"BPM: Created workflow state '{ws['state']}'")


def _create_workflow_actions():
	for action_name in WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action_name):
			frappe.get_doc({
				"doctype": "Workflow Action Master",
				"workflow_action_name": action_name,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"BPM: Created workflow action '{action_name}'")


def _create_workflows():
	for wf_def in ALL_WORKFLOWS:
		wf_name = wf_def["workflow_name"]

		if frappe.db.exists("Workflow", wf_name):
			frappe.logger().info(f"BPM: Workflow '{wf_name}' already exists, updating...")
			wf_doc = frappe.get_doc("Workflow", wf_name)
			# Clear existing states and transitions for clean update
			wf_doc.states = []
			wf_doc.transitions = []
		else:
			wf_doc = frappe.new_doc("Workflow")
			wf_doc.workflow_name = wf_name

		wf_doc.document_type = wf_def["document_type"]
		wf_doc.is_active = wf_def["is_active"]
		wf_doc.send_email_alert = wf_def.get("send_email_alert", 0)
		wf_doc.workflow_state_field = wf_def.get("workflow_state_field", "workflow_state")

		# Add states
		for state_def in wf_def["states"]:
			wf_doc.append("states", {
				"state": state_def["state"],
				"doc_status": str(state_def["doc_status"]),
				"allow_edit": state_def["allow_edit"],
				"is_optional_state": state_def.get("is_optional_state", 0),
				"update_field": state_def.get("update_field", ""),
				"update_value": state_def.get("update_value", ""),
			})

		# Add transitions
		for trans_def in wf_def["transitions"]:
			wf_doc.append("transitions", {
				"state": trans_def["state"],
				"action": trans_def["action"],
				"next_state": trans_def["next_state"],
				"allowed": trans_def["allowed"],
				"allow_self_approval": trans_def.get("allow_self_approval", 0),
				"condition": trans_def.get("condition", ""),
			})

		wf_doc.save(ignore_permissions=True)
		frappe.logger().info(f"BPM: Workflow '{wf_name}' configured for {wf_def['document_type']}")
