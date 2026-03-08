# Troubleshooting

Common issues and solutions for lifegence_jp. For setup instructions, see the [Setup Guide](setup.md). For configuration details, see the [Configuration Reference](configuration.md).

## Table of Contents

- [BPM Module Issues](#bpm-module-issues)
- [JP HR Module Issues](#jp-hr-module-issues)
- [JP Accounting Module Issues](#jp-accounting-module-issues)
- [General Issues](#general-issues)

---

## BPM Module Issues

### Workflow not triggering on document update

**Symptom:** Updating a document's workflow state does not trigger any BPM Actions.

**Possible causes and solutions:**

1. **Automation is disabled in BPM Settings.**
   - Navigate to **BPM > BPM Settings**.
   - Confirm that `enable_automation` is checked.

2. **No matching BPM Action exists.**
   - Navigate to **BPM > BPM Action** and verify that an action exists for the relevant DocType and state transition.
   - Check that the BPM Action's `Enabled` checkbox is checked.
   - Verify that the `From State` and `To State` fields match the actual workflow transition occurring on the document.

3. **The doc_events hook is not loaded.**
   - Run `bench --site your-site migrate` to ensure hooks are registered.
   - Restart the bench: `bench restart`.

4. **Error in the BPM Action execution.**
   - Check **BPM > BPM Action Log** for error entries related to the action.
   - Review the Frappe error log: `bench --site your-site show-error-log` or navigate to **Setup > Error Log** in the web interface.

### Approval not escalating to the correct role

**Symptom:** A document requiring Director or Executive approval is being approved by a Manager, or the escalation step is skipped.

**Possible causes and solutions:**

1. **Authorization Rules are misconfigured.**
   - Navigate to **Setup > Authorization Rule**.
   - Verify that rules exist for the correct DocType (Quotation, Sales Order, or Purchase Order).
   - Check that the `above_value` thresholds are set correctly. The value is in the document's currency (typically JPY).
   - Ensure each rule has the correct `approving_role` assigned.

2. **Amount field is not populated.**
   - The Authorization Rule checks the document's grand total or base amount. Confirm the amount field contains a value before submitting for approval.

3. **User has multiple approval roles.**
   - If a user holds both Approval Manager and Approval Director roles, the system may allow approval at the lower threshold. Review role assignments in **Setup > User**.

### n8n integration not working

**Symptom:** BPM Actions with type "n8n Workflow" fail or produce no result.

**Possible causes and solutions:**

1. **n8n URL or API key is incorrect.**
   - Navigate to **BPM > BPM Settings**.
   - Verify that `n8n_base_url` is correct and does not include a trailing slash.
   - Confirm the API key is valid and has not expired.

2. **Network connectivity issue.**
   - From the Frappe server, test connectivity to the n8n instance:
     ```bash
     curl -s -o /dev/null -w "%{http_code}" https://n8n.example.com/api/v1/workflows -H "X-N8N-API-KEY: your-api-key"
     ```
   - A `200` response confirms connectivity. A timeout or connection error indicates a network or firewall issue.

3. **n8n workflow is inactive.**
   - Log in to your n8n instance and verify that the target workflow is active (not paused or disabled).

4. **Timeout exceeded.**
   - If the n8n workflow takes longer than the configured `default_timeout` (default: 30 seconds), the call will time out. Increase the timeout value in BPM Settings or optimize the n8n workflow.

5. **Check BPM Action Log.**
   - Navigate to **BPM > BPM Action Log** and look for entries with error status. The log entry contains the response body and error message from the n8n call.

### Webhook receive endpoint returning 403

**Symptom:** External systems receive a 403 Forbidden response when calling the webhook receive endpoint.

**Solution:**
- The `webhook.receive` endpoint allows guest access, but the request must include a valid HMAC-SHA256 signature in the request headers.
- Verify that the sending system is computing the signature correctly using the shared secret.
- Check the Frappe error log for signature validation failures.

---

## JP HR Module Issues

### My Number access denied

**Symptom:** A user receives a permission error when trying to view or access My Number records.

**Possible causes and solutions:**

1. **User lacks the required role.**
   - My Number access requires **HR Manager** or **System Manager** role.
   - The **HR User** role does not grant My Number access.
   - Navigate to **Setup > User**, select the user, and verify their roles under the Roles tab.

2. **Access purpose not specified.**
   - When using the `access_my_number` API, the `purpose` parameter is required. Calls without a purpose will be rejected.

3. **Checking access history.**
   - All access attempts (successful and denied) are recorded in **JP HR > My Number Access Log**. Review the log to understand the denial reason.

### Withholding tax calculation returns incorrect amount

**Symptom:** The calculated monthly withholding tax does not match expected values.

**Possible causes and solutions:**

1. **Withholding Tax Table is not loaded.**
   - Navigate to **JP HR > Withholding Tax Table** and confirm that the current year's table exists (e.g., "令和7年").
   - If missing, run `bench --site your-site migrate` to load the fixture data.

2. **Incorrect dependents count.**
   - The withholding tax calculation uses the number of dependents to select the correct column in the Class A (甲欄) table.
   - Verify that the employee's dependent count is correct in their HR record.
   - If the employee has not submitted a dependent deduction declaration (扶養控除等申告書), Class B (乙欄) should be used instead of Class A.

3. **Salary amount falls outside table range.**
   - The NTA table covers specific salary ranges. If the gross salary exceeds the maximum row in the table, the calculation may return an unexpected result or error.
   - Check the table's maximum salary row and verify the input amount.

### Social insurance premium mismatch

**Symptom:** Calculated social insurance premiums do not match the expected amounts from your insurance association or the official rate table.

**Possible causes and solutions:**

1. **Rate table effective dates.**
   - Social insurance rates are updated annually (typically effective March or April). Ensure you are using the rate table for the correct period.
   - Navigate to **JP HR > Social Insurance Rate** and verify the effective dates on the applicable rate record.

2. **Wrong prefecture selected.**
   - Health insurance rates vary by prefecture. Confirm that the employee's insurance records reference the correct prefecture.

3. **Health insurance association mismatch.**
   - If your company belongs to a union-managed health insurance association (組合管掌健保), the rates differ from the standard Kyokai Kenpo rates.
   - Set the correct association in **JP HR > JP HR Settings** > `health_insurance_association`.

4. **Standard Monthly Remuneration grade is outdated.**
   - Premiums are calculated based on the Standard Monthly Remuneration (標準報酬月額) grade. If the grade has not been updated to reflect salary changes, the premium will be incorrect.
   - Update the employee's Standard Monthly Remuneration record to the current grade.

### Overtime alerts not being generated

**Symptom:** Employees are approaching or exceeding overtime limits, but no alerts appear in the Overtime Alert Log.

**Possible causes and solutions:**

1. **No Overtime Agreement exists.**
   - Navigate to **JP HR > Overtime Agreement** and confirm that an agreement is defined for the employee's department or the company.

2. **Attendance or timesheet data is missing.**
   - Overtime calculations depend on recorded attendance or timesheet entries. Verify that the employee's working hours are being tracked.

3. **Threshold configuration.**
   - Alerts are generated when overtime approaches the configured limits (45h/month, 360h/year for general; 100h/month, 720h/year for special). If customized thresholds are set on the Overtime Agreement, verify they are correct.

---

## JP Accounting Module Issues

### Qualified Invoice issuer number validation error

**Symptom:** The system rejects the Qualified Invoice Issuer registration number.

**Solution:**
- The number must follow the format **T** (uppercase) followed by exactly 13 digits.
- Example of valid format: `T1234567890123`.
- Do not include spaces, hyphens, or other characters.
- Verify the number on the [NTA's Qualified Invoice Issuer Public Registry](https://www.invoice-kohyo.nta.go.jp/).

### Withholding tax rule not applied to a payment

**Symptom:** A payment to a vendor does not have withholding tax applied.

**Possible causes and solutions:**

1. **No matching Withholding Tax Rule exists.**
   - Navigate to **JP Accounting > Withholding Tax Rule** and verify that a rule exists for the applicable income type.

2. **Income type mismatch.**
   - The Withholding Tax Rule matches by income type. Confirm that the vendor's payment category corresponds to one of the six defined income types (Fees/Commissions, Salary, Retirement, Dividend, Interest, Other).

---

## General Issues

### Fixtures not loaded after migration

**Symptom:** Workflows, roles, rate tables, or settings are missing after running `bench migrate`.

**Solution:**

```bash
bench --site your-site migrate
bench --site your-site clear-cache
bench restart
```

If fixtures are still missing, verify the app is installed:

```bash
bench --site your-site list-apps
```

If `lifegence_jp` is not listed, reinstall it:

```bash
bench --site your-site install-app lifegence_jp
bench --site your-site migrate
```

### Permission errors on module pages

**Symptom:** Users see "Insufficient Permission" when accessing BPM, JP HR, or JP Accounting pages.

**Solution:**
- Assign the appropriate module access role to the user in **Setup > User**.
- For BPM: any of the BPM approval roles grants module access.
- For JP HR: HR Manager or HR User role is required.
- For JP Accounting: Accounts User or Accounts Manager role is required (standard ERPNext roles).

### App update overwrites custom workflows

**Symptom:** After running `bench get-app lifegence_jp --upgrade` and `bench migrate`, custom workflow modifications are reverted to defaults.

**Solution:**
- The app uses Frappe fixtures to manage workflows. Running `bench migrate` re-imports fixture data, which can overwrite customizations.
- To preserve custom workflows, remove the specific workflow from the fixtures list in `hooks.py` before migrating, or maintain your customizations in a separate custom app.

---

## Getting Help

If you cannot resolve an issue using this guide:

1. Check the Frappe error log: **Setup > Error Log** or `bench --site your-site show-error-log`.
2. Review the BPM Action Log for automation-related issues.
3. Open an issue on [GitHub](https://github.com/lifegence/lifegence-jp/issues) with:
   - The steps to reproduce the problem
   - Relevant error messages from the error log
   - Your Frappe/ERPNext version (`bench version`)
   - Your lifegence_jp version

---

## See Also

- [Setup Guide](setup.md) -- installation and initial configuration
- [Module Documentation](modules.md) -- DocType details and API reference
- [Configuration Reference](configuration.md) -- complete settings field reference
