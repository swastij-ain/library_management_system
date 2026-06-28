import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Fine(Document):
	def validate(self):
		if self.overdue_days < 0:
			frappe.throw("Overdue Days cannot be negative.")
		self.amount = flt(self.overdue_days) * flt(self.rate_per_day)

		if not self.status:
			self.status = "Unpaid"

	def before_submit(self):
		member = frappe.get_doc("Library Member", self.member)
		if not member.customer:
			from library_management_system.library_management_system.doctype.library_member.library_member import (
				ensure_customer,
			)
			ensure_customer(member)
			member.reload()
		if not member.customer:
			frappe.throw(
				"Member has no linked ERPNext Customer. Cannot post fine to accounts."
			)

	def on_submit(self):
		self._post_je()
		_refresh_member_outstanding(self.member)

	def on_cancel(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.flags.ignore_links = True
				je.cancel()
		_refresh_member_outstanding(self.member)

	def _post_je(self):
		settings = frappe.get_single("Library Settings")
		_require_accounts(settings)

		member = frappe.get_doc("Library Member", self.member)

		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"posting_date": self.fine_date,
				"company": settings.company,
				"user_remark": f"Library fine for {member.member_name} ({self.name})",
				"accounts": [
					{
						"account": settings.default_receivable_account,
						"party_type": "Customer",
						"party": member.customer,
						"debit_in_account_currency": flt(self.amount),
						"credit_in_account_currency": 0,
					},
					{
						"account": settings.default_income_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": flt(self.amount),
					},
				],
			}
		).insert(ignore_permissions=True)
		je.submit()
		self.db_set("journal_entry", je.name)


@frappe.whitelist()
def waive(name, reason):
	doc = frappe.get_doc("Fine", name)
	if doc.docstatus != 1:
		frappe.throw("Only submitted Fines can be waived.")
	if doc.status != "Unpaid":
		frappe.throw(f"Cannot waive a Fine with status {doc.status}.")
	if not reason:
		frappe.throw("Waiver reason is required.")

	if doc.journal_entry:
		je = frappe.get_doc("Journal Entry", doc.journal_entry)
		if je.docstatus == 1:
			je.flags.ignore_links = True
			je.cancel()

	doc.db_set("status", "Waived")
	doc.db_set("waiver_reason", reason)
	_refresh_member_outstanding(doc.member)
	return doc.name


def _require_accounts(settings):
	missing = [
		f
		for f in (
			"company",
			"default_receivable_account",
			"default_income_account",
		)
		if not settings.get(f)
	]
	if missing:
		frappe.throw(
			"Library Settings is missing required accounts: "
			+ ", ".join(missing)
			+ ". Please configure Library Settings before posting fines."
		)


def _refresh_member_outstanding(member_name):
	member = frappe.get_doc("Library Member", member_name)
	member.update_outstanding()
