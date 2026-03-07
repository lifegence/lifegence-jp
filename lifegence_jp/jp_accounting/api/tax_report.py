import frappe
from frappe.utils import getdate, get_first_day, get_last_day


@frappe.whitelist()
def get_withholding_tax_summary(year=None, month=None):
    """Get withholding tax summary for a given period."""
    if not year:
        year = getdate().year

    filters = {"docstatus": 1}

    if month:
        start_date = get_first_day(f"{year}-{month:02d}-01")
        end_date = get_last_day(f"{year}-{month:02d}-01")
        filters["payment_date"] = ["between", [start_date, end_date]]
    else:
        filters["payment_date"] = ["between", [f"{year}-01-01", f"{year}-12-31"]]

    entries = frappe.get_all(
        "Withholding Tax Entry",
        filters=filters,
        fields=["payee_name", "gross_amount", "tax_amount", "net_amount", "payment_date"],
        order_by="payment_date asc",
    )

    total_gross = sum(e.gross_amount or 0 for e in entries)
    total_tax = sum(e.tax_amount or 0 for e in entries)

    return {
        "entries": entries,
        "total_gross": total_gross,
        "total_tax": total_tax,
        "total_net": total_gross - total_tax,
        "count": len(entries),
    }
