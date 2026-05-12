import frappe

TRADE_ROLES = [
    "Trade - Sales Executive",
    "Trade - Purchase Executive",
    "Trade - Warehouse Staff",
    "Trade - Accountant",
    "Trade - Manager",
]

TRADE_WORKSPACES = [
    "Pipeline", "Sales", "Purchasing", "Warehouse", "Finance", "Asset Register"
]

# role -> list of (doctype, read, write, create, delete, submit, cancel, amend)
TRADE_PERMISSIONS = {
    "Trade - Sales Executive": [
        ("Lead",           1, 1, 1, 0, 0, 0, 0),
        ("Opportunity",    1, 1, 1, 0, 0, 0, 0),
        ("Quotation",      1, 1, 1, 0, 1, 1, 1),
        ("Sales Order",    1, 1, 1, 0, 1, 1, 1),
        ("Purchase Order", 1, 0, 0, 0, 0, 0, 0),
        ("Delivery Note",  1, 0, 0, 0, 0, 0, 0),
        ("Sales Invoice",  1, 0, 0, 0, 0, 0, 0),
        ("Customer",       1, 1, 1, 0, 0, 0, 0),
        ("Supplier",       1, 0, 0, 0, 0, 0, 0),
        ("Item",           1, 0, 0, 0, 0, 0, 0),
        ("Contact",        1, 1, 1, 0, 0, 0, 0),
        ("Address",        1, 1, 1, 0, 0, 0, 0),
    ],
    "Trade - Purchase Executive": [
        ("Purchase Order",   1, 1, 1, 0, 1, 1, 1),
        ("Purchase Invoice", 1, 0, 0, 0, 0, 0, 0),
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0),
        ("Purchase Receipt", 1, 0, 0, 0, 0, 0, 0),
        ("Supplier",         1, 1, 1, 0, 0, 0, 0),
        ("Customer",         1, 0, 0, 0, 0, 0, 0),
        ("Item",             1, 0, 0, 0, 0, 0, 0),
        ("Contact",          1, 1, 1, 0, 0, 0, 0),
        ("Address",          1, 1, 1, 0, 0, 0, 0),
    ],
    "Trade - Warehouse Staff": [
        ("Purchase Receipt", 1, 1, 1, 0, 1, 1, 1),
        ("Delivery Note",    1, 1, 1, 0, 1, 1, 1),
        ("Stock Entry",      1, 1, 1, 0, 1, 1, 1),
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0),
        ("Purchase Order",   1, 0, 0, 0, 0, 0, 0),
        ("Item",             1, 0, 0, 0, 0, 0, 0),
        ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
    ],
    "Trade - Accountant": [
        ("Sales Invoice",    1, 1, 1, 0, 1, 1, 1),
        ("Purchase Invoice", 1, 1, 1, 0, 1, 1, 1),
        ("Payment Entry",    1, 1, 1, 0, 1, 1, 1),
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0),
        ("Purchase Order",   1, 0, 0, 0, 0, 0, 0),
        ("Purchase Receipt", 1, 0, 0, 0, 0, 0, 0),
        ("Delivery Note",    1, 0, 0, 0, 0, 0, 0),
        ("Customer",         1, 0, 0, 0, 0, 0, 0),
        ("Supplier",         1, 0, 0, 0, 0, 0, 0),
        ("Item",             1, 0, 0, 0, 0, 0, 0),
        ("Bank Account",     1, 0, 0, 0, 0, 0, 0),
        ("Asset",            1, 1, 1, 0, 1, 1, 1),
        ("Asset Category",   1, 0, 0, 0, 0, 0, 0),
        ("Asset Movement",   1, 1, 1, 0, 1, 1, 1),
    ],
    "Trade - Manager": [
        ("Lead",             1, 1, 1, 1, 0, 0, 0),
        ("Opportunity",      1, 1, 1, 1, 0, 0, 0),
        ("Quotation",        1, 1, 1, 1, 1, 1, 1),
        ("Sales Order",      1, 1, 1, 1, 1, 1, 1),
        ("Purchase Order",   1, 1, 1, 1, 1, 1, 1),
        ("Purchase Receipt", 1, 1, 1, 1, 1, 1, 1),
        ("Delivery Note",    1, 1, 1, 1, 1, 1, 1),
        ("Sales Invoice",    1, 1, 1, 1, 1, 1, 1),
        ("Purchase Invoice", 1, 1, 1, 1, 1, 1, 1),
        ("Payment Entry",    1, 1, 1, 1, 1, 1, 1),
        ("Customer",         1, 1, 1, 1, 0, 0, 0),
        ("Supplier",         1, 1, 1, 1, 0, 0, 0),
        ("Item",             1, 1, 1, 1, 0, 0, 0),
        ("Contact",          1, 1, 1, 1, 0, 0, 0),
        ("Address",          1, 1, 1, 1, 0, 0, 0),
        ("Warehouse",        1, 1, 1, 1, 0, 0, 0),
        ("Bank Account",     1, 1, 1, 1, 0, 0, 0),
        ("Asset",            1, 1, 1, 1, 1, 1, 1),
        ("Asset Category",   1, 1, 1, 1, 0, 0, 0),
        ("Asset Movement",   1, 1, 1, 1, 1, 1, 1),
    ],
}

BLOCK_MODULES = [
    "Accounts", "Stock", "Selling", "Buying", "CRM",
    "Manufacturing", "Projects", "HR", "Payroll", "Assets",
    "Support", "Quality Management", "Subcontracting",
    "ERPNext Integrations", "Regional",
    "Build", "Integrations", "Website",
    "Core", "Email", "Automation", "Desk", "Custom",
    "Geo", "Printing", "Workflow",
]

HIDE_FIELDS = {
    "Customer": [
        "lead_name", "account_manager", "industry", "website",
        "market_segment", "language", "customer_details",
        "loyalty_program", "loyalty_program_tier",
        "default_sales_partner", "default_commission_rate", "sales_team",
    ],
    "Supplier": [
        "default_bank_account", "payment_terms", "represents_company",
        "is_transporter", "language", "website", "supplier_details",
        "warn_rfqs", "warn_pos", "prevent_rfqs", "prevent_pos",
    ],
    "Item": [
        "brand", "shelf_life_in_days", "end_of_life",
        "has_serial_no", "has_batch_no", "has_variants",
        "is_sub_contracted_item", "reorder_levels",
        "inspection_required_before_purchase",
        "inspection_required_before_delivery",
        "quality_inspection_template",
        "is_fixed_asset", "auto_create_assets",
    ],
    "Quotation": [
        "order_type", "language", "auto_repeat",
        "utm_source", "utm_campaign", "utm_medium", "utm_content",
        "referral_sales_partner",
    ],
    "Sales Order": [
        "utm_source", "utm_campaign", "utm_medium", "utm_content",
        "commission_rate", "total_commission", "sales_team",
        "auto_repeat", "skip_delivery_note",
        "is_internal_customer", "represents_company",
        "dispatch_address_name", "dispatch_address", "cost_center",
    ],
    "Purchase Order": [
        "buying_price_list", "price_list_currency", "supplier_warehouse",
        "auto_repeat", "is_subcontracted",
        "order_confirmation_no", "order_confirmation_date",
    ],
    "Delivery Note": [
        "lr_no", "lr_date", "vehicle_no", "driver_name",
        "transporter", "transporter_name", "instructions",
        "commission_rate", "sales_team", "is_internal_customer",
        "language", "letter_head",
    ],
    "Purchase Receipt": [
        "rejected_warehouse", "supplier_delivery_note",
        "is_subcontracted", "supplier_warehouse",
        "language", "letter_head",
    ],
    "Sales Invoice": [
        "project", "commission_rate", "total_commission",
        "loyalty_program", "sales_partner", "sales_team",
        "utm_source", "utm_campaign", "utm_medium", "utm_content",
        "language", "letter_head",
    ],
    "Purchase Invoice": [
        "project", "language", "letter_head",
        "is_subcontracted", "supplier_warehouse",
    ],
    "Payment Entry": [
        "project", "cost_center", "letter_head", "print_heading", "auto_repeat",
    ],
    "Asset": [
        "next_depreciation_date", "default_finance_book", "booked_fixed_asset",
    ],
}


def after_install():
    hide_default_workspaces()
    setup_permissions()
    setup_module_profiles()
    setup_property_setters()
    frappe.db.commit()


def hide_default_workspaces():
    frappe.db.sql("""
        UPDATE `tabWorkspace`
        SET is_hidden = 1
        WHERE (module != 'Trade MVP' OR module IS NULL OR module = '')
        AND name != 'Workspace'
    """)


def setup_permissions():
    for role, perms in TRADE_PERMISSIONS.items():
        for (doctype, read, write, create, delete, submit, cancel, amend) in perms:
            existing = frappe.db.get_value(
                "Custom DocPerm",
                {"parent": doctype, "role": role, "permlevel": 0},
                "name"
            )
            values = {
                "read": read, "write": write, "create": create,
                "delete": delete, "submit": submit, "cancel": cancel, "amend": amend
            }
            if existing:
                frappe.db.set_value("Custom DocPerm", existing, values)
            else:
                perm = frappe.new_doc("Custom DocPerm")
                perm.update({
                    "parent": doctype, "parenttype": "DocType",
                    "parentfield": "permissions", "role": role, "permlevel": 0,
                })
                perm.update(values)
                perm.insert(ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)


def setup_module_profiles():
    if frappe.db.exists("Module Profile", "Trade User"):
        return
    profile = frappe.new_doc("Module Profile")
    profile.module_profile_name = "Trade User"
    for module in BLOCK_MODULES:
        profile.append("block_modules", {"module": module})
    profile.insert(ignore_permissions=True)


def setup_property_setters():
    for doctype, fields in HIDE_FIELDS.items():
        for fieldname in fields:
            _safe_hide_field(doctype, fieldname)


def _safe_hide_field(doctype, fieldname):
    if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
        return
    existing = frappe.db.get_value(
        "Property Setter",
        {"doc_type": doctype, "field_name": fieldname, "property": "hidden"},
        "name"
    )
    if existing:
        frappe.db.set_value("Property Setter", existing, "value", "1")
    else:
        frappe.make_property_setter({
            "doctype": doctype,
            "doctype_or_field": "DocField",
            "fieldname": fieldname,
            "property": "hidden",
            "value": "1",
            "property_type": "Check",
        })
