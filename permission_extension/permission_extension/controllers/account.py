import frappe

from permission_extension.permission_extension.utils import get_permission_settings


def get_permission_query_conditions(user=None):
	"""The hook that Frappe calls to build the WHERE for Account lists/links."""
	settings = get_permission_settings()
	if not settings.get("account_permission"):
		return ""

	user = user or frappe.session.user
	if user == "Administrator":
		return ""

	return get_account_query_conditions(user)


def get_account_query_conditions(user):
	"""Builds the SQL fragment to filter Account.custom_user_group by User Permissions."""
	allowed = frappe.get_all(
		"User Permission", filters={"user": user, "allow": "User Group"}, pluck="for_value"
	)

	if not allowed:
		return ""

	escaped = [frappe.db.escape(g) for g in allowed]
	quoted = ", ".join(escaped)

	return f"""
	(
	  -- permitted leaves
	  `tabAccount`.custom_user_group IN ({quoted})
	  OR
	  -- any parent of a permitted leaf
	  EXISTS (
	    SELECT 1 FROM `tabAccount` AS child
	     WHERE child.lft > `tabAccount`.lft
	       AND child.rgt < `tabAccount`.rgt
	       AND child.custom_user_group IN ({quoted})
	  )
	)
	"""


@frappe.whitelist()
def get_allowed_accounts_for_coa(company):
	user = frappe.session.user
	all_accounts = frappe.get_all(
		"Account",
		filters={"company": company},
		fields=[
			"name",
			"account_name",
			"parent_account",
			"is_group",
			"custom_user_group",
			"account_currency",
			"account_number",
			"root_type",
			"company",
		],
		order_by="lft",
	)

	if user == "Administrator":
		# only leaf accounts
		allowed_accounts = all_accounts
	else:
		allowed_groups = frappe.get_all(
			"User Permission", filters={"user": user, "allow": "User Group"}, pluck="for_value"
		)

		if not allowed_groups:
			allowed_accounts = all_accounts

		else:
			allowed_set = set(allowed_groups)

			# only leaf accounts in allowed groups
			allowed_accounts = [
				acc
				for acc in all_accounts
				if not acc.get("is_group") and acc.get("custom_user_group") in allowed_set
			]

	# Wrap each account dict to include `value` for get_account_balances
	wrapped_accounts = []
	for acc in allowed_accounts:
		wrapped_accounts.append(
			{
				"value": acc["name"],
				"account_currency": acc.get("account_currency"),
				"company": acc.get("company"),
				"root_type": acc.get("root_type"),
				"is_group": acc.get("is_group"),
			}
		)

	return wrapped_accounts
