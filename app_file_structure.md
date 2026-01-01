# File Structure

```
bank_management/
├── hooks.py
├── bank_management/
│   ├── doctype/
│   │   ├── bulk_bank_transaction/
│   │   │   ├── bulk_bank_transaction.py
│   │   │   ├── bulk_bank_transaction.js
│   │   │   └── bulk_bank_transaction.json
│   │   └── bank_transactions_table/
│   │       ├── bank_transactions_table.py
│   │       └── bank_transactions_table.json
│   ├── report/
│   │   └── bank_reconcile_report/
│   │       ├── bank_reconcile_report.py
│   │       ├── bank_reconcile_report.js
│   │       └── bank_reconcile_report.json
│   ├── workspace/
│   │   └── bank_management/
│   │       └── bank_management.json
│   └── public/
│       └── js/
│           └── bank_transaction.js
└── templates/
    └── pages/
```

## Key Files

- `hooks.py` - App hooks (doctype_js for Bank Transaction)
- `bulk_bank_transaction/` - Bulk import DocType
- `bank_reconcile_report/` - Bank reconciliation report
- `bank_transaction.js` - Bank Transaction form customization

