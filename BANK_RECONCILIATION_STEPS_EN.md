# Bank Reconciliation Steps - Quick Guide

## DocTypes and System Paths

### Main DocTypes Used in Bank Reconciliation:

| DocType Name                 | System Path                                                                  | Navigation Menu Path                     |
| ---------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------- |
| **Bank Transaction**         | `erpnext.accounts.doctype.bank_transaction.bank_transaction`                 | Accounting → Bank Transaction            |
| **Bank Reconciliation Tool** | `erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool` | Accounting → Bank Reconciliation Tool    |
| **Bank Statement Import**    | `erpnext.accounts.doctype.bank_statement_import.bank_statement_import`       | Accounting → Bank Statement Import       |
| **Payment Entry**            | `erpnext.accounts.doctype.payment_entry.payment_entry`                       | Accounting → Payment Entry               |
| **Journal Entry**            | `erpnext.accounts.doctype.journal_entry.journal_entry`                       | Accounting → Journal Entry               |
| **Bank Account**             | `erpnext.accounts.doctype.bank_account.bank_account`                         | Accounting → Setup → Bank Account        |
| **Mode of Payment**          | `erpnext.accounts.doctype.mode_of_payment.mode_of_payment`                   | Accounting → Setup → Mode of Payment     |
| **Account**                  | `erpnext.accounts.doctype.account.account`                                   | Accounting → Chart of Accounts → Account |

### Related Child/Table DocTypes:

| DocType Name                  | System Path                                                                    | Parent DocType           |
| ----------------------------- | ------------------------------------------------------------------------------ | ------------------------ |
| **Bank Transaction Payments** | `erpnext.accounts.doctype.bank_transaction_payments.bank_transaction_payments` | Bank Transaction (Table) |
| **Bank Clearance Detail**     | `erpnext.accounts.doctype.bank_clearance_detail.bank_clearance_detail`         | Bank Clearance (Table)   |
| **Mode of Payment Account**   | `erpnext.accounts.doctype.mode_of_payment_account.mode_of_payment_account`     | Mode of Payment (Table)  |

### Reports:

| Report Name                       | System Path                                                                           | Navigation Menu Path                    |
| --------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------- |
| **Bank Reconciliation Statement** | `erpnext.accounts.report.bank_reconciliation_statement.bank_reconciliation_statement` | Reports → Bank Reconciliation Statement |
| **Bank Clearance Summary**        | `erpnext.accounts.report.bank_clearance_summary.bank_clearance_summary`               | Reports → Bank Clearance Summary        |

### Old/Alternative DocTypes:

| DocType Name       | System Path                                              | Notes                                           |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------- |
| **Bank Clearance** | `erpnext.accounts.doctype.bank_clearance.bank_clearance` | Single DocType (legacy tool for clearance date) |

---

## 0. Setup: Create Bank Charges Account (Required Before Reconciliation)

**Path**: `Accounting → Chart of Accounts → New Account`

**⚠️ Important**: Bank charges are **Indirect Expenses** (not Direct Expenses).

**Account Structure in Chart of Accounts**:

```
Expenses (Root Type)
└── Indirect Expenses (Parent Group) ✅ Must be here
    ├── Administrative Expenses (Parent Group) ← Recommended
    │   └── Bank Charges (Account) ← Create here
    └── Miscellaneous Expenses (Parent Group) ← Alternative
        └── Bank Charges (Account) ← Or here
```

**Required Fields**:

| Field            | Value                         | Notes                                |
| ---------------- | ----------------------------- | ------------------------------------ |
| `account_name`   | **"Bank Charges"**            | Name of the account                  |
| `parent_account` | **"Administrative Expenses"** | Must be under Indirect Expenses only |
| `account_type`   | **"Expense Account"**         | Account type                         |
| `root_type`      | **"Expense"**                 | Auto-filled                          |
| `report_type`    | **"Profit and Loss"**         | Auto-filled                          |
| `company`        | Select your company           | Required                             |
| `is_group`       | **☐ Unchecked**               | Must be ledger (not group)           |

**Action**: Save

**Examples of Bank Expenses** (Common types):

| Expense Type                | Description                       | Example                                                            |
| --------------------------- | --------------------------------- | ------------------------------------------------------------------ |
| **Monthly Service Charges** | Periodic account maintenance fees | Monthly account fee, Annual account fee                            |
| **Transaction Fees**        | Fees for specific transactions    | Wire transfer fee, SWIFT fee, Interbank transfer fee               |
| **ATM Fees**                | Cash withdrawal charges           | ATM withdrawal fee, ATM balance inquiry fee                        |
| **Cheque Charges**          | Fees related to cheques           | Cheque book charges, Cheque processing fee, Bounced cheque fee     |
| **Penalty Fees**            | Penalties for violations          | Insufficient funds penalty, Overdraft fee, Minimum balance penalty |
| **Service Charges**         | General banking services          | Account statement fee, Certificate charges, Standing order fee     |
| **Credit Card Fees**        | Credit card related charges       | Annual credit card fee, Cash advance fee                           |
| **Exchange Fees**           | Currency conversion charges       | Foreign exchange fee, Currency conversion fee                      |

**Example Account Names**:

- Bank Charges (general)
- Bank Fees (general)
- Transaction Fees (wire transfers)
- Penalty Fees (violations)
- ATM Charges (cash withdrawals)
- Cheque Charges (cheque-related)

---

## 0.1. Setup: Create Bank Interest Account (Required for Interest Income)

**Path**: `Accounting → Chart of Accounts → New Account`

**⚠️ Important**: Bank Interest is **Income** (not Expense).

**Account Structure in Chart of Accounts**:

```
Income (Root Type)
└── Indirect Income (Parent Group) ✅ Must be here
    └── Bank Interest (Account) ← Create here
```

**Required Fields**:

| Field            | Value                 | Notes                      |
| ---------------- | --------------------- | -------------------------- |
| `account_name`   | **"Bank Interest"**   | Name of the account        |
| `parent_account` | **"Indirect Income"** | Must be under Income       |
| `account_type`   | **"Income Account"**  | Account type               |
| `root_type`      | **"Income"**          | Auto-filled                |
| `report_type`    | **"Profit and Loss"** | Auto-filled                |
| `company`        | Select your company   | Required                   |
| `is_group`       | **☐ Unchecked**       | Must be ledger (not group) |

**Action**: Save

**Note**: Bank Interest is different from Bank Charges:

- ✅ **Bank Interest** → Income → Indirect Income (money earned)
- ✅ **Bank Charges** → Expense → Indirect Expenses (money spent)

---

## 1. Record Financial Transactions First

**Note**: Choose one based on transaction type:

### When to use Payment Entry:

- ✅ Payment to/from **Customer or Supplier** (party exists)
- ✅ Examples: Receiving payment from customer, Paying supplier
- ✅ **Requires**: `party_type` and `party` fields

### When to use Journal Entry:

- ✅ General bank transactions **without a party**
- ✅ Examples: Bank charges/fees, Bank interest, Internal transfers, Adjustments
- ✅ No party needed (can use `pay_to_recd_from` if needed)

---

### Option 1: Record Payment Entry (If transaction related to a party)

**Path**: `Accounting → Payment Entry → New`

**Required Fields**:

- `payment_type`: Receive (for collection) / Pay (for payment)
- `party_type`: Customer / Supplier (**Required**)
- `party`: Party name (**Required**)
- `posting_date`: Posting date
- `paid_from`: Debit account
- `paid_to`: Credit account
- `paid_amount`: Amount
- `reference_no`: **Reference number (needed for reconciliation)**
- `reference_date`: Reference date
- `mode_of_payment`: **Payment method** (Link → Mode of Payment)
  - **Optional**: Not used in reconciliation
  - **For**: Document payment method only
  - **Select**: Click field → Choose from list
    - Examples: "Cash", "Cheque", "Wire Transfer"
    - Find in: `Accounting → Setup → Mode of Payment`
  - **Note**: Reconciliation uses `reference_no` + Date + Amount + `payment_type`
  - **If empty**: Works fine, just documentation

**Action**: Save → Submit

---

### Option 2: Record Journal Entry (If transaction does not involve a party)

**Path**: `Accounting → Journal Entry → New`

**Required Fields**:

- `voucher_type`: Bank Entry
- `posting_date`: Posting date
- `cheque_no`: **Reference number (needed for reconciliation)**
- `cheque_date`: Reference date
- `accounts` table: Bank account + Second account (e.g., Bank Charges, Interest Income)

**Action**: Save → Submit

---

## 2. Upload Bank Statement

### Method 1: From Bank Reconciliation Tool

**Path**: `Accounting → Bank Reconciliation Tool`

**Steps**:

1. Fill: `company`, `bank_account`
2. Click button: **"Upload Bank Statement"**
3. Opens: `Bank Statement Import`

---

### Method 2: Direct

**Path**: `Accounting → Bank Statement Import → New`

**Required Fields**:

- `company`: **Required (fixed after save)**
- `bank_account`: **Required (fixed after save)**
- `import_file`: Upload CSV/XLS/XLSX file

**Hidden Fields (automatic)**:

- `reference_doctype`: "Bank Transaction"
- `import_type`: "Insert New Records"
- `submit_after_import`: 1

**Actions**:

1. Upload `import_file`
2. Review `import_preview`
3. Click: **"Start Import"** (or Save then Start Import)
4. Wait for `status`: Success / Partial Success / Error

**Result**: Creates `Bank Transaction` for each row, all auto-submitted

---

## 3. Perform Reconciliation

### Setup Reconciliation Screen

**Path**: `Accounting → Bank Reconciliation Tool`

**Required Fields**:

- `company`
- `bank_account`
- `bank_statement_from_date`: Bank statement start date
- `bank_statement_to_date`: Bank statement end date
- `bank_statement_closing_balance`: **Closing balance from bank statement**

**Additional Options**:

- `filter_by_reference_date`: Checkbox
  - If enabled: Uses `from_reference_date` and `to_reference_date` instead of `bank_statement_from_date/to_date`

**Automatic Fields (read-only)**:

- `account_currency`: From bank_account → account → account_currency
- `account_opening_balance`: Auto-calculated until `bank_statement_from_date - 1 day`

---

### Auto Reconcile

**Button**: "Auto Reconcile"

**Python Function**: `erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.auto_reconcile_vouchers`

**Parameters Sent**:

- `bank_account`
- `from_date`: `bank_statement_from_date`
- `to_date`: `bank_statement_to_date`
- `filter_by_reference_date`
- `from_reference_date`
- `to_reference_date`

**Auto Reconcile Conditions** (mandatory):

1. `reference_number` in Bank Transaction = `reference_no` in Payment Entry
   - Or `reference_number` = `cheque_no` in Journal Entry
2. Date within range:
   - If `filter_by_reference_date = False`: `posting_date` between `from_date` and `to_date`
   - If `filter_by_reference_date = True`: `reference_date`/`cheque_date` between `from_reference_date` and `to_reference_date`
3. `payment_type` matches (Receive for deposit, Pay for withdrawal)
4. `clearance_date = NULL` (not reconciled previously)

**Result**: Message with number of reconciled transactions

---

### Manual Match

**Button**: "Get Unreconciled Entries"

**Steps**:

1. Click "Get Unreconciled Entries"
2. Statistics cards appear:
   - Bank Statement Balance (from `bank_statement_closing_balance`)
   - Cleared Balance (auto-calculated)
   - Difference (should = 0)
3. In `reconciliation_tool_dt` table, click "Actions" button on transaction
4. Dialog opens: "Reconcile Bank Transaction"

---

### Dialog: Reconcile Bank Transaction

**Open**: Click "Actions" on any unreconciled transaction

**Dialog shows**:

- Transaction details (read-only): Date, Deposit, Withdrawal, Description, Allocated Amount, Unallocated Amount
- Action dropdown: 3 options

---

## Case 1: Match Against Existing Voucher (Payment Entry/Journal Entry already exists)

### Scenario 1A: One Bank Transaction matches One Payment Entry

**Example**:

- ✅ You recorded: Payment Entry (Customer paid 1000, reference_no = CHQ-001)
- ✅ Bank statement shows: Deposit 1000, reference_number = CHQ-001
- ✅ Goal: Match Bank Transaction with existing Payment Entry

### Steps:

1. **Open Dialog**: Click "Actions" on the Bank Transaction (deposit 1000)

2. **Select Action**:

   - `action`: **"Match Against Voucher"** (default)

3. **Enable Document Type Filters**:

   - ☑ Check `payment_entry` (to search in Payment Entries)
   - ☑ Check `journal_entry` (if needed)
   - ☑ Check `exact_match` (optional - to show only exact amount matches)

4. **Wait for Search**:

   - System searches for matching vouchers
   - Function called: `get_linked_payments()`
   - Search criteria: Amount, Reference Number, Party, Date range

5. **Review Results in Table** (`payment_proposals`):

   - **If match found**: Table shows matching vouchers
     - Example row:
       - Document Type: Payment Entry
       - Document Name: ACC-PAY-00001 (clickable link)
       - Reference Date: 2024-01-15
       - Remaining: 1000
       - Reference Number: CHQ-001
       - Party: Customer Name
   - **If no match**: Shows "No Matching Vouchers Found"

6. **Select Voucher(s)**:

   - ☑ Check the checkbox next to the correct voucher

7. **Click "Reconcile"**:
   - Function called: `reconcile_vouchers()`
   - System links Bank Transaction with Payment Entry
   - Updates `allocated_amount` and `unallocated_amount`
   - Updates `clearance_date` in Payment Entry
   - **Result**: Transaction disappears from unreconciled list (if fully matched)

---

### Scenario 1B: One Bank Transaction matches Multiple Payment Entries (Partial Matching)

**Example**:

- ✅ Bank statement shows: Deposit 2000, reference_number = 123123 (one check)
- ✅ You recorded: Payment Entry 1 (1000, reference_no = 123123)
- ✅ You recorded: Payment Entry 2 (1000, reference_no = 123123)
- ✅ Goal: Match one Bank Transaction with two Payment Entries

### Steps:

1. **Open Dialog**: Click "Actions" on the Bank Transaction (deposit 2000)

2. **Select Action**:

   - `action`: **"Match Against Voucher"** (default)

3. **Enable Document Type Filters**:

   - ☑ Check `payment_entry`
   - ☐ Do NOT check `exact_match` (to see all matching vouchers regardless of amount)

4. **Wait for Search**:

   - System searches for all matching vouchers
   - Function called: `get_linked_payments()`
   - **Search finds**: Both Payment Entries with reference_no = 123123

5. **Review Results in Table** (`payment_proposals`):

   - **Table shows 2 rows**:
     - Row 1:
       - Document Type: Payment Entry
       - Document Name: ACC-PAY-00001
       - Remaining: 1000
       - Reference Number: 123123
     - Row 2:
       - Document Type: Payment Entry
       - Document Name: ACC-PAY-00002
       - Remaining: 1000
       - Reference Number: 123123

6. **Select Multiple Vouchers**:

   - ☑ Check checkbox for Payment Entry 1 (1000)
   - ☑ Check checkbox for Payment Entry 2 (1000)
   - **Total selected**: 2000 (matches Bank Transaction amount)

7. **Click "Reconcile"**:
   - Function called: `reconcile_vouchers()`
   - System links Bank Transaction with BOTH Payment Entries
   - Updates Bank Transaction:
     - `allocated_amount` = 2000 (1000 + 1000)
     - `unallocated_amount` = 0 (2000 - 2000)
     - `status` = Reconciled
   - Updates both Payment Entries:
     - Payment Entry 1: `clearance_date` = Bank Transaction date
     - Payment Entry 2: `clearance_date` = Bank Transaction date
   - **Result**: Bank Transaction disappears from unreconciled list (fully matched)

### Partial Matching Rules:

- ✅ **Can match**: Multiple vouchers to one Bank Transaction
- ✅ **Can match**: One voucher to multiple Bank Transactions (if amounts allow)
- ✅ Total selected = Bank Transaction unallocated amount
- ⚠️ Cannot exceed Bank Transaction amount
- ⚠️ Each voucher matches once only

### Example: Bank Transaction with Partial Amount Matched

**Scenario**:

- Bank Transaction: Deposit 2000, unallocated_amount = 2000
- Payment Entry 1: 1000 (already matched with another Bank Transaction)
- Payment Entry 2: 1500, reference_no = 123123

**In Table, you will see**:

- Payment Entry 2: Remaining = 1500 (not 1500, because part already matched)

**Select**:

- Payment Entry 2: 1500
- **Result**:
  - `allocated_amount` = 1500
  - `unallocated_amount` = 500 (2000 - 1500)
  - Status remains Unreconciled (until fully matched)

---

## Case 2: Create Payment Entry (No voucher exists, transaction related to a party)

### ⚠️ When to Use This Case:

**Use Case 2 when**:

- ✅ Bank Transaction **related to a Customer or Supplier** (party exists)
- ✅ Party visible in bank statement description
- ❌ No Payment Entry already recorded in system
- ✅ Examples: Customer payment, Supplier payment, Employee advance

**Do NOT use Case 2 when**:

- ❌ Transaction has **NO party** (no customer, no supplier) → Use Case 3 (Journal Entry)
- ❌ Transaction is bank charges/fees → Use Case 3 (Journal Entry)
- ❌ Transaction is bank interest → Use Case 3 (Journal Entry)
- ❌ Transaction is internal transfer → Use Case 3 (Journal Entry)

### Scenario Example:

- ❌ No Payment Entry recorded in system
- ✅ Bank statement shows: Deposit 1000 (description: "Payment from Customer ABC")
- ✅ **Party identified**: Customer ABC
- ✅ Goal: Create Payment Entry for Customer ABC and match it

### Steps:

1. **Open Dialog**: Click "Actions" on the Bank Transaction

2. **Select Action**:

   - `action`: **"Create Voucher"**

3. **Select Document Type**:

   - `document_type`: **"Payment Entry"**

4. **Fill Required Fields**:

   - `party_type`: **Customer** (for deposit) or **Supplier** (for withdrawal)
   - `party`: **Select customer/supplier name**
   - `reference_number`: **CHQ-001** (auto-filled from Bank Transaction)
   - `posting_date`: **2024-01-15** (auto-filled from Bank Transaction date)
   - `reference_date`: **2024-01-15** (auto-filled from Bank Transaction date)

5. **Fill Optional Fields**:

   - `mode_of_payment`: Select from list (or leave empty)
   - `project`: Optional
   - `cost_center`: Optional

6. **Click "Reconcile"**:
   - Function called: `create_payment_entry_bts()`
   - System creates Payment Entry with:
     - `payment_type`: Receive (for deposit) or Pay (for withdrawal)
     - `paid_from` / `paid_to`: Bank account + Party account
     - `paid_amount`: From Bank Transaction amount
   - System submits Payment Entry
   - System links it with Bank Transaction
   - **Result**: Payment Entry created, submitted, and matched

---

## Case 3: Create Journal Entry (No voucher exists, general transaction without party)

### ⚠️ When to Use Journal Entry:

**Use Journal Entry when the bank transaction**:

- ❌ **Does NOT involve a Customer or Supplier** (no party)
- ✅ **Is a bank-related transaction** (charges, fees, interest, transfers)
- ✅ **Is an adjustment or correction**

**Rule**: No Customer/Supplier? → Use Journal Entry

---

### Scenario 3A: Bank Charges / Bank Fees

**Real Example**:

- Bank statement shows: Withdrawal 100
- Description: "Monthly Bank Service Charges"
- **Question**: Who is the party? → **No one** (not a customer, not a supplier)
- **Answer**: This is an expense → Use Journal Entry

**Bank Transaction**:

```
Withdrawal: 100
Description: "Monthly Bank Service Charges"
Reference Number: "FEE-001"
```

**Step-by-Step**:

1. **Open Dialog**: Click "Actions" on the Bank Transaction (withdrawal 100)

2. **Select Action**:

   - `action`: **"Create Voucher"**

3. **Select Document Type**:

   - `document_type`: **"Journal Entry"**

4. **Fill Required Fields**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **Select "Bank Charges"** (or "Bank Fees" expense account)
     - This account receives the debit (expense)
   - `reference_number`: **"FEE-001"** (auto-filled or enter manually)
   - `posting_date`: **2024-01-15** (auto-filled from Bank Transaction date)
   - `reference_date`: **2024-01-15** (auto-filled)

5. **Click "Reconcile"**:
   - System creates Journal Entry:
     - **Row 1**: Bank Account (Credit: 100) - Money leaving bank
     - **Row 2**: Bank Charges (Debit: 100) - Expense account
   - System submits Journal Entry
   - System links it with Bank Transaction
   - **Result**: Journal Entry created, submitted, and matched

---

### Scenario 3B: Bank Interest (Income)

**Real Example**:

- Bank statement shows: Deposit 50
- Description: "Interest Earned on Savings"
- **Question**: Who is the party? → **No one** (not a customer, not a supplier)
- **Answer**: This is income → Use Journal Entry

**Bank Transaction**:

```
Deposit: 50
Description: "Interest Earned on Savings"
Reference Number: "INT-001"
```

**Step-by-Step**:

1. **Open Dialog**: Click "Actions" on the Bank Transaction (deposit 50)

2. **Select Action**: `action`: **"Create Voucher"**

3. **Select Document Type**: `document_type`: **"Journal Entry"**

4. **Fill Required Fields**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **Select "Bank Interest"** (or "Interest Income" account)
     - This account receives the credit (income)
   - `reference_number`: **"INT-001"**
   - `posting_date`: **2024-01-15**
   - `reference_date`: **2024-01-15**

5. **Click "Reconcile"**:
   - System creates Journal Entry:
     - **Row 1**: Bank Account (Debit: 50) - Money entering bank
     - **Row 2**: Bank Interest (Credit: 50) - Income account
   - **Result**: Journal Entry created, submitted, and matched

---

### Scenario 3C: Internal Bank Transfer

**Real Example**:

- Bank statement shows: Withdrawal 5000
- Description: "Transfer to Account 12345"
- **Question**: Who is the party? → **No one** (transferring to your own account)
- **Answer**: This is a transfer → Use Journal Entry

**Bank Transaction**:

```
Withdrawal: 5000
Description: "Transfer to Account 12345"
Reference Number: "TRF-001"
```

**Step-by-Step**:

1. **Open Dialog**: Click "Actions" on the Bank Transaction

2. **Select Action**: `action`: **"Create Voucher"**

3. **Select Document Type**: `document_type`: **"Journal Entry"**

4. **Fill Required Fields**:

   - `journal_entry_type`: **"Bank Entry"** or **"Contra Entry"**
   - `second_account`: **Select the destination bank account** (Account 12345)
   - `reference_number`: **"TRF-001"**
   - `posting_date`: **2024-01-15**
   - `reference_date`: **2024-01-15**

5. **Click "Reconcile"**:
   - System creates Journal Entry:
     - **Row 1**: Source Bank Account (Credit: 5000) - Money leaving
     - **Row 2**: Destination Bank Account (Debit: 5000) - Money entering
   - **Result**: Journal Entry created, submitted, and matched

---

### Scenario 3D: Wire Transfer Fee / Transaction Fee

**Real Example**:

- Bank statement shows: Withdrawal 25
- Description: "Wire Transfer Fee"
- **Question**: Who is the party? → **No one** (service fee, not a payment to supplier)
- **Answer**: This is a service fee → Use Journal Entry

**Same steps as Scenario 3A** - Use expense account like "Bank Service Charges"

---

### Scenario 3E: Adjustment / Correction Entry

**Real Example**:

- Bank statement shows: Deposit 100
- Description: "Correction Entry - Previous Error"
- **Question**: Who is the party? → **No one** (just an adjustment)
- **Answer**: This is an adjustment → Use Journal Entry

**Step-by-Step**:

- Same steps as above
- `second_account`: Select appropriate account (Suspense Account, Previous Year Adjustments, etc.)

---

### Decision Table: When to Use Journal Entry

| Bank Statement Description  | Has Customer/Supplier? | Use               | Second Account Type         |
| --------------------------- | ---------------------- | ----------------- | --------------------------- |
| "Monthly Bank Charges"      | ❌ No                  | **Journal Entry** | Expense (Bank Charges)      |
| "Interest Earned"           | ❌ No                  | **Journal Entry** | Income (Bank Interest)      |
| "Transfer to Account X"     | ❌ No                  | **Journal Entry** | Bank Account (Destination)  |
| "Wire Transfer Fee"         | ❌ No                  | **Journal Entry** | Expense (Service Charges)   |
| "Correction Entry"          | ❌ No                  | **Journal Entry** | Suspense/Adjustment Account |
| "Payment from Customer ABC" | ✅ Yes (Customer)      | **Payment Entry** | Customer Account            |
| "Payment to Supplier XYZ"   | ✅ Yes (Supplier)      | **Payment Entry** | Supplier Account            |

---

### Quick Decision Guide:

**Question**: "Customer or Supplier in this transaction?"

- ✅ **Yes** → Use **Payment Entry**
- ❌ **No** → Use **Journal Entry**

**Common Journal Entry scenarios**:

1. 💰 Bank charges/fees (money leaving, no party)
2. 💰 Bank interest (money entering, no party)
3. 💰 Transfer between your accounts (no party)
4. 💰 Service fees (no party)
5. 💰 Adjustments/corrections (no party)

---

### Summary - Journal Entry Scenarios:

| Scenario          | Bank Transaction Type | Second Account     | Example Account Names                       |
| ----------------- | --------------------- | ------------------ | ------------------------------------------- |
| **Bank Charges**  | Withdrawal            | Expense            | Bank Charges, Bank Fees, Service Charges    |
| **Bank Interest** | Deposit               | Income             | Bank Interest, Interest Income              |
| **Transfer**      | Withdrawal/Deposit    | Bank Account       | Another Bank Account in your system         |
| **Service Fees**  | Withdrawal            | Expense            | Transaction Fees, Wire Transfer Fees        |
| **Adjustments**   | Deposit/Withdrawal    | Adjustment Account | Suspense Account, Previous Year Adjustments |

---

## Case 3F: Handling Bank Fees (Account Fees & Transaction Fees)

### ⚠️ Understanding Fee Fields:

- **`included_fee`**: Fee included within the withdrawal/deposit amount (part of the transaction)
- **`excluded_fee`**: Fee deducted separately (auto-converts to `included_fee` on save)

**Note**: `excluded_fee` auto-converts to `included_fee` and adjusts deposit/withdrawal amount.

---

### Scenario 3F1: Periodic Account Fees (Monthly/Annual Fees)

**Bank Statement Example**: Monthly service charge deducted from account

**Bank Transaction Fields**:

```
withdrawal: 100
included_fee: 0
excluded_fee: 0
description: "Monthly Bank Service Charges"
reference_number: "FEE-MONTHLY-001"
```

**OR (if fee shown separately in statement)**:

```
withdrawal: 100
included_fee: 0
excluded_fee: 100
description: "Monthly Bank Service Charges"
reference_number: "FEE-MONTHLY-001"
```

**Step-by-Step**:

1. **Upload Bank Statement**: System creates Bank Transaction with fee

2. **Dialog: Reconcile Bank Transaction**:

   - `action`: **"Create Voucher"**
   - `document_type`: **"Journal Entry"**

3. **Fill Fields**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **"Bank Charges"** (expense account)
   - `reference_number`: **"FEE-MONTHLY-001"** (auto-filled)
   - `posting_date`: **2024-01-15** (auto-filled)
   - `reference_date`: **2024-01-15** (auto-filled)

4. **Click "Reconcile"**:
   - System creates Journal Entry:
     - Bank Account (Credit: 100)
     - Bank Charges (Debit: 100)
   - **Result**: Journal Entry created, submitted, and matched

---

### Scenario 3F2: Random Account Fees (Unexpected Fees)

**Bank Statement Example**: Unplanned fee or penalty charge

**Bank Transaction Fields**:

```
withdrawal: 50
included_fee: 0
excluded_fee: 0
description: "Penalty Fee - Minimum Balance"
reference_number: "FEE-PENALTY-001"
```

**OR (if fee shown separately)**:

```
withdrawal: 50
included_fee: 0
excluded_fee: 50
description: "Penalty Fee - Minimum Balance"
reference_number: "FEE-PENALTY-001"
```

**Step-by-Step**:

1. **Upload Bank Statement**: System creates Bank Transaction

2. **Dialog: Reconcile Bank Transaction**:

   - `action`: **"Create Voucher"**
   - `document_type`: **"Journal Entry"**

3. **Fill Fields**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **"Bank Charges"** or **"Penalty Fees"** (expense account)
   - `reference_number`: **"FEE-PENALTY-001"** (auto-filled)
   - `posting_date`: **2024-01-15** (auto-filled)
   - `reference_date`: **2024-01-15** (auto-filled)

4. **Click "Reconcile"**:
   - System creates Journal Entry:
     - Bank Account (Credit: 50)
     - Bank Charges/Penalty Fees (Debit: 50)
   - **Result**: Journal Entry created, submitted, and matched

---

### Scenario 3F3: Transaction Fees (Fees Related to Deposit/Withdrawal)

**Case A: Fee on Deposit (Customer Payment Fee)**

**Bank Statement Example**: Customer payment received, but bank deducted fee

**Bank Transaction Fields**:

```
deposit: 1000
included_fee: 0
excluded_fee: 25
description: "Payment from Customer ABC - Transaction Fee"
reference_number: "CHQ-001"
party_type: Customer
party: Customer ABC
```

**Note**: System auto-converts `excluded_fee` to `included_fee`:

- After save: `deposit: 975`, `included_fee: 25`, `excluded_fee: 0`

**Step-by-Step**:

1. **Upload Bank Statement**: System creates Bank Transaction

2. **Dialog: Reconcile Bank Transaction**:

   - **Option 1**: Match against existing Payment Entry (if customer payment already recorded)
     - `action`: **"Match Against Voucher"**
     - Select Payment Entry
   - **Option 2**: Create Payment Entry for customer + Journal Entry for fee
     - First: Create Payment Entry (amount: 975)
     - Then: Create Journal Entry for fee (amount: 25)
       - `action`: **"Create Voucher"**
       - `document_type`: **"Journal Entry"**
       - `second_account`: **"Transaction Fees"** (expense account)

3. **Fill Fields (Journal Entry)**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **"Transaction Fees"**
   - `reference_number`: **"CHQ-001-FEE"**
   - `posting_date`: **2024-01-15**
   - `reference_date`: **2024-01-15**

4. **Click "Reconcile"**:
   - **Result**: Payment Entry matched (975) + Journal Entry matched (25) = Fully reconciled (1000)

---

**Case B: Fee on Withdrawal (Wire Transfer Fee)**

**Bank Statement Example**: Supplier payment made, bank charged transfer fee

**Bank Transaction Fields**:

```
withdrawal: 5000
included_fee: 0
excluded_fee: 50
description: "Payment to Supplier XYZ - Wire Transfer Fee"
reference_number: "WIRE-001"
party_type: Supplier
party: Supplier XYZ
```

**Note**: System auto-converts: `withdrawal: 5050`, `included_fee: 50`, `excluded_fee: 0`

**Step-by-Step**:

1. **Upload Bank Statement**: System creates Bank Transaction

2. **Dialog: Reconcile Bank Transaction**:

   - **Option 1**: Match against existing Payment Entry (if supplier payment already recorded)
     - Match Payment Entry (amount: 5000)
     - Create Journal Entry for fee (amount: 50)
   - **Option 2**: Create Payment Entry for supplier + Journal Entry for fee
     - Create Payment Entry (amount: 5000)
     - Create Journal Entry (amount: 50)

3. **Fill Fields (Journal Entry)**:

   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **"Wire Transfer Fees"** (expense account)
   - `reference_number`: **"WIRE-001-FEE"**
   - `posting_date`: **2024-01-15**
   - `reference_date`: **2024-01-15**

4. **Click "Reconcile"**:
   - **Result**: Payment Entry matched (5000) + Journal Entry matched (50) = Fully reconciled (5050)

---

**Case C: Fee Included in Withdrawal Amount**

**Bank Statement Example**: Withdrawal shows total amount (includes fee)

**Bank Transaction Fields**:

```
withdrawal: 1050
included_fee: 50
excluded_fee: 0
description: "Payment to Supplier XYZ"
reference_number: "CHQ-002"
party_type: Supplier
party: Supplier XYZ
```

**Step-by-Step**:

1. **Match or Create Payment Entry**: Amount = 1000 (1050 - 50 fee)

2. **Create Journal Entry for Fee**:

   - `action`: **"Create Voucher"**
   - `document_type`: **"Journal Entry"**
   - `journal_entry_type`: **"Bank Entry"**
   - `second_account`: **"Transaction Fees"**
   - `reference_number`: **"CHQ-002-FEE"**
   - Amount: 50

3. **Click "Reconcile"**:
   - **Result**: Payment Entry (1000) + Journal Entry (50) = Fully reconciled (1050)

---

### Fee Handling Summary Table:

| Fee Type                       | Bank Statement                  | Bank Transaction Fields                                 | Action                                               |
| ------------------------------ | ------------------------------- | ------------------------------------------------------- | ---------------------------------------------------- |
| **Periodic Fee**               | Withdrawal 100 (service charge) | `withdrawal: 100`, `included_fee: 0`, `excluded_fee: 0` | Create Journal Entry (amount: 100)                   |
| **Random Fee**                 | Withdrawal 50 (penalty)         | `withdrawal: 50`, `included_fee: 0`, `excluded_fee: 0`  | Create Journal Entry (amount: 50)                    |
| **Transaction Fee (Excluded)** | Deposit 1000, Fee 25 separate   | `deposit: 1000`, `excluded_fee: 25`                     | Auto-converts to: `deposit: 975`, `included_fee: 25` |
| **Transaction Fee (Included)** | Withdrawal 1050 (1000 + 50 fee) | `withdrawal: 1050`, `included_fee: 50`                  | Create Payment Entry (1000) + Journal Entry (50)     |

**Key Rules**:

- `excluded_fee` → Auto-converts to `included_fee` on save
- For transaction fees: Create Payment Entry for party amount + Journal Entry for fee
- All fees (account or transaction) → Use Journal Entry with expense account

---

## Case 4: Update Bank Transaction (Fix missing reference number or party)

### Scenario Example:

- ❌ Bank Transaction missing `reference_number`
- ❌ Bank Transaction missing `party`
- ✅ Goal: Update Bank Transaction to enable auto-reconcile

### Steps:

1. **Open Dialog**: Click "Actions" on the Bank Transaction

2. **Select Action**:

   - `action`: **"Update Bank Transaction"**

3. **Update Fields**:

   - `reference_number`: Enter reference number (e.g., "CHQ-001")
   - `party_type`: Select party type (Customer/Supplier)
   - `party`: Select party name

4. **Click "Reconcile"**:
   - Function called: `update_bank_transaction()`
   - System updates Bank Transaction fields
   - **Result**: Bank Transaction updated, can now be auto-reconciled

---

## Summary Table: When to Use Each Option

| Case         | Scenario                                               | Action                                      | Result                                     |
| ------------ | ------------------------------------------------------ | ------------------------------------------- | ------------------------------------------ |
| **Case 1A**  | One voucher exists matching Bank Transaction           | Match Against Voucher (select one)          | Links one voucher                          |
| **Case 1B**  | Multiple vouchers exist (one check = multiple entries) | Match Against Voucher (select multiple)     | Links multiple vouchers to one transaction |
| **Case 2**   | Deposit/Withdrawal with party, no voucher              | Create Voucher → Payment Entry              | Creates and matches Payment Entry          |
| **Case 3**   | Bank charges/fees, no party, no voucher                | Create Voucher → Journal Entry              | Creates and matches Journal Entry          |
| **Case 3F1** | Periodic account fees (monthly/annual)                 | Create Voucher → Journal Entry              | Creates and matches Journal Entry          |
| **Case 3F2** | Random account fees (penalties/unexpected)             | Create Voucher → Journal Entry              | Creates and matches Journal Entry          |
| **Case 3F3** | Transaction fees (on deposit/withdrawal with party)    | Payment Entry (party) + Journal Entry (fee) | Creates both vouchers and matches          |
| **Case 4**   | Missing reference_number or party in Bank Transaction  | Update Bank Transaction                     | Updates fields for auto-reconcile          |

### Examples for Case 1B (Multiple Vouchers Matching):

| Bank Transaction         | Recorded Vouchers                              | Action                | Result                                        |
| ------------------------ | ---------------------------------------------- | --------------------- | --------------------------------------------- |
| Deposit 2000, ref=123123 | PE1: 1000, ref=123123<br>PE2: 1000, ref=123123 | Select both PE1 & PE2 | ✅ Fully reconciled (2000)                    |
| Deposit 2000, ref=123123 | PE1: 800, ref=123123<br>PE2: 1200, ref=123123  | Select both PE1 & PE2 | ✅ Fully reconciled (2000)                    |
| Deposit 2000, ref=123123 | PE1: 1500, ref=123123<br>PE2: 1000, ref=123123 | Select PE1 only       | ⚠️ Partially reconciled (1500), 500 remaining |
| Deposit 2000, ref=123123 | PE1: 1500, ref=123123<br>PE2: 1000, ref=123123 | Select both PE1 & PE2 | ✅ Fully reconciled (2000)                    |

---

## Technical Details

### Match Against Voucher - Python Functions:

- **Search**: `get_linked_payments(bank_transaction_name, document_types, ...)`
- **Reconcile**: `reconcile_vouchers(bank_transaction_name, vouchers)`
  - `vouchers`: JSON array of selected vouchers

### Create Payment Entry - Python Function:

- `create_payment_entry_bts(bank_transaction_name, party_type, party, reference_number, ...)`
- Creates → Submits → Links auto

### Create Journal Entry - Python Function:

- `create_journal_entry_bts(bank_transaction_name, second_account, reference_number, ...)`
- Creates → Submits → Links auto

### Update Bank Transaction - Python Function:

- `update_bank_transaction(bank_transaction_name, reference_number, party_type, party)`

---

## 4. Record Bank Charges/Fees

### In Bank Transaction

**Path**: `Accounting → Bank Transaction → [Open Transaction]`

**Section**: "Extended Bank Statement"

**Fields**:

- `included_fee`: Fees included in amount
- `excluded_fee`: Separate fees (auto-converts to `included_fee` on save)

**Automatic Conversion**:

- On save: `excluded_fee` → `included_fee`
- If `deposit > 0`: `deposit` = `deposit - excluded_fee`
- If `withdrawal >= 0`: `withdrawal` = `withdrawal + excluded_fee`

**Rule**: `included_fee` cannot be greater than `withdrawal`

---

## 5. Verify Reconciliation

### Statistics Cards

**In Bank Reconciliation Tool**:

1. **Bank Statement Balance**: From `bank_statement_closing_balance`
2. **Cleared Balance**: Auto-calculated
   - Function: `erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.get_account_balance`
   - Parameters: `bank_account`, `till_date`, `company`
3. **Difference**: `bank_statement_closing_balance - cleared_balance`
   - **Goal**: Should be = 0

---

### Bank Reconciliation Statement Report

**Path**: `Reports → Bank Reconciliation Statement`

**Filters**:

- `company`
- `account`: **From Bank Account → account** (not bank_account)
- `report_date`: Bank statement end date
- `include_pos_transactions`: Checkbox

**Python Function**: `erpnext.accounts.report.bank_reconciliation_statement.bank_reconciliation_statement.execute`

**Report Sections**:

1. **Bank Statement balance as per General Ledger**: System balance
2. **Outstanding Cheques and Deposits**: Unreconciled transactions
3. **Cheques and Deposits incorrectly cleared**: Incorrectly reconciled transactions
4. **Calculated Bank Statement balance**: Calculated balance
   - **Goal**: Should match bank statement balance

---

## 6. Key Bank Transaction Fields

**Basic Fields**:

- `date`: Transaction date
- `bank_account`: Bank account
- `company`: Company (automatic)
- `deposit`: Deposit amount
- `withdrawal`: Withdrawal amount
- `currency`: Currency (automatic)
- `description`: Description
- `reference_number`: **Reference number (needed for reconciliation)**
- `transaction_type`: Transaction type (Data field)
  - **Usage**: Auto-copied to `mode_of_payment` when Create Voucher
  - **Example**: "Wire Transfer", "Cheque", "Cash"
- `party_type`: Party type
- `party`: Party

**Fee Fields**:

- `included_fee`: Included fees
- `excluded_fee`: Separate fees

**Reconciliation Fields**:

- `payment_entries`: Table of matched vouchers
  - `payment_document`: Voucher type
  - `payment_entry`: Voucher number
  - `allocated_amount`: Allocated amount
- `allocated_amount`: Total allocated amount (automatic)
- `unallocated_amount`: Unallocated amount (automatic)
  - **Formula**: `|deposit - withdrawal| - allocated_amount`

**Status**:

- `status`: Pending / Settled / Unreconciled / Reconciled / Cancelled
  - **Reconciled**: When `unallocated_amount = 0`

---

## 7. Quick Workflow

```
1. Record Payment Entry / Journal Entry
   → reference_no / cheque_no required
   → Submit

2. Bank Reconciliation Tool
   → company, bank_account
   → Upload Bank Statement

3. Bank Statement Import
   → import_file (CSV/XLS/XLSX)
   → Start Import
   → Result: Bank Transactions Submitted

4. Bank Reconciliation Tool
   → bank_statement_from_date
   → bank_statement_to_date
   → bank_statement_closing_balance
   → Get Unreconciled Entries

5. Auto Reconcile
   → Searches for: reference_number + Date

6. Manual Match (for remaining)
   → Actions → Match Against Voucher
   → Select vouchers → Reconcile

7. Verify
   → Statistics cards: Difference = 0
   → Bank Reconciliation Statement Report: Calculated Balance = bank statement balance
```

---

## 8. Main Python Functions

### Get Bank Transactions

```python
get_bank_transactions(bank_account, from_date=None, to_date=None)
```

### Calculate Account Balance

```python
get_account_balance(bank_account, till_date, company)
```

### Auto Reconcile

```python
auto_reconcile_vouchers(
    bank_account,
    from_date=None,
    to_date=None,
    filter_by_reference_date=None,
    from_reference_date=None,
    to_reference_date=None
)
```

### Get Proposed Vouchers

```python
get_linked_payments(
    bank_transaction_name,
    document_types=None,
    from_date=None,
    to_date=None,
    filter_by_reference_date=None,
    from_reference_date=None,
    to_reference_date=None
)
```

### Execute Reconciliation

```python
reconcile_vouchers(bank_transaction_name, vouchers)
# vouchers: JSON string
```

### Create Payment Entry

```python
create_payment_entry_bts(
    bank_transaction_name,
    reference_number=None,
    reference_date=None,
    party_type=None,
    party=None,
    posting_date=None,
    mode_of_payment=None,
    project=None,
    cost_center=None,
    allow_edit=None
)
```

### Create Journal Entry

```python
create_journal_entry_bts(
    bank_transaction_name,
    reference_number=None,
    reference_date=None,
    posting_date=None,
    entry_type=None,
    second_account=None,
    mode_of_payment=None,
    party_type=None,
    party=None,
    allow_edit=None
)
```

### Update Bank Transaction

```python
update_bank_transaction(bank_transaction_name, reference_number, party_type=None, party=None)
```

---

## 9. mode_of_payment - Clarification

### ⚠️ Regarding Bank Reconciliation:

- **`mode_of_payment` is NOT used in reconciliation logic**
- **Reconciliation conditions used**:
  1. `reference_no` (Payment Entry) / `cheque_no` (Journal Entry) = `reference_number` (Bank Transaction)
  2. Date within specified range
  3. `payment_type` matches (Receive/Pay)
  4. Amount
  5. `party` (for ranking priority only)

### In Bank Transaction:

- **No direct `mode_of_payment` field**
- Field `transaction_type` exists (Data field, 50 characters)
- `transaction_type` describes transaction type (e.g., "Wire Transfer", "Cheque", "Cash")
- **`transaction_type` is NOT used in reconciliation**

### When Create Voucher:

- **In Dialog**: `transaction_type` from Bank Transaction auto-copies to `mode_of_payment`
- **Code**: `mode_of_payment: this.bank_transaction.transaction_type` (dialog_manager.js:65)
- **Purpose**: Document payment method in created voucher only

### In Payment Entry / Journal Entry:

- `mode_of_payment` is **Link → Mode of Payment** (DocType)
- **Completely optional**: Not required for reconciliation or operation
- **Purpose**: Only to document payment method (Cash, Bank Transfer, Cheque, etc.)
- **How to select**:
  - Click on `mode_of_payment` field
  - Select from list of enabled Mode of Payment records
  - Records are created in: `Accounting → Setup → Mode of Payment`
  - Common examples: "Cash", "Cheque", "Wire Transfer", "Bank Transfer", "Credit Card"
- **If `transaction_type` exists**: Auto-copied when Create Voucher
- **If not exists**: Can be left empty or manually selected

### Difference:

- `transaction_type` (Bank Transaction): Free text (Data field) - **NOT used in reconciliation**
- `mode_of_payment` (Payment Entry/Journal Entry): Link to DocType "Mode of Payment" - **NOT used in reconciliation**

### Summary:

- ✅ **For reconciliation**: Rely on `reference_no` + Date + Amount
- ❌ **For reconciliation**: `mode_of_payment` not required
- 📝 **For documentation**: `mode_of_payment` is useful but optional

---

## 10. Quick Points

✅ **Reference Number + Date** = Key to auto reconciliation  
✅ **bank_statement_closing_balance** needed for comparison  
✅ **Unallocated Amount = 0** = fully reconciled  
✅ **excluded_fee** auto-converts to `included_fee` on save  
✅ **clearance_date = NULL** condition for vouchers eligible for reconciliation  
✅ **Auto Reconcile** searches only for Reference Number + Date match  
✅ **Manual Match** can match without Reference Number  
✅ **mode_of_payment** is optional - select from Mode of Payment list or leave empty

---

**Last Updated**: Based on ERPNext code
