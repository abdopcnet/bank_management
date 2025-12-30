// Copyright (c) 2025, abdopcnet@gmail.com and contributors
// For license information, please see license.txt

frappe.query_reports['Bank Reconcile Report'] = {
	filters: [
		// First row: company, bank_account, bank_statement_from_date, bank_statement_to_date, created_by
		{
			fieldname: 'company',
			label: __('Company'),
			fieldtype: 'Link',
			options: 'Company',
			reqd: 1,
			default: frappe.defaults.get_default('company'),
			columns: 2,
		},
		{
			fieldname: 'bank_account',
			label: __('Bank Account'),
			fieldtype: 'Link',
			options: 'Bank Account',
			reqd: 1,
			columns: 2,
			get_query: function () {
				return {
					filters: {
						company: frappe.query_report.get_filter_value('company'),
						is_company_account: 1,
					},
				};
			},
		},
		{
			fieldname: 'bank_statement_from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.month_start(),
			depends_on: 'eval:!doc.filter_by_reference_date',
			columns: 2,
		},
		{
			fieldname: 'bank_statement_to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.month_end(),
			depends_on: 'eval:!doc.filter_by_reference_date',
			columns: 2,
		},
		{
			fieldname: 'created_by',
			label: __('Created By'),
			fieldtype: 'Link',
			options: 'User',
			columns: 2,
		},
		// Second row: filter_by_reference_date, from_reference_date, to_reference_date, account_opening_balance, bank_statement_closing_balance
		{
			fieldname: 'filter_by_reference_date',
			label: __('Filter by Reference Date'),
			fieldtype: 'Check',
			default: 0,
			columns: 2,
		},
		{
			fieldname: 'from_reference_date',
			label: __('From Reference Date'),
			fieldtype: 'Date',
			depends_on: 'eval:doc.filter_by_reference_date',
			columns: 2,
		},
		{
			fieldname: 'to_reference_date',
			label: __('To Reference Date'),
			fieldtype: 'Date',
			depends_on: 'eval:doc.filter_by_reference_date',
			columns: 2,
		},
		{
			fieldname: 'account_opening_balance',
			label: __('Account Opening Balance'),
			fieldtype: 'Currency',
			read_only: 1,
			depends_on: 'eval:doc.bank_statement_from_date',
			columns: 2,
		},
		{
			fieldname: 'bank_statement_closing_balance',
			label: __('Closing Balance'),
			fieldtype: 'Currency',
			depends_on: 'eval:doc.bank_statement_to_date',
			columns: 2,
		},
		{
			fieldname: 'show_unmatched_vouchers',
			label: __('Show Unmatched Vouchers'),
			fieldtype: 'Check',
			default: 0,
			description: __(
				'Show Payment Entries and Journal Entries that match by reference number and payment type but are not yet linked to Bank Transactions.',
			),
			columns: 2,
		},
	],

	onload: function (report) {
		// Add buttons (direct buttons, not in dropdown)
		report.page.add_inner_button(__('📖 General Ledger'), function () {
			open_general_ledger(report);
		});

		report.page.add_inner_button(__('➕ Create Bulk Bank Transaction'), function () {
			open_bulk_bank_transaction(report);
		});

		// Set default dates
		let filters = report.get_filter_values();
		if (!filters.bank_statement_from_date) {
			let today = frappe.datetime.get_today();
			report.set_filter_value(
				'bank_statement_from_date',
				frappe.datetime.add_months(today, -1),
			);
		}
		if (!filters.bank_statement_to_date) {
			report.set_filter_value('bank_statement_to_date', frappe.datetime.get_today());
		}
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Format status column with colors
		// Keep original status names, only apply colors
		if (column.fieldname === 'reconciled_status') {
			if (value.includes('❌ Unmatched')) {
				// Unmatched voucher: Red color with X emoji
				value = '<span style="color: red; font-weight: bold;">' + value + '</span>';
			} else if (value.includes('✅ Reconciled')) {
				// Fully reconciled: Green color with checkmark and number
				value = '<span style="color: green; font-weight: bold;">' + value + '</span>';
			} else if (value.includes('Unreconciled')) {
				// Partially reconciled (has voucher but still Unreconciled): Orange color with number
				// Or Bank Transaction Unreconciled without voucher: Orange color with number
				value = '<span style="color: orange; font-weight: bold;">' + value + '</span>';
			} else if (value.includes('⏳')) {
				// Pending: Gray color
				value = '<span style="color: #666; font-weight: bold;">' + value + '</span>';
			}
		}

		// Format button columns (already HTML)
		if (['btn_reconcile', 'btn_create_pe', 'btn_create_je'].includes(column.fieldname)) {
			// Buttons are already HTML
			return value || '';
		}

		return value;
	},

	after_datatable_render: function (report) {
		// Setup event handlers for action buttons
		setup_action_buttons(report);
	},
};

function setup_action_buttons(report) {
	// Reconcile button handler
	$(document)
		.off('click', '.reconcile-btn')
		.on('click', '.reconcile-btn', function () {
			const $btn = $(this);
			const bt_name = $btn.data('bt');
			const voucher_name = $btn.data('voucher');
			const doctype = $btn.data('doctype');

			if (voucher_name && doctype) {
				// Reconcile specific voucher
				reconcile_voucher(bt_name, voucher_name, doctype);
			} else {
				// Open reconcile dialog
				open_reconcile_dialog(bt_name);
			}
		});

	// Create Payment Entry button handler
	$(document)
		.off('click', '.create-pe-btn')
		.on('click', '.create-pe-btn', function () {
			const $btn = $(this);
			const bt_name = $btn.data('bt');
			const reference_number = $btn.data('reference-number');
			const date = $btn.data('date');

			// Party type and party will be selected in dialog
			create_payment_entry(bt_name, null, null, reference_number, date);
		});

	// Create Journal Entry button handler
	$(document)
		.off('click', '.create-je-btn')
		.on('click', '.create-je-btn', function () {
			const $btn = $(this);
			const bt_name = $btn.data('bt');

			create_journal_entry(bt_name);
		});

	// Create Bank Transaction button
	$(document).on('click', '.create-bt-btn', function () {
		const $btn = $(this);
		const voucher_doc_type = $btn.data('doctype');
		const voucher_name = $btn.data('voucher');

		create_bank_transaction(voucher_doc_type, voucher_name);
	});
}

function reconcile_voucher(bt_name, voucher_name, doctype) {
	frappe.confirm(
		__('Reconcile Bank Transaction {0} with {1} {2}?', [bt_name, doctype, voucher_name]),
		function () {
			// Get voucher amount first
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: doctype,
					name: voucher_name,
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						const voucher = r.message;
						let amount = 0;

						if (doctype === 'Payment Entry') {
							amount = flt(
								voucher.base_paid_amount_after_tax || voucher.paid_amount,
							);
						} else if (doctype === 'Journal Entry') {
							// Get amount from journal entry accounts
							amount = 0;
							if (voucher.accounts) {
								voucher.accounts.forEach(function (account) {
									const bank_account = frappe.db.get_value(
										'Account',
										account.account,
										'account_type',
									);
									if (bank_account === 'Bank') {
										amount = Math.abs(
											flt(
												account.debit_in_account_currency -
													account.credit_in_account_currency,
											),
										);
									}
								});
							}
						}

						const vouchers = JSON.stringify([
							{
								payment_doctype: doctype,
								payment_name: voucher_name,
								amount: amount,
							},
						]);

						// Use ERPNext's reconcile_vouchers method
						frappe.call({
							method: 'erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.reconcile_vouchers',
							args: {
								bank_transaction_name: bt_name,
								vouchers: vouchers,
							},
							freeze: true,
							freeze_message: __('Reconciling...'),
							callback: function (r) {
								if (!r.exc) {
									frappe.show_alert({
										message: __('Reconciled successfully'),
										indicator: 'green',
									});
									frappe.query_report.refresh();
								}
							},
						});
					}
				},
			});
		},
	);
}

function open_reconcile_dialog(bt_name) {
	// Use ERPNext's dialog manager if available, or create custom dialog
	frappe.set_route('Form', 'Bank Reconciliation Tool');
	frappe.route_options = {
		bank_account: frappe.query_report.get_filter_value('bank_account'),
	};
}

function create_payment_entry(bt_name, party_type, party, reference_number, date) {
	// Get filters to access company
	const filters = frappe.query_report.get_filter_values();
	const company = filters.company || frappe.defaults.get_default('company');

	// Get Bank Transaction details for reference_number and dates if not provided
	if (!reference_number || !date) {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Bank Transaction',
				name: bt_name,
			},
			callback: function (r) {
				if (r.exc || !r.message) {
					frappe.msgprint(__('Error loading Bank Transaction'));
					return;
				}

				const bt = r.message;
				show_payment_entry_dialog(
					bt_name,
					bt.reference_number || null,
					bt.date || null,
					company,
				);
			},
		});
	} else {
		show_payment_entry_dialog(bt_name, reference_number, date, company);
	}
}

function show_payment_entry_dialog(bt_name, reference_number, date, company) {
	// Create dialog for selecting party_type and party
	const dialog = new frappe.ui.Dialog({
		title: __('Create Payment Entry'),
		fields: [
			{
				fieldtype: 'Link',
				fieldname: 'party_type',
				label: __('Party Type'),
				options: 'DocType',
				reqd: 1,
				get_query: () => ({
					filters: {
						name: ['in', Object.keys(frappe.boot.party_account_types || {})],
					},
				}),
			},
			{
				fieldtype: 'Dynamic Link',
				fieldname: 'party',
				label: __('Party'),
				options: 'party_type',
				reqd: 1,
			},
		],
		primary_action_label: __('Create'),
		primary_action: function (values) {
			dialog.hide();

			const args = {
				bank_transaction_name: bt_name,
				party_type: values.party_type,
				party: values.party,
			};

			// Add reference_number and reference_date if available
			if (reference_number) {
				args.reference_number = reference_number;
			}
			if (date) {
				args.reference_date = date;
				args.posting_date = date;
			}

			frappe.call({
				method: 'erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.create_payment_entry_bts',
				args: args,
				freeze: true,
				freeze_message: __('Creating Payment Entry...'),
				callback: function (r) {
					if (!r.exc && r.message) {
						// Payment Entry is already added to Bank Transaction by create_payment_entry_bts
						// Just refresh the report
						frappe.show_alert({
							message: __('Payment Entry created and linked to Bank Transaction'),
							indicator: 'green',
						});
						frappe.query_report.refresh();
					}
				},
			});
		},
	});
	dialog.show();
}

function create_journal_entry(bt_name) {
	// Get filters to access company
	const filters = frappe.query_report.get_filter_values();
	const company = filters.company || frappe.defaults.get_default('company');

	// Get Bank Transaction details for reference_number and dates
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Bank Transaction',
			name: bt_name,
		},
		callback: function (r) {
			if (r.exc || !r.message) {
				frappe.msgprint(__('Error loading Bank Transaction'));
				return;
			}

			const bt = r.message;

			// Create dialog for selecting bank expense account
			const dialog = new frappe.ui.Dialog({
				title: __('Create Journal Entry'),
				fields: [
					{
						fieldtype: 'Link',
						fieldname: 'second_account',
						label: __('Bank Expense Account'),
						options: 'Account',
						reqd: 1,
						get_query: () => ({
							filters: {
								is_group: 0,
								company: company,
							},
						}),
					},
					{
						fieldtype: 'Select',
						fieldname: 'entry_type',
						label: __('Journal Entry Type'),
						options: 'Bank Entry\nJournal Entry',
						default: 'Bank Entry',
					},
				],
				primary_action_label: __('Create'),
				primary_action: function (values) {
					dialog.hide();

					const args = {
						bank_transaction_name: bt_name,
						second_account: values.second_account,
						entry_type: values.entry_type || 'Bank Entry',
						reference_number: bt.reference_number || null,
						reference_date: bt.date || null,
						posting_date: bt.date || null,
					};

					frappe.call({
						method: 'erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.create_journal_entry_bts',
						args: args,
						freeze: true,
						freeze_message: __('Creating Journal Entry...'),
						callback: function (r) {
							if (!r.exc && r.message) {
								// Journal Entry is already added to Bank Transaction by create_journal_entry_bts
								// Just refresh the report
								frappe.show_alert({
									message: __(
										'Journal Entry created and linked to Bank Transaction',
									),
									indicator: 'green',
								});
								frappe.query_report.refresh();
							}
						},
					});
				},
			});
			dialog.show();
		},
	});
}

function create_bank_transaction(voucher_doc_type, voucher_name) {
	frappe.call({
		method: 'bank_management.bank_management.report.bank_reconcile_report.bank_reconcile_report.create_bank_transaction_from_voucher',
		args: {
			voucher_doc_type: voucher_doc_type,
			voucher_name: voucher_name,
		},
		freeze: true,
		freeze_message: __('Creating Bank Transaction...'),
		callback: function (r) {
			if (!r.exc && r.message) {
				frappe.show_alert({
					message: __('Bank Transaction created and linked to voucher'),
					indicator: 'green',
				});
				frappe.query_report.refresh();
			}
		},
	});
}

function open_general_ledger(report) {
	const filters = report.get_filter_values();

	if (!filters.bank_account) {
		frappe.msgprint(__('Please select Bank Account first'));
		return;
	}

	// Get GL Account from Bank Account
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Bank Account',
			name: filters.bank_account,
		},
		callback: function (r) {
			if (!r.exc && r.message) {
				const bank_account = r.message;
				const gl_account = bank_account.account;

				if (!gl_account) {
					frappe.msgprint(
						__('Bank Account {0} does not have a GL Account configured').format(
							filters.bank_account,
						),
					);
					return;
				}

				// Build route options
				const route_options = {
					company: filters.company || '',
					from_date: filters.bank_statement_from_date || filters.from_date || '',
					to_date: filters.bank_statement_to_date || filters.to_date || '',
					account: JSON.stringify([gl_account]),
					categorize_by: 'Categorize by Voucher (Consolidated)',
					include_dimensions: 1,
					include_default_book_entries: 1,
				};

				// Set route options and navigate
				frappe.set_route('query-report', 'General Ledger', route_options);
			}
		},
	});
}

function open_bulk_bank_transaction(report) {
	const filters = report.get_filter_values();

	// Open new Bulk Bank Transaction form with bank_account pre-filled
	frappe.set_route('Form', 'Bulk Bank Transaction', 'new');

	// Set bank_account after form loads
	frappe.route_options = {
		bank_account: filters.bank_account || '',
		company: filters.company || '',
	};
}

function add_filter_separator() {
	// Add separator after first 5 filters (first row)
	const filter_wrapper = $('.filter-section .filter-container');
	if (filter_wrapper.length) {
		const filter_items = filter_wrapper.find('.form-group');
		if (filter_items.length >= 5) {
			// Find the 5th filter (created_by)
			const fifth_filter = filter_items.eq(4);
			if (fifth_filter.length && !fifth_filter.next().hasClass('filter-separator')) {
				const separator = $(
					'<div class="filter-separator" style="width: 100%; height: 1px; background: #d1d8dd; margin: 15px 0; clear: both;"></div>',
				);
				fifth_filter.after(separator);
			}
		}
	}
}

function bulk_reconcile_selected(report) {
	const data = report.data;
	const checked_rows = [];

	// Get checked rows from datatable
	if (report.datatable && report.datatable.dt) {
		const checked_indexes = report.datatable.dt.getCheckedRows();
		checked_indexes.forEach((idx) => {
			if (data[idx]) {
				checked_rows.push(data[idx]);
			}
		});
	}

	if (checked_rows.length === 0) {
		frappe.msgprint(__('Please select at least one row'));
		return;
	}

	const bank_transactions = [...new Set(checked_rows.map((row) => row.bt_name).filter(Boolean))];
	const vouchers = [];

	checked_rows.forEach((row) => {
		if (row.voucher_name && row.voucher_doc_type) {
			vouchers.push({
				document_type: row.voucher_doc_type,
				payment_entry: row.voucher_name,
				paid_amount: row.voucher_amount || 0,
			});
		}
	});

	if (bank_transactions.length === 0) {
		frappe.msgprint(__('Please select at least one Bank Transaction'));
		return;
	}

	if (vouchers.length === 0) {
		frappe.msgprint(__('Please select rows with vouchers'));
		return;
	}

	frappe.confirm(
		__('Reconcile {0} bank transaction(s) with {1} voucher(s)?', [
			bank_transactions.length,
			vouchers.length,
		]),
		function () {
			frappe.call({
				method: 'bank_management.bank_management.doctype.bank_reconcile.bank_reconcile.reconcile_selected',
				args: {
					bank_transactions: bank_transactions,
					vouchers: vouchers,
				},
				freeze: true,
				freeze_message: __('Reconciling...'),
				callback: function (r) {
					if (!r.exc) {
						frappe.show_alert({
							message: __('Reconciled {0} transactions', [
								r.message.reconciled_count || 0,
							]),
							indicator: 'green',
						});
						frappe.query_report.refresh();
					}
				},
			});
		},
	);
}
