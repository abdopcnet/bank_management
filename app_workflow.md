# Workflow

## Bank Reconciliation Flow

```
1. Record Payment Entry / Journal Entry
   ├─ Set reference_no / cheque_no
   └─ Submit

2. Upload Bank Statement
   ├─ Select file (CSV/XLS/XLSX)
   ├─ Import transactions
   └─ Bank Transactions created (Submitted)

3. Bank Reconciliation Tool
   ├─ Select company, bank_account
   ├─ Set date range
   ├─ Set closing balance
   └─ Get Unreconciled Entries

4. Auto Reconcile
   ├─ Match by: reference_number + Date
   └─ Automatically reconcile matches

5. Manual Reconciliation
   ├─ For unmatched transactions:
   │   ├─ Match Against Voucher
   │   │   ├─ Search for vouchers
   │   │   ├─ Select vouchers
   │   │   └─ Reconcile
   │   ├─ Create Payment Entry
   │   │   └─ Auto-create and link
   │   ├─ Create Journal Entry
   │   │   └─ Auto-create and link
   │   └─ Update Bank Transaction
   │       └─ Set reference_number, party

6. Verify Reconciliation
   ├─ Check Statistics: Difference = 0
   └─ Verify Bank Reconciliation Statement
```

## Bulk Bank Transaction Import

```
1. Create Bulk Bank Transaction
   ├─ Select bank_account
   ├─ Add transactions to table
   └─ Save

2. Create Bank Transactions
   ├─ Click "Create Bank Transactions"
   ├─ Validates rows
   ├─ Creates Bank Transaction (Draft) for each row
   └─ Links to bulk document

3. Review and Submit
   ├─ Review draft transactions
   └─ Submit individually or in bulk
```

## Create Bank Transaction from Voucher

```
User Clicks "Create Bank Transaction"
    ↓
Select Voucher (Payment Entry / Journal Entry)
    ↓
Extract Bank Account from Voucher
    ↓
Extract Amount (deposit/withdrawal)
    ↓
Create Bank Transaction
    ↓
Submit Bank Transaction
    ↓
Auto-reconcile with source voucher
```

