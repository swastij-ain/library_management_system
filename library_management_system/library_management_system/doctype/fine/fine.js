frappe.ui.form.on("Fine", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Unpaid") {
			frm.add_custom_button(__("Waive"), () => {
				frappe.prompt(
					{
						fieldname: "reason",
						label: __("Reason"),
						fieldtype: "Small Text",
						reqd: 1,
					},
					(values) => {
						frappe.call({
							method: "library_management_system.library_management_system.doctype.fine.fine.waive",
							args: { name: frm.doc.name, reason: values.reason },
							freeze: true,
							callback: () => {
								frappe.show_alert({ message: __("Fine waived"), indicator: "orange" });
								frm.reload_doc();
							},
						});
					},
					__("Waive Fine"),
					__("Confirm")
				);
			});

			frm.add_custom_button(__("Record Payment"), () => {
				frappe.new_doc("Fine Payment", { fine: frm.doc.name, member: frm.doc.member });
			}).addClass("btn-primary");
		}
	},
});
