# Lifegence JP

Japanese business process modules for [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/).

Provides workflow automation (BPM), Japanese HR/payroll, and Japanese accounting compliance features tailored for Japanese SMBs.

## Modules

### BPM (ワークフロー)
Approval workflow engine with n8n integration for business process automation.
- Multi-level approval workflows (Manager → Director → Executive)
- Ringi (稟議) and general application templates
- Seal request management
- Webhook-based automation with n8n

### JP HR (人事労務)
Japanese HR and payroll management.
- Social insurance rate calculation (社会保険)
- Withholding tax tables (源泉徴収)
- Overtime agreements (36協定)
- Japanese payroll compliance

### JP Accounting (会計)
Japanese accounting and invoicing compliance.
- Qualified Invoice System (インボイス制度) support
- JP Invoice Settings for tax compliance

## Prerequisites

- Python 3.10+
- Frappe Framework v15+
- ERPNext v15+

## Installation

```bash
bench get-app https://github.com/lifegence/lifegence-jp.git
bench --site your-site install-app lifegence_jp
```

## After Installation

Run migrations to set up fixtures:

```bash
bench --site your-site migrate
```

### BPM Setup
Configure BPM Settings with your n8n instance URL and API key if using workflow automation.

## License

MIT - see [LICENSE](LICENSE)

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/lifegence/lifegence-jp).
