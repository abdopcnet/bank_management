# Copyright (c) 2025, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class BulkBankTransaction(Document):
    def validate(self):
        # Validate that bank_account is set
        if not self.bank_account:
            frappe.throw(_("Bank Account is required"))

        # Validate that at least one row exists
        if not self.bank_transactions_table:
            frappe.throw(
                _("Please add at least one Bank Transaction in the table"))

        # Validate each row
        for row in self.bank_transactions_table:
            if not row.date:
                frappe.throw(_("Date is required for all Bank Transactions"))

            # At least one of deposit or withdrawal must be provided
            if not flt(row.deposit) and not flt(row.withdrawal):
                frappe.throw(
                    _("Either Deposit or Withdrawal must be provided for row with date {0}").format(row.date))

    @frappe.whitelist()
    def create_bank_transactions(self):
        """Create all Bank Transactions from the table as Draft"""
        # Ensure document is saved first to get name
        if self.is_new():
            self.save()

        # Reload to get latest data
        self.reload()

        # Validate bank_account is set
        if not self.bank_account:
            frappe.throw(_("Bank Account is required"))

        if not self.bank_transactions_table:
            frappe.throw(_("No Bank Transactions to create"))

        created_count = 0
        errors = []

        # Store the Bulk Bank Transaction name for linking
        bulk_bank_transaction_name = self.name

        # Get company from bank account if not provided in parent
        company = self.company
        if not company:
            company = frappe.db.get_value(
                "Bank Account", self.bank_account, "company")
            if not company:
                frappe.throw(
                    _("Company not found for Bank Account {0}").format(self.bank_account))

        # Get currency from bank account's linked account, or company default
        account = frappe.db.get_value(
            "Bank Account", self.bank_account, "account")
        if account:
            currency = frappe.db.get_value(
                "Account", account, "account_currency")
        else:
            currency = None

        # Fallback to company default currency if not found
        if not currency:
            currency = frappe.db.get_value(
                "Company", company, "default_currency")

        if not currency:
            frappe.throw(
                _("Currency not found for Bank Account {0}").format(self.bank_account))

        for idx, row in enumerate(self.bank_transactions_table, start=1):
            try:
                # Skip if Bank Transaction already created for this row
                if row.bank_transaction:
                    continue

                # Validate required fields
                if not row.date:
                    errors.append(_("Row {0}: Date is required").format(idx))
                    continue

                if not flt(row.deposit) and not flt(row.withdrawal):
                    errors.append(
                        _("Row {0}: Either Deposit or Withdrawal must be provided").format(idx))
                    continue

                # Create Bank Transaction
                bank_transaction = frappe.new_doc("Bank Transaction")
                bank_transaction.date = row.date
                bank_transaction.bank_account = self.bank_account
                bank_transaction.company = company
                bank_transaction.deposit = flt(row.deposit)
                bank_transaction.withdrawal = flt(row.withdrawal)
                bank_transaction.currency = currency
                bank_transaction.description = row.description or ""
                bank_transaction.reference_number = row.reference_number or ""
                # Link to Bulk Bank Transaction
                bank_transaction.custom_created_from = bulk_bank_transaction_name

                # Insert as Draft (don't submit)
                bank_transaction.insert()

                # Update the row with created Bank Transaction name
                row.bank_transaction = bank_transaction.name

                created_count += 1

            except Exception as e:
                frappe.log_error(
                    "[bulk_bank_transaction.py] method: create_bank_transactions", "Bulk Bank Transaction")
                errors.append(_("Row {0}: {1}").format(idx, str(e)))

        # Save the Bulk Bank Transaction to persist the bank_transaction links in child table
        if created_count > 0:
            self.save()

        # Show message
        message = _("{0} Bank Transaction(s) created successfully").format(
            created_count)
        if errors:
            message += "\n\n" + _("Errors:\n{0}").format("\n".join(errors))
            frappe.msgprint(message, title=_(
                "Bank Transactions Created"), indicator="orange" if errors else "green")
        else:
            frappe.msgprint(message, title=_(
                "Bank Transactions Created"), indicator="green")

        return {
            "created": created_count,
            "errors": errors
        }
