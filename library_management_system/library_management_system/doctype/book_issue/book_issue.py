import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today


class BookIssue(Document):
	def validate(self):
		member = frappe.get_doc("Library Member", self.member)
		if member.membership_status == "Expired":
			frappe.throw(f"Membership for {member.member_name} has expired.")

		if not self.due_date:
			loan_period = (
				frappe.db.get_single_value("Library Settings", "default_loan_period_days") or 14
			)
			self.due_date = add_days(self.issue_date, int(loan_period))

		if getdate(self.due_date) < getdate(self.issue_date):
			frappe.throw("Due Date cannot be before Issue Date.")

	def on_submit(self):
		book = frappe.get_doc("Book", self.book)
		if book.available_copies <= 0:
			frappe.throw(f"No copies of '{book.title}' are available for issue.")

		book.available_copies -= 1
		book.save(ignore_permissions=True)

		self.db_set("status", "Issued")

	def on_cancel(self):
		if self.status in ("Issued", "Overdue"):
			book = frappe.get_doc("Book", self.book)
			book.available_copies += 1
			book.save(ignore_permissions=True)


@frappe.whitelist()
def mark_returned(name):
	doc = frappe.get_doc("Book Issue", name)
	if doc.docstatus != 1:
		frappe.throw("Only submitted Book Issues can be returned.")
	if doc.status == "Returned":
		frappe.throw("This Book Issue has already been returned.")

	doc.db_set("return_date", today())
	doc.db_set("status", "Returned")

	book = frappe.get_doc("Book", doc.book)
	book.available_copies += 1
	book.save(ignore_permissions=True)

	_raise_fine_if_overdue(doc)

	return doc.name


def _raise_fine_if_overdue(book_issue):
	from frappe.utils import date_diff

	overdue_days = date_diff(today(), book_issue.due_date)
	if overdue_days <= 0:
		return

	rate = frappe.db.get_single_value("Library Settings", "fine_per_day") or 0
	if not rate:
		return

	try:
		fine = frappe.get_doc(
			{
				"doctype": "Fine",
				"member": book_issue.member,
				"book_issue": book_issue.name,
				"fine_date": today(),
				"overdue_days": overdue_days,
				"rate_per_day": rate,
			}
		).insert(ignore_permissions=True)
		fine.submit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Library: auto-fine creation failed")
		frappe.msgprint(
			"Book returned, but automatic fine creation failed. Check Library Settings.",
			alert=True,
			indicator="orange",
		)


def mark_overdue():
	frappe.db.sql(
		"""
		UPDATE `tabBook Issue`
		SET status = 'Overdue'
		WHERE docstatus = 1 AND status = 'Issued' AND due_date < %s
		""",
		(today(),),
	)
