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

ROLE_WORKSPACES = {
    "Trade - Sales Executive":    ["Pipeline", "Sales"],
    "Trade - Purchase Executive": ["Purchasing"],
    "Trade - Warehouse Staff":    ["Warehouse"],
    "Trade - Accountant":         ["Finance", "Asset Register"],
    "Trade - Manager":            TRADE_WORKSPACES,
}

# Sidebar items for each trade workspace
# Each entry: (label, link_type, link_to) — "Section Break" rows have no link_type/link_to
SIDEBAR_ITEMS = {
    "Pipeline": [
        ("Overview",    "Section Break", None),
        ("Dashboard",   "Dashboard",     "CRM"),
        ("CRM",         "Section Break", None),
        ("Lead",        "DocType",       "Lead"),
        ("Opportunity", "DocType",       "Opportunity"),
        ("Masters",     "Section Break", None),
        ("Customer",    "DocType",       "Customer"),
        ("Contact",     "DocType",       "Contact"),
    ],
    "Sales": [
        ("Overview",     "Section Break", None),
        ("Dashboard",    "Dashboard",     "Selling"),
        ("Orders",       "Section Break", None),
        ("Quotation",    "DocType",       "Quotation"),
        ("Sales Order",  "DocType",       "Sales Order"),
        ("Delivery Note","DocType",       "Delivery Note"),
        ("Sales Invoice","DocType",       "Sales Invoice"),
        ("Catalogue",    "Section Break", None),
        ("Item",         "DocType",       "Item"),
        ("Customer",     "DocType",       "Customer"),
    ],
    "Purchasing": [
        ("Overview",        "Section Break", None),
        ("Dashboard",       "Dashboard",     "Buying"),
        ("Orders",          "Section Break", None),
        ("Purchase Order",  "DocType",       "Purchase Order"),
        ("Purchase Receipt","DocType",       "Purchase Receipt"),
        ("Purchase Invoice","DocType",       "Purchase Invoice"),
        ("Masters",         "Section Break", None),
        ("Supplier",        "DocType",       "Supplier"),
        ("Item",            "DocType",       "Item"),
    ],
    "Warehouse": [
        ("Overview",        "Section Break", None),
        ("Dashboard",       "Dashboard",     "Stock"),
        ("Transactions",    "Section Break", None),
        ("Purchase Receipt","DocType",       "Purchase Receipt"),
        ("Delivery Note",   "DocType",       "Delivery Note"),
        ("Stock Entry",     "DocType",       "Stock Entry"),
        ("Masters",         "Section Break", None),
        ("Item",            "DocType",       "Item"),
        ("Warehouse",       "DocType",       "Warehouse"),
    ],
    "Finance": [
        ("Overview",                              "Section Break", None),
        ("Dashboard",                             "Dashboard",     "Accounts"),
        ("Invoices",                              "Section Break", None),
        ("Sales Invoice",                         "DocType",       "Sales Invoice"),
        ("Purchase Invoice",                      "DocType",       "Purchase Invoice"),
        ("Payments",                              "Section Break", None),
        ("Payment Entry",                         "DocType",       "Payment Entry"),
        ("Banking",                               "Section Break", None),
        ("Bank Account",                          "DocType",       "Bank Account"),
        ("Financial Statements",                  "Section Break", None),
        ("General Ledger",                        "Report",        "General Ledger"),
        ("Trial Balance",                         "Report",        "Trial Balance"),
        ("Profit and Loss Statement",             "Report",        "Profit and Loss Statement"),
        ("Balance Sheet",                         "Report",        "Balance Sheet"),
        ("Cash Flow",                             "Report",        "Cash Flow"),
        ("Receivables",                           "Section Break", None),
        ("Accounts Receivable",                   "Report",        "Accounts Receivable"),
        ("Accounts Receivable Summary",           "Report",        "Accounts Receivable Summary"),
        ("Customer Ledger Summary",               "Report",        "Customer Ledger Summary"),
        ("Payables",                              "Section Break", None),
        ("Accounts Payable",                      "Report",        "Accounts Payable"),
        ("Accounts Payable Summary",              "Report",        "Accounts Payable Summary"),
        ("Supplier Ledger Summary",               "Report",        "Supplier Ledger Summary"),
        ("Analysis",                              "Section Break", None),
        ("Gross Profit",                          "Report",        "Gross Profit"),
        ("Sales Invoice Trends",                  "Report",        "Sales Invoice Trends"),
        ("Purchase Invoice Trends",               "Report",        "Purchase Invoice Trends"),
        ("Payment Period Based On Invoice Date",  "Report",        "Payment Period Based On Invoice Date"),
        ("Bank Reconciliation Statement",         "Report",        "Bank Reconciliation Statement"),
    ],
    "Asset Register": [
        ("Overview",        "Section Break", None),
        ("Dashboard",       "Dashboard",     "Asset"),
        ("Assets",          "Section Break", None),
        ("Asset",           "DocType",       "Asset"),
        ("Asset Category",  "DocType",       "Asset Category"),
        ("Asset Movement",  "DocType",       "Asset Movement"),
    ],
}

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
        ("Warehouse",      1, 0, 0, 0, 0, 0, 0),
        ("Contact",        1, 1, 1, 0, 0, 0, 0),
        ("Address",        1, 1, 1, 0, 0, 0, 0),
        ("Workflow",       1, 0, 0, 0, 0, 0, 0),
        ("Workflow State", 1, 0, 0, 0, 0, 0, 0),
    ],
    "Trade - Purchase Executive": [
        ("Purchase Order",   1, 1, 1, 0, 1, 1, 1),
        ("Purchase Invoice", 1, 0, 0, 0, 0, 0, 0),
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0),
        ("Purchase Receipt", 1, 0, 0, 0, 0, 0, 0),
        ("Supplier",         1, 1, 1, 0, 0, 0, 0),
        ("Customer",         1, 0, 0, 0, 0, 0, 0),
        ("Item",             1, 0, 0, 0, 0, 0, 0),
        ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
        ("Contact",          1, 1, 1, 0, 0, 0, 0),
        ("Address",          1, 1, 1, 0, 0, 0, 0),
        ("Workflow",         1, 0, 0, 0, 0, 0, 0),
        ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
    ],
    "Trade - Warehouse Staff": [
        ("Purchase Receipt", 1, 1, 1, 0, 1, 1, 1),
        ("Delivery Note",    1, 1, 1, 0, 1, 1, 1),
        ("Stock Entry",      1, 1, 1, 0, 1, 1, 1),
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0),
        ("Purchase Order",   1, 0, 0, 0, 0, 0, 0),
        ("Item",             1, 0, 0, 0, 0, 0, 0),
        ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
        ("Customer",         1, 0, 0, 0, 0, 0, 0),
        ("Supplier",         1, 0, 0, 0, 0, 0, 0),
        ("Contact",          1, 0, 0, 0, 0, 0, 0),
        ("Address",          1, 0, 0, 0, 0, 0, 0),
        ("Workflow",         1, 0, 0, 0, 0, 0, 0),
        ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
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
        ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
        ("Bank Account",     1, 0, 0, 0, 0, 0, 0),
        ("Asset",            1, 1, 1, 0, 1, 1, 1),
        ("Asset Category",   1, 0, 0, 0, 0, 0, 0),
        ("Asset Movement",   1, 1, 1, 0, 1, 1, 1),
        ("Workflow",         1, 0, 0, 0, 0, 0, 0),
        ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
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
        ("Workflow",         1, 0, 0, 0, 0, 0, 0),
        ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
    ],
}

# Reference/master DocTypes that every Trade role must be able to READ.
# These appear as link fields inside forms the roles can edit, but their
# default DocType permissions only list built-in ERPNext roles — not ours.
TRADE_READ_REFS = [
    # Core masters used as link targets in every transactional form
    "Territory",
    "Customer Group",
    "Supplier Group",
    "Item Group",
    "Price List",
    "Currency",
    "UOM",
    "Payment Terms Template",
    "Tax Category",
    "Sales Taxes and Charges Template",
    "Purchase Taxes and Charges Template",
    "Shipping Rule",
    "Terms and Conditions",
    "Incoterm",
    "Cost Center",
    "Account",
    "Letter Head",
    "Stock Entry Type",
    "Lead Source",
    # Item / stock references (appear in item line child tables)
    "Item Tax Template",
    "Batch",
    "Serial and Batch Bundle",
    "Manufacturer",
    "Product Bundle",
    "Material Request",
    "Putaway Rule",
    "Blanket Order",
    "Supplier Quotation",
    # CRM / contact references
    "Salutation",
    "Gender",
    "Country",
    "Industry Type",
    "Market Segment",
    "Opportunity Type",
    "Sales Stage",
    # Accounting / finance references
    "Mode of Payment",
    "Journal Entry",
    "Payment Term",
    "Payment Request",
    "Finance Book",
    "Tax Withholding Category",
    # Misc form fields
    "Project",
    "Location",
    # Company and Fiscal Year — appear on every transactional DocType and report filter
    "Company",
    "Fiscal Year",
    # Misc form-level fields
    "Print Heading",
    "Language",
    "Journal Entry Template",
    "Party Type",
    "Party Account",
    # Banking — appear when opening Bank Account records
    "Bank",
    "Bank Account Type",
    "Bank Account Subtype",
    "Bank Transaction",
    # Accounting ledger — ref_doctype for General Ledger, Trial Balance,
    # P&L, Balance Sheet, Cash Flow reports; needs report=1 to pass
    # frappe.has_permission(ref_doctype, "report") check in query_report.py
    "GL Entry",
    "Payment Ledger Entry",
]

# Reports that Trade - Accountant and Trade - Manager must be able to run.
# ERPNext restricts these to Accounts User / Accounts Manager by default.
FINANCE_REPORTS = [
    "General Ledger",
    "Trial Balance",
    "Profit and Loss Statement",
    "Balance Sheet",
    "Cash Flow",
    "Accounts Receivable",
    "Accounts Receivable Summary",
    "Accounts Payable",
    "Accounts Payable Summary",
    "Customer Ledger Summary",
    "Supplier Ledger Summary",
    "Gross Profit",
    "Sales Invoice Trends",
    "Purchase Invoice Trends",
    "Payment Period Based On Invoice Date",
    "Bank Reconciliation Statement",
]

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
    # Fixtures must be synced before setup_permissions() because the Role
    # records (Trade - *) are defined in fixtures and are not yet in the DB
    # when after_install is called (Frappe runs sync_fixtures *after* after_install).
    # Set in_migrate so workspace validate_route_conflict is skipped.
    from frappe.utils.fixtures import sync_fixtures
    frappe.flags.in_migrate = True
    try:
        sync_fixtures("trade_mvp")
    finally:
        frappe.flags.in_migrate = False

    hide_default_workspaces()
    setup_permissions()
    setup_report_permissions()
    setup_module_profiles()
    setup_property_setters()
    setup_workspace_sidebars()
    frappe.db.commit()

    from frappe.desk.doctype.desktop_icon.desktop_icon import create_desktop_icons_from_workspace
    from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import create_workspace_sidebar_for_workspaces
    create_workspace_sidebar_for_workspaces()
    create_desktop_icons_from_workspace()
    # "Trade MVP" has no DocTypes so it never appears in user.allow_modules.
    # Clearing module on Workspace prevents the PermissionError in Workspace.__init__
    # (line 42-48 frappe/desk/desktop.py) that silently excludes trade workspaces.
    # Clearing module on Workspace Sidebar makes get_sidebar_items() include them
    # unconditionally (bypasses the allow_modules check there too).
    if TRADE_WORKSPACES:
        placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
        frappe.db.sql(
            f"UPDATE `tabWorkspace` SET module = '' WHERE name IN ({placeholders})",
            TRADE_WORKSPACES,
        )
        frappe.db.sql(
            f"UPDATE `tabWorkspace Sidebar` SET module = NULL WHERE title IN ({placeholders})",
            TRADE_WORKSPACES,
        )
    frappe.cache.flushall()


def hide_default_workspaces():
    placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
    frappe.db.sql(
        f"UPDATE `tabWorkspace` SET is_hidden = 1 WHERE name NOT IN ({placeholders}) AND name != 'Workspace'",
        TRADE_WORKSPACES,
    )


def setup_workspace_sidebars():
    for ws_name, items in SIDEBAR_ITEMS.items():
        if not frappe.db.exists("Workspace Sidebar", ws_name):
            continue
        doc = frappe.get_doc("Workspace Sidebar", ws_name)
        doc.set("items", [])
        for idx, (label, item_type, link_to) in enumerate(items, start=1):
            row = {"label": label, "idx": idx}
            if item_type == "Section Break":
                row["type"] = "Section Break"
                row["collapsible"] = 1
            else:
                row["type"] = "Link"
                row["link_type"] = item_type
                row["link_to"] = link_to
                row["child"] = 1
                row["indent"] = 1
            doc.append("items", row)
        doc.save(ignore_permissions=True)


def _upsert_perm(doctype, role, values):
    # Grant report access whenever read is granted so that
    # frappe.has_permission(ref_doctype, "report") passes in query_report.py
    if values.get("read"):
        values = {**values, "report": 1}
    existing = frappe.db.get_value(
        "Custom DocPerm",
        {"parent": doctype, "role": role, "permlevel": 0},
        "name",
    )
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


def setup_permissions():
    touched = set()

    for role, perms in TRADE_PERMISSIONS.items():
        for (doctype, read, write, create, delete, submit, cancel, amend) in perms:
            _upsert_perm(doctype, role, {
                "read": read, "write": write, "create": create,
                "delete": delete, "submit": submit, "cancel": cancel, "amend": amend,
            })
            touched.add(doctype)

    read_only = {"read": 1, "write": 0, "create": 0, "delete": 0, "submit": 0, "cancel": 0, "amend": 0}
    for doctype in TRADE_READ_REFS:
        for role in TRADE_ROLES:
            _upsert_perm(doctype, role, read_only)
        touched.add(doctype)

    for doctype in touched:
        frappe.clear_cache(doctype=doctype)


def setup_report_permissions():
    from frappe.utils import now
    finance_roles = ["Trade - Accountant", "Trade - Manager"]
    for report_name in FINANCE_REPORTS:
        if not frappe.db.exists("Report", report_name):
            continue
        for role in finance_roles:
            already = frappe.db.sql(
                "SELECT name FROM `tabHas Role` WHERE parent=%s AND parenttype='Report' AND role=%s",
                (report_name, role),
            )
            if not already:
                frappe.db.sql(
                    """INSERT INTO `tabHas Role`
                           (name, creation, modified, modified_by, owner, docstatus,
                            parent, parenttype, parentfield, role)
                       VALUES (%s, %s, %s, 'Administrator', 'Administrator', 0,
                               %s, 'Report', 'roles', %s)""",
                    (frappe.generate_hash(), now(), now(), report_name, role),
                )


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


def filter_bootinfo_for_trade_users(bootinfo):
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return

    user_trade_roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "role": ["in", TRADE_ROLES]},
        pluck="role",
    )
    if not user_trade_roles:
        return

    allowed = set()
    for role in user_trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))

    _filter_workspaces(bootinfo, allowed)
    _filter_desktop_icons(bootinfo, allowed)
    _filter_sidebar(bootinfo, allowed)
    _filter_app_data(bootinfo)


def _filter_workspaces(bootinfo, allowed):
    if not hasattr(bootinfo, "workspaces"):
        return
    pages = bootinfo.workspaces.get("pages", [])
    bootinfo.workspaces["pages"] = [
        p for p in pages if p.get("title") in allowed
    ]


def _filter_desktop_icons(bootinfo, allowed):
    if not hasattr(bootinfo, "desktop_icons"):
        return
    bootinfo.desktop_icons = [
        icon for icon in bootinfo.desktop_icons
        if icon.get("module_name") in allowed
        or icon.get("label") in allowed
    ]


def _filter_sidebar(bootinfo, allowed):
    if not hasattr(bootinfo, "workspace_sidebar_item"):
        return
    lower_allowed = {w.lower() for w in allowed}
    bootinfo.workspace_sidebar_item = {
        k: v for k, v in bootinfo.workspace_sidebar_item.items()
        if k.lower() in lower_allowed
    }


def _filter_app_data(bootinfo):
    if not hasattr(bootinfo, "app_data"):
        return
    bootinfo.app_data = [
        a for a in bootinfo.app_data if a.get("name") == "trade_mvp"
    ]


def check_credit_limit(doc, method=None):
    if not doc.customer:
        return

    credit_limit = frappe.db.get_value("Customer", doc.customer, "trade_credit_limit") or 0
    if not credit_limit:
        return  # 0 = unlimited

    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
    """, doc.customer)[0][0] or 0

    if float(outstanding) + float(doc.grand_total or 0) > float(credit_limit):
        frappe.throw(
            f"Customer {doc.customer} has exceeded their credit limit of "
            f"{frappe.format_value(credit_limit, {'fieldtype': 'Currency'})}. "
            f"Outstanding: {frappe.format_value(float(outstanding), {'fieldtype': 'Currency'})}."
        )
