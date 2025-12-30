# Copyright (c) 2025, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import flt, getdate
from erpnext.accounts.report.bank_reconciliation_statement.bank_reconciliation_statement import (
    get_amounts_not_reflected_in_system,
    get_entries,
)
from erpnext.accounts.utils import get_account_currency, get_balance_on


@frappe.whitelist()
def create_bank_transaction_from_voucher(voucher_doc_type, voucher_name, bank_account=None):
    """Create Bank Transaction from Payment Entry or Journal Entry"""
    try:
        voucher_doc = frappe.get_doc(voucher_doc_type, voucher_name)

        if voucher_doc_type == "Payment Entry":
            # Get bank account from Payment Entry
            bank_account_field = "paid_to" if voucher_doc.payment_type == "Receive" else "paid_from"
            target_bank_account = bank_account or get_bank_account_from_account(
                voucher_doc.get(bank_account_field))

            if not target_bank_account:
                frappe.throw(_("Bank Account not found in Payment Entry"))

            # Determine deposit/withdrawal
            if voucher_doc.payment_type == "Receive":
                deposit = flt(voucher_doc.received_amount)
                withdrawal = 0.0
            else:
                deposit = 0.0
                withdrawal = flt(voucher_doc.paid_amount)

            reference_number = voucher_doc.reference_no
            reference_date = voucher_doc.reference_date
            party_type = voucher_doc.party_type
            party = voucher_doc.party

        elif voucher_doc_type == "Journal Entry":
            # Get bank account from Journal Entry
            bank_accounts = []
            for account in voucher_doc.accounts:
                if frappe.db.get_value("Account", account.account, "account_type") == "Bank":
                    bank_accounts.append(account.account)

            if not bank_accounts:
                frappe.throw(_("Bank Account not found in Journal Entry"))

            target_bank_account = bank_account or get_bank_account_from_account(
                bank_accounts[0])
            if not target_bank_account:
                frappe.throw(_("Bank Account not found"))

            # Calculate deposit/withdrawal from bank account row
            bank_row = None
            for account in voucher_doc.accounts:
                if account.account == bank_accounts[0]:
                    bank_row = account
                    break

            if bank_row:
                deposit = flt(bank_row.debit_in_account_currency)
                withdrawal = flt(bank_row.credit_in_account_currency)
            else:
                deposit = 0.0
                withdrawal = 0.0

            reference_number = voucher_doc.cheque_no
            reference_date = voucher_doc.cheque_date
            party_type = voucher_doc.accounts[0].party_type if voucher_doc.accounts else None
            party = voucher_doc.accounts[0].party if voucher_doc.accounts else None
        else:
            frappe.throw(
                _("Unsupported voucher type: {0}").format(voucher_doc_type))

        # Create Bank Transaction
        bank_transaction = frappe.new_doc("Bank Transaction")
        bank_transaction.date = voucher_doc.posting_date
        bank_transaction.bank_account = target_bank_account
        bank_transaction.deposit = deposit
        bank_transaction.withdrawal = withdrawal
        bank_transaction.reference_number = reference_number
        bank_transaction.description = f"Created from {voucher_doc_type} {voucher_name}"
        bank_transaction.currency = frappe.get_cached_value("Bank Account", target_bank_account, "default_currency") or frappe.get_cached_value(
            "Company", voucher_doc.company, "default_currency")
        bank_transaction.party_type = party_type
        bank_transaction.party = party

        bank_transaction.insert()
        bank_transaction.submit()

        # Auto-reconcile with the voucher
        from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import reconcile_vouchers
        vouchers = json.dumps([
            {
                "payment_doctype": voucher_doc_type,
                "payment_name": voucher_name,
                "amount": deposit or withdrawal
            }
        ])
        reconcile_vouchers(bank_transaction.name, vouchers)

        return {"name": bank_transaction.name}

    except Exception as e:
        frappe.log_error(
            "[bank_reconcile_report.py] method: create_bank_transaction_from_voucher", "Bank Reconcile Report")
        frappe.throw(_("Error creating Bank Transaction: {0}").format(str(e)))


def get_bank_account_from_account(account):
    """Get Bank Account name from GL Account"""
    bank_accounts = frappe.get_all(
        "Bank Account",
        filters={"account": account},
        limit=1
    )
    return bank_accounts[0].name if bank_accounts else None


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)

    # Calculate report summary (closing balances)
    report_summary = get_report_summary(filters, data)

    return columns, data, None, None, report_summary


def get_columns(filters):
    columns = [
        {
            "fieldname": "bt_name",
            "label": "Bank Transaction",
            "fieldtype": "Link",
            "options": "Bank Transaction"
        },
        {
            "fieldname": "bt_date",
            "label": "BT Date",
            "fieldtype": "Date"
        },
        {
            "fieldname": "bt_deposit",
            "label": "BT Deposit",
            "fieldtype": "Currency"
        },
        {
            "fieldname": "bt_withdrawal",
            "label": "BT Withdrawal",
            "fieldtype": "Currency"
        },
        {
            "fieldname": "bt_reference_number",
            "label": "BT Reference No",
            "fieldtype": "Data"
        },
        {
            "fieldname": "bt_unallocated_amount",
            "label": "BT Unallocated",
            "fieldtype": "Currency"
        },
        {
            "fieldname": "voucher_doc_type",
            "label": "Voucher Type",
            "fieldtype": "Data"
        },
        {
            "fieldname": "voucher_name",
            "label": "Voucher Name",
            "fieldtype": "Dynamic Link",
            "options": "voucher_doc_type"
        },
        {
            "fieldname": "voucher_reference_no",
            "label": "Voucher Ref No",
            "fieldtype": "Data"
        },
        {
            "fieldname": "voucher_posting_date",
            "label": "Voucher Date",
            "fieldtype": "Date"
        },
        {
            "fieldname": "voucher_amount",
            "label": "Voucher Amount",
            "fieldtype": "Currency"
        },
        {
            "fieldname": "voucher_party_type",
            "label": "Voucher Party Type",
            "fieldtype": "Data"
        },
        {
            "fieldname": "voucher_party",
            "label": "Voucher Party",
            "fieldtype": "Data"
        },
        {
            "fieldname": "reconciled_status",
            "label": "Status",
            "fieldtype": "Data"
        },
        {
            "fieldname": "btn_reconcile",
            "label": "Reconcile",
            "fieldtype": "HTML"
        },
        {
            "fieldname": "btn_create_pe",
            "label": "Create Payment Entry",
            "fieldtype": "HTML"
        },
        {
            "fieldname": "btn_create_je",
            "label": "Create Journal Entry",
            "fieldtype": "HTML"
        },
        {
            "fieldname": "btn_create_bt",
            "label": "Create Bank Transaction",
            "fieldtype": "HTML"
        }
    ]

    return columns


def get_data(filters):
    data = []

    # Get Bank Transactions
    bt_filters = {
        "docstatus": 1
    }

    if filters.get("company"):
        bt_filters["company"] = filters.get("company")
    if filters.get("bank_account"):
        bt_filters["bank_account"] = filters.get("bank_account")

    # Use bank_statement_from_date/to_date or fallback to from_date/to_date
    from_date = filters.get(
        "bank_statement_from_date") or filters.get("from_date")
    to_date = filters.get(
        "bank_statement_to_date") or filters.get("to_date")

    if from_date and to_date:
        bt_filters["date"] = ["between", [from_date, to_date]]
    elif from_date:
        bt_filters["date"] = [">=", from_date]
    elif to_date:
        bt_filters["date"] = ["<=", to_date]

    # Filter by reference date if enabled
    if filters.get("filter_by_reference_date"):
        from_ref_date = filters.get("from_reference_date")
        to_ref_date = filters.get("to_reference_date")
        if from_ref_date:
            bt_filters["reference_date"] = [">=", from_ref_date]
        if to_ref_date:
            if "reference_date" in bt_filters and isinstance(bt_filters["reference_date"], list):
                bt_filters["reference_date"].append(["<=", to_ref_date])
            else:
                bt_filters["reference_date"] = ["<=", to_ref_date]
    if filters.get("reference_number"):
        bt_filters["reference_number"] = [
            "like", f"%{filters.get('reference_number')}%"]

    # Filter by created_by
    if filters.get("created_by"):
        bt_filters["owner"] = filters.get("created_by")

    # Filter by reconciliation status (if exists, keep for backward compatibility)
    if filters.get("reconciliation_status"):
        if filters.get("reconciliation_status") == "Reconciled":
            bt_filters["status"] = "Reconciled"
        elif filters.get("reconciliation_status") == "Unreconciled":
            bt_filters["status"] = ["in", ["Pending", "Unreconciled"]]
            bt_filters["unallocated_amount"] = [">", 0]

    # Filter: Show Unmatched Vouchers - only show Unreconciled Bank Transactions
    if filters.get("show_unmatched_vouchers"):
        bt_filters["status"] = ["in", ["Pending", "Unreconciled"]]
        bt_filters["unallocated_amount"] = [">", 0]

    bank_transactions = frappe.get_all(
        "Bank Transaction",
        fields=[
            "name",
            "date",
            "deposit",
            "withdrawal",
            "reference_number",
            "unallocated_amount",
            "allocated_amount",
            "status",
            "party",
            "party_type",
            "currency",
            "bank_account",
            "company"
        ],
        filters=bt_filters,
        order_by="date desc, reference_number"
    )

    # Track all matched vouchers to exclude them when showing unmatched
    all_matched_vouchers = set()

    # First: Show all Bank Transactions with matched vouchers (one row per BT with matched voucher)
    for bt in bank_transactions:
        base_row = {
            "bt_name": bt.name,
            "bt_date": bt.date,
            "bt_deposit": flt(bt.deposit),
            "bt_withdrawal": flt(bt.withdrawal),
            "bt_reference_number": bt.reference_number or "",
            "bt_unallocated_amount": flt(bt.unallocated_amount),
        }

        # Get matched voucher (linked or unmatched by reference_number)
        matched_voucher = get_matched_voucher_for_bt(bt, filters)

        if matched_voucher:
            # Case 1, 2, 3: BT with matched voucher - show in same row
            all_matched_vouchers.add(
                (matched_voucher.get("doctype"), matched_voucher.get("name")))
            row = base_row.copy()
            row.update({
                "voucher_doc_type": matched_voucher.get("doctype", ""),
                "voucher_name": matched_voucher.get("name", ""),
                "voucher_reference_no": matched_voucher.get("reference_no", ""),
                "voucher_posting_date": matched_voucher.get("posting_date", ""),
                "voucher_amount": flt(matched_voucher.get("amount", 0)),
                "voucher_party_type": matched_voucher.get("party_type", ""),
                "voucher_party": matched_voucher.get("party", ""),
                "reconciled_status": get_status_emoji(bt.status, flt(bt.unallocated_amount), has_voucher=True, is_matched=matched_voucher.get("is_linked", False), row_number=1),
                "btn_reconcile": get_reconcile_button(bt.name, flt(bt.unallocated_amount), matched_voucher.get("name"), matched_voucher.get("doctype"), bt.status) if not matched_voucher.get("is_linked", False) else "",
                "btn_create_pe": "",
                "btn_create_je": "",
                "btn_create_bt": ""
            })
            data.append(row)
        else:
            # BT without matched voucher - show BT only with create buttons
            row = base_row.copy()
            row.update({
                "voucher_doc_type": "",
                "voucher_name": "",
                "voucher_reference_no": "",
                "voucher_posting_date": "",
                "voucher_amount": 0,
                "voucher_party_type": "",
                "voucher_party": "",
                "reconciled_status": get_status_emoji(bt.status, flt(bt.unallocated_amount), has_voucher=False, is_matched=False, row_number=1),
                "btn_reconcile": get_reconcile_button(bt.name, flt(bt.unallocated_amount)),
                "btn_create_pe": get_create_pe_button(bt.name, flt(bt.unallocated_amount), bt.party_type, bt.party, bt.reference_number, bt.date),
                "btn_create_je": get_create_je_button(bt.name, flt(bt.unallocated_amount)),
                "btn_create_bt": ""
            })
            data.append(row)

    # Second: Show unmatched Payment Entries (Case 5)
    unmatched_payment_entries = get_unmatched_payment_entries(
        filters, all_matched_vouchers)
    for pe in unmatched_payment_entries:
        row = {
            "bt_name": "",
            "bt_date": "",
            "bt_deposit": 0,
            "bt_withdrawal": 0,
            "bt_reference_number": pe.get("reference_no", ""),
            "bt_unallocated_amount": 0,
            "voucher_doc_type": "Payment Entry",
            "voucher_name": pe.get("name", ""),
            "voucher_reference_no": pe.get("reference_no", ""),
            "voucher_posting_date": pe.get("posting_date", ""),
            "voucher_amount": flt(pe.get("amount", 0)),
            "voucher_party_type": pe.get("party_type", ""),
            "voucher_party": pe.get("party", ""),
            "reconciled_status": "❌ Unmatched",
            "btn_reconcile": "",
            "btn_create_pe": "",
            "btn_create_je": "",
            "btn_create_bt": get_create_bt_button("Payment Entry", pe.get("name"), has_bt=False)
        }
        data.append(row)

    # Third: Show unmatched Journal Entries (Case 4)
    unmatched_journal_entries = get_unmatched_journal_entries(
        filters, all_matched_vouchers)
    for je in unmatched_journal_entries:
        row = {
            "bt_name": "",
            "bt_date": "",
            "bt_deposit": 0,
            "bt_withdrawal": 0,
            "bt_reference_number": je.get("cheque_no", ""),
            "bt_unallocated_amount": 0,
            "voucher_doc_type": "Journal Entry",
            "voucher_name": je.get("name", ""),
            "voucher_reference_no": je.get("cheque_no", ""),
            "voucher_posting_date": je.get("posting_date", ""),
            "voucher_amount": flt(je.get("amount", 0)),
            "voucher_party_type": je.get("party_type", ""),
            "voucher_party": je.get("party", ""),
            "reconciled_status": "❌ Unmatched",
            "btn_reconcile": "",
            "btn_create_pe": "",
            "btn_create_je": "",
            "btn_create_bt": get_create_bt_button("Journal Entry", je.get("name"), has_bt=False)
        }
        data.append(row)

    return data


def get_matched_voucher_for_bt(bank_transaction, filters):
    """
    Get matched voucher for Bank Transaction based on exact matching rules:
    - Case 1: BT withdrawal + PE payment_type = Pay + same reference_number
    - Case 2: BT deposit + PE payment_type = Receive + same reference_number
    - Case 3: BT withdrawal + JE cheque_no + same reference_number
    """
    if not bank_transaction.reference_number:
        return None

    try:
        bank_account_doc = frappe.get_doc(
            "Bank Account", bank_transaction.bank_account)
        bank_gl_account = bank_account_doc.account

        # First: Check linked vouchers
        linked = frappe.get_all(
            "Bank Transaction Payments",
            filters={"parent": bank_transaction.name},
            fields=["payment_entry", "payment_document"],
            limit=1
        )

        if linked:
            link = linked[0]
            try:
                doc = frappe.get_cached_doc(
                    link.payment_document, link.payment_entry)
                voucher_data = {
                    "doctype": link.payment_document,
                    "name": link.payment_entry,
                    "is_linked": True
                }

                if link.payment_document == "Payment Entry":
                    voucher_data.update({
                        "reference_no": doc.reference_no or "",
                        "posting_date": doc.posting_date,
                        "amount": flt(doc.base_paid_amount_after_tax),
                        "party_type": doc.party_type or "",
                        "party": doc.party or ""
                    })
                elif link.payment_document == "Journal Entry":
                    voucher_data.update({
                        "reference_no": doc.cheque_no or "",
                        "posting_date": doc.posting_date,
                        "amount": 0,  # Will calculate from accounts
                        "party_type": "",  # Journal Entry doesn't have party_type at document level
                        "party": doc.pay_to_recd_from or ""
                    })

                return voucher_data
            except:
                pass

        # Second: Check unmatched vouchers by reference_number
        # Case 1 & 2: Payment Entry matching
        if bank_transaction.reference_number:
            payment_type = "Receive" if bank_transaction.deposit > 0.0 else "Pay"

            pe_filters = {
                "company": bank_transaction.company,
                "docstatus": 1,
                "clearance_date": ["is", "not set"],
                "reference_no": bank_transaction.reference_number,
                "payment_type": payment_type
            }

            # Date filters - use SQL for better control
            from_date = filters.get(
                "bank_statement_from_date") or filters.get("from_date")
            to_date = filters.get(
                "bank_statement_to_date") or filters.get("to_date")

            payment_entries = frappe.db.sql("""
                SELECT
                    name,
                    posting_date,
                    reference_no,
                    reference_date,
                    party,
                    party_type,
                    base_paid_amount_after_tax as paid_amount
                FROM `tabPayment Entry`
                WHERE company = %(company)s
                    AND docstatus = 1
                    AND (clearance_date IS NULL OR clearance_date = '')
                    AND reference_no = %(reference_no)s
                    AND payment_type = %(payment_type)s
                    AND (paid_to = %(bank_account)s OR paid_from = %(bank_account)s)
                    AND (%(from_date)s IS NULL OR posting_date >= %(from_date)s)
                    AND (%(to_date)s IS NULL OR posting_date <= %(to_date)s)
                LIMIT 1
            """, {
                "company": bank_transaction.company,
                "reference_no": bank_transaction.reference_number,
                "payment_type": payment_type,
                "bank_account": bank_gl_account,
                "from_date": from_date or None,
                "to_date": to_date or None
            }, as_dict=True)

            if payment_entries:
                pe = payment_entries[0]
                # Verify matching: Case 1 or Case 2
                if (bank_transaction.withdrawal > 0 and payment_type == "Pay") or \
                   (bank_transaction.deposit > 0 and payment_type == "Receive"):
                    return {
                        "doctype": "Payment Entry",
                        "name": pe.name,
                        "reference_no": pe.reference_no or "",
                        "posting_date": pe.posting_date,
                        "amount": flt(pe.paid_amount),
                        "party_type": pe.party_type or "",
                        "party": pe.party or "",
                        "is_linked": False
                    }

        # Case 3: Journal Entry matching (only for withdrawal)
        if bank_transaction.withdrawal > 0 and bank_transaction.reference_number:
            journal_entries = frappe.db.sql("""
                SELECT DISTINCT
                    je.name,
                    je.posting_date,
                    je.cheque_no,
                    je.pay_to_recd_from as party,
                    SUM(jea.debit_in_account_currency - jea.credit_in_account_currency) as amount
                FROM `tabJournal Entry` je
                INNER JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
                WHERE je.company = %(company)s
                    AND je.docstatus = 1
                    AND je.clearance_date IS NULL
                    AND je.voucher_type != 'Opening Entry'
                    AND je.cheque_no = %(cheque_no)s
                    AND jea.account = %(bank_account)s
                    AND (je.posting_date >= %(date_from)s OR %(date_from)s IS NULL)
                    AND (je.posting_date <= %(date_to)s OR %(date_to)s IS NULL)
                GROUP BY je.name
                LIMIT 1
            """, {
                "company": bank_transaction.company,
                "cheque_no": bank_transaction.reference_number,
                "bank_account": bank_gl_account,
                "date_from": filters.get("bank_statement_from_date") or filters.get("from_date") or None,
                "date_to": filters.get("bank_statement_to_date") or filters.get("to_date") or None
            }, as_dict=True)

            if journal_entries:
                je = journal_entries[0]
                return {
                    "doctype": "Journal Entry",
                    "name": je.name,
                    "reference_no": je.cheque_no or "",
                    "posting_date": je.posting_date,
                    "amount": abs(flt(je.amount)),
                    "party_type": "",  # Journal Entry doesn't have party_type at document level
                    "party": je.party or "",
                    "is_linked": False
                }

        return None

    except Exception as e:
        frappe.log_error(
            "[bank_reconcile_report.py] method: get_matched_voucher_for_bt", "Bank Reconcile Report")
        return None


def get_linked_vouchers(bank_transaction_name):
    """Get vouchers linked to bank transaction"""
    linked = frappe.get_all(
        "Bank Transaction Payments",
        fields=[
            "payment_document",
            "payment_entry",
            "allocated_amount"
        ],
        filters={"parent": bank_transaction_name},
        order_by="creation"
    )

    vouchers = []
    for link in linked:
        try:
            doc = frappe.get_cached_doc(
                link.payment_document, link.payment_entry)

            voucher_data = {
                "doctype": link.payment_document,
                "name": link.payment_entry,
                "amount": link.allocated_amount
            }

            if link.payment_document == "Payment Entry":
                voucher_data.update({
                    "reference_no": doc.reference_no or "",
                    "posting_date": doc.posting_date,
                    "party": (doc.party or "") + (" (" + doc.party_type + ")" if doc.party_type else "")
                })
            elif link.payment_document == "Journal Entry":
                voucher_data.update({
                    "reference_no": doc.cheque_no or "",
                    "posting_date": doc.posting_date,
                    "party": doc.pay_to_recd_from or ""
                })

            vouchers.append(voucher_data)
        except Exception as e:
            frappe.log_error(
                "[bank_reconcile_report.py] method: get_linked_vouchers", "Bank Reconcile Report")
            continue

    return vouchers


def get_unmatched_payment_entries(filters, matched_vouchers):
    """
    Get Payment Entries that are NOT matched to any Bank Transaction (Case 5)
    """
    try:
        if not filters.get("bank_account") or not filters.get("company"):
            return []

        bank_account_doc = frappe.get_doc(
            "Bank Account", filters.get("bank_account"))
        bank_gl_account = bank_account_doc.account

        from_date = filters.get(
            "bank_statement_from_date") or filters.get("from_date")
        to_date = filters.get(
            "bank_statement_to_date") or filters.get("to_date")

        # Use SQL for better control and to handle filters correctly
        payment_entries = frappe.db.sql("""
            SELECT
                name,
                posting_date,
                reference_no,
                reference_date,
                party,
                party_type,
                payment_type,
                base_paid_amount_after_tax as paid_amount
            FROM `tabPayment Entry`
            WHERE company = %(company)s
                AND docstatus = 1
                AND (clearance_date IS NULL OR clearance_date = '')
                AND reference_no IS NOT NULL
                AND reference_no != ''
                AND (paid_to = %(bank_account)s OR paid_from = %(bank_account)s)
                AND (%(from_date)s IS NULL OR posting_date >= %(from_date)s)
                AND (%(to_date)s IS NULL OR posting_date <= %(to_date)s)
            ORDER BY posting_date DESC
        """, {
            "company": filters.get("company"),
            "bank_account": bank_gl_account,
            "from_date": from_date or None,
            "to_date": to_date or None
        }, as_dict=True)

        # Filter out matched vouchers
        unmatched = []
        for pe in payment_entries:
            match_key = ("Payment Entry", pe.name)
            if match_key not in matched_vouchers:
                # Check if this PE has a matching BT by reference_number and payment_type
                # Use SQL to check matching based on exact rules
                matching_bt = frappe.db.sql("""
                    SELECT name, deposit, withdrawal
                    FROM `tabBank Transaction`
                    WHERE reference_number = %(reference_no)s
                        AND company = %(company)s
                        AND bank_account = %(bank_account)s
                        AND docstatus = 1
                        AND (
                            (deposit > 0 AND %(payment_type)s = 'Receive') OR
                            (withdrawal > 0 AND %(payment_type)s = 'Pay')
                        )
                    LIMIT 1
                """, {
                    "reference_no": pe.reference_no,
                    "company": filters.get("company"),
                    "bank_account": filters.get("bank_account"),
                    "payment_type": pe.get("payment_type", "")
                }, as_dict=True)

                # If no matching BT found, add to unmatched
                if not matching_bt:
                    unmatched.append({
                        "name": pe.name,
                        "posting_date": pe.posting_date,
                        "reference_no": pe.reference_no or "",
                        "amount": flt(pe.paid_amount),
                        "party_type": pe.party_type or "",
                        "party": pe.party or ""
                    })

        return unmatched

    except Exception as e:
        frappe.log_error(
            "[bank_reconcile_report.py] method: get_unmatched_payment_entries", "Bank Reconcile Report")
        return []


def get_unmatched_journal_entries(filters, matched_vouchers):
    """
    Get Journal Entries that are NOT matched to any Bank Transaction (Case 4)
    """
    try:
        if not filters.get("bank_account") or not filters.get("company"):
            return []

        bank_account_doc = frappe.get_doc(
            "Bank Account", filters.get("bank_account"))
        bank_gl_account = bank_account_doc.account

        from_date = filters.get(
            "bank_statement_from_date") or filters.get("from_date")
        to_date = filters.get(
            "bank_statement_to_date") or filters.get("to_date")

        journal_entries = frappe.db.sql("""
            SELECT DISTINCT
                je.name,
                je.posting_date,
                je.cheque_no,
                je.pay_to_recd_from as party,
                MAX(jea.party_type) as party_type,
                SUM(jea.debit_in_account_currency - jea.credit_in_account_currency) as amount
            FROM `tabJournal Entry` je
            INNER JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
            WHERE je.company = %(company)s
                AND je.docstatus = 1
                AND je.clearance_date IS NULL
                AND je.voucher_type != 'Opening Entry'
                AND je.cheque_no IS NOT NULL
                AND je.cheque_no != ''
                AND jea.account = %(bank_account)s
                AND (je.posting_date >= %(date_from)s OR %(date_from)s IS NULL)
                AND (je.posting_date <= %(date_to)s OR %(date_to)s IS NULL)
            GROUP BY je.name
            ORDER BY je.posting_date DESC
        """, {
            "company": filters.get("company"),
            "bank_account": bank_gl_account,
            "date_from": from_date or None,
            "date_to": to_date or None
        }, as_dict=True)

        # Filter out matched vouchers and check for matching BT
        unmatched = []
        for je in journal_entries:
            match_key = ("Journal Entry", je.name)
            if match_key not in matched_vouchers:
                # Check if this JE has a matching BT by cheque_no
                # JE matches BT withdrawal only (Case 3)
                matching_bt = frappe.db.sql("""
                    SELECT name
                    FROM `tabBank Transaction`
                    WHERE reference_number = %(cheque_no)s
                        AND company = %(company)s
                        AND bank_account = %(bank_account)s
                        AND docstatus = 1
                        AND withdrawal > 0
                    LIMIT 1
                """, {
                    "cheque_no": je.cheque_no,
                    "company": filters.get("company"),
                    "bank_account": filters.get("bank_account")
                }, as_dict=True)

                # If no matching BT found, add to unmatched
                if not matching_bt:
                    unmatched.append({
                        "name": je.name,
                        "posting_date": je.posting_date,
                        "cheque_no": je.cheque_no or "",
                        "amount": abs(flt(je.amount)),
                        "party_type": je.party_type or "",
                        "party": je.party or ""
                    })

        return unmatched

    except Exception as e:
        frappe.log_error(
            "[bank_reconcile_report.py] method: get_unmatched_journal_entries", "Bank Reconcile Report")
        return []


def get_unmatched_vouchers(bank_transaction, filters):
    """
    Get potential matching vouchers for bank transaction that are NOT yet linked.

    Matching criteria (ONLY):
    - Reference Number (must match exactly)
    - Payment Type (Receive/Pay matches Deposit/Withdrawal)

    Other criteria (amount, party) are NOT used for matching.
    """
    vouchers = []

    # If no reference_number, cannot match
    if not bank_transaction.reference_number:
        return vouchers

    try:
        bank_account_doc = frappe.get_doc(
            "Bank Account", bank_transaction.bank_account)
        bank_gl_account = bank_account_doc.account

        # Determine payment type based on deposit/withdrawal
        payment_type = "Receive" if bank_transaction.deposit > 0.0 else "Pay"

        # Get already linked vouchers to exclude them
        linked_voucher_names = set()
        linked = frappe.get_all(
            "Bank Transaction Payments",
            filters={"parent": bank_transaction.name},
            fields=["payment_entry", "payment_document"]
        )
        for link in linked:
            linked_voucher_names.add(
                (link.payment_document, link.payment_entry))

        # Get Payment Entries matching reference_number and payment_type ONLY
        pe_filters = {
            "company": bank_transaction.company,
            "docstatus": 1,
            "clearance_date": ["is", "not set"],
            "reference_no": bank_transaction.reference_number,
            "payment_type": ["in", [payment_type, "Internal Transfer"]]
        }

        # Use bank_statement_from_date/to_date or fallback to from_date/to_date
        from_date = filters.get(
            "bank_statement_from_date") or filters.get("from_date")
        to_date = filters.get(
            "bank_statement_to_date") or filters.get("to_date")

        if from_date or to_date:
            if from_date and to_date:
                pe_filters["posting_date"] = ["between", [from_date, to_date]]
            elif from_date:
                pe_filters["posting_date"] = [">=", from_date]
            elif to_date:
                pe_filters["posting_date"] = ["<=", to_date]

        payment_entries = frappe.get_all(
            "Payment Entry",
            fields=["name", "posting_date", "reference_no", "reference_date",
                    "party", "party_type", "base_paid_amount_after_tax as paid_amount"],
            filters=pe_filters,
            or_filters=[
                {"paid_to": bank_gl_account},
                {"paid_from": bank_gl_account}
            ],
            order_by="posting_date desc"
        )

        for pe in payment_entries:
            match_key = ("Payment Entry", pe.name)
            if match_key not in linked_voucher_names:
                vouchers.append({
                    "doctype": "Payment Entry",
                    "name": pe.name,
                    "reference_no": pe.reference_no or "",
                    "posting_date": pe.posting_date,
                    "amount": flt(pe.paid_amount),
                    "party": (pe.party or "") + (" (" + pe.party_type + ")" if pe.party_type else "")
                })

        # Get Journal Entries matching cheque_no (reference_number) ONLY
        journal_entries = frappe.db.sql("""
			SELECT DISTINCT
				je.name,
				je.posting_date,
				je.cheque_no,
				je.cheque_date,
				je.pay_to_recd_from as party,
				SUM(jea.debit_in_account_currency - jea.credit_in_account_currency) as amount
			FROM `tabJournal Entry` je
			INNER JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
			WHERE je.company = %(company)s
				AND je.docstatus = 1
				AND je.clearance_date IS NULL
				AND je.voucher_type != 'Opening Entry'
				AND je.cheque_no = %(cheque_no)s
				AND jea.account = %(bank_account)s
				AND (je.posting_date >= %(date_from)s OR %(date_from)s IS NULL)
				AND (je.posting_date <= %(date_to)s OR %(date_to)s IS NULL)
			GROUP BY je.name
			ORDER BY je.posting_date DESC
		""", {
            "company": bank_transaction.company,
            "cheque_no": bank_transaction.reference_number,
            "bank_account": bank_gl_account,
            "date_from": filters.get("bank_statement_from_date") or filters.get("from_date") or None,
            "date_to": filters.get("bank_statement_to_date") or filters.get("to_date") or None
        }, as_dict=True)

        for je in journal_entries:
            match_key = ("Journal Entry", je.name)
            if match_key not in linked_voucher_names:
                vouchers.append({
                    "doctype": "Journal Entry",
                    "name": je.name,
                    "reference_no": je.cheque_no or "",
                    "posting_date": je.posting_date,
                    "amount": abs(flt(je.amount)),
                    "party": je.party or ""
                })

        return vouchers[:10]  # Limit to 10 results

    except Exception as e:
        frappe.log_error(
            "[bank_reconcile_report.py] method: get_unmatched_vouchers", "Bank Reconcile Report")
        return []


def get_status_emoji(status, unallocated_amount, has_voucher=False, is_matched=False, row_number=0):
    """
    Get status with emoji and number. Keep original Bank Transaction status name.
    Colors are applied in JavaScript formatter.

    Args:
            status: Bank Transaction status (original name: Reconciled, Unreconciled, Pending)
            unallocated_amount: Unallocated amount
            has_voucher: Whether row has a voucher
            is_matched: Whether voucher is matched to Bank Transaction
            row_number: Row number for same reference (1, 2, 3...)
    """
    # Number emoji mapping
    number_emoji = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
        10: "🔟"
    }

    emoji = number_emoji.get(row_number, f"{row_number}.")

    # Get original status name
    status_name = status if status else "Unreconciled"

    # If voucher exists and is matched: Show status with checkmark and number
    if has_voucher and is_matched:
        # Status is usually "Unreconciled" (partial) or "Reconciled" (full)
        if status == "Reconciled" or unallocated_amount == 0:
            return f"{emoji} ✅ {status_name}"
        else:
            # Partially reconciled - still Unreconciled
            return f"{emoji} {status_name}"

    # If voucher exists but not matched: Show "Unmatched" with X
    if has_voucher and not is_matched:
        return f"❌ Unmatched"

    # If no voucher: Show Bank Transaction status with appropriate emoji
    if status == "Reconciled" or unallocated_amount == 0:
        return f"{emoji} ✅ {status_name}"
    elif status == "Unreconciled" and unallocated_amount > 0:
        return f"{emoji} {status_name}"
    else:
        return f"{emoji} ⏳ {status_name}"


def get_reconcile_button(bt_name, unallocated_amount, voucher_name=None, voucher_doc_type=None, status=None):
    # Show button only if status is NOT "Reconciled"
    if status == "Reconciled":
        return ""

    if unallocated_amount <= 0 and not voucher_name:
        return ""

    if voucher_name and voucher_doc_type:
        return f'<button class="btn btn-xs btn-primary reconcile-btn" data-bt="{bt_name}" data-voucher="{voucher_name}" data-doctype="{voucher_doc_type}">🔗 Reconcile</button>'
    else:
        return f'<button class="btn btn-xs btn-primary reconcile-btn" data-bt="{bt_name}">🔗 Reconcile</button>'


def get_create_pe_button(bt_name, unallocated_amount, party_type, party, reference_number=None, date=None, has_voucher=False, voucher_type=None):
    """Button to create Payment Entry - show if voucher_type is NOT Payment Entry or no voucher exists"""
    if voucher_type == "Payment Entry":
        return ""
    if has_voucher and voucher_type and voucher_type != "Payment Entry":
        # Show button even if voucher exists but it's not Payment Entry
        pass
    elif has_voucher:
        return ""
    if unallocated_amount <= 0:
        return ""
    if not party_type or not party:
        return ""
    ref_no_attr = f' data-reference-number="{reference_number}"' if reference_number else ""
    date_attr = f' data-date="{date}"' if date else ""
    return f'<button class="btn btn-xs btn-success create-pe-btn" data-bt="{bt_name}" data-party-type="{party_type}" data-party="{party}"{ref_no_attr}{date_attr}>➕ Payment Entry</button>'


def get_create_je_button(bt_name, unallocated_amount, has_voucher=False, voucher_type=None):
    """Button to create Journal Entry - show if voucher_type is NOT Journal Entry or no voucher exists"""
    if voucher_type == "Journal Entry":
        return ""
    if has_voucher and voucher_type and voucher_type != "Journal Entry":
        # Show button even if voucher exists but it's not Journal Entry
        pass
    elif has_voucher:
        return ""
    if unallocated_amount <= 0:
        return ""
    return f'<button class="btn btn-xs btn-info create-je-btn" data-bt="{bt_name}">📝 Journal Entry</button>'


def get_create_bt_button(voucher_doc_type, voucher_name, has_bt=False):
    """Button to create Bank Transaction from Payment Entry or Journal Entry - only show if bt_name is null (no Bank Transaction exists)"""
    if has_bt:
        return ""
    if not voucher_doc_type or not voucher_name:
        return ""
    return f'<button class="btn btn-xs btn-warning create-bt-btn" data-doctype="{voucher_doc_type}" data-voucher="{voucher_name}">➕ Bank Transaction</button>'


def get_account_balance(bank_account, till_date, company):
    """Returns account balance till the specified date (from ERPNext Bank Reconciliation Tool)"""
    account = frappe.db.get_value("Bank Account", bank_account, "account")
    if not account:
        return 0.0

    filters = frappe._dict({
        "account": account,
        "report_date": till_date,
        "include_pos_transactions": 1,
        "company": company,
    })

    data = get_entries(filters)
    balance_as_per_system = get_balance_on(
        filters["account"], filters["report_date"])

    total_debit, total_credit = 0.0, 0.0
    for d in data:
        total_debit += flt(d.debit)
        total_credit += flt(d.credit)

    amounts_not_reflected_in_system = get_amounts_not_reflected_in_system(
        filters)

    return flt(balance_as_per_system) - flt(total_debit) + flt(total_credit) + amounts_not_reflected_in_system


def get_report_summary(filters, data):
    """Calculate and return report summary with closing balances"""
    summary = []

    if not filters.get("bank_account") or not filters.get("company"):
        return summary

    # Get account currency
    account = frappe.db.get_value(
        "Bank Account", filters.get("bank_account"), "account")
    if not account:
        return summary

    currency = get_account_currency(account) or frappe.db.get_value(
        "Company", filters.get("company"), "default_currency")

    # Get closing balance as per bank statement
    bank_statement_closing = flt(filters.get(
        "bank_statement_closing_balance", 0))

    # Get closing balance as per ERP (system)
    to_date = filters.get("bank_statement_to_date") or filters.get("to_date")
    if to_date:
        cleared_balance = get_account_balance(
            filters.get("bank_account"),
            to_date,
            filters.get("company")
        )
    else:
        cleared_balance = 0.0

    # Calculate difference
    difference = bank_statement_closing - cleared_balance

    # Build summary
    summary.append({
        "value": cleared_balance,
        "label": _("Closing Balance as per ERP"),
        "indicator": "blue",
        "currency": currency
    })

    summary.append({
        "value": bank_statement_closing,
        "label": _("Closing Balance as per Bank Statement"),
        "indicator": "orange",
        "currency": currency
    })

    summary.append({
        "value": abs(difference),
        "label": _("Difference"),
        "indicator": "green" if abs(difference) < 0.01 else "red",
        "currency": currency
    })

    return summary
