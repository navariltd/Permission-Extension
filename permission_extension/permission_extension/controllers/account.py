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

	escaped = [g.replace("'", "''") for g in allowed]
	quoted = ", ".join(f"'{g}'" for g in escaped)

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
