import frappe
from frappe.model.document import Document


class Book(Document):
	def validate(self):
		if self.total_copies < 0:
			frappe.throw("Total Copies cannot be negative.")

		if self.is_new() and (self.available_copies is None or self.available_copies == 0):
			self.available_copies = self.total_copies

		if self.available_copies > self.total_copies:
			self.available_copies = self.total_copies

		if self.available_copies < 0:
			self.available_copies = 0

		self.status = "Available" if self.available_copies > 0 else "Out of Stock"
