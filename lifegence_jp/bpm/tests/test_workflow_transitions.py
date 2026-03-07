"""Automated workflow transition tests for Lifegence BPM.

Covers all 25 test cases across 5 workflows:
  - Lead Approval (TC-L01 ~ TC-L04)
  - Opportunity Approval (TC-O01 ~ TC-O05)
  - Quotation Approval (TC-Q01 ~ TC-Q05)
  - Sales Order Approval (TC-S01 ~ TC-S05)
  - Purchase Order Approval (TC-P01 ~ TC-P06)

Note on self-approval:
  Frappe's ``has_approval_access`` checks ``user != doc.owner``.
  Documents are therefore created as Administrator so that every
  test user satisfies ``user != owner``.  TC-L04 deliberately
  creates a document as DUAL_USER to trigger the self-approval block.
"""

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests.utils import FrappeTestCase

# ─── Test User Definitions ──────────────────────────────────────────────────
SALES_USER = "test-wf-sales@example.com"
SALES_MANAGER = "test-wf-salesmgr@example.com"
CRM_APPROVER = "test-wf-crm@example.com"
APPROVAL_MANAGER = "test-wf-appmgr@example.com"
APPROVAL_DIRECTOR = "test-wf-appdir@example.com"
APPROVAL_EXECUTIVE = "test-wf-appexec@example.com"
BUDGET_CONTROLLER = "test-wf-budget@example.com"
PURCHASE_USER = "test-wf-purchase@example.com"
DUAL_USER = "test-wf-dual@example.com"

# User → role mappings
TEST_USERS = {
	SALES_USER: ["Sales User"],
	SALES_MANAGER: ["Sales Manager"],
	CRM_APPROVER: ["CRM Approver"],
	APPROVAL_MANAGER: ["Approval Manager"],
	APPROVAL_DIRECTOR: ["Approval Director"],
	APPROVAL_EXECUTIVE: ["Approval Executive"],
	BUDGET_CONTROLLER: ["Budget Controller"],
	PURCHASE_USER: ["Purchase User"],
	DUAL_USER: ["Sales User", "CRM Approver"],
}


# ─── Setup Helpers ──────────────────────────────────────────────────────────
def _ensure_user(email, roles):
	"""Create a test user with given roles if it does not exist."""
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"enabled": 1,
			"new_password": "TestPass@123",
			"send_welcome_email": 0,
		})
		user.insert(ignore_permissions=True)

	existing_roles = {r.role for r in user.roles}
	for role in roles:
		if role not in existing_roles:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	return user


def _ensure_customer(name="Test WF Customer"):
	"""Create a test Customer if it does not exist."""
	if not frappe.db.exists("Customer", name):
		frappe.get_doc({
			"doctype": "Customer",
			"customer_name": name,
			"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group")
			or frappe.db.get_value("Customer Group", {"is_group": 0}),
			"territory": frappe.db.get_single_value("Selling Settings", "territory")
			or frappe.db.get_value("Territory", {"is_group": 0}),
		}).insert(ignore_permissions=True)
	return name


def _ensure_supplier(name="Test WF Supplier"):
	"""Create a test Supplier if it does not exist."""
	if not frappe.db.exists("Supplier", name):
		supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0})
		if not supplier_group:
			# Create a default Supplier Group if none exists (fresh ERPNext v16)
			if not frappe.db.exists("Supplier Group", "All Supplier Groups"):
				frappe.get_doc({
					"doctype": "Supplier Group",
					"supplier_group_name": "All Supplier Groups",
				}).insert(ignore_permissions=True)
			supplier_group = "All Supplier Groups"
		frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": name,
			"supplier_group": supplier_group,
		}).insert(ignore_permissions=True)
	return name


def _ensure_item(item_code="Test WF Item"):
	"""Create a test Item if it does not exist."""
	if not frappe.db.exists("Item", item_code):
		# Ensure UOM 'Nos' exists
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)
		# Ensure Item Group exists
		if not frappe.db.exists("Item Group", "All Item Groups"):
			frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": "All Item Groups",
				"is_group": 1,
			}).insert(ignore_permissions=True)
		doc = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_code,
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 0,
		})
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True)
	return item_code


def _ensure_company():
	"""Create a test Company if none exists (required by Opportunity, Quotation, etc.)."""
	if frappe.db.exists("Company", "_Test BPM Company"):
		_ensure_fiscal_year()
		return "_Test BPM Company"
	existing = frappe.db.get_value("Company", {}, "name")
	if existing:
		_ensure_fiscal_year()
		return existing
	# Create Warehouse Type 'Transit' if missing (required by Company creation in ERPNext v16)
	if frappe.db.exists("DocType", "Warehouse Type") and not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(ignore_permissions=True)
	company = frappe.get_doc({
		"doctype": "Company",
		"company_name": "_Test BPM Company",
		"abbr": "TBC",
		"default_currency": "JPY",
		"country": "Japan",
	})
	company.flags.ignore_links = True
	company.insert(ignore_permissions=True)
	_ensure_fiscal_year()
	frappe.db.commit()
	return company.name


def _ensure_fiscal_year():
	"""Create Fiscal Year for current year if missing (needed for PO/SO submit)."""
	from frappe.utils import nowdate, getdate
	current_year = getdate(nowdate()).year
	fy_name = f"_Test FY {current_year}"
	if frappe.db.exists("Fiscal Year", fy_name):
		return
	# Also check for any FY covering today
	existing = frappe.db.get_value(
		"Fiscal Year",
		{"year_start_date": ["<=", nowdate()], "year_end_date": [">=", nowdate()]},
		"name",
	)
	if existing:
		return
	fy = frappe.new_doc("Fiscal Year")
	fy.year = fy_name
	fy.year_start_date = f"{current_year}-01-01"
	fy.year_end_date = f"{current_year}-12-31"
	fy.flags.ignore_validate = True
	fy.insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_price_list():
	"""Create a selling Price List if none exists (needed for Quotation/SO)."""
	pl_name = "Standard Selling"
	if frappe.db.exists("Price List", pl_name):
		return pl_name
	# Check for any selling price list
	existing = frappe.db.get_value("Price List", {"selling": 1}, "name")
	if existing:
		return existing
	pl = frappe.get_doc({
		"doctype": "Price List",
		"price_list_name": pl_name,
		"currency": "JPY",
		"selling": 1,
	})
	pl.flags.ignore_links = True
	pl.flags.ignore_validate = True
	pl.insert(ignore_permissions=True)
	frappe.db.commit()
	return pl_name


def _ensure_crm_master_data():
	"""Create CRM master data (Opportunity Type, Sales Stage) if missing."""
	_ensure_company()
	if frappe.db.exists("DocType", "Opportunity Type") and not frappe.db.exists("Opportunity Type", "Sales"):
		frappe.get_doc({"doctype": "Opportunity Type", "name": "Sales"}).insert(ignore_permissions=True)
	if frappe.db.exists("DocType", "Sales Stage"):
		for stage in ["Prospecting", "Qualification", "Proposal/Price Quote", "Negotiation/Review"]:
			if not frappe.db.exists("Sales Stage", stage):
				frappe.get_doc({"doctype": "Sales Stage", "stage_name": stage}).insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_workflows():
	"""Run setup_workflows to ensure all BPM workflows exist."""
	from lifegence_bpm.setup.setup_workflow import setup_workflows

	setup_workflows()
	frappe.db.commit()


def _ensure_custom_role_permissions():
	"""Add DocType-level permissions for custom BPM roles.

	Standard roles (Sales User, Sales Manager, Purchase User) already have
	DocPerm entries.  Custom roles created by the BPM module need explicit
	Custom DocPerm entries so that ``get_transitions`` (which calls
	``doc.check_permission("read")``) and ``doc.save()`` succeed.
	"""
	from frappe.permissions import setup_custom_perms

	ROLE_PERMS = {
		"CRM Approver": {
			"Lead": ["read", "write"],
		},
		"Approval Manager": {
			"Opportunity": ["read", "write"],
			"Quotation": ["read", "write", "submit", "cancel"],
			"Sales Order": ["read", "write", "submit", "cancel"],
			"Purchase Order": ["read", "write", "submit", "cancel"],
		},
		"Approval Director": {
			"Quotation": ["read", "write", "submit", "cancel"],
			"Sales Order": ["read", "write", "submit", "cancel"],
			"Purchase Order": ["read", "write", "submit", "cancel"],
		},
		"Approval Executive": {
			"Sales Order": ["read", "write", "submit", "cancel"],
			"Purchase Order": ["read", "write", "submit", "cancel"],
		},
		"Budget Controller": {
			"Purchase Order": ["read", "write"],
		},
	}

	for role, doctypes in ROLE_PERMS.items():
		for doctype, perms in doctypes.items():
			# Ensure Custom DocPerm table is initialized for this DocType
			setup_custom_perms(doctype)

			# Skip if permission already exists for this role
			if frappe.db.exists(
				"Custom DocPerm",
				{"parent": doctype, "role": role, "permlevel": 0},
			):
				continue

			perm_doc = frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
			})
			for p in perms:
				perm_doc.set(p, 1)
			perm_doc.insert(ignore_permissions=True)

	frappe.db.commit()
	# Clear permission cache so new permissions take effect
	frappe.clear_cache()


# ─── Document Creation Helpers ──────────────────────────────────────────────
# All helpers run as the current session user.  Tests should call them
# while session user is Administrator so that doc.owner = "Administrator",
# avoiding the Frappe self-approval block (user == owner).

def _make_lead():
	"""Create a new Lead document in Draft state."""
	doc = frappe.get_doc({
		"doctype": "Lead",
		"first_name": "WF Test",
		"email_id": f"wf-lead-{frappe.generate_hash(length=6)}@example.com",
		"company_name": "Test WF Company",
	})
	doc.insert(ignore_permissions=True)
	return doc


def _make_opportunity():
	"""Create a new Opportunity document in Draft state."""
	customer = _ensure_customer()
	company = _ensure_company()
	doc = frappe.get_doc({
		"doctype": "Opportunity",
		"opportunity_from": "Customer",
		"party_name": customer,
		"opportunity_type": "Sales",
		"company": company,
	})
	doc.insert(ignore_permissions=True)
	return doc


def _make_quotation(grand_total):
	"""Create a new Quotation with specified grand_total (qty=1, rate=grand_total)."""
	customer = _ensure_customer()
	item_code = _ensure_item()
	company = _ensure_company()
	price_list = _ensure_price_list()
	doc = frappe.get_doc({
		"doctype": "Quotation",
		"quotation_to": "Customer",
		"party_name": customer,
		"company": company,
		"selling_price_list": price_list,
		"price_list_currency": "JPY",
		"plc_conversion_rate": 1,
		"currency": "JPY",
		"conversion_rate": 1,
		"ignore_pricing_rule": 1,
		"items": [{
			"item_code": item_code,
			"qty": 1,
			"rate": grand_total,
			"price_list_rate": grand_total,
		}],
	})
	doc.insert(ignore_permissions=True)
	return doc


def _make_sales_order(grand_total):
	"""Create a new Sales Order with specified grand_total."""
	customer = _ensure_customer()
	item_code = _ensure_item()
	company = _ensure_company()
	price_list = _ensure_price_list()
	doc = frappe.get_doc({
		"doctype": "Sales Order",
		"customer": customer,
		"company": company,
		"selling_price_list": price_list,
		"price_list_currency": "JPY",
		"plc_conversion_rate": 1,
		"currency": "JPY",
		"conversion_rate": 1,
		"delivery_date": frappe.utils.add_days(frappe.utils.today(), 7),
		"ignore_pricing_rule": 1,
		"items": [{
			"item_code": item_code,
			"qty": 1,
			"rate": grand_total,
			"price_list_rate": grand_total,
			"delivery_date": frappe.utils.add_days(frappe.utils.today(), 7),
		}],
	})
	doc.insert(ignore_permissions=True)
	return doc


def _make_purchase_order(grand_total):
	"""Create a new Purchase Order with specified grand_total."""
	supplier = _ensure_supplier()
	item_code = _ensure_item()
	company = _ensure_company()
	doc = frappe.get_doc({
		"doctype": "Purchase Order",
		"supplier": supplier,
		"company": company,
		"ignore_pricing_rule": 1,
		"items": [{
			"item_code": item_code,
			"qty": 1,
			"rate": grand_total,
			"price_list_rate": grand_total,
			"schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
		}],
	})
	doc.insert(ignore_permissions=True)
	return doc


# ─── Test Class ─────────────────────────────────────────────────────────────
class TestWorkflowTransitions(FrappeTestCase):
	"""Test all 25 BPM workflow transition scenarios."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		# Ensure CRM master data exists (Opportunity Type, Sales Stage)
		_ensure_crm_master_data()

		# Ensure workflows, roles, states, actions are set up
		_ensure_workflows()

		# Add DocType-level permissions for custom BPM roles
		_ensure_custom_role_permissions()

		# Create test users with required roles
		for email, roles in TEST_USERS.items():
			_ensure_user(email, roles)
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")

	# ═══════════════════════════════════════════════════════════════════════
	# Lead Approval (4 tests)
	# ═══════════════════════════════════════════════════════════════════════

	def test_tc_l01_lead_normal_flow(self):
		"""TC-L01: Draft → Submit for Review → Qualify → Convert"""
		# Create as Administrator (owner=Administrator)
		doc = _make_lead()
		self.assertEqual(doc.workflow_state, "Draft")

		# Sales User submits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# CRM Approver qualifies
		frappe.set_user(CRM_APPROVER)
		doc.reload()
		apply_workflow(doc, "Qualify")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Qualified")
		self.assertEqual(doc.status, "Interested")

		# CRM Approver converts
		apply_workflow(doc, "Convert")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Converted")
		self.assertEqual(doc.status, "Converted")

	def test_tc_l02_lead_disqualify_resubmit(self):
		"""TC-L02: Draft → Submit → Disqualify → Resubmit"""
		doc = _make_lead()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# CRM Approver disqualifies
		frappe.set_user(CRM_APPROVER)
		doc.reload()
		apply_workflow(doc, "Disqualify")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Unqualified")
		self.assertEqual(doc.status, "Do Not Contact")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

	def test_tc_l03_lead_request_changes(self):
		"""TC-L03: Draft → Submit → Request Changes → Draft → Resubmit"""
		doc = _make_lead()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# CRM Approver requests changes
		frappe.set_user(CRM_APPROVER)
		doc.reload()
		apply_workflow(doc, "Request Changes")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Draft")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

	def test_tc_l04_lead_self_approval_prevention(self):
		"""TC-L04: Document owner cannot apply workflow (allow_self_approval=0).

		Frappe checks ``user != doc.owner``.  When the creating user
		tries to apply any transition with allow_self_approval=0,
		it is rejected.
		"""
		# Create as DUAL_USER so owner == DUAL_USER
		frappe.set_user(DUAL_USER)
		doc = _make_lead()
		self.assertEqual(doc.workflow_state, "Draft")

		# Same owner tries Submit for Review — blocked by self-approval check
		with self.assertRaises(frappe.ValidationError):
			apply_workflow(doc, "Submit for Review")

		doc.reload()
		self.assertEqual(doc.workflow_state, "Draft")

	# ═══════════════════════════════════════════════════════════════════════
	# Opportunity Approval (5 tests)
	# ═══════════════════════════════════════════════════════════════════════

	def test_tc_o01_opportunity_normal_approval(self):
		"""TC-O01: Draft → Submit for Review → Approve"""
		doc = _make_opportunity()
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager approves
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.status, "Open")

	def test_tc_o02_opportunity_reject_resubmit(self):
		"""TC-O02: Draft → Submit → Reject → Resubmit"""
		doc = _make_opportunity()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		# Approval Manager rejects
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Reject")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")
		self.assertEqual(doc.status, "Closed")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

	def test_tc_o03_opportunity_request_changes(self):
		"""TC-O03: Draft → Submit → Request Changes → Draft → Resubmit"""
		doc = _make_opportunity()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		# Approval Manager requests changes
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Request Changes")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Draft")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

	def test_tc_o04_opportunity_convert(self):
		"""TC-O04: Approved → Convert"""
		doc = _make_opportunity()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

		# Convert
		apply_workflow(doc, "Convert")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Converted")
		self.assertEqual(doc.status, "Converted")

	def test_tc_o05_opportunity_mark_as_lost(self):
		"""TC-O05: Approved → Mark as Lost"""
		doc = _make_opportunity()

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

		# Mark as Lost
		apply_workflow(doc, "Mark as Lost")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Lost")
		self.assertEqual(doc.status, "Lost")

	# ═══════════════════════════════════════════════════════════════════════
	# Quotation Approval (5 tests)
	# ═══════════════════════════════════════════════════════════════════════

	def test_tc_q01_quotation_under_5m(self):
		"""TC-Q01: <=500万 → Sales Manager 直接承認"""
		doc = _make_quotation(grand_total=4_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# Sales Manager directly approves (grand_total <= 5,000,000)
		frappe.set_user(SALES_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_q02_quotation_5m_to_20m(self):
		"""TC-Q02: 500万超〜2000万以下 → Manager承認"""
		doc = _make_quotation(grand_total=10_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# Sales Manager escalates (grand_total > 5,000,000)
		frappe.set_user(SALES_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager approves (grand_total <= 20,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_q03_quotation_over_20m(self):
		"""TC-Q03: 2000万超 → Director承認（段階エスカレーション）"""
		doc = _make_quotation(grand_total=30_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

		# Sales Manager escalates
		frappe.set_user(SALES_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager escalates (grand_total > 20,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Director Approval")

		# Approval Director approves
		frappe.set_user(APPROVAL_DIRECTOR)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_q04_quotation_confirm_submit(self):
		"""TC-Q04: Approved → Confirm → Submitted (docstatus=1)"""
		doc = _make_quotation(grand_total=3_000_000)

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		frappe.set_user(SALES_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

		# Sales Manager confirms → docstatus=1
		apply_workflow(doc, "Confirm")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Submitted")
		self.assertEqual(doc.docstatus, 1)

	def test_tc_q05_quotation_reject_resubmit(self):
		"""TC-Q05: Reject → Resubmit"""
		doc = _make_quotation(grand_total=2_000_000)

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		# Sales Manager rejects
		frappe.set_user(SALES_MANAGER)
		doc.reload()
		apply_workflow(doc, "Reject")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Review")

	# ═══════════════════════════════════════════════════════════════════════
	# Sales Order Approval (5 tests)
	# ═══════════════════════════════════════════════════════════════════════

	def test_tc_s01_sales_order_under_20m(self):
		"""TC-S01: <=2000万 → Approval Manager承認"""
		doc = _make_sales_order(grand_total=15_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager approves (grand_total <= 20,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_s02_sales_order_20m_to_100m(self):
		"""TC-S02: 2000万超〜1億以下 → Director承認"""
		doc = _make_sales_order(grand_total=60_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager escalates (grand_total > 20,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Director Approval")

		# Approval Director approves (grand_total <= 100,000,000)
		frappe.set_user(APPROVAL_DIRECTOR)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_s03_sales_order_over_100m(self):
		"""TC-S03: 1億超 → Executive承認（最上位エスカレーション）"""
		doc = _make_sales_order(grand_total=150_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager escalates
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Director Approval")

		# Approval Director escalates (grand_total > 100,000,000)
		frappe.set_user(APPROVAL_DIRECTOR)
		doc.reload()
		apply_workflow(doc, "Escalate to Executive")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Executive Approval")

		# Approval Executive approves
		frappe.set_user(APPROVAL_EXECUTIVE)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_s04_sales_order_confirm(self):
		"""TC-S04: Approved → Confirm → Confirmed (docstatus=1)"""
		doc = _make_sales_order(grand_total=10_000_000)

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

		# Confirm → docstatus=1
		apply_workflow(doc, "Confirm")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Confirmed")
		self.assertEqual(doc.docstatus, 1)

	def test_tc_s05_sales_order_reject_resubmit(self):
		"""TC-S05: Reject → Resubmit"""
		doc = _make_sales_order(grand_total=5_000_000)

		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()

		# Approval Manager rejects
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Reject")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")

		# Sales User resubmits
		frappe.set_user(SALES_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Review")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

	# ═══════════════════════════════════════════════════════════════════════
	# Purchase Order Approval (6 tests)
	# ═══════════════════════════════════════════════════════════════════════

	def test_tc_p01_purchase_order_under_10m(self):
		"""TC-P01: <=1000万 → Budget Check → Manager承認"""
		doc = _make_purchase_order(grand_total=8_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Budget Check")

		# Budget Controller passes
		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Pass Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager approves (grand_total <= 10,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_p02_purchase_order_10m_to_50m(self):
		"""TC-P02: 1000万超〜5000万以下 → Budget Check → Director承認"""
		doc = _make_purchase_order(grand_total=20_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Budget Check")

		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Pass Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager escalates (grand_total > 10,000,000)
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Director Approval")

		# Approval Director approves (grand_total <= 50,000,000)
		frappe.set_user(APPROVAL_DIRECTOR)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_p03_purchase_order_over_50m(self):
		"""TC-P03: 5000万超 → Budget Check → Executive承認"""
		doc = _make_purchase_order(grand_total=60_000_000)
		self.assertEqual(doc.workflow_state, "Draft")

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Budget Check")

		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Pass Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Manager Approval")

		# Approval Manager escalates
		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Escalate to Director")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Director Approval")

		# Approval Director escalates (grand_total > 50,000,000)
		frappe.set_user(APPROVAL_DIRECTOR)
		doc.reload()
		apply_workflow(doc, "Escalate to Executive")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Executive Approval")

		# Approval Executive approves
		frappe.set_user(APPROVAL_EXECUTIVE)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

	def test_tc_p04_purchase_order_budget_reject(self):
		"""TC-P04: Budget Controller rejects at budget check stage"""
		doc = _make_purchase_order(grand_total=5_000_000)

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Budget Check")

		# Budget Controller rejects
		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Reject")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")

	def test_tc_p05_purchase_order_confirm(self):
		"""TC-P05: Approved → Confirm → Confirmed (docstatus=1)"""
		doc = _make_purchase_order(grand_total=5_000_000)

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()

		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Pass Budget Check")
		doc.reload()

		frappe.set_user(APPROVAL_MANAGER)
		doc.reload()
		apply_workflow(doc, "Approve")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")

		# Confirm → docstatus=1
		apply_workflow(doc, "Confirm")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Confirmed")
		self.assertEqual(doc.docstatus, 1)

	def test_tc_p06_purchase_order_reject_resubmit(self):
		"""TC-P06: Budget Reject → Resubmit from Rejected"""
		doc = _make_purchase_order(grand_total=3_000_000)

		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()

		# Budget Controller rejects
		frappe.set_user(BUDGET_CONTROLLER)
		doc.reload()
		apply_workflow(doc, "Reject")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")

		# Purchase User resubmits from Rejected
		frappe.set_user(PURCHASE_USER)
		doc.reload()
		apply_workflow(doc, "Submit for Budget Check")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending Budget Check")
