# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from typing import Dict, Any, Optional


@frappe.whitelist()
def get_year_end_adjustment_guide(
	employee: Optional[str] = None,
	topic: Optional[str] = None,
) -> Dict[str, Any]:
	"""Provide year-end adjustment guidance and deduction explanations."""
	try:
		guide = {
			"success": True,
			"title": "年末調整ガイド",
			"deduction_types": [
				{
					"name": "基礎控除",
					"amount": "480,000円（所得2,400万円以下）",
					"description": "全ての納税者に適用される基本控除",
				},
				{
					"name": "配偶者控除",
					"amount": "最大380,000円",
					"description": "配偶者の合計所得が48万円以下の場合に適用",
				},
				{
					"name": "扶養控除",
					"amount": "380,000〜630,000円",
					"description": "一般38万・特定63万・老人48万・同居老親58万",
				},
				{
					"name": "生命保険料控除",
					"amount": "最大120,000円",
					"description": "一般・介護医療・個人年金の3区分、各最大4万円",
				},
				{
					"name": "地震保険料控除",
					"amount": "最大50,000円",
					"description": "地震保険料の全額（上限5万円）",
				},
				{
					"name": "住宅借入金等特別控除",
					"amount": "借入金残高の0.7%",
					"description": "住宅ローン減税（税額控除）、初年度は確定申告が必要",
				},
			],
			"workflow": [
				"1. 従業員が控除申告書を提出",
				"2. 給与・社保データを集計",
				"3. 各種控除額を計算",
				"4. 年税額を算出",
				"5. 源泉徴収済額との過不足を計算",
				"6. 還付または徴収を実施",
			],
		}

		if employee and frappe.db.exists("Employee", employee):
			employee_name = frappe.db.get_value("Employee", employee, "employee_name")
			guide["employee"] = employee
			guide["employee_name"] = employee_name

			# Check for existing year-end adjustment
			current_year = frappe.utils.now_datetime().year
			yea = frappe.db.get_value(
				"Year End Adjustment",
				{"employee": employee, "fiscal_year": current_year},
				["name", "status"],
				as_dict=True,
			)
			if yea:
				guide["existing_adjustment"] = yea

		return guide

	except Exception as e:
		return {"success": False, "error": str(e)}
