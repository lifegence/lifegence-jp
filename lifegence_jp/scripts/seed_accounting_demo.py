# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

"""Seed data for the "AI agent accounting with governance" demo.

Story: a service-business SMB (みらいワークス株式会社) runs its month-end
accounting through the chat agent. Three personas with different
permissions show the governance model built in Phase 2:

  · 経理担当 山田 (Accounts User)    — classify tax, draft journals, AR
  · 経理マネージャ 佐藤 (Accounts Manager) — approves step-up requests
  · 管理部長 鈴木 (read-only)          — reviews the audit trail

Governance wired via Agent Skill Policy:
  · create_journal_draft — allow, but step-up when amount > ¥100,000
    (Task 5 conditional policy)
  · post_journal / close_period — step-up-required (Task 6 approval queue)

Run:
    bench --site <site> execute \
        lifegence_jp.scripts.seed_accounting_demo.run

Reset (destructive — demo company data only):
    bench --site <site> execute \
        lifegence_jp.scripts.seed_accounting_demo.reset --kwargs "{'confirm': True}"
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, flt, nowdate

COMPANY = "みらいワークス株式会社"
ABBR = "MW"
DEMO_AGENT_NAME = "keiri-demo-agent"

DEMO_USERS = [
	{
		"email": "acct-staff@demo.lifegence.com",
		"first_name": "太郎",
		"last_name": "山田",
		"password": "Demo@Keiri2026",
		"roles": ["Accounts User"],
		"label": "経理担当",
	},
	{
		"email": "acct-manager@demo.lifegence.com",
		"first_name": "花子",
		"last_name": "佐藤",
		"password": "Demo@Keiri2026",
		"roles": ["Accounts User", "Accounts Manager"],
		"label": "経理マネージャ（承認者）",
	},
	{
		"email": "acct-viewer@demo.lifegence.com",
		"first_name": "一郎",
		"last_name": "鈴木",
		"password": "Demo@Keiri2026",
		"roles": ["Accounts User"],
		"label": "管理部長（監査・参照）",
	},
]

CUSTOMERS = [
	"株式会社ABCコンサルティング",
	"DEFシステムズ株式会社",
	"GHIマーケティング合同会社",
	"JKL不動産株式会社",
]

SERVICE_ITEMS = [
	{"code": "SVC-CONSULT", "name": "コンサルティング料", "rate": 300000},
	{"code": "SVC-SUPPORT", "name": "保守サポート料", "rate": 80000},
	{"code": "SVC-DEV", "name": "システム開発料", "rate": 500000},
]

# Agent Skill Policy rules that drive the governance demo.
DEMO_POLICIES = [
	{
		"skill_id": "create_journal_draft",
		"site_pattern": "*",
		"role": "Accounts User",
		"action_pattern": "*",
		"decision": "allow",
		"priority": 10,
		"conditions": (
			'{"max_amount": 100000, "amount_param": "amount", '
			'"on_violation": "step-up-required"}'
		),
		"reason": "経理担当は10万円以下の仕訳ドラフトを自動作成可。超過分は承認へ。",
	},
	{
		"skill_id": "post_journal",
		"site_pattern": "*",
		"role": "*",
		"action_pattern": "*",
		"decision": "step-up-required",
		"step_up_required": 1,
		"priority": 10,
		"reason": "仕訳確定は必ず承認を要する確定操作。",
	},
	{
		"skill_id": "close_period",
		"site_pattern": "*",
		"role": "*",
		"action_pattern": "*",
		"decision": "step-up-required",
		"step_up_required": 1,
		"priority": 10,
		"reason": "月次期間締めは必ず承認を要する確定操作。",
	},
]

DEMO_SKILLS = [
	"classify_tax_category",
	"verify_invoice_qualification",
	"suggest_ar_matching",
	"check_monthly_closing",
	"detect_balance_anomaly",
	"create_journal_draft",
	"assist_journal_entry",
	"post_journal",
	"clear_ar",
	"close_period",
	"query_withholding_tax_summary",
]


# ── helpers ────────────────────────────────────────────────────────


def _acct(fragment: str) -> str:
	"""Resolve an account name for the demo company by leaf-name fragment."""
	name = frappe.db.get_value(
		"Account",
		{"company": COMPANY, "account_name": fragment, "is_group": 0},
		"name",
	)
	return name


def _ensure_company() -> None:
	if frappe.db.exists("Company", COMPANY):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY,
			"abbr": ABBR,
			"default_currency": "JPY",
			"country": "Japan",
			"chart_of_accounts": "Standard",
			"create_chart_of_accounts_based_on": "Standard Template",
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_fiscal_year() -> None:
	"""ERPNext rejects overlapping *global* fiscal years, so reuse any FY
	that already covers today; only create one if none exists."""
	today = frappe.utils.getdate(nowdate())
	covering = frappe.db.sql(
		"""SELECT name FROM `tabFiscal Year`
		   WHERE year_start_date <= %s AND year_end_date >= %s LIMIT 1""",
		(today, today),
	)
	if covering:
		return
	start_year = today.year if today.month >= 4 else today.year - 1
	frappe.get_doc(
		{
			"doctype": "Fiscal Year",
			"year": f"{start_year}-{start_year + 1} (Demo)",
			"year_start_date": frappe.utils.getdate(f"{start_year}-04-01"),
			"year_end_date": frappe.utils.getdate(f"{start_year + 1}-03-31"),
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_users() -> None:
	for spec in DEMO_USERS:
		email = spec["email"]
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.new_doc("User")
			user.email = email
			user.send_welcome_email = 0
		user.first_name = spec["first_name"]
		user.last_name = spec["last_name"]
		user.enabled = 1
		user.new_password = spec["password"]
		existing = {r.role for r in (user.roles or [])}
		for role in spec["roles"]:
			if role not in existing and frappe.db.exists("Role", role):
				user.append("roles", {"role": role})
		user.flags.ignore_password_policy = True
		user.save(ignore_permissions=True)
	frappe.db.commit()


def _ensure_customers() -> None:
	for name in CUSTOMERS:
		if frappe.db.exists("Customer", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
				or "All Customer Groups",
				"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name")
				or "All Territories",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_items() -> None:
	income = _acct("Sales") or _acct("Service")
	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
	for spec in SERVICE_ITEMS:
		if frappe.db.exists("Item", spec["code"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": spec["code"],
				"item_name": spec["name"],
				"item_group": item_group,
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"is_purchase_item": 0,
				"standard_rate": spec["rate"],
			}
		)
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


def _seed_sales_invoices() -> list[str]:
	"""Submitted, unpaid Sales Invoices → AR for the reconciliation scene."""
	debtors = _acct("Debtors")
	income = _acct("Sales") or _acct("Service")
	out: list[str] = []
	plan = [
		(CUSTOMERS[0], "SVC-CONSULT", 1),
		(CUSTOMERS[1], "SVC-SUPPORT", 2),
		(CUSTOMERS[2], "SVC-DEV", 1),
		(CUSTOMERS[3], "SVC-SUPPORT", 1),
	]
	for cust, item, qty in plan:
		# idempotency: skip if an unpaid invoice for this customer+item exists
		existing = frappe.db.sql(
			"""SELECT si.name FROM `tabSales Invoice` si
			   JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			   WHERE si.customer = %s AND sii.item_code = %s AND si.company = %s
			     AND si.docstatus = 1 LIMIT 1""",
			(cust, item, COMPANY),
		)
		if existing:
			out.append(existing[0][0])
			continue
		rate = flt(frappe.db.get_value("Item", item, "standard_rate") or 0)
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": COMPANY,
				"customer": cust,
				"currency": "JPY",
				"posting_date": add_days(nowdate(), -20),
				"due_date": add_days(nowdate(), 10),
				"debit_to": debtors,
				"items": [
					{
						"item_code": item,
						"qty": qty,
						"rate": rate,
						"income_account": income,
					}
				],
			}
		)
		si.insert(ignore_permissions=True)
		si.submit()
		out.append(si.name)
	frappe.db.commit()
	return out


def _seed_unreconciled_payment(invoices: list[str]) -> str | None:
	"""One received payment left UNRECONCILED (no references) so
	suggest_ar_matching has something to propose."""
	if not invoices:
		return None
	cash = _acct("Cash") or _acct("Bank Account") or _acct("Bank")
	debtors = _acct("Debtors")
	cust = frappe.db.get_value("Sales Invoice", invoices[0], "customer")
	amount = flt(frappe.db.get_value("Sales Invoice", invoices[0], "grand_total") or 0)
	# idempotency: skip if an unallocated payment for this customer exists
	dup = frappe.db.sql(
		"""SELECT name FROM `tabPayment Entry`
		   WHERE party = %s AND company = %s AND docstatus = 1
		     AND unallocated_amount > 0 LIMIT 1""",
		(cust, COMPANY),
	)
	if dup:
		return dup[0][0]
	pe = frappe.get_doc(
		{
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"company": COMPANY,
			"posting_date": add_days(nowdate(), -2),
			"party_type": "Customer",
			"party": cust,
			"paid_from": debtors,
			"paid_to": cash,
			"paid_amount": amount,
			"received_amount": amount,
		}
	)
	pe.insert(ignore_permissions=True)
	pe.submit()
	frappe.db.commit()
	return pe.name


def _seed_draft_journal() -> str | None:
	"""A DRAFT Journal Entry the demo can post via post_journal."""
	expense = _acct("Miscellaneous Expenses") or _acct("Administrative Expenses") or _acct("Expenses")
	cash = _acct("Cash") or _acct("Bank Account") or _acct("Bank")
	if not (expense and cash):
		return None
	existing = frappe.db.get_value(
		"Journal Entry",
		{"company": COMPANY, "docstatus": 0, "user_remark": ["like", "%デモ用ドラフト%"]},
		"name",
	)
	if existing:
		return existing
	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": COMPANY,
			"posting_date": nowdate(),
			"user_remark": "デモ用ドラフト仕訳（消耗品費）",
			"accounts": [
				{"account": expense, "debit_in_account_currency": 30000},
				{"account": cash, "credit_in_account_currency": 30000},
			],
		}
	)
	je.insert(ignore_permissions=True)  # left as draft (docstatus=0)
	frappe.db.commit()
	return je.name


def _ensure_policies() -> None:
	for spec in DEMO_POLICIES:
		if not frappe.db.exists("Agent Skill Manifest", spec["skill_id"]):
			continue  # skill not seeded yet; skip silently
		name = f"{spec['skill_id']}-{spec.get('priority', 100)}-{spec['role']}"
		if frappe.db.exists("Agent Skill Policy", name):
			doc = frappe.get_doc("Agent Skill Policy", name)
		else:
			doc = frappe.new_doc("Agent Skill Policy")
		doc.update(
			{
				"skill_id": spec["skill_id"],
				"site_pattern": spec["site_pattern"],
				"role": spec["role"],
				"action_pattern": spec["action_pattern"],
				"decision": spec["decision"],
				"priority": spec.get("priority", 100),
				"step_up_required": spec.get("step_up_required", 0),
				"conditions": spec.get("conditions", ""),
				"reason": spec.get("reason", ""),
				"is_active": 1,
			}
		)
		doc.save(ignore_permissions=True)
	frappe.db.commit()


def _ensure_conversations(agent_doc_name: str) -> None:
	"""Pre-create a real AI Direct conversation per persona so the chat_room
	tile opens directly (a virtual/unstarted tile is flakier to click in
	recording)."""
	from lifegence_agent.api.conversation_agents import create_ai_direct_conversation

	original = frappe.session.user
	try:
		for spec in DEMO_USERS:
			if not frappe.db.exists("User", spec["email"]):
				continue
			frappe.set_user(spec["email"])
			try:
				res = create_ai_direct_conversation(agent_doc_name)
				conv = res.get("name")
				# Seed a greeting agent message so the conversation shows as a
				# real "recent" tile (not a virtual "start chat" tile), which is
				# what the recording clicks. is_agent_message=1 avoids triggering
				# a real agent response.
				if conv and not frappe.db.exists("Chat Message", {"conversation": conv}):
					frappe.get_doc(
						{
							"doctype": "Chat Message",
							"conversation": conv,
							"is_agent_message": 1,
							"agent": agent_doc_name,
							"message_type": "Text",
							"content": "こんにちは、経理アシスタントです。月次決算のご用件をどうぞ。",
						}
					).insert(ignore_permissions=True)
			except Exception as e:
				print(f"    conv for {spec['email']} skipped: {e}")
	finally:
		frappe.set_user(original)
	frappe.db.commit()


def _ensure_demo_agent() -> str:
	if frappe.db.exists("Chat Agent", {"agent_name": DEMO_AGENT_NAME}):
		agent = frappe.get_doc("Chat Agent", {"agent_name": DEMO_AGENT_NAME})
	else:
		agent = frappe.new_doc("Chat Agent")
		agent.agent_name = DEMO_AGENT_NAME
		agent.display_name = "経理アシスタント"
		agent.description = "月次決算を支援する会計エージェント（デモ）"
		agent.is_active = 1
		agent.trigger_type = "Mention"
		agent.system_prompt = (
			"あなたは日本の中小企業「みらいワークス株式会社」の経理を支援する AI アシスタントです。\n"
			"会計操作は必ず frappe-tool の run-skill を使って実行してください。自分で仕訳表を"
			"文章で書くのではなく、対応するスキルを呼び出します。\n"
			"- 消費税区分: classify_tax_category\n"
			"- 仕訳ドラフト作成: create_journal_draft（company/posting_date/debit_account/"
			"credit_account/amount/remark）\n"
			"- 仕訳確定: post_journal、売掛金消込: clear_ar、月次締め: close_period\n"
			"- 売掛金消込候補: suggest_ar_matching\n"
			"確定操作（仕訳確定・期間締め等）も**拒否せず run-skill で呼び出してください**。"
			"権限や金額により承認が必要な場合はスキルが『承認待ち（approval_id）』を返すので、"
			"その内容をそのままユーザーに伝えます。勘定科目名は frappe-tool query で "
			"Account（company=みらいワークス株式会社）から確認できます。"
		)
		agent.company = COMPANY
	agent.openclaw_thinking_level = "medium"  # reasoning on → reliably calls run-skill
	existing = {row.skill for row in (agent.enabled_skills or [])}
	for skill in DEMO_SKILLS:
		if skill in existing:
			continue
		if not frappe.db.exists("Chat Agent Skill", skill):
			continue
		agent.append("enabled_skills", {"skill": skill})
	agent.save(ignore_permissions=True)
	frappe.db.commit()
	return agent.name


# ── orchestration ──────────────────────────────────────────────────


def run() -> dict:
	print("→ Seeding accounting governance demo…")
	_ensure_company()
	print(f"  ✓ Company: {COMPANY}")
	_ensure_fiscal_year()
	print("  ✓ Fiscal year")
	_ensure_users()
	print(f"  ✓ Users: {', '.join(u['email'] for u in DEMO_USERS)}")
	_ensure_customers()
	print(f"  ✓ Customers: {len(CUSTOMERS)}")
	_ensure_items()
	print(f"  ✓ Service items: {len(SERVICE_ITEMS)}")
	invoices = _seed_sales_invoices()
	print(f"  ✓ Sales invoices (unpaid AR): {len(invoices)}")
	pe = _seed_unreconciled_payment(invoices)
	print(f"  ✓ Unreconciled payment: {pe}")
	je = _seed_draft_journal()
	print(f"  ✓ Draft journal entry: {je}")
	_ensure_policies()
	print(f"  ✓ Agent Skill Policies: {len(DEMO_POLICIES)}")
	agent = _ensure_demo_agent()
	print(f"  ✓ Demo agent: {agent}")
	_ensure_conversations(agent)
	print("  ✓ AI Direct conversations per persona")
	frappe.db.commit()
	print("✓ Accounting demo seed complete")
	return {
		"company": COMPANY,
		"invoices": invoices,
		"payment": pe,
		"draft_journal": je,
		"agent": agent,
		"users": [u["email"] for u in DEMO_USERS],
	}


def reset(confirm: bool = False) -> None:
	"""Delete demo transactions + the demo agent + policies (keeps company/users)."""
	if not confirm:
		print("Destructive. Pass confirm=True to proceed.")
		return
	# Cancel + delete transactions
	for dt in ("Payment Entry", "Sales Invoice", "Journal Entry"):
		for name in frappe.get_all(dt, filters={"company": COMPANY}, pluck="name"):
			try:
				doc = frappe.get_doc(dt, name)
				if doc.docstatus == 1:
					doc.cancel()
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
			except Exception as e:
				print(f"  skipped {dt} {name}: {e}")
	for spec in DEMO_POLICIES:
		name = f"{spec['skill_id']}-{spec.get('priority', 100)}-{spec['role']}"
		if frappe.db.exists("Agent Skill Policy", name):
			frappe.delete_doc("Agent Skill Policy", name, force=True, ignore_permissions=True)
	for name in frappe.get_all("Pending Skill Approval", filters={"tid": frappe.local.site}, pluck="name"):
		frappe.delete_doc("Pending Skill Approval", name, force=True, ignore_permissions=True)
	frappe.db.commit()
	print("✓ Accounting demo reset complete")
