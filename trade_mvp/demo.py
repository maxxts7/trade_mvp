import frappe

DEMO_USERS = [
    {"email": "sales@trade.local",     "role": "Trade - Sales Executive",    "first_name": "Sarah", "last_name": "Sales"},
    {"email": "purchase@trade.local",  "role": "Trade - Purchase Executive", "first_name": "Peter", "last_name": "Purchase"},
    {"email": "warehouse@trade.local", "role": "Trade - Warehouse Staff",    "first_name": "Wes",   "last_name": "Warehouse"},
    {"email": "accounts@trade.local",  "role": "Trade - Accountant",         "first_name": "Anna",  "last_name": "Accounts"},
    {"email": "manager@trade.local",   "role": "Trade - Manager",            "first_name": "Mike",  "last_name": "Manager"},
]

DEMO_ITEMS = [
    {"item_code": "ELEC-001", "item_name": "Electronics Component",  "item_group": "Products", "stock_uom": "Nos",   "gst_hsn_code": "999900"},
    {"item_code": "TEXT-001", "item_name": "Industrial Textile",      "item_group": "Products", "stock_uom": "Meter", "gst_hsn_code": "999900"},
    {"item_code": "CHEM-001", "item_name": "Chemical Raw Material",   "item_group": "Products", "stock_uom": "Kg",    "gst_hsn_code": "999900"},
    {"item_code": "MACH-001", "item_name": "Machinery Part",          "item_group": "Products", "stock_uom": "Nos",   "gst_hsn_code": "999900"},
    {"item_code": "CONS-001", "item_name": "Consumer Goods",          "item_group": "Products", "stock_uom": "Nos",   "gst_hsn_code": "999900"},
]

DEMO_CUSTOMERS = [
    {"customer_name": "Alpha Imports Ltd",  "customer_group": "Commercial", "territory": "All Territories", "credit_limit": 100_000},
    {"customer_name": "Beta Trading Co",    "customer_group": "Commercial", "territory": "All Territories", "credit_limit": 75_000},
    {"customer_name": "Gamma Distributors", "customer_group": "Commercial", "territory": "All Territories", "credit_limit": 0},
]

DEMO_SUPPLIERS = [
    {"supplier_name": "XYZ Exports",         "supplier_group": "All Supplier Groups", "country": "China"},
    {"supplier_name": "ABC Manufacturing",   "supplier_group": "All Supplier Groups", "country": "Germany"},
    {"supplier_name": "Global Sourcing LLC", "supplier_group": "All Supplier Groups", "country": "United Arab Emirates"},
]


def create_demo_data():
    _create_users()
    _create_items()
    _create_customers()
    _create_suppliers()
    frappe.db.commit()
    print("Demo data created successfully.")


def _create_users():
    for u in DEMO_USERS:
        if frappe.db.exists("User", u["email"]):
            print(f"  skip (exists): {u['email']}")
            continue
        user = frappe.new_doc("User")
        user.email = u["email"]
        user.first_name = u["first_name"]
        user.last_name = u["last_name"]
        user.send_welcome_email = 0
        user.new_password = "Trade@1234"
        user.insert(ignore_permissions=True)
        user.add_roles(u["role"])
        print(f"  created user: {u['email']}")


def _create_items():
    for i in DEMO_ITEMS:
        if frappe.db.exists("Item", i["item_code"]):
            print(f"  skip (exists): {i['item_code']}")
            continue
        item = frappe.new_doc("Item")
        item.item_code = i["item_code"]
        item.item_name = i["item_name"]
        item.item_group = i["item_group"]
        item.stock_uom = i["stock_uom"]
        item.is_stock_item = 1
        item.gst_hsn_code = i["gst_hsn_code"]
        item.insert(ignore_permissions=True)
        print(f"  created item: {i['item_code']}")


def _create_customers():
    for c in DEMO_CUSTOMERS:
        if frappe.db.exists("Customer", c["customer_name"]):
            print(f"  skip (exists): {c['customer_name']}")
            continue
        customer = frappe.new_doc("Customer")
        customer.customer_name = c["customer_name"]
        customer.customer_group = c["customer_group"]
        customer.territory = c["territory"]
        customer.trade_credit_limit = c["credit_limit"]
        customer.insert(ignore_permissions=True)
        print(f"  created customer: {c['customer_name']}")


def _create_suppliers():
    for s in DEMO_SUPPLIERS:
        if frappe.db.exists("Supplier", s["supplier_name"]):
            print(f"  skip (exists): {s['supplier_name']}")
            continue
        supplier = frappe.new_doc("Supplier")
        supplier.supplier_name = s["supplier_name"]
        supplier.supplier_group = s["supplier_group"]
        supplier.country = s["country"]
        supplier.insert(ignore_permissions=True)
        print(f"  created supplier: {s['supplier_name']}")
