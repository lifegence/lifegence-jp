# Configuration Reference

Complete field reference for all settings DocTypes in lifegence_jp. For initial setup instructions, see the [Setup Guide](setup.md).

## Table of Contents

- [BPM Settings](#bpm-settings)
- [JP HR Settings](#jp-hr-settings)
- [JP Invoice Settings](#jp-invoice-settings)
- [Role Assignments](#role-assignments)
- [Workflow Customization](#workflow-customization)

---

## BPM Settings

Navigate to: **BPM > BPM Settings**

Global configuration for the BPM workflow automation module.

### General Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_automation` | Check | 0 | Master switch for BPM automation. When disabled, no BPM Actions are triggered on workflow state changes. |
| `default_timeout` | Int | 30 | Timeout in seconds for webhook and n8n API calls. |
| `max_retry_count` | Int | 3 | Maximum number of retry attempts for failed BPM Actions. |
| `log_retention_days` | Int | 90 | Number of days to retain BPM Action Log entries. Older entries are automatically deleted. |

### n8n Integration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `n8n_base_url` | Data | (empty) | Base URL of your n8n instance (e.g., `https://n8n.example.com`). Required for n8n Workflow action type. |
| `n8n_api_key` | Password | (empty) | API key for authenticating with the n8n instance. Stored encrypted. |

#### Setting up n8n integration

1. Deploy an n8n instance (self-hosted or cloud).
2. Generate an API key in n8n under **Settings > API**.
3. Enter the n8n base URL and API key in BPM Settings.
4. Enable automation by checking `enable_automation`.
5. Create BPM Actions with action type "n8n Workflow" and specify the workflow ID.

The n8n base URL should not include a trailing slash. Example: `https://n8n.example.com` (not `https://n8n.example.com/`).

### BPM Action Configuration

Each BPM Action document defines an automation that triggers on workflow state changes. The action is configured separately from BPM Settings.

| Field | Description |
|-------|-------------|
| Action Type | One of: Webhook, n8n Workflow, Frappe API, Custom Script |
| Document Type | The DocType this action applies to |
| From State | The workflow state before the transition (leave blank for any) |
| To State | The workflow state after the transition (leave blank for any) |
| URL / Workflow ID | Target URL for Webhook, or n8n workflow ID |
| API Method | Frappe API method path (for Frappe API type) |
| Script | Python code to execute (for Custom Script type) |
| Enabled | Whether this action is active |

---

## JP HR Settings

Navigate to: **JP HR > JP HR Settings**

Global configuration for the Japanese HR module.

### Organization Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `health_insurance_association` | Data | (empty) | Name of the health insurance association (健康保険組合) your company belongs to. Used for premium calculation with association-specific rates. |
| `pension_office_code` | Data | (empty) | The pension office code (年金事務所コード) for your jurisdiction. |

### Insurance Calculation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `employment_insurance_rate_type` | Select | General | Industry classification for employment insurance rates. Options: **General** (一般), **Construction** (建設業), **Agriculture** (農林水産業). |
| `auto_calculate_premiums` | Check | 1 | When enabled, social insurance premiums are automatically recalculated when the Standard Monthly Remuneration changes. |

### Fiscal Year

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fiscal_year_start` | Select | April | The starting month of the fiscal year. Options: **April** (4月) or **January** (1月). Most Japanese companies use April. |

### Notes

- The `employment_insurance_rate_type` determines which rate column is used from the labor insurance rate tables. General applies to most businesses.
- Setting `health_insurance_association` is required for accurate premium calculation. If left blank, the system uses default Kyokai Kenpo (協会けんぽ) rates.
- Changing `auto_calculate_premiums` does not retroactively recalculate existing records.

---

## JP Invoice Settings

Navigate to: **JP Accounting > JP Invoice Settings**

Company-level settings for the Qualified Invoice System (適格請求書等保存方式 / インボイス制度) and electronic invoicing.

### Company Registration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company_registration_number` | Data | (empty) | The 13-digit corporate number (法人番号) assigned by the National Tax Agency. |
| `qualified_invoice_issuer_number` | Data | (empty) | The Qualified Invoice Issuer registration number. Format: **T** followed by 13 digits (e.g., T1234567890123). |

### Tax Rates

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_tax_rate` | Percent | 10 | The standard consumption tax rate applied to invoices. |
| `reduced_tax_rate` | Percent | 8 | The reduced tax rate for qualifying items (food and beverages, newspapers). |

### Electronic Invoicing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_e_invoice` | Check | 0 | Enable electronic invoice generation and processing. |
| `e_invoice_format` | Select | (empty) | The e-invoice standard to use. Options: **Peppol BIS** (European standard adopted in Japan), **JP PINT** (Japan-specific Peppol adaptation). |

### About the Qualified Invoice System

The Qualified Invoice System (インボイス制度), effective since October 2023, requires businesses to issue invoices with specific information for consumption tax credit purposes. Key points:

- Only registered Qualified Invoice Issuers can issue invoices that allow buyers to claim input tax credits.
- The registration number (T + 13 digits) must appear on all qualifying invoices.
- Both standard (10%) and reduced (8%) tax rates must be itemized separately on invoices.
- The `qualified_invoice_issuer_number` can be verified on the NTA's public registry.

---

## Role Assignments

The BPM module installs 10 roles. Assign these to users in **Setup > User** under the Roles tab.

### BPM Approval Roles

| Role | Purpose | Typical Assignment |
|------|---------|-------------------|
| CRM Approver | Approve/qualify Leads and Opportunities | Sales team leaders |
| Approval Manager | Approve documents up to 5M JPY | Department managers |
| Approval Director | Approve documents up to 20M JPY | Division directors |
| Approval Executive | Approve documents above 20M JPY | C-level executives |
| Budget Controller | Verify purchase order budgets | Finance team members |
| Ringi Approver | Approve Ringi documents | Varies by organization |
| General Affairs | Process seal requests and general applications | General affairs staff |
| Legal Reviewer | Legal review step in seal request workflow | Legal department |

### JP HR Roles

| Role | Purpose | Typical Assignment |
|------|---------|-------------------|
| HR Manager | Full access to JP HR module including My Number | HR department heads |
| HR User | Standard access to JP HR features (no My Number access) | HR staff |

### Assignment Guidelines

- A user can hold multiple roles (e.g., a director may have both Approval Manager and Approval Director).
- Approval roles determine which workflow transitions a user can execute. Without the correct role, the approve/reject buttons will not appear.
- My Number access is restricted to HR Manager and System Manager for compliance with the My Number Act.

---

## Workflow Customization

The pre-installed workflows can be customized to match your organization's specific requirements.

### Modifying Approval Thresholds

1. Navigate to **Setup > Authorization Rule**.
2. Find the rule for the relevant DocType (e.g., Quotation).
3. Adjust the `above_value` and `approving_role` fields.
4. Save the rule.

Example: To require Director approval for quotations above 3M JPY instead of 5M JPY, change the Approval Manager rule's `above_value` to 3000000.

### Adding Workflow Steps

1. Navigate to **Setup > Workflow** and select the workflow to modify.
2. Add new states to the Workflow States table.
3. Add transitions between states in the Workflow Transitions table, specifying the required role and action.
4. Save and test the workflow with a sample document.

### Best Practices

- **Test changes in a development environment** before applying to production. Workflow changes take effect immediately and may affect in-progress documents.
- **Do not delete workflow states** that are referenced by existing documents. Change in-progress documents to a valid state first.
- **Document your changes** so that customizations are preserved during app updates. Custom workflows may be overwritten by fixture updates during `bench migrate`.
- To prevent fixture overwrites, remove the modified workflow from the fixtures list in `hooks.py` or use Frappe's `fixtures` configuration to exclude specific records.

---

## See Also

- [Setup Guide](setup.md) -- installation and initial configuration
- [Module Documentation](modules.md) -- DocType details and API reference
- [Troubleshooting](troubleshooting.md) -- common issues and solutions
