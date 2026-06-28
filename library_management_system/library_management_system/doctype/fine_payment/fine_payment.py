import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FinePayment(Document):
	def validate(self):
		fine = frappe.get_doc("Fine", self.fine)
		if fine.docstatus != 1:
			frappe.throw("Linked Fine must be submitted.")
		if fine.status != "Unpaid":
			frappe.throw(f"Fine is {fine.status}; cannot accept payment.")
		if fine.member != self.member:
			frappe.throw("Fine does not belong to the selected member.")
		if flt(self.amount) != flt(fine.amount):
			frappe.throw(
				f"Partial payments are not supported. Amount must equal {fine.amount}."
			)

	def on_submit(self):
		self._post_je()
		fine = frappe.get_doc("Fine", self.fine)
		fine.db_set("status", "Paid")
		_refresh_member_outstanding(self.member)

	def on_cancel(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.flags.ignore_links = True
				je.cancel()
		fine = frappe.get_doc("Fine", self.fine)
		if fine.docstatus == 1 and fine.status == "Paid":
			fine.db_set("status", "Unpaid")
		_refresh_member_outstanding(self.member)

	def _post_je(self):
		settings = frappe.get_single("Library Settings")
		_require_payment_accounts(settings)

		member = frappe.get_doc("Library Member", self.member)

		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"posting_date": self.payment_date,
				"company": settings.company,
				"user_remark": f"Library fine payment from {member.member_name} ({self.name})",
				"accounts": [
					{
						"account": settings.default_cash_account,
						"debit_in_account_currency": flt(self.amount),
						"credit_in_account_currency": 0,
					},
					{
						"account": settings.default_receivable_account,
						"party_type": "Customer",
						"party": member.customer,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": flt(self.amount),
					},
				],
			}
		).insert(ignore_permissions=True)
		je.submit()
		self.db_set("journal_entry", je.name)


def _require_payment_accounts(settings):
	missing = [
		f
		for f in (
			"company",
			"default_receivable_account",
			"default_cash_account",
		)
		if not settings.get(f)
	]
	if missing:
		frappe.throw(
			"Library Settings is missing required accounts: " + ", ".join(missing)
		)


def _refresh_member_outstanding(member_name):
	member = frappe.get_doc("Library Member", member_name)
	member.update_outstanding()
