frappe.ui.form.on("Book Issue", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status !== "Returned") {
			frm.add_custom_button(__("Return Book"), () => {
				frappe.call({
					method: "library_management_system.library_management_system.doctype.book_issue.book_issue.mark_returned",
					args: { name: frm.doc.name },
					freeze: true,
					freeze_message: __("Processing return..."),
					callback: () => {
						frappe.show_alert({ message: __("Book returned"), indicator: "green" });
						frm.reload_doc();
					},
				});
			}).addClass("btn-primary");
		}
	},
});
