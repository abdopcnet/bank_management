# API Tree

## DocType Methods

### Bulk Bank Transaction

- `create_bank_transactions()`
  - Description: Create all Bank Transactions from table as Draft
  - Returns: created (count), errors (list)

## Report Methods

### Bank Reconcile Report

- `create_bank_transaction_from_voucher(voucher_doc_type, voucher_name, bank_account=None)`
  - Description: Create Bank Transaction from Payment Entry or Journal Entry
  - Auto-reconciles with source voucher
  - Supported: Payment Entry, Journal Entry

## ERPNext Integration

Uses standard ERPNext Bank Reconciliation APIs:
- `get_bank_transactions()` - Get bank transactions
- `get_account_balance()` - Calculate account balance
- `auto_reconcile_vouchers()` - Auto-reconcile transactions
- `get_linked_payments()` - Get proposed vouchers
- `reconcile_vouchers()` - Execute reconciliation
- `create_payment_entry_bts()` - Create Payment Entry from bank transaction
- `create_journal_entry_bts()` - Create Journal Entry from bank transaction
- `update_bank_transaction()` - Update bank transaction fields

