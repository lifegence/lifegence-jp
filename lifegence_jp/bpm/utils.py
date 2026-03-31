# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


def get_current_employee():
	"""Return the Employee name linked to the current session user.

	Returns:
		str or None: Employee name if found, None otherwise.
	"""
	return frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		"name",
	)
