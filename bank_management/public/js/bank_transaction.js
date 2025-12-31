// Copyright (c) 2025, abdopcnet@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Transaction', {
	refresh(frm) {
		// Add button to open Bank Reconcile Report in new window
		// Only show button when document is submitted (docstatus = 1)
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Bank Reconcile Report'), function () {
				open_bank_reconcile_report_new_window(frm);
			});
		}
	},
});

function open_bank_reconcile_report_new_window(frm) {
	// Get default company
	let company = frm.doc.company || frappe.defaults.get_default('company');

	// Get bank account from current document
	let bank_account = frm.doc.bank_account;

	// Set route options for filters
	frappe.route_options = {
		company: company,
	};

	if (bank_account) {
		frappe.route_options.bank_account = bank_account;
	}

	// Open in new window
	frappe.open_in_new_tab = true;
	frappe.set_route('query-report', 'Bank Reconcile Report');
}
