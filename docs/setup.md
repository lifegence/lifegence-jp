# Setup Guide

This guide covers installing and configuring lifegence_jp, a Frappe/ERPNext app that provides Japanese business process modules: BPM (workflow automation), JP HR (human resources and payroll), and JP Accounting (invoicing and tax compliance).

## Prerequisites

| Requirement | Minimum Version |
|-------------|-----------------|
| Python | 3.10+ |
| Frappe Framework | v15+ |
| ERPNext | v15+ |

You need a working Frappe Bench environment with ERPNext already installed on your target site. See the [Frappe Bench documentation](https://frappeframework.com/docs/user/en/installation) for initial setup.

## Installation

### 1. Download the app

```bash
bench get-app https://github.com/lifegence/lifegence-jp.git
```

For a specific branch or tag:

```bash
bench get-app https://github.com/lifegence/lifegence-jp.git --branch main
```

### 2. Install the app on your site

```bash
bench --site your-site install-app lifegence_jp
```

### 3. Run migrations

```bash
bench --site your-site migrate
```

## What Happens After Installation

The `after_install` hook runs automatically during `install-app` and performs the following setup:

**BPM Module:**
- Creates 8 approval workflows (Lead, Opportunity, Quotation, Sales Order, Purchase Order, Ringi, Seal Request, General Application)
- Sets up Authorization Rules for amount-based approval escalation
- Installs Workflow States and Workflow Action Masters used by approval flows

**JP HR Module:**
- Creates default JP HR Settings with:
  - Employment insurance rate type set to General
  - Auto-calculate premiums enabled
  - Fiscal year start set to April

**Fixtures loaded via `bench migrate`:**
- 8 custom Roles (CRM Approver, Approval Manager, Approval Director, etc.)
- Workflow States (Draft, Pending Review, Approved, Rejected, etc.)
- Workflow Action Masters (Submit for Review, Approve, Reject, etc.)
- Authorization Rules for approval thresholds
- Social Insurance Rate tables
- Withholding Tax Tables (NTA Reiwa 7)
- Default settings documents (BPM Settings, JP HR Settings, JP Invoice Settings)

## Initial Configuration

After installation, configure each module for your organization. See the [Configuration Reference](configuration.md) for detailed field descriptions.

### BPM Module

1. Navigate to **BPM Settings** and review the default values.
2. If using n8n for workflow automation, set the `n8n_base_url` and `n8n_api_key` fields.
3. Assign approval roles to users as needed:
   - **CRM Approver** -- for Lead and Opportunity approvals
   - **Approval Manager** -- for standard-amount approvals
   - **Approval Director** -- for mid-range amount approvals
   - **Approval Executive** -- for high-amount approvals
   - **Budget Controller** -- for purchase order budget checks
   - **Ringi Approver** -- for Ringi document approvals
   - **General Affairs** -- for seal requests and general applications
   - **Legal Reviewer** -- for contract and legal review steps

4. Review the pre-installed Authorization Rules to confirm amount thresholds match your organization's policies (for example, Quotation approval: Manager up to 5M JPY, Director up to 20M JPY, Executive above 20M JPY).

### JP HR Module

1. Navigate to **JP HR Settings**.
2. Set the **health_insurance_association** to your organization's health insurance association name.
3. Set the **pension_office_code** for your jurisdiction.
4. Confirm the **employment_insurance_rate_type** matches your industry (General, Construction, or Agriculture).
5. Verify that Social Insurance Rate tables for the current fiscal year are loaded. These are included as fixtures -- run `bench --site your-site migrate` if they are missing.

### JP Accounting Module

1. Navigate to **JP Invoice Settings**.
2. Enter your **company_registration_number** (13-digit corporate number).
3. Enter your **qualified_invoice_issuer_number** (format: T + 13 digits) if your company is a registered Qualified Invoice issuer.
4. Set the **default_tax_rate** (typically 10%) and **reduced_tax_rate** (8%) as applicable.
5. If using electronic invoicing, enable **enable_e_invoice** and select the appropriate **e_invoice_format** (Peppol BIS or JP PINT).

## Updating the App

To update to the latest version:

```bash
cd ~/frappe-bench
bench get-app lifegence_jp --upgrade
bench --site your-site migrate
bench build
bench restart
```

If you are running in production with Supervisor:

```bash
sudo supervisorctl restart all
```

## Uninstalling

To remove the app from a site:

```bash
bench --site your-site uninstall-app lifegence_jp
bench remove-app lifegence_jp
```

Note that uninstalling removes the app's DocTypes and associated data from the site database. Back up your site before uninstalling.

## Next Steps

- [Module Documentation](modules.md) -- detailed description of all three modules, DocTypes, and APIs
- [Configuration Reference](configuration.md) -- complete settings field reference
- [Troubleshooting](troubleshooting.md) -- common issues and solutions

---

This software is released under the [MIT License](../LICENSE).
