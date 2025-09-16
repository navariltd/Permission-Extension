frappe.treeview_settings["Account"].on_get_node = function (nodes, deep = false) {
	if (frappe.boot.user.can_read.indexOf("GL Entry") === -1) return;

	frappe.call({
		method: "permission_extension.permission_extension.controllers.account.get_allowed_accounts_for_coa",
		args: { company: cur_tree.args.company },
		callback: function (r) {
			let accounts = r.message || [];

			frappe.db
				.get_single_value("Accounts Settings", "show_balance_in_coa")
				.then((value) => {
					if (!value) return;

					frappe.call({
						method: "erpnext.accounts.utils.get_account_balances",
						args: {
							accounts: accounts,
							company: cur_tree.args.company,
						},
						callback: function (res) {
							const balances = res.message || [];

							for (let account of balances) {
								const node = cur_tree.nodes && cur_tree.nodes[account.value];
								if (!node || node.is_root) continue;

								const balance =
									account.balance_in_account_currency || account.balance;
								const dr_or_cr = balance > 0 ? "Dr" : "Cr";
								const format = (value, currency) =>
									format_currency(Math.abs(value), currency);

								if (account.balance !== undefined) {
									node.parent && node.parent.find(".balance-area").remove();
									$(
										'<span class="balance-area pull-right">' +
											(account.balance_in_account_currency
												? format(
														account.balance_in_account_currency,
														account.account_currency
												  ) + " / "
												: "") +
											format(account.balance, account.company_currency) +
											" " +
											dr_or_cr +
											"</span>"
									).insertBefore(node.$ul);
								}
							}
						},
					});
				});
		},
	});
};
