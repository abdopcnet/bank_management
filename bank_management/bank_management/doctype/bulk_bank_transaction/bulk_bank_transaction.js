// Copyright (c) 2025, abdopcnet@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Bank Transaction', {
	refresh(frm) {
		// Add button to create Bank Transactions (directly on toolbar, not under Actions)
		if (!frm.is_new()) {
			frm.add_custom_button(__('Create Bank Transactions'), function () {
				create_bank_transactions(frm);
			});
		}
	},
});

frappe.ui.form.on('Bank Transactions Table', {
	bank_account(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.bank_account) {
			// Auto-fetch company from bank account if not set in parent
			frappe.db.get_value('Bank Account', row.bank_account, 'company', function (r) {
				if (r && r.company && !frm.doc.company) {
					frappe.model.set_value(
						'Bulk Bank Transaction',
						frm.doc.name,
						'company',
						r.company,
					);
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
					// Refresh the form
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
