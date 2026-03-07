# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MyNumberAccessLog(Document):
	def before_save(self):
		"""Prevent updates to existing logs (append-only)."""
		if not self.is_new():
			frappe.throw(_("マイナンバーアクセスログは変更できません（追記専用）"))

	def on_trash(self):
		"""Prevent deletion of access logs."""
		frappe.throw(_("マイナンバーアクセスログは削除できません（追記専用）"))
