import frappe


# ─── Authorization Rules ─────────────────────────────────────────────────────
# Japanese Yen thresholds for enterprise-scale approval chains

AUTHORIZATION_RULES = [
	# ── Sales: Quotation ──────────────────────────────────────────────────
	{
		"transaction": "Quotation",
		"based_on": "Grand Total",
		"value": 5000000,
		"system_role": "Sales User",
		"approving_role": "Sales Manager",
	},
	{
		"transaction": "Quotation",
		"based_on": "Grand Total",
		"value": 20000000,
		"system_role": "Sales Manager",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Quotation",
		"based_on": "Grand Total",
		"value": 50000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},
	{
		"transaction": "Quotation",
		"based_on": "Average Discount",
		"value": 10,
		"system_role": "Sales User",
		"approving_role": "Sales Manager",
	},
	{
		"transaction": "Quotation",
		"based_on": "Average Discount",
		"value": 20,
		"system_role": "Sales Manager",
		"approving_role": "Approval Manager",
	},

	# ── Sales: Sales Order ────────────────────────────────────────────────
	{
		"transaction": "Sales Order",
		"based_on": "Grand Total",
		"value": 20000000,
		"system_role": "Sales User",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Sales Order",
		"based_on": "Grand Total",
		"value": 100000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},
	{
		"transaction": "Sales Order",
		"based_on": "Grand Total",
		"value": 300000000,
		"system_role": "Approval Director",
		"approving_role": "Approval Executive",
	},
	{
		"transaction": "Sales Order",
		"based_on": "Average Discount",
		"value": 10,
		"system_role": "Sales User",
		"approving_role": "Sales Manager",
	},
	{
		"transaction": "Sales Order",
		"based_on": "Average Discount",
		"value": 20,
		"system_role": "Sales Manager",
		"approving_role": "Approval Manager",
	},

	# ── Sales: Sales Invoice ──────────────────────────────────────────────
	{
		"transaction": "Sales Invoice",
		"based_on": "Grand Total",
		"value": 20000000,
		"system_role": "Sales User",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Sales Invoice",
		"based_on": "Grand Total",
		"value": 100000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},

	# ── Purchase: Purchase Order ──────────────────────────────────────────
	{
		"transaction": "Purchase Order",
		"based_on": "Grand Total",
		"value": 10000000,
		"system_role": "Purchase User",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Purchase Order",
		"based_on": "Grand Total",
		"value": 50000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},
	{
		"transaction": "Purchase Order",
		"based_on": "Grand Total",
		"value": 100000000,
		"system_role": "Approval Director",
		"approving_role": "Approval Executive",
	},

	# ── Purchase: Purchase Invoice ────────────────────────────────────────
	{
		"transaction": "Purchase Invoice",
		"based_on": "Grand Total",
		"value": 10000000,
		"system_role": "Purchase User",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Purchase Invoice",
		"based_on": "Grand Total",
		"value": 50000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},

	# ── Purchase: Purchase Receipt ────────────────────────────────────────
	{
		"transaction": "Purchase Receipt",
		"based_on": "Grand Total",
		"value": 10000000,
		"system_role": "Purchase User",
		"approving_role": "Approval Manager",
	},
	{
		"transaction": "Purchase Receipt",
		"based_on": "Grand Total",
		"value": 50000000,
		"system_role": "Approval Manager",
		"approving_role": "Approval Director",
	},
]


def setup_authorization_rules():
	"""Create all authorization rules. Idempotent - safe to re-run."""
	for rule_def in AUTHORIZATION_RULES:
		existing = frappe.db.exists("Authorization Rule", {
			"transaction": rule_def["transaction"],
			"based_on": rule_def["based_on"],
			"value": rule_def["value"],
			"system_role": rule_def["system_role"],
			"approving_role": rule_def["approving_role"],
		})

		if existing:
			frappe.logger().info(
				f"BPM: Authorization Rule already exists for "
				f"{rule_def['transaction']} {rule_def['based_on']} {rule_def['value']}"
			)
			continue

		doc = frappe.get_doc({
			"doctype": "Authorization Rule",
			"transaction": rule_def["transaction"],
			"based_on": rule_def["based_on"],
			"value": rule_def["value"],
			"system_role": rule_def["system_role"],
			"approving_role": rule_def["approving_role"],
		})
		doc.insert(ignore_permissions=True)
		frappe.logger().info(
			f"BPM: Created Authorization Rule - {rule_def['transaction']} "
			f"{rule_def['based_on']} > {rule_def['value']} "
			f"({rule_def['system_role']} -> {rule_def['approving_role']})"
		)
