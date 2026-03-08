# Module Documentation

lifegence_jp provides three modules for Japanese business operations. This document covers each module's DocTypes, workflows, APIs, and pre-installed data.

## Table of Contents

- [BPM Module](#bpm-module)
- [JP HR Module](#jp-hr-module)
- [JP Accounting Module](#jp-accounting-module)

---

## BPM Module

**Japanese name:** ワークフロー

An approval workflow engine with n8n integration for business process automation. The BPM module provides multi-level approval workflows with amount-based escalation, Ringi (formal approval request) management, and webhook-driven automation.

### DocTypes

| DocType | Purpose |
|---------|---------|
| BPM Settings | Global configuration for the BPM module (automation toggle, timeouts, n8n connection) |
| BPM Action | Defines an automation action (Webhook, n8n Workflow, Frappe API, or Custom Script) |
| BPM Action Log | Audit log of executed BPM actions with results and timestamps |
| Ringi | Formal approval request document (稟議書) |
| Ringi Approver | Child table linking approvers to a Ringi document |
| Ringi Template | Reusable template for Ringi documents |
| Ringi Template Approver | Child table defining default approvers for a Ringi Template |
| Seal Request | Request for company seal (社印) usage approval |
| General Application | Multipurpose application form for internal requests |
| Application Template | Reusable template for General Application documents |

### Approval Workflows

The module installs 8 workflows that apply to both standard ERPNext documents and custom BPM DocTypes.

#### ERPNext Document Workflows

| Workflow | Document | Flow |
|----------|----------|------|
| Lead Approval | Lead | Draft -> Pending Review -> Qualified / Unqualified |
| Opportunity Approval | Opportunity | Draft -> Pending Review -> Converted / Lost |
| Quotation Approval | Quotation | Draft -> Pending Manager Approval -> (escalation) -> Approved / Rejected |
| Sales Order Approval | Sales Order | Draft -> Pending Manager Approval -> (escalation) -> Confirmed / Rejected |
| Purchase Order Approval | Purchase Order | Draft -> Pending Manager Approval -> Pending Budget Check -> (escalation) -> Approved / Rejected |

#### BPM DocType Workflows

| Workflow | Document | Flow |
|----------|----------|------|
| Ringi Approval | Ringi | Draft -> Pending Supervisor Approval -> Pending Department Head Approval -> Approved / Rejected |
| Seal Request Approval | Seal Request | Draft -> Pending Legal Review -> Pending General Affairs -> Approved / Rejected |
| General Application Approval | General Application | Draft -> Pending HR Review -> Completed / Rejected |

#### Amount-Based Escalation

For Quotation, Sales Order, and Purchase Order workflows, approval authority escalates based on document amount:

| Amount Range (JPY) | Required Approver Role |
|---------------------|----------------------|
| Up to 5,000,000 | Approval Manager |
| 5,000,001 -- 20,000,000 | Approval Director |
| Above 20,000,000 | Approval Executive |

These thresholds are configured via Authorization Rules installed during setup. Adjust them in **Setup > Authorization Rule** to match your organization's policies.

### BPM Action Types

BPM Actions trigger when a document's workflow state changes. The `doc_events` hook monitors `on_update` for all DocTypes and routes matching state changes to the dispatcher.

| Action Type | Description |
|-------------|-------------|
| Webhook | Send HTTP POST to an external URL with document data |
| n8n Workflow | Trigger an n8n workflow via the n8n API |
| Frappe API | Call a whitelisted Frappe API method |
| Custom Script | Execute a server-side Python script |

Each BPM Action can specify conditions (document type, workflow state transition) that determine when it fires.

### API Reference

All API endpoints are accessible at `/api/method/lifegence_jp.bpm.api.<module>.<function>`.

#### Workflow API (`lifegence_jp.bpm.api.workflow`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `get_pending_approvals` | `user` (optional) | Returns documents awaiting approval for the given user (defaults to current user) |
| `apply_action` | `doctype`, `name`, `action` | Applies a workflow action to a document |
| `get_workflow_status` | `doctype`, `name` | Returns the current workflow state of a document |
| `get_workflow_history` | `doctype`, `name` | Returns the workflow transition history for a document |

#### Ringi API (`lifegence_jp.bpm.api.ringi`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `get_pending_ringis` | `user` (optional) | Returns Ringi documents awaiting approval |
| `approve_ringi` | `name`, `comments` (optional) | Approves a Ringi document |
| `return_ringi` | `name`, `comments` | Returns a Ringi to its submitter with comments |
| `get_ringi_summary` | `filters` (optional) | Returns summary statistics for Ringi documents |

#### Webhook API (`lifegence_jp.bpm.api.webhook`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `receive` | (request body) | Receives incoming webhooks. Guest access allowed. Validates HMAC-SHA256 signature. |

### Pre-Installed Data

**Roles (8):**
CRM Approver, Approval Manager, Approval Director, Approval Executive, Budget Controller, Ringi Approver, General Affairs, Legal Reviewer

**Workflow States (21):**
Draft, Pending Review, Pending Manager Approval, Pending Director Approval, Pending Executive Approval, Pending Budget Check, Approved, Rejected, Cancelled, Qualified, Unqualified, Converted, Lost, Confirmed, Submitted, Pending Supervisor Approval, Pending Department Head Approval, Pending Legal Review, Pending General Affairs, Pending HR Review, Completed

**Workflow Action Masters (17):**
Submit for Review, Approve, Reject, Request Changes, Escalate to Director, Escalate to Executive, Qualify, Disqualify, Mark as Lost, Convert, Confirm, Submit for Budget Check, Pass Budget Check, Cancel, Submit for Approval, Return, Complete

---

## JP HR Module

**Japanese name:** 人事労務

Japanese HR and payroll management module covering social insurance, withholding tax, overtime tracking, My Number management, and year-end adjustment.

### DocTypes

| DocType | Purpose |
|---------|---------|
| JP HR Settings | Global configuration for the JP HR module |
| Social Insurance Rate | Insurance rate tables by prefecture and fiscal year (健康保険・厚生年金保険料率) |
| Standard Monthly Remuneration | Employee's standard monthly remuneration grade (標準報酬月額) |
| Social Insurance Record | Employee's social insurance enrollment and premium records |
| Labor Insurance Record | Employee's labor insurance records (労災保険・雇用保険) |
| Overtime Agreement | 36 Agreement (三六協定) definitions with hour limits |
| Overtime Alert Log | Alerts generated when employees approach overtime limits |
| My Number Record | Encrypted storage of Individual Number (マイナンバー) |
| My Number Access Log | Audit log of all access to My Number records |
| Withholding Tax Table | Monthly withholding tax amount tables from the NTA (源泉徴収税額表) |
| Remuneration Calculation | Calculation records for employee compensation |
| Resident Tax | Annual resident tax data by employee (住民税) |
| Resident Tax Monthly | Monthly resident tax deduction amounts |
| Year End Adjustment | Year-end tax adjustment document (年末調整) |
| Year End Adjustment Deduction | Child table for deduction entries in Year End Adjustment |

### Social Insurance

The module includes rate tables for health insurance and employee pension (Kousei Nenkin) premiums. Rates vary by prefecture and are updated annually.

Key features:
- Automatic premium calculation based on Standard Monthly Remuneration grade
- Support for different health insurance associations (Kyokai Kenpo, union-managed)
- Labor insurance tracking (Workers' Compensation, Employment Insurance)

### Withholding Tax

Built-in withholding tax tables based on the National Tax Agency (NTA) Reiwa 7 schedule.

- **Class A (甲欄):** For employees who have submitted a dependent deduction declaration. Columns for 0 through 7 dependents.
- **Class B (乙欄):** For employees without a dependent deduction declaration. A single flat column.

### Overtime Management (36 Agreement)

Tracks employee overtime against 36 Agreement limits defined by your labor-management agreement.

**General limits (standard employees):**

| Period | Limit |
|--------|-------|
| Monthly | 45 hours |
| Annual | 360 hours |

**Special provision limits (when special clause applies):**

| Period | Limit |
|--------|-------|
| Monthly | 100 hours |
| Annual | 720 hours |

Overtime Alert Logs are generated when an employee approaches or exceeds configured thresholds.

### My Number Management

My Number (Individual Number / マイナンバー) records are stored with encryption and strict access controls.

- Storage is encrypted in the database
- Every access is logged in My Number Access Log with the action type (View, Export, Provide, Delete)
- Access requires **HR Manager** or **System Manager** role
- Designed for compliance with the My Number Act (番号法)

### Year End Adjustment

The Year End Adjustment (年末調整) document supports 11 deduction types and can auto-populate data from the employee's social insurance and withholding records.

### API Reference

All API endpoints are accessible at `/api/method/lifegence_jp.jp_hr.api.<module>.<function>`.

#### Overtime API (`lifegence_jp.jp_hr.api.overtime`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `check_overtime_against_agreement` | `employee`, `month` (optional) | Checks an employee's current overtime against their 36 Agreement limits |
| `get_overtime_alerts` | `employee` (optional), `status` (optional) | Returns overtime alert logs, optionally filtered by employee and status |

#### My Number API (`lifegence_jp.jp_hr.api.my_number`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `get_my_number_masked` | `employee` | Returns the masked My Number (last 4 digits visible) |
| `access_my_number` | `employee`, `purpose` | Retrieves the full My Number and logs the access. Requires HR Manager or System Manager. |
| `check_my_number_status` | `employee` | Returns whether a My Number record exists for the employee |

#### Social Insurance API (`lifegence_jp.jp_hr.api.social_insurance`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `calculate_premiums` | `employee`, `effective_date` (optional) | Calculates health insurance and pension premiums based on current remuneration grade |
| `get_employee_insurance_summary` | `employee` | Returns a summary of the employee's insurance enrollment and premium details |

#### Withholding Tax API (`lifegence_jp.jp_hr.api.withholding_tax`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `calculate_monthly_withholding` | `employee`, `gross_salary`, `dependents_count` | Calculates the monthly withholding tax amount using the NTA table |
| `get_employee_annual_withholding` | `employee`, `fiscal_year` | Returns the total annual withholding tax for an employee |

#### Year End Adjustment API (`lifegence_jp.jp_hr.api.year_end_adjustment`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `auto_populate_year_end_data` | `employee`, `fiscal_year` | Auto-populates the Year End Adjustment document with data from social insurance and withholding records |

---

## JP Accounting Module

**Japanese name:** 会計

Japanese accounting and invoicing compliance module supporting the Qualified Invoice System (インボイス制度) and withholding tax on payments.

### DocTypes

| DocType | Purpose |
|---------|---------|
| JP Invoice Settings | Company-level settings for the Qualified Invoice System and e-invoicing |
| Withholding Tax Entry | Individual withholding tax transaction record for payments to vendors/individuals |
| Withholding Tax Rule | Rules defining withholding tax rates by income type |

### Qualified Invoice System (インボイス制度)

Since October 2023, Japan's Qualified Invoice System requires registered businesses to issue invoices containing specific information (including the issuer's registration number) for consumption tax credit purposes.

JP Invoice Settings stores:
- The company's 13-digit corporate number
- The Qualified Invoice Issuer registration number (T + 13 digits)
- Default and reduced tax rates
- Electronic invoice configuration

### Withholding Tax Rules

Six income types are supported with their corresponding withholding rates:

| Income Type | Japanese | Description |
|-------------|----------|-------------|
| Fees/Commissions | 報酬・料金 | Professional fees, consulting, etc. |
| Salary | 給与 | Employee salary income |
| Retirement | 退職 | Retirement income |
| Dividend | 配当 | Dividend income |
| Interest | 利子 | Interest income |
| Other | その他 | Other income types |

### API Reference

#### Tax Report API (`lifegence_jp.jp_accounting.api.tax_report`)

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `get_withholding_tax_summary` | `company`, `fiscal_year`, `income_type` (optional) | Returns a summary of withholding tax entries, optionally filtered by income type |

---

## See Also

- [Setup Guide](setup.md) -- installation and initial configuration
- [Configuration Reference](configuration.md) -- complete settings field reference
- [Troubleshooting](troubleshooting.md) -- common issues and solutions
