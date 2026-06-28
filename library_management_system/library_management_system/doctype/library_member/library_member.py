import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class LibraryMember(Document):
	def validate(self):
		if getdate(self.membership_end_date) < getdate(self.membership_start_date):
			frappe.throw("Membership End Date cannot be before Start Date.")

		self.membership_status = (
			"Expired" if getdate(self.membership_end_date) < getdate(today()) else "Active"
		)

	def after_insert(self):
		if self.customer:
			return
		ensure_customer(self)

	def update_outstanding(self):
		unpaid = frappe.db.sql(
			"""SELECT COALESCE(SUM(amount), 0) FROM `tabFine`
			   WHERE member = %s AND status = 'Unpaid' AND docstatus = 1""",
			(self.name,),
		)[0][0]
		self.db_set("outstanding_fine", flt(unpaid))


def ensure_customer(member):
	if member.customer and frappe.db.exists("Customer", member.customer):
		return member.customer

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": member.member_name,
			"customer_type": "Individual",
			"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
			or "Individual",
			"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name")
			or "All Territories",
		}
	).insert(ignore_permissions=True)

	member.db_set("customer", customer.name)
	return customer.name


def expire_memberships():
	frappe.db.sql(
		"""
		UPDATE `tabLibrary Member`
		SET membership_status = 'Expired'
		WHERE membership_end_date < %s AND membership_status != 'Expired'
		""",
		(today(),),
	)
