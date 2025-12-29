// Copyright (c) 2025, abdopcnet@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Bank Transaction', {
	refresh(frm) {
		// Add button to create Bank Transactions (directly on toolbar, not under Actions)
		if (!frm.is_new()) {
			frm.add_custom_button(__('Create Bank Transactions'), function () {
				create_bank_transactions(frm);
			});

			// Add button to open Bank Reconcile Report
			if (frm.doc.bank_account) {
				frm.add_custom_button(__('Bank Reconcile Report'), function () {
					open_bank_reconcile_report(frm);
				});
			}
		}
	},

	bank_account(frm) {
		// Auto-fetch company from bank account if not set
		if (frm.doc.bank_account && !frm.doc.company) {
			frappe.db.get_value('Bank Account', frm.doc.bank_account, 'company', function (r) {
				if (r && r.company) {
					frm.set_value('company', r.company);
				}
			});
		}
	},
});

function create_bank_transactions(frm) {
	if (!frm.doc.bank_transactions_table || frm.doc.bank_transactions_table.length === 0) {
		frappe.msgprint(__('Please add at least one Bank Transaction in the table'));
		return;
	}

	frappe.confirm(
		__('Create {0} Bank Transaction(s) as Draft?', [frm.doc.bank_transactions_table.length]),
		function () {
			// Save document if dirty, then create bank transactions
			if (frm.is_dirty()) {
				frm.save().then(function () {
					call_create_method(frm);
				});
			} else {
				// Document is already saved, call method directly
				call_create_method(frm);
			}
		},
	);
}

function call_create_method(frm) {
	// Count rows without bank_transaction already set
	let rows_to_create = frm.doc.bank_transactions_table.filter(function (row) {
		return !row.bank_transaction;
	}).length;

	// Use frm.call() with doc to call Document method correctly
	frm.call({
		doc: frm.doc,
		method: 'create_bank_transactions',
		freeze: true,
		freeze_message: __('Creating Bank Transactions...'),
		callback: function (r) {
			if (!r.exc && r.message) {
				if (r.message.created > 0) {
					frappe.show_alert({
						message: __('{0} Bank Transaction(s) created successfully', [
							r.message.created,
						]),
						indicator: 'green',
					});
					// Refresh the form to show updated bank_transaction links
					frm.reload_doc();
				}
				if (r.message.errors && r.message.errors.length > 0) {
					frappe.msgprint({
						title: __('Errors occurred'),
						message: r.message.errors.join('<br>'),
						indicator: 'orange',
					});
				}
			}
		},
	});
}

function open_bank_reconcile_report(frm) {
	if (!frm.doc.bank_account) {
		frappe.msgprint(__('Please select Bank Account first'));
		return;
	}

	// Get default company
	let company = frm.doc.company || frappe.defaults.get_default('company');

	// Build URL with filters
	let filters = {
		company: company,
		bank_account: frm.doc.bank_account,
	};

	// Convert filters to URL format
	let filter_string = Object.keys(filters)
		.map((key) => `${key}=${encodeURIComponent(filters[key])}`)
		.join('&');

	// Open report
	frappe.set_route('query-report', 'Bank Reconcile Report', {
		company: company,
		bank_account: frm.doc.bank_account,
	});
}
