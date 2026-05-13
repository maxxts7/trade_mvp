import logging as _logging

import frappe


def _log():
    """Return a named logger that always writes at DEBUG level regardless of
    Frappe's global log_level setting (which defaults to ERROR in production).

    Log destinations (both written simultaneously):
      bench-level : {bench}/logs/trade_mvp.log
      site-level  : {bench}/sites/{site}/logs/trade_mvp.log

    On Frappe Cloud both files appear under:
      Site dashboard → Logs → trade_mvp.log
    """
    log = frappe.logger("trade_mvp", allow_site=True, file_count=20)
    log.setLevel(_logging.DEBUG)
    return log

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
    log = _log()
    log.info("after_install: START")

    from frappe.utils.fixtures import sync_fixtures
    frappe.flags.in_migrate = True
    try:
        sync_fixtures("trade_mvp")
        log.info("after_install: sync_fixtures OK")
    except Exception:
        log.exception("after_install: sync_fixtures FAILED")
        raise
    finally:
        frappe.flags.in_migrate = False

    try:
        n = hide_default_workspaces()
        log.info(f"after_install: hide_default_workspaces OK — {n} rows hidden")
    except Exception:
        log.exception("after_install: hide_default_workspaces FAILED")
        raise

    try:
        setup_permissions()
        log.info("after_install: setup_permissions OK")
    except Exception:
        log.exception("after_install: setup_permissions FAILED")
        raise

    try:
        setup_report_permissions()
        log.info("after_install: setup_report_permissions OK")
    except Exception:
        log.exception("after_install: setup_report_permissions FAILED")
        raise

    try:
        setup_module_profiles()
        log.info("after_install: setup_module_profiles OK")
    except Exception:
        log.exception("after_install: setup_module_profiles FAILED")
        raise

    try:
        setup_property_setters()
        log.info("after_install: setup_property_setters OK")
    except Exception:
        log.exception("after_install: setup_property_setters FAILED")
        raise

    try:
        setup_workspace_sidebars()
        log.info("after_install: setup_workspace_sidebars OK")
    except Exception:
        log.exception("after_install: setup_workspace_sidebars FAILED")
        raise

    frappe.db.commit()
    log.info("after_install: db.commit OK")

    from frappe.desk.doctype.desktop_icon.desktop_icon import create_desktop_icons_from_workspace
    from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import create_workspace_sidebar_for_workspaces

    try:
        create_workspace_sidebar_for_workspaces()
        log.info("after_install: create_workspace_sidebar_for_workspaces OK")
    except Exception:
        log.exception("after_install: create_workspace_sidebar_for_workspaces FAILED")
        raise

    try:
        create_desktop_icons_from_workspace()
        log.info("after_install: create_desktop_icons_from_workspace OK")
    except Exception:
        log.exception("after_install: create_desktop_icons_from_workspace FAILED")
        raise

    # "Trade MVP" has no DocTypes so it never appears in user.allow_modules.
    # Clearing module on Workspace prevents the PermissionError in Workspace.__init__
    # (line 42-48 frappe/desk/desktop.py) that silently excludes trade workspaces.
    # Clearing module on Workspace Sidebar makes get_sidebar_items() include them
    # unconditionally (bypasses the allow_modules check there too).
    if TRADE_WORKSPACES:
        placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))

        result = frappe.db.sql(
            f"UPDATE `tabWorkspace` SET module = '' WHERE name IN ({placeholders})",
            TRADE_WORKSPACES,
        )
        log.info(f"after_install: cleared Workspace.module for {TRADE_WORKSPACES}")

        frappe.db.sql(
            f"UPDATE `tabWorkspace Sidebar` SET module = NULL WHERE title IN ({placeholders})",
            TRADE_WORKSPACES,
        )
        log.info(f"after_install: cleared Workspace Sidebar.module for {TRADE_WORKSPACES}")

    _create_trade_desktop_icons()
    log.info("after_install: _create_trade_desktop_icons OK")

    # Verify workspaces actually landed in the DB before flushing cache
    found = frappe.db.get_all(
        "Workspace",
        filters={"name": ["in", TRADE_WORKSPACES]},
        fields=["name", "module", "is_hidden", "public"],
    )
    log.info(f"after_install: workspace DB verification — found {len(found)}/{len(TRADE_WORKSPACES)}: {found}")
    if len(found) < len(TRADE_WORKSPACES):
        missing = set(TRADE_WORKSPACES) - {w.name for w in found}
        log.warning(f"after_install: MISSING workspaces in DB: {missing}")

    frappe.cache.flushall()
    log.info("after_install: cache flushed — COMPLETE")


def hide_default_workspaces():
    placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
    frappe.db.sql(
        f"UPDATE `tabWorkspace` SET is_hidden = 1 WHERE name NOT IN ({placeholders}) AND name != 'Workspace'",
        TRADE_WORKSPACES,
    )
    hidden = frappe.db.sql("SELECT COUNT(*) FROM `tabWorkspace` WHERE is_hidden = 1")[0][0]
    return hidden


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
    log = _log()
    user = frappe.session.user
    log.debug(f"[boot] user={user!r}")

    if user in ("Guest", "Administrator"):
        log.debug(f"[boot] user={user!r} → skipped (system account), bootinfo untouched")
        return

    user_trade_roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "role": ["in", TRADE_ROLES]},
        pluck="role",
    )
    log.debug(f"[boot] user={user!r} trade_roles={user_trade_roles}")

    if not user_trade_roles:
        # No trade role — user sees raw bootinfo.
        # ERPNext workspaces are hidden (is_hidden=1), trade workspaces should be visible.
        ws_in_boot = [p.get("title") for p in bootinfo.workspaces.get("pages", [])] if hasattr(bootinfo, "workspaces") else []
        log.warning(
            f"[boot] user={user!r} has NO trade roles. "
            f"Bootinfo workspaces passed through as-is: {ws_in_boot}. "
            f"If this list is empty the desk will be blank."
        )
        return

    allowed = set()
    for role in user_trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))
    log.debug(f"[boot] user={user!r} allowed_workspaces={sorted(allowed)}")

    # Capture state BEFORE filtering so we can log what was there vs what survived
    ws_before  = [p.get("title") for p in bootinfo.workspaces.get("pages", [])] if hasattr(bootinfo, "workspaces") else []
    icons_before  = len(getattr(bootinfo, "desktop_icons", []))
    sidebar_before = sorted(getattr(bootinfo, "workspace_sidebar_item", {}).keys())
    app_before = [a.get("name") for a in getattr(bootinfo, "app_data", [])]

    log.debug(
        f"[boot] BEFORE filter — "
        f"workspaces={ws_before} "
        f"icons={icons_before} "
        f"sidebar_keys={sidebar_before} "
        f"app_data={app_before}"
    )

    _filter_workspaces(bootinfo, allowed)
    _filter_desktop_icons(bootinfo, allowed)
    _filter_sidebar(bootinfo, allowed)
    _filter_app_data(bootinfo)

    ws_after   = [p.get("title") for p in bootinfo.workspaces.get("pages", [])] if hasattr(bootinfo, "workspaces") else []
    icons_after   = len(getattr(bootinfo, "desktop_icons", []))
    sidebar_after  = sorted(getattr(bootinfo, "workspace_sidebar_item", {}).keys())
    app_after  = [a.get("name") for a in getattr(bootinfo, "app_data", [])]

    log.debug(
        f"[boot] AFTER filter — "
        f"workspaces={ws_after} "
        f"icons={icons_after} "
        f"sidebar_keys={sidebar_after} "
        f"app_data={app_after}"
    )

    if not ws_after:
        log.warning(
            f"[boot] user={user!r} desk will be BLANK. "
            f"allowed={sorted(allowed)} but nothing matched in bootinfo workspaces={ws_before}. "
            f"Check that trade workspace records exist in tabWorkspace with is_hidden=0 and module=''."
        )


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
    # get_desktop_icons() does not return a module_name field — only label
    # identifies which workspace each icon belongs to.
    bootinfo.desktop_icons = [
        icon for icon in bootinfo.desktop_icons
        if icon.get("label") in allowed
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
    log = _log()
    # The boot payload uses app_name, not name — log all keys on first entry
    # so we can verify the field name if this changes in a future Frappe version.
    if bootinfo.app_data:
        log.debug(f"[app_data] keys on first entry: {list(bootinfo.app_data[0].keys())}")
    bootinfo.app_data = [
        a for a in bootinfo.app_data
        if a.get("app_name") == "trade_mvp" or a.get("name") == "trade_mvp"
    ]


@frappe.whitelist()
def get_trade_debug_info():
    """On-demand desk-state inspector.

    No SSH needed — call this from the browser JS console while logged into
    any account that has System Manager or Administrator:

        frappe.call('trade_mvp.setup.get_trade_debug_info')
            .then(r => console.log(JSON.stringify(r.message, null, 2)))

    Returns a complete snapshot of every decision point that controls what
    appears on the desk for the current user.
    """
    if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
        frappe.throw("Requires System Manager or Administrator")

    user = frappe.session.user
    user_roles = frappe.get_roles()
    trade_roles = [r for r in user_roles if r in TRADE_ROLES]

    allowed: set = set()
    for role in trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))

    # 1. What's in tabWorkspace for the 6 trade workspaces?
    trade_ws_in_db = frappe.db.get_all(
        "Workspace",
        filters={"name": ["in", TRADE_WORKSPACES]},
        fields=["name", "module", "is_hidden", "public", "app"],
    )

    # 2. What does get_workspace_sidebar_items() actually return for this user?
    #    This is exactly what populates bootinfo.workspaces["pages"].
    from frappe.desk.desktop import get_workspace_sidebar_items
    sidebar_result = get_workspace_sidebar_items()
    pages_from_frappe = [
        {"title": p.get("title"), "is_hidden": p.get("is_hidden"), "module": p.get("module")}
        for p in sidebar_result.get("pages", [])
    ]

    # 3. What's in tabWorkspace Sidebar?
    ws_sidebars = frappe.db.get_all(
        "Workspace Sidebar",
        filters={"name": ["in", TRADE_WORKSPACES]},
        fields=["name", "module"],
    )

    # 4. What module profile is this user on?
    module_profile = frappe.db.get_value("User", user, "module_profile")
    blocked_modules = frappe.get_cached_doc("User", user).get_blocked_modules()

    # 5. Does "Workspace Manager" role gate apply?
    has_workspace_manager = "Workspace Manager" in user_roles

    # 6. All hidden workspaces
    all_ws = frappe.db.get_all(
        "Workspace",
        fields=["name", "is_hidden", "module", "public"],
        order_by="is_hidden desc, name asc",
    )

    return {
        "user": user,
        "user_trade_roles": trade_roles,
        "allowed_workspaces_for_roles": sorted(allowed),
        "has_workspace_manager_role": has_workspace_manager,
        "module_profile": module_profile,
        "blocked_modules": blocked_modules,
        "trade_workspaces_in_db": trade_ws_in_db,
        "trade_workspaces_expected": TRADE_WORKSPACES,
        "trade_workspaces_missing": sorted(set(TRADE_WORKSPACES) - {w.name for w in trade_ws_in_db}),
        "workspace_sidebars_in_db": ws_sidebars,
        "pages_frappe_filter_returns": pages_from_frappe,
        "pages_frappe_filter_count": len(pages_from_frappe),
        "all_workspaces_hidden_count": sum(1 for w in all_ws if w.is_hidden),
        "all_workspaces_visible_count": sum(1 for w in all_ws if not w.is_hidden),
        "all_workspaces": [
            {"name": w.name, "is_hidden": w.is_hidden, "module": w.module, "public": w.public}
            for w in all_ws
        ],
        "diagnosis": _diagnose(trade_ws_in_db, pages_from_frappe, trade_roles, allowed),
    }


def _create_trade_desktop_icons():
    """Create Desktop Icon records for trade workspaces.

    create_desktop_icons_from_workspace() (Frappe core) only creates icons
    inside an `if w.module:` block — workspaces with module='' are skipped.
    We clear module on trade workspaces to bypass the allow_modules gate, so
    we must create their icons explicitly here.
    """
    log = _log()
    # icon values sourced directly from the workspace JSON fixtures
    ws_icons = {
        "Pipeline":      "crm",
        "Sales":         "sell",
        "Purchasing":    "buying",
        "Warehouse":     "stock",
        "Finance":       "accounting",
        "Asset Register": "asset",
    }
    for ws_name, icon_name in ws_icons.items():
        if frappe.db.exists("Desktop Icon", {"label": ws_name, "icon_type": "Link"}):
            log.info(f"[icons] Desktop Icon for '{ws_name}' already exists — skipped")
            continue
        icon = frappe.new_doc("Desktop Icon")
        icon.label      = ws_name
        icon.link_type  = "Workspace Sidebar"
        icon.link_to    = ws_name
        icon.icon_type  = "Link"
        icon.icon       = icon_name
        icon.standard   = 1
        icon.insert(ignore_permissions=True)
        log.info(f"[icons] Created Desktop Icon for '{ws_name}'")


def _diagnose(trade_ws_in_db, pages_from_frappe, trade_roles, allowed):
    """Return a plain-English summary of what's wrong."""
    issues = []

    if len(trade_ws_in_db) < len(TRADE_WORKSPACES):
        missing = set(TRADE_WORKSPACES) - {w.name for w in trade_ws_in_db}
        issues.append(f"MISSING workspace records in DB: {sorted(missing)}. Run after_install().")

    for ws in trade_ws_in_db:
        if ws.module:
            issues.append(
                f"Workspace '{ws.name}' has module='{ws.module}' — should be blank. "
                f"Frappe's allow_modules gate will block it. Run the module-clearing SQL."
            )
        if ws.is_hidden:
            issues.append(f"Workspace '{ws.name}' has is_hidden=1 — it will never appear in the sidebar.")

    if not trade_roles:
        issues.append(
            "Current user has NO trade roles. boot_session filter will pass bootinfo through "
            "unmodified. The user will see whatever Frappe's own filters return — if those "
            "workspaces are empty the desk is blank."
        )

    if trade_roles and not pages_from_frappe:
        issues.append(
            "User HAS trade roles but Frappe's get_workspace_sidebar_items() returned 0 pages. "
            "The boot_session filter has nothing to work with. Check workspace DB records and module field."
        )

    if trade_roles and allowed and pages_from_frappe:
        page_titles = {p["title"] for p in pages_from_frappe}
        unmatched = allowed - page_titles
        if unmatched:
            issues.append(
                f"Trade roles allow {sorted(allowed)} but these are NOT in Frappe's page list: "
                f"{sorted(unmatched)}. After the boot filter runs, those workspaces will be stripped."
            )

    if not issues:
        return "No issues detected. Desk should show workspaces correctly."
    return issues


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
