# Copyright (c) Lifegence Corporation and contributors
# For license information, please see license.txt
"""Japanese consumption tax (消費税) setup for companies.

ERPNext's stock setup creates a single ``Japan Tax`` template backed by one
``CT`` account at an outdated 5% rate (see ``country_wise_tax.json``). This
module replaces that with a structure that matches Japanese bookkeeping:

* ``仮受消費税`` – output tax (liability), charged on sales
* ``仮払消費税`` – input tax (asset), charged on purchases
* standard 10% and reduced 8% templates for Sales / Purchase / Item

The same routine is used both to back-fill existing companies and, via the
``Company`` ``on_update`` hook, to set up newly created Japanese companies.
It is idempotent: re-running it is a no-op once the structure exists.
"""

import frappe

STANDARD_RATE = 10.0
REDUCED_RATE = 8.0

OUTPUT_TAX = "仮受消費税"  # 売上にかかる消費税（負債）
INPUT_TAX = "仮払消費税"   # 仕入にかかる消費税（資産）

# (rate, template title, is_default)
RATE_TEMPLATES = [
	(STANDARD_RATE, "消費税 10%", True),
	(REDUCED_RATE, "消費税 8%（軽減）", False),
]


def setup_for_company_event(doc, method=None):
	"""``Company`` ``on_update`` hook entry point.

	Runs after ERPNext has built the chart of accounts and its default tax
	template. Guards keep it cheap and safe to fire on every company save.
	"""
	if (doc.get("country") or "") != "Japan":
		return
	abbr = doc.abbr
	# Already set up -> nothing to do.
	if frappe.db.exists("Account", f"{OUTPUT_TAX} - {abbr}"):
		return
	# Chart of accounts not built yet (too early in the creation flow).
	if not frappe.db.exists("Account", f"Duties and Taxes - {abbr}"):
		return
	try:
		setup_jp_consumption_tax(doc.name)
	except Exception:
		# Never block company creation because of tax setup.
		frappe.log_error(title="JP consumption tax setup failed", message=frappe.get_traceback())


@frappe.whitelist()
def setup_jp_consumption_tax(company_name: str) -> dict:
	"""Build the Japanese consumption tax structure for ``company_name``."""
	company = frappe.get_doc("Company", company_name)
	if (company.country or "") != "Japan":
		frappe.throw(f"{company_name} is not a Japanese company (country={company.country!r}).")
	abbr = company.abbr

	output_acc = _ensure_output_account(company_name, abbr)
	input_acc = _ensure_input_account(company_name, abbr)

	_delete_legacy_template(company_name, abbr)

	created = []
	for rate, title, is_default in RATE_TEMPLATES:
		created.append(
			_ensure_taxes_template(company_name, "Sales Taxes and Charges Template", title, output_acc, rate, is_default)
		)
		created.append(
			_ensure_taxes_template(company_name, "Purchase Taxes and Charges Template", title, input_acc, rate, is_default)
		)
		created.append(
			_ensure_item_tax_template(company_name, title, [(output_acc, rate), (input_acc, rate)])
		)

	frappe.db.commit()
	return {"company": company_name, "output_account": output_acc, "input_account": input_acc, "templates": created}


def _group_account(company_name: str, abbr: str, group_name: str) -> str | None:
	name = f"{group_name} - {abbr}"
	if frappe.db.exists("Account", name):
		return name
	return frappe.db.get_value(
		"Account", {"company": company_name, "account_name": group_name, "is_group": 1}, "name"
	)


def _ensure_output_account(company_name: str, abbr: str) -> str:
	target = f"{OUTPUT_TAX} - {abbr}"
	if frappe.db.exists("Account", target):
		return target

	# Repurpose ERPNext's default ``CT`` account (already a Tax account under
	# Duties and Taxes). Renaming updates any linked references.
	legacy = f"CT - {abbr}"
	if frappe.db.exists("Account", legacy):
		frappe.db.set_value("Account", legacy, "account_name", OUTPUT_TAX)
		frappe.rename_doc("Account", legacy, target, force=True)
		frappe.db.set_value("Account", target, "tax_rate", 0)
		return target

	parent = _group_account(company_name, abbr, "Duties and Taxes")
	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": OUTPUT_TAX,
			"parent_account": parent,
			"company": company_name,
			"account_type": "Tax",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_input_account(company_name: str, abbr: str) -> str:
	target = f"{INPUT_TAX} - {abbr}"
	if frappe.db.exists("Account", target):
		return target

	parent = _group_account(company_name, abbr, "Tax Assets") or _group_account(
		company_name, abbr, "Current Assets"
	)
	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": INPUT_TAX,
			"parent_account": parent,
			"company": company_name,
			"account_type": "Tax",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _delete_legacy_template(company_name: str, abbr: str) -> None:
	legacy = f"Japan Tax - {abbr}"
	for doctype in (
		"Sales Taxes and Charges Template",
		"Purchase Taxes and Charges Template",
		"Item Tax Template",
	):
		if frappe.db.exists(doctype, legacy):
			frappe.delete_doc(doctype, legacy, force=True, ignore_permissions=True)


def _ensure_taxes_template(
	company_name: str, doctype: str, title: str, account_head: str, rate: float, is_default: bool
) -> str:
	existing = frappe.get_all(doctype, filters={"company": company_name, "title": title}, pluck="name")
	if existing:
		return existing[0]

	doc = frappe.get_doc(
		{
			"doctype": doctype,
			"title": title,
			"company": company_name,
			"is_default": 1 if is_default else 0,
			"taxes": [
				{
					"charge_type": "On Net Total",
					"account_head": account_head,
					"description": title,
					"rate": rate,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_item_tax_template(company_name: str, title: str, account_rates: list) -> str:
	existing = frappe.get_all("Item Tax Template", filters={"company": company_name, "title": title}, pluck="name")
	if existing:
		return existing[0]

	doc = frappe.get_doc(
		{
			"doctype": "Item Tax Template",
			"title": title,
			"company": company_name,
			"taxes": [{"tax_type": account, "tax_rate": rate} for account, rate in account_rates],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def backfill_existing_companies() -> list:
	"""Run the setup for every existing Japanese company. Used for back-fill."""
	results = []
	for company_name in frappe.get_all("Company", filters={"country": "Japan"}, pluck="name"):
		# Skip ERPNext's automated-test companies.
		if company_name.startswith("_Test"):
			continue
		results.append(setup_jp_consumption_tax(company_name))
	return results
