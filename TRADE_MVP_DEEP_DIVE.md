# Trade MVP — Complete Technical & Business Reference

This document covers the full picture: why the system is designed the way it is, how Frappe's
internals work in each area, the exact code that implements each mechanism, and the rationale
behind every design decision.

---

## Table of Contents

1. [Business Context](#1-business-context)
2. [App Architecture](#2-app-architecture)
3. [The Five Roles](#3-the-five-roles)
4. [The Six Workspaces](#4-the-six-workspaces)
5. [Permission System — All Layers](#5-permission-system--all-layers)
   - 5.1 [DocType Permissions (Custom DocPerm)](#51-doctype-permissions-custom-docperm)
   - 5.2 [Module Profile](#52-module-profile)
   - 5.3 [Boot Session Filter](#53-boot-session-filter)
   - 5.4 [Property Setter (Field Visibility)](#54-property-setter-field-visibility)
   - 5.5 [Report Permissions](#55-report-permissions)
6. [Workflow Approval Gates](#6-workflow-approval-gates)
7. [Credit Limit Business Rule](#7-credit-limit-business-rule)
8. [Custom Fields](#8-custom-fields)
9. [UI Layer (Client-side)](#9-ui-layer-client-side)
10. [Installation Sequence](#10-installation-sequence)
11. [Demo Data](#11-demo-data)
12. [Permission Summary Table](#12-permission-summary-table)

---

## 1. Business Context

### What the company does

An import/export trading company buys goods from overseas suppliers and sells them to domestic
customers. The core operational cycle is:

```
Supplier → Purchase Order → Purchase Receipt → Stock → Delivery Note → Customer
                                                 ↕
                                        Sales Order ← Customer enquiry
```

Financial settlements run on either side:
- Customers pay via Sales Invoice → Payment Entry (inbound)
- Company pays suppliers via Purchase Invoice → Payment Entry (outbound)

Fixed assets (machinery, vehicles, equipment) are tracked separately as they depreciate over time.

### Why a custom app on ERPNext?

ERPNext is a complete ERP covering ~20 modules: Accounting, HR, Payroll, Manufacturing,
Projects, Quality Management, Subcontracting, and more. A trading company uses only a fraction
of this. Exposing the full ERPNext UI to trading staff creates three problems:

1. **Cognitive overload** — staff waste time navigating irrelevant modules.
2. **Accidental writes** — a Warehouse user stumbling into Payroll can cause harm.
3. **Compliance** — audit trails are cleaner when users are locked to their domain.

The trade_mvp app solves this by layering a focused, role-scoped interface on top of ERPNext
without modifying ERPNext core code. All data still lives in ERPNext's standard DocTypes (Sales
Order, Purchase Invoice, etc.) — the app only controls *who sees what* and *what they can do*.

### Trade-specific data requirements

Import/export transactions require fields that ERPNext doesn't include by default:

- **Port of Loading / Port of Discharge** — the physical ports on each trade document
- **LC Number (Letter of Credit)** — the bank instrument number financing the shipment
- **Customer Credit Limit** — cap on outstanding exposure per buyer

These are added as Custom Fields so they survive ERPNext upgrades.

---

## 2. App Architecture

```
apps/trade_mvp/
├── trade_mvp/
│   ├── hooks.py                    # App entry points — Frappe reads this first
│   ├── setup.py                    # All setup logic + business rules
│   ├── demo.py                     # Demo users, items, customers, suppliers
│   ├── fixtures/
│   │   ├── role.json               # 5 Trade roles
│   │   ├── custom_field.json       # Trade-specific fields
│   │   ├── workflow.json           # SO / PO / Payment approval workflows
│   │   └── workflow_state.json     # Draft / Pending Approval / Approved / Rejected
│   ├── public/
│   │   ├── js/trade_mvp.js         # Client-side role check + UI tweaks
│   │   └── css/trade_mvp.css       # Minimal styling overrides
│   └── trade_mvp/
│       └── workspace/              # 6 Workspace JSON definitions
│           ├── pipeline/
│           ├── sales/
│           ├── purchasing/
│           ├── warehouse/
│           ├── finance/
│           └── asset_register/
└── tests/
    └── test_credit_limit.py        # Unit tests for credit limit logic
```

### How Frappe loads an app

When Frappe starts, it reads every installed app's `hooks.py`. This file is the app's
declaration — it tells Frappe what to call, when to call it, and what assets to serve.

```python
# hooks.py — the complete file
app_name = "trade_mvp"
app_title = "Trade MVP"
app_publisher = "Trade"
app_description = "Import/export trading app built on ERPNext"
app_email = "admin@trade.local"
app_license = "MIT"

app_include_js = "/assets/trade_mvp/js/trade_mvp.js"   # served on every desk page
app_include_css = "/assets/trade_mvp/css/trade_mvp.css"

after_install = "trade_mvp.setup.after_install"         # called once on install

boot_session = "trade_mvp.setup.filter_bootinfo_for_trade_users"  # called on every login

doc_events = {
    "Sales Order": {
        "validate": "trade_mvp.setup.check_credit_limit"   # called on every SO save
    }
}

fixtures = [
    {"dt": "Role",           "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field",   "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Pending Approval", "Approved", "Rejected"]]]},
    {"dt": "Workflow",       "filters": [["name", "like", "Trade%"]]},
]
```

**Key hooks explained:**

| Hook | Frappe behaviour | Trade MVP use |
|------|-----------------|---------------|
| `after_install` | Called once when `bench install-app trade_mvp` runs | Sets up all permissions, workspaces, module profiles |
| `boot_session` | Called on every successful login; receives the `bootinfo` dict before it is JSON-serialized to the browser | Strips non-trade workspaces/icons from the response |
| `doc_events` | Maps DocType + event to a Python function | Enforces credit limit on every Sales Order save |
| `fixtures` | Tells `bench migrate` which records to export/import | Keeps roles, custom fields, and workflows in version control |

---

## 3. The Five Roles

### Frappe's role system

Frappe uses a role-based access control (RBAC) model. A `Role` is a named group. Each `User`
has one or more roles assigned via the `Has Role` child table. Permissions are defined per role,
not per user.

Roles that have `desk_access: 1` can log into the desk UI. Without it, a user is limited to
the web portal.

### Trade roles (fixtures/role.json)

```json
[
  {"doctype": "Role", "name": "Trade - Sales Executive",    "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Purchase Executive", "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Warehouse Staff",    "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Accountant",         "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Manager",            "desk_access": 1}
]
```

All five have `desk_access: 1` because trade users work in the Frappe desk, not a portal.

The `Trade -` prefix namespaces them away from ERPNext's built-in roles (Sales User, Accounts
User, etc.) and makes them easy to filter in code with `["name", "like", "Trade%"]`.

### Business hierarchy

```
Trade - Manager                  ← strategic oversight; approves high-value transactions
  ├── Trade - Sales Executive    ← manages the customer-facing sales pipeline
  ├── Trade - Purchase Executive ← manages supplier relationships and purchase orders
  ├── Trade - Warehouse Staff    ← manages physical stock movements
  └── Trade - Accountant         ← manages financial records and reporting
```

**Design principle — segregation of duties:**

Each operational role owns its documents end-to-end (create → write → submit → cancel →
amend) but only *reads* documents from adjacent departments. This prevents, for example, a
Sales Executive from posting their own invoice, or a Warehouse user from approving payments.
The Manager role has full CRUD across all documents and serves as the approval authority for
high-value transactions via workflow.

### Role-to-workspace mapping

```python
# setup.py
ROLE_WORKSPACES = {
    "Trade - Sales Executive":    ["Pipeline", "Sales"],
    "Trade - Purchase Executive": ["Purchasing"],
    "Trade - Warehouse Staff":    ["Warehouse"],
    "Trade - Accountant":         ["Finance", "Asset Register"],
    "Trade - Manager":            ["Pipeline", "Sales", "Purchasing",
                                   "Warehouse", "Finance", "Asset Register"],
}
```

This dict is the single source of truth for UI access. It is consumed by
`filter_bootinfo_for_trade_users` at boot time to decide which workspace icons reach the browser.

---

## 4. The Six Workspaces

### What a Workspace is in Frappe

A `Workspace` is a Frappe DocType that represents a page in the desk UI. Each workspace has:
- A desktop icon on the home screen
- A left-nav sidebar with links to DocTypes, reports, and dashboards
- An optional content area with charts and number cards

Workspaces are stored as JSON files in the app directory and imported as fixtures via
`bench migrate`. They appear in `tabWorkspace` in the database.

### Trade workspaces

```python
TRADE_WORKSPACES = [
    "Pipeline", "Sales", "Purchasing", "Warehouse", "Finance", "Asset Register"
]
```

Each workspace JSON has these key fields:

```json
{
  "doctype": "Workspace",
  "name": "Sales",
  "module": "",           ← intentionally empty; see installation section
  "app": "trade_mvp",
  "public": 1,            ← visible to all users (filtered per role at boot time)
  "roles": []             ← NOT used for role filtering; boot hook handles that instead
}
```

**Why `module: ""`?**

Frappe's `Workspace.__init__` (frappe/desk/desktop.py:42-48) checks whether the workspace's
module is in `user.allow_modules` before including it in the desk. Since "Trade MVP" registers
no DocTypes, it never appears in `allow_modules`. Setting `module` to empty bypasses this check
entirely. The post-install SQL in `after_install()` clears this field:

```python
frappe.db.sql(
    "UPDATE `tabWorkspace` SET module = '' WHERE name IN (%s, %s, ...)",
    TRADE_WORKSPACES,
)
```

### Sidebar items

Each workspace has a programmatically built sidebar defined in `SIDEBAR_ITEMS`:

```python
SIDEBAR_ITEMS = {
    "Sales": [
        ("Overview",      "Section Break", None),
        ("Dashboard",     "Dashboard",     "Selling"),
        ("Orders",        "Section Break", None),
        ("Quotation",     "DocType",       "Quotation"),
        ("Sales Order",   "DocType",       "Sales Order"),
        ("Delivery Note", "DocType",       "Delivery Note"),
        ("Sales Invoice", "DocType",       "Sales Invoice"),
        ("Catalogue",     "Section Break", None),
        ("Item",          "DocType",       "Item"),
        ("Customer",      "DocType",       "Customer"),
    ],
    # ... (Pipeline, Purchasing, Warehouse, Finance, Asset Register)
}
```

`Section Break` rows render as collapsible headers; `Link` rows are clickable navigation items.
The Finance workspace is the most extensive, with links to P&L, Balance Sheet, Cash Flow,
Accounts Receivable/Payable, and bank reconciliation reports.

`setup_workspace_sidebars()` writes these programmatically into `Workspace Sidebar` documents:

```python
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
```

---

## 5. Permission System — All Layers

The system enforces access through five independent layers. Each covers a different attack
surface; no single layer is sufficient on its own.

```
Request lifecycle:
  Browser login → boot_session hook (Layer 3) strips bootinfo
  Desk renders  → Module Profile (Layer 2) blocks module icons
                → JS/CSS (Layer 9) hides nav items
  Form opens    → DocPerm (Layer 1) governs read access
                → Property Setter (Layer 4) hides fields
  Form saves    → DocPerm (Layer 1) governs write access
                → Workflow (Layer 6) controls state transitions
                → Credit limit hook (Layer 7) validates business rule
  Report runs   → DocPerm (Layer 1) on ref_doctype
                → Report.roles (Layer 5) on the report record
```

---

### 5.1 DocType Permissions (Custom DocPerm)

#### How Frappe's permission system works

Every DocType has a `permissions` child table. Each row is a `DocPerm` record that associates
a `role` with a set of boolean flags: `read`, `write`, `create`, `delete`, `submit`, `cancel`,
`amend`, `report`, `import`, `export`, `print`, `email`, `share`.

Frappe checks these on every server-side access: `frappe.get_doc()`, list queries, REST API
calls, and form saves. If the current user has no matching role+doctype row with the required
flag set to 1, Frappe raises a `PermissionError`.

`Custom DocPerm` is an override mechanism — it lives in `tabCustom DocPerm` and takes
precedence over the DocType's built-in permissions. This allows trade_mvp to grant access to
ERPNext's existing DocTypes (Sales Order, Purchase Invoice, etc.) without modifying ERPNext's
core code.

#### Permission matrix

```python
# setup.py — TRADE_PERMISSIONS
# Tuple: (doctype, read, write, create, delete, submit, cancel, amend)

"Trade - Sales Executive": [
    ("Lead",           1, 1, 1, 0, 0, 0, 0),  # owns leads end-to-end
    ("Opportunity",    1, 1, 1, 0, 0, 0, 0),  # owns opportunities
    ("Quotation",      1, 1, 1, 0, 1, 1, 1),  # full lifecycle incl. amend
    ("Sales Order",    1, 1, 1, 0, 1, 1, 1),  # full lifecycle
    ("Purchase Order", 1, 0, 0, 0, 0, 0, 0),  # read-only: cross-check supply
    ("Delivery Note",  1, 0, 0, 0, 0, 0, 0),  # read-only: track shipment status
    ("Sales Invoice",  1, 0, 0, 0, 0, 0, 0),  # read-only: see billing status
    ("Customer",       1, 1, 1, 0, 0, 0, 0),  # manage customer master
    ("Supplier",       1, 0, 0, 0, 0, 0, 0),  # read-only supplier info
    ("Item",           1, 0, 0, 0, 0, 0, 0),  # read-only catalogue
    ("Contact",        1, 1, 1, 0, 0, 0, 0),  # manage contacts
    ("Address",        1, 1, 1, 0, 0, 0, 0),  # manage addresses
    ("Workflow",       1, 0, 0, 0, 0, 0, 0),  # read-only: see approval state
    ("Workflow State", 1, 0, 0, 0, 0, 0, 0),
],

"Trade - Purchase Executive": [
    ("Purchase Order",   1, 1, 1, 0, 1, 1, 1),  # owns PO lifecycle
    ("Purchase Invoice", 1, 0, 0, 0, 0, 0, 0),  # read-only: check billing
    ("Sales Order",      1, 0, 0, 0, 0, 0, 0),  # read-only: understand demand
    ("Purchase Receipt", 1, 0, 0, 0, 0, 0, 0),  # read-only: confirm delivery
    ("Supplier",         1, 1, 1, 0, 0, 0, 0),  # manage supplier master
    ("Customer",         1, 0, 0, 0, 0, 0, 0),  # read-only
    ("Item",             1, 0, 0, 0, 0, 0, 0),
    ("Contact",          1, 1, 1, 0, 0, 0, 0),
    ("Address",          1, 1, 1, 0, 0, 0, 0),
    ("Workflow",         1, 0, 0, 0, 0, 0, 0),
    ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
],

"Trade - Warehouse Staff": [
    ("Purchase Receipt", 1, 1, 1, 0, 1, 1, 1),  # receives goods inbound
    ("Delivery Note",    1, 1, 1, 0, 1, 1, 1),  # dispatches goods outbound
    ("Stock Entry",      1, 1, 1, 0, 1, 1, 1),  # internal stock movements
    ("Sales Order",      1, 0, 0, 0, 0, 0, 0),  # read-only: pick list reference
    ("Purchase Order",   1, 0, 0, 0, 0, 0, 0),  # read-only: inbound reference
    ("Item",             1, 0, 0, 0, 0, 0, 0),
    ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
    # read-only on Customer/Supplier/Contact/Address for delivery address lookup
    ("Customer",         1, 0, 0, 0, 0, 0, 0),
    ("Supplier",         1, 0, 0, 0, 0, 0, 0),
    ("Contact",          1, 0, 0, 0, 0, 0, 0),
    ("Address",          1, 0, 0, 0, 0, 0, 0),
    ("Workflow",         1, 0, 0, 0, 0, 0, 0),
    ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
],

"Trade - Accountant": [
    ("Sales Invoice",    1, 1, 1, 0, 1, 1, 1),  # creates and posts sales invoices
    ("Purchase Invoice", 1, 1, 1, 0, 1, 1, 1),  # creates and posts purchase invoices
    ("Payment Entry",    1, 1, 1, 0, 1, 1, 1),  # records payments (in/out)
    ("Sales Order",      1, 0, 0, 0, 0, 0, 0),  # read-only: billing reference
    ("Purchase Order",   1, 0, 0, 0, 0, 0, 0),  # read-only: billing reference
    ("Purchase Receipt", 1, 0, 0, 0, 0, 0, 0),
    ("Delivery Note",    1, 0, 0, 0, 0, 0, 0),
    ("Bank Account",     1, 0, 0, 0, 0, 0, 0),  # read-only: settlement accounts
    ("Asset",            1, 1, 1, 0, 1, 1, 1),  # manages fixed asset lifecycle
    ("Asset Category",   1, 0, 0, 0, 0, 0, 0),
    ("Asset Movement",   1, 1, 1, 0, 1, 1, 1),
    # read-only masters
    ("Customer",         1, 0, 0, 0, 0, 0, 0),
    ("Supplier",         1, 0, 0, 0, 0, 0, 0),
    ("Item",             1, 0, 0, 0, 0, 0, 0),
    ("Warehouse",        1, 0, 0, 0, 0, 0, 0),
    ("Workflow",         1, 0, 0, 0, 0, 0, 0),
    ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
],

"Trade - Manager": [
    # Full CRUD on all operational DocTypes
    ("Lead",             1, 1, 1, 1, 0, 0, 0),  # delete=1 (can purge bad leads)
    ("Opportunity",      1, 1, 1, 1, 0, 0, 0),
    ("Quotation",        1, 1, 1, 1, 1, 1, 1),
    ("Sales Order",      1, 1, 1, 1, 1, 1, 1),
    ("Purchase Order",   1, 1, 1, 1, 1, 1, 1),
    ("Purchase Receipt", 1, 1, 1, 1, 1, 1, 1),
    ("Delivery Note",    1, 1, 1, 1, 1, 1, 1),
    ("Sales Invoice",    1, 1, 1, 1, 1, 1, 1),
    ("Purchase Invoice", 1, 1, 1, 1, 1, 1, 1),
    ("Payment Entry",    1, 1, 1, 1, 1, 1, 1),
    ("Customer",         1, 1, 1, 1, 0, 0, 0),  # delete=0 on masters (protect data integrity)
    ("Supplier",         1, 1, 1, 1, 0, 0, 0),
    ("Item",             1, 1, 1, 1, 0, 0, 0),
    ("Warehouse",        1, 1, 1, 1, 0, 0, 0),
    ("Bank Account",     1, 1, 1, 1, 0, 0, 0),
    ("Asset",            1, 1, 1, 1, 1, 1, 1),
    ("Asset Category",   1, 1, 1, 1, 0, 0, 0),
    ("Asset Movement",   1, 1, 1, 1, 1, 1, 1),
    ("Contact",          1, 1, 1, 1, 0, 0, 0),
    ("Address",          1, 1, 1, 1, 0, 0, 0),
    ("Workflow",         1, 0, 0, 0, 0, 0, 0),
    ("Workflow State",   1, 0, 0, 0, 0, 0, 0),
],
```

**Why Manager can delete transactional documents but not masters:**
Transactional documents in Draft state (docstatus=0) can be deleted as they haven't been
posted. Submitted documents cannot be deleted in Frappe regardless of delete permission —
they must be cancelled first. Masters (Customer, Supplier, Item) are intentionally protected
from deletion since they are referenced by historical transactions.

#### Reference DocType read permissions (TRADE_READ_REFS)

Every form in ERPNext has link fields that point to reference DocTypes: a Sales Order has
`currency` (link to Currency), `price_list` (link to Price List), `tax_category` (link to
Tax Category), and so on. Without read permission on these reference DocTypes, Frappe throws
a PermissionError when it tries to validate the link field value.

```python
TRADE_READ_REFS = [
    # Core masters used as link targets in every transactional form
    "Territory", "Customer Group", "Supplier Group", "Item Group",
    "Price List", "Currency", "UOM", "Payment Terms Template",
    "Tax Category", "Sales Taxes and Charges Template",
    "Purchase Taxes and Charges Template", "Shipping Rule",
    "Terms and Conditions", "Incoterm", "Cost Center", "Account",
    "Letter Head", "Stock Entry Type", "Lead Source",

    # Item / stock references (appear in item line child tables)
    "Item Tax Template", "Batch", "Serial and Batch Bundle",
    "Manufacturer", "Product Bundle", "Material Request",
    "Putaway Rule", "Blanket Order", "Supplier Quotation",

    # CRM / contact references
    "Salutation", "Gender", "Country", "Industry Type",
    "Market Segment", "Opportunity Type", "Sales Stage",

    # Accounting / finance references
    "Mode of Payment", "Journal Entry", "Payment Term",
    "Payment Request", "Finance Book", "Tax Withholding Category",

    # Misc
    "Project", "Location", "Print Heading", "Language",
    "Journal Entry Template", "Party Type", "Party Account",

    # Critical for financial reports
    "GL Entry",              # General Ledger, Trial Balance, P&L, Balance Sheet
    "Payment Ledger Entry",  # Accounts Payable/Receivable reports
    "Company", "Fiscal Year",
]
```

All five trade roles receive `read: 1` on every entry in this list. The `_upsert_perm` function
automatically adds `report: 1` alongside `read: 1` — this satisfies `frappe.has_permission(
ref_doctype, "report")` which `query_report.py` calls before running script reports.

**Why `GL Entry` and `Payment Ledger Entry` need read permission:**
Financial reports (General Ledger, Trial Balance, etc.) run server-side queries against
`tabGL Entry`. Before executing the query, Frappe calls `has_permission("GL Entry", "report")`.
Without a Custom DocPerm row granting `read` on GL Entry for Trade - Accountant and Trade -
Manager, every financial report returns a permission error even though those roles are listed
in `Report.roles`.

#### Implementation: `_upsert_perm`

```python
def _upsert_perm(doctype, role, values):
    # Always bundle report=1 with read=1 to satisfy query_report.py's
    # has_permission(ref_doctype, "report") check.
    if values.get("read"):
        values = {**values, "report": 1}

    existing = frappe.db.get_value(
        "Custom DocPerm",
        {"parent": doctype, "role": role, "permlevel": 0},
        "name",
    )
    if existing:
        # Update existing row rather than creating duplicates
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

    read_only = {"read": 1, "write": 0, "create": 0, "delete": 0,
                 "submit": 0, "cancel": 0, "amend": 0}
    for doctype in TRADE_READ_REFS:
        for role in TRADE_ROLES:
            _upsert_perm(doctype, role, read_only)
        touched.add(doctype)

    # Clear Frappe's in-memory permission cache for all affected DocTypes
    for doctype in touched:
        frappe.clear_cache(doctype=doctype)
```

**Why `ignore_permissions=True` on insert:** During `after_install`, the session user is
Administrator but the permission tables are being freshly built. Using `ignore_permissions`
prevents Frappe from checking permissions against a half-built table while creating the rows.

**Why clear cache per DocType:** Frappe caches the computed permission set for each DocType
in memory (and in Redis). After writing new Custom DocPerm rows, the cache must be invalidated
or Frappe continues serving the old (empty) permission set for the rest of the request.

---

### 5.2 Module Profile

#### How Module Profile works in Frappe

A `Module Profile` is a Frappe DocType that lists modules to block for users assigned to it.
When a user has a Module Profile set, Frappe's desktop excludes workspaces belonging to blocked
modules when computing what icons to show.

The mechanism is `frappe/desk/desktop.py` → `Workspace.__init__`: before including a workspace
in the icon list, Frappe checks `workspace.module in user.allow_modules`. If blocked, the
workspace is silently excluded.

#### Implementation

```python
BLOCK_MODULES = [
    # ERPNext functional modules not needed by trade
    "Accounts", "Stock", "Selling", "Buying", "CRM",
    "Manufacturing", "Projects", "HR", "Payroll", "Assets",
    "Support", "Quality Management", "Subcontracting",
    "ERPNext Integrations", "Regional",
    # Frappe core modules not needed by trade staff
    "Build", "Integrations", "Website",
    "Core", "Email", "Automation", "Desk", "Custom",
    "Geo", "Printing", "Workflow",
]

def setup_module_profiles():
    if frappe.db.exists("Module Profile", "Trade User"):
        return   # idempotent — don't recreate on re-install
    profile = frappe.new_doc("Module Profile")
    profile.module_profile_name = "Trade User"
    for module in BLOCK_MODULES:
        profile.append("block_modules", {"module": module})
    profile.insert(ignore_permissions=True)
```

**Important limitation:** Module Profile is a UX gate, not a security gate. It prevents the
module's workspace icons from appearing on the desk, but does not prevent API access to
DocTypes in those modules. An authenticated trade user who knows the URL can still navigate
directly to any DocType. The DocType permission system (Layer 1) is the actual security gate.

**Who assigns the profile:** The Module Profile "Trade User" must be manually set on each trade
user via User → Module Profile. The `after_install` hook creates the profile but does not
auto-assign it to the demo users — that is done manually after creating users.

---

### 5.3 Boot Session Filter

#### How boot_session works in Frappe

When a user logs in (or refreshes the desk), Frappe calls `get_bootinfo()` in `frappe/boot.py`.
This function builds a Python dict (`bootinfo`) containing everything the desk JavaScript needs
to initialise: the user's roles, permissions, installed apps, workspaces, sidebar items, desktop
icons, and app switcher tiles.

After `get_bootinfo()` is complete, Frappe calls every `boot_session` hook registered by any
installed app, passing the `bootinfo` dict. Hooks can mutate `bootinfo` in place. The mutated
dict is then JSON-serialised and sent to the browser.

**The four structures that must be filtered:**

```python
# frappe/boot.py (simplified sequence)
bootinfo.workspaces             = load_desktop_data()     # workspace list
bootinfo.workspace_sidebar_item = get_sidebar_items()     # left-nav content
bootinfo.app_data               = get_app_data()          # app-switcher tiles
bootinfo.desktop_icons          = get_desktop_icons()     # home screen icons

# Then hooks run:
for hook in frappe.get_hooks("boot_session"):
    frappe.get_attr(hook)(bootinfo)     # ← our filter runs here
```

If any of the four structures are not filtered, non-trade content leaks to the browser even
if the workspace page itself would reject access — the browser has already received the icon
data and may render it.

#### Implementation

```python
def filter_bootinfo_for_trade_users(bootinfo):
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return   # never filter these system users

    user_trade_roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "role": ["in", TRADE_ROLES]},
        pluck="role",
    )
    if not user_trade_roles:
        return   # not a trade user — leave bootinfo untouched

    # Build the set of allowed workspaces for this user's specific roles
    allowed = set()
    for role in user_trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))

    _filter_workspaces(bootinfo, allowed)
    _filter_desktop_icons(bootinfo, allowed)
    _filter_sidebar(bootinfo, allowed)
    _filter_app_data(bootinfo)
```

```python
def _filter_workspaces(bootinfo, allowed):
    # bootinfo.workspaces["pages"] is the list of workspace dicts
    if not hasattr(bootinfo, "workspaces"):
        return
    pages = bootinfo.workspaces.get("pages", [])
    bootinfo.workspaces["pages"] = [
        p for p in pages if p.get("title") in allowed
    ]


def _filter_desktop_icons(bootinfo, allowed):
    # Desktop icons can reference workspace by "module_name" OR "label"
    if not hasattr(bootinfo, "desktop_icons"):
        return
    bootinfo.desktop_icons = [
        icon for icon in bootinfo.desktop_icons
        if icon.get("module_name") in allowed or icon.get("label") in allowed
    ]


def _filter_sidebar(bootinfo, allowed):
    # workspace_sidebar_item is a dict keyed by lowercase workspace name
    if not hasattr(bootinfo, "workspace_sidebar_item"):
        return
    lower_allowed = {w.lower() for w in allowed}
    bootinfo.workspace_sidebar_item = {
        k: v for k, v in bootinfo.workspace_sidebar_item.items()
        if k.lower() in lower_allowed
    }


def _filter_app_data(bootinfo):
    # App switcher — trade users should only see the trade_mvp app tile,
    # not the Frappe Framework / ERPNext tiles
    if not hasattr(bootinfo, "app_data"):
        return
    bootinfo.app_data = [
        a for a in bootinfo.app_data if a.get("name") == "trade_mvp"
    ]
```

#### The desktop icon permission bypass problem

Frappe's `DesktopIcon.is_permitted()` (frappe/desk/doctype/desktop_icon/desktop_icon.py:88)
evaluates differently based on icon type:

- `type == "Link"` → checks `bootinfo.workspace_sidebar_item[label.lower()]`; raises KeyError
  if label is not in the sidebar dict → returns False (access denied)
- `type == "Folder"` → **always returns True**, bypassing all checks
- `type == "App"` → calls `check_app_permission()` which returns True unless a `has_permission`
  method is explicitly defined on the app

This means the "Accounting" Folder icon and the "Frappe Framework" App tile always pass
`is_permitted` regardless of module profiles or Custom DocPerm. The boot hook filter is the
only mechanism that prevents them reaching the browser.

#### The Redis cache problem

`get_desktop_icons()` caches its result in Redis under the key `desktop_icons:{user}`. If a
user first logged in before the module profile was assigned, the Redis entry contains the
full unrestricted icon list. On subsequent logins, `get_desktop_icons()` serves the cached
stale result, skipping the module profile check.

The boot hook runs *after* `get_desktop_icons()` has already populated `bootinfo.desktop_icons`
from the (potentially stale) cache. By filtering `bootinfo.desktop_icons` in the hook, the
client always receives the clean list regardless of cache state. Running `bench clear-cache`
between profile assignment and the next login also clears the stale Redis entry.

---

### 5.4 Property Setter (Field Visibility)

#### How Property Setter works in Frappe

A `Property Setter` record overrides a specific metadata attribute of a DocType field without
modifying the DocType itself. Setting `property = "hidden"` and `value = "1"` on a field
causes Frappe to exclude that field from the form JSON sent to the browser on every render.

This is a **global** override — it affects all users, not just trade users. The rationale is
that the hidden fields are ERPNext complexity that serves no purpose in a focused trading
context (UTM tracking, loyalty programmes, sales commission structures, etc.).

#### Implementation

```python
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
    "Quotation":       ["order_type", "language", "auto_repeat",
                        "utm_source", "utm_campaign", "utm_medium",
                        "utm_content", "referral_sales_partner"],
    "Sales Order":     ["utm_source", "utm_campaign", "utm_medium", "utm_content",
                        "commission_rate", "total_commission", "sales_team",
                        "auto_repeat", "skip_delivery_note",
                        "is_internal_customer", "represents_company",
                        "dispatch_address_name", "dispatch_address", "cost_center"],
    "Purchase Order":  ["buying_price_list", "price_list_currency", "supplier_warehouse",
                        "auto_repeat", "is_subcontracted",
                        "order_confirmation_no", "order_confirmation_date"],
    "Delivery Note":   ["lr_no", "lr_date", "vehicle_no", "driver_name",
                        "transporter", "transporter_name", "instructions",
                        "commission_rate", "sales_team", "is_internal_customer",
                        "language", "letter_head"],
    "Purchase Receipt":["rejected_warehouse", "supplier_delivery_note",
                        "is_subcontracted", "supplier_warehouse",
                        "language", "letter_head"],
    "Sales Invoice":   ["project", "commission_rate", "total_commission",
                        "loyalty_program", "sales_partner", "sales_team",
                        "utm_source", "utm_campaign", "utm_medium", "utm_content",
                        "language", "letter_head"],
    "Purchase Invoice":["project", "language", "letter_head",
                        "is_subcontracted", "supplier_warehouse"],
    "Payment Entry":   ["project", "cost_center", "letter_head",
                        "print_heading", "auto_repeat"],
    "Asset":           ["next_depreciation_date", "default_finance_book",
                        "booked_fixed_asset"],
}

def setup_property_setters():
    for doctype, fields in HIDE_FIELDS.items():
        for fieldname in fields:
            _safe_hide_field(doctype, fieldname)


def _safe_hide_field(doctype, fieldname):
    # Verify the field actually exists before creating a setter —
    # ERPNext field names can change across versions.
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
```

**Why `_safe_hide_field` checks for field existence:** If a field is renamed or removed in a
future ERPNext version, `frappe.make_property_setter` raises an exception. The existence check
makes the install idempotent across ERPNext versions.

**This is a UX control, not a security control.** The data in hidden fields still exists in
the database and is still accessible via the REST API to users with DocPerm. Do not use
Property Setter for security-sensitive field hiding.

---

### 5.5 Report Permissions

#### The two-check problem for script reports

Frappe's `query_report.py` checks permissions in two separate places:

1. `frappe.has_permission(ref_doctype, "report")` — checks `tabCustom DocPerm` or the
   DocType's built-in permissions for `report=1` on the reference DocType (e.g., GL Entry)
2. `frappe.has_permission("Report", "read", report_name)` — checks the `roles` child table
   of the Report record itself

Layer 1 (DocPerm) handles check #1 by automatically granting `report=1` alongside every
`read=1`. Layer 5 handles check #2 by adding trade roles to the Report record's roles table.

#### Implementation

```python
FINANCE_REPORTS = [
    "General Ledger", "Trial Balance",
    "Profit and Loss Statement", "Balance Sheet", "Cash Flow",
    "Accounts Receivable", "Accounts Receivable Summary",
    "Accounts Payable", "Accounts Payable Summary",
    "Customer Ledger Summary", "Supplier Ledger Summary",
    "Gross Profit", "Sales Invoice Trends", "Purchase Invoice Trends",
    "Payment Period Based On Invoice Date", "Bank Reconciliation Statement",
]

def setup_report_permissions():
    finance_roles = ["Trade - Accountant", "Trade - Manager"]
    for report_name in FINANCE_REPORTS:
        if not frappe.db.exists("Report", report_name):
            continue
        doc = frappe.get_doc("Report", report_name)
        existing_roles = {row.role for row in doc.get("roles", [])}
        changed = False
        for role in finance_roles:
            if role not in existing_roles:
                doc.append("roles", {"role": role})
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
```

**Why only Accountant and Manager:** Sales/Purchase Executives and Warehouse Staff have no
business need for P&L, Balance Sheet, or cash flow reports. Giving them report access would
expose financial data outside their operational domain.

---

## 6. Workflow Approval Gates

### Business rationale

High-value transactions (large purchase orders, significant payments, customer shipments) should
require a second set of eyes before being financially committed. A Sales Executive should not
be able to unilaterally post a $500,000 Sales Order. A Frappe workflow enforces this by
requiring a Manager to explicitly approve before the document reaches submitted (docstatus=1)
state.

### How Frappe workflows work

A `Workflow` DocType defines:
- `states`: a list of states, each with a `doc_status` (0=Draft, 1=Submitted, 2=Cancelled)
  and `allow_edit` (the role allowed to edit the document while in this state)
- `transitions`: edges between states; each has `action` (button label), `allowed` (role who
  can trigger the transition), and `next_state`

The workflow adds a `workflow_state` field to the document. Frappe's workflow engine:
1. Replaces the standard Submit button with workflow action buttons
2. Checks the current state's `allow_edit` role before allowing any field edits
3. Checks the transition's `allowed` role before processing the action
4. Sets `docstatus` to the target state's `doc_status` when the transition fires

Setting `override_status: 0` means the workflow state and the document status coexist — the
workflow controls the approval gate while the document status (docstatus) governs whether the
document is legally posted in the ledger.

### The three workflows

#### Trade SO Approval (Sales Order)

```
Draft         [allow_edit: Sales Executive, doc_status: 0]
  ↓ "Submit for Approval" [allowed: Sales Executive]
Pending Approval [allow_edit: Manager, doc_status: 0]
  ↓ "Approve" [allowed: Manager]      ↓ "Reject" [allowed: Manager]
Approved (doc_status: 1)              Rejected (doc_status: 0)
                                        ↓ "Resubmit" [allowed: Sales Executive]
                                      Pending Approval
```

**Business logic:**
- A Sales Executive creates the SO in Draft, fills in items and prices, then submits for approval
- While Pending Approval, only the Manager can edit (prevents the Sales Exec from modifying
  after submission to game the approval)
- Manager approves → SO becomes docstatus=1 (submitted), which triggers stock reservation
  and makes it eligible for Delivery Note creation
- Manager rejects → SO stays Draft-level (docstatus=0) and returns to Sales Exec who can revise
  and resubmit

#### Trade PO Approval (Purchase Order)

Mirrors SO Approval with Purchase Executive in the Sales Executive role. This ensures the
Manager reviews every commitment to a supplier before it is formally placed.

#### Trade Payment Approval (Payment Entry)

```
Draft         [allow_edit: Accountant, doc_status: 0]
  ↓ "Submit for Approval" [allowed: Accountant]
Pending Approval [allow_edit: Manager, doc_status: 0]
  ↓ "Approve" [allowed: Manager]      ↓ "Reject" [allowed: Manager]
Approved (doc_status: 1)              Rejected (doc_status: 0)
```

**Business logic:** The Accountant prepares the payment entry (amount, mode, bank account)
and submits it for approval. The Manager authorises the actual cash movement. This is a
standard **dual-control** pattern for payment processing — the person preparing the payment
cannot also approve it.

### Workflow fixtures

```json
{
  "doctype": "Workflow",
  "name": "Trade SO Approval",
  "document_type": "Sales Order",
  "is_active": 1,
  "override_status": 0,
  "workflow_state_field": "workflow_state",
  "states": [
    {"state": "Draft",            "doc_status": "0", "allow_edit": "Trade - Sales Executive"},
    {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Trade - Manager"},
    {"state": "Approved",         "doc_status": "1", "allow_edit": "Trade - Manager"},
    {"state": "Rejected",         "doc_status": "0", "allow_edit": "Trade - Sales Executive"}
  ],
  "transitions": [
    {"state": "Draft",            "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Trade - Sales Executive"},
    {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Trade - Manager"},
    {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",          "allowed": "Trade - Manager"},
    {"state": "Rejected",         "action": "Resubmit",            "next_state": "Pending Approval", "allowed": "Trade - Sales Executive"}
  ]
}
```

The workflow states are also stored as `Workflow State` fixtures for styling:

```json
[
  {"name": "Draft",            "style": ""},
  {"name": "Pending Approval", "style": "Warning"},
  {"name": "Approved",         "style": "Success"},
  {"name": "Rejected",         "style": "Danger"}
]
```

The `style` value maps to Bootstrap badge colours in the Frappe desk UI.

---

## 7. Credit Limit Business Rule

### Business rationale

In import/export trading, customers often buy on credit — goods are shipped before payment is
received. The company needs to cap its credit exposure per customer. If a customer already has
unpaid invoices totalling close to their credit limit, a new large sales order would push the
total exposure over the limit, creating collection risk.

The credit limit enforces this constraint automatically at the point of order entry, before any
goods are committed.

### Custom field

`trade_credit_limit` (Currency) on the Customer DocType, defined in fixtures:

```json
{
  "doctype": "Custom Field",
  "name": "Customer-trade_credit_limit",
  "dt": "Customer",
  "module": "Trade MVP",
  "fieldname": "trade_credit_limit",
  "label": "Credit Limit",
  "fieldtype": "Currency",
  "insert_after": "customer_group",
  "default": "0",
  "description": "Set to 0 for unlimited credit"
}
```

**Design choice:** Zero means unlimited rather than zero-credit. This is a convention common in
ERP systems — "no limit set" is safer as a default than "credit blocked". A customer with
`trade_credit_limit = 0` can receive any size order.

### Implementation

```python
def check_credit_limit(doc, method=None):
    if not doc.customer:
        return   # Quotation-type SO with no customer yet — skip

    credit_limit = frappe.db.get_value(
        "Customer", doc.customer, "trade_credit_limit"
    ) or 0
    if not credit_limit:
        return   # 0 = unlimited

    # Sum of outstanding (unpaid) submitted Sales Invoices for this customer
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
```

**Key design decisions:**

- **Fires on `validate`, not `on_submit`:** The check runs every time the SO is saved, not
  just when submitted. This gives early feedback — the user cannot even save a new SO that
  would breach the limit, preventing them from investing time filling in details on a blocked
  order.

- **Only counts `docstatus = 1` (submitted) invoices:** Draft or cancelled invoices don't
  represent real outstanding debt. Only posted, unpaid invoices count against the limit.

- **`outstanding_amount > 0` filter:** Fully paid invoices have `outstanding_amount = 0` after
  payment is reconciled. These should not block new orders.

- **`grand_total or 0`:** Guard against None if the SO has no items yet.

- **Hooked via `doc_events`:** The hook in `hooks.py` is declared as:
  ```python
  doc_events = {
      "Sales Order": {"validate": "trade_mvp.setup.check_credit_limit"}
  }
  ```
  Frappe calls this function automatically on every Sales Order save — the logic lives entirely
  in trade_mvp and requires no modification to ERPNext's Sales Order code.

### Demo customer credit limits

```python
DEMO_CUSTOMERS = [
    {"customer_name": "Alpha Imports Ltd",  "credit_limit": 100_000},  # ₹1 lakh limit
    {"customer_name": "Beta Trading Co",    "credit_limit": 75_000},   # ₹75k limit
    {"customer_name": "Gamma Distributors", "credit_limit": 0},        # unlimited
]
```

### Unit tests

The credit limit logic is unit-tested in isolation using a mocked `frappe` module:

```python
# tests/test_credit_limit.py

def test_unlimited_credit_passes(self):
    """credit_limit=0 means unlimited — must not raise"""
    _frappe_mock.db.get_value.return_value = 0
    check_credit_limit(self._make_so("CUST-001", 999_999))
    _frappe_mock.throw.assert_not_called()

def test_over_limit_throws(self):
    """outstanding=40k, SO=20k, limit=50k — must call frappe.throw"""
    _frappe_mock.db.get_value.return_value = 50_000
    _frappe_mock.db.sql.return_value = [[40_000]]
    _frappe_mock.throw.side_effect = Exception("credit limit exceeded")
    with self.assertRaises(Exception):
        check_credit_limit(self._make_so("CUST-001", 20_000))
    _frappe_mock.throw.assert_called_once()

def test_exactly_at_limit_passes(self):
    """outstanding=50k, SO=0, limit=50k — equal to limit must pass (not strictly greater)"""
    _frappe_mock.db.get_value.return_value = 50_000
    _frappe_mock.db.sql.return_value = [[50_000]]
    check_credit_limit(self._make_so("CUST-001", 0))
    _frappe_mock.throw.assert_not_called()
```

The test file installs the mock before importing `trade_mvp.setup`, ensuring the module
resolves `frappe` to the mock throughout all test cases.

---

## 8. Custom Fields

### Trade-specific transaction fields

Three fields are added to Quotation, Sales Order, and Purchase Order:

```json
[
  {"dt": "Sales Order",    "fieldname": "port_of_loading",  "label": "Port of Loading",  "fieldtype": "Data", "insert_after": "incoterm"},
  {"dt": "Sales Order",    "fieldname": "port_of_discharge", "label": "Port of Discharge","fieldtype": "Data", "insert_after": "port_of_loading"},
  {"dt": "Sales Order",    "fieldname": "lc_number",         "label": "LC Number",        "fieldtype": "Data", "insert_after": "port_of_discharge"},
  {"dt": "Purchase Order", "fieldname": "port_of_loading",  ...},
  {"dt": "Purchase Order", "fieldname": "port_of_discharge", ...},
  {"dt": "Purchase Order", "fieldname": "lc_number",         ...},
  {"dt": "Quotation",      "fieldname": "port_of_loading",  ...},
  {"dt": "Quotation",      "fieldname": "port_of_discharge", ...},
  {"dt": "Quotation",      "fieldname": "lc_number",         ...}
]
```

All three are inserted after the existing `incoterm` field, grouping them logically with
the shipping terms section.

**Port of Loading / Port of Discharge:** Required for customs declarations, shipping
documentation (Bill of Lading), and logistics coordination. The export country's customs
authority and the import country's customs authority both require these on commercial documents.

**LC Number:** A Letter of Credit is a bank guarantee where the buyer's bank promises to pay
the seller upon presentation of shipping documents. The LC number ties the financial instrument
to the commercial transaction and must appear on invoices, packing lists, and shipping documents
to enable payment.

### Why `module: "Trade MVP"` on Custom Fields

The fixtures filter is `[["module", "=", "Trade MVP"]]`. Setting `module` on Custom Fields
ensures they are included in the fixture export and can be cleanly identified as belonging to
this app. Without this, `bench export-fixtures` would not know which custom fields to export.

---

## 9. UI Layer (Client-side)

### JavaScript: role detection and body class

```javascript
// trade_mvp/public/js/trade_mvp.js
frappe.provide("trade_mvp");

frappe.ready(function () {
    const tradeRoles = [
        "Trade - Sales Executive",
        "Trade - Purchase Executive",
        "Trade - Warehouse Staff",
        "Trade - Accountant",
        "Trade - Manager",
    ];

    const isTradeUser = tradeRoles.some((r) => frappe.user_roles.includes(r));
    if (!isTradeUser) return;

    // Add CSS hook for targeted styling
    document.body.classList.add("trade-minimal");

    // Hide Help and Explore nav items after AJAX is ready
    frappe.after_ajax(function () {
        $('[data-label="Help"]').closest(".nav-item").hide();
        $('[data-label="Explore"]').closest(".nav-item").hide();
    });
});
```

`frappe.user_roles` is populated from the bootinfo and contains the current user's role list.
The check runs client-side — it's purely for UX, not security. `frappe.after_ajax` defers the
DOM manipulation until after Frappe's initial AJAX setup completes, ensuring the nav items
exist before trying to hide them.

### CSS: declarative hiding

```css
/* trade_mvp/public/css/trade_mvp.css */
body.trade-minimal .navbar-help,
body.trade-minimal [data-label="Help"],
body.trade-minimal [data-label="Explore"] {
    display: none !important;
}
```

The CSS provides belt-and-suspenders coverage: even if the jQuery `.hide()` call in the JS
fails for any reason (timing, selector change), the CSS ensures the items remain hidden as
long as `body.trade-minimal` is present.

**Why hide Help and Explore:** The Help menu links to ERPNext documentation and community
forums. The Explore menu shows all installed DocTypes across all modules. Both would allow a
trade user to navigate to ERPNext modules they don't have permission to use, breaking the
focused UX. The DocPerm system would still block access, but the experience would be
confusing — the user sees a menu item, clicks it, and gets a permission error.

**This is purely cosmetic.** Removing these elements via browser devtools would reveal the
menus, but navigating to a blocked DocType would still yield a permission error from the server.

---

## 10. Installation Sequence

The `after_install()` function orchestrates the entire setup. The order is strictly defined
because each step has dependencies on the previous one.

```python
def after_install():
    # Step 1 — Sync fixtures FIRST
    # Frappe normally runs sync_fixtures AFTER after_install. But setup_permissions()
    # needs the Role records to exist before it can create Custom DocPerm rows.
    # Manually triggering sync_fixtures here solves this chicken-and-egg problem.
    # in_migrate flag suppresses workspace route conflict validation.
    from frappe.utils.fixtures import sync_fixtures
    frappe.flags.in_migrate = True
    try:
        sync_fixtures("trade_mvp")
    finally:
        frappe.flags.in_migrate = False

    # Step 2 — Hide ERPNext workspaces
    # Must run before creating desktop icons so hidden workspaces don't get icons.
    hide_default_workspaces()

    # Step 3 — Create Custom DocPerm rows for all trade roles
    setup_permissions()

    # Step 4 — Add trade roles to financial Report.roles tables
    setup_report_permissions()

    # Step 5 — Create the "Trade User" Module Profile
    setup_module_profiles()

    # Step 6 — Hide irrelevant fields via Property Setter
    setup_property_setters()

    # Step 7 — Populate Workspace Sidebar items
    setup_workspace_sidebars()

    frappe.db.commit()   # commit all of the above before running Frappe stdlib

    # Step 8 — Create Workspace Sidebar and Desktop Icon records
    from frappe.desk.doctype.desktop_icon.desktop_icon import create_desktop_icons_from_workspace
    from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import create_workspace_sidebar_for_workspaces
    create_workspace_sidebar_for_workspaces()
    create_desktop_icons_from_workspace()

    # Step 9 — Clear module field on trade workspaces
    # Frappe's Workspace.__init__ checks workspace.module in user.allow_modules.
    # "Trade MVP" has no DocTypes so it never appears in allow_modules.
    # Clearing module bypasses the check, making trade workspaces always visible
    # to users whose bootinfo has been filtered to include them.
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

    # Step 10 — Flush Redis to eliminate stale desktop icon cache
    frappe.cache.flushall()
```

### `hide_default_workspaces`

```python
def hide_default_workspaces():
    placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
    frappe.db.sql(
        f"UPDATE `tabWorkspace` SET is_hidden = 1 "
        f"WHERE name NOT IN ({placeholders}) AND name != 'Workspace'",
        TRADE_WORKSPACES,
    )
```

Sets `is_hidden = 1` on every non-trade workspace (Accounting, Selling, Buying, CRM, Stock,
etc.). The `name != 'Workspace'` exclusion preserves the built-in workspace management page
that administrators need. This is a direct SQL UPDATE rather than a Frappe ORM operation for
performance — there can be 30+ workspaces to hide.

---

## 11. Demo Data

```python
# demo.py — run via: bench --site frappe_mvp.localhost execute trade_mvp.demo.create_demo_data

DEMO_USERS = [
    {"email": "sales@trade.local",     "role": "Trade - Sales Executive",    "first_name": "Sarah"},
    {"email": "purchase@trade.local",  "role": "Trade - Purchase Executive", "first_name": "Peter"},
    {"email": "warehouse@trade.local", "role": "Trade - Warehouse Staff",    "first_name": "Wes"},
    {"email": "accounts@trade.local",  "role": "Trade - Accountant",         "first_name": "Anna"},
    {"email": "manager@trade.local",   "role": "Trade - Manager",            "first_name": "Mike"},
]
# Password for all: Trade@1234
```

Each user maps 1:1 to a Trade role, allowing clean testing of role-based behaviour. The
`send_welcome_email = 0` flag prevents the email sending step, which would fail in a local
development environment with no mail server configured.

---

## 12. Permission Summary Table

| Layer | Mechanism | DocType / Location | Scope | Type |
|-------|-----------|-------------------|-------|------|
| 1a | Custom DocPerm (TRADE_PERMISSIONS) | `tabCustom DocPerm` | Per-role R/W/CRUD on operational DocTypes | Security |
| 1b | Custom DocPerm (TRADE_READ_REFS) | `tabCustom DocPerm` | Read-only on ~50 reference DocTypes, all roles | Security |
| 2 | Module Profile | `tabModule Profile` | Blocks ERPNext module workspace icons | UX + partial security |
| 3 | boot_session hook | Python (filter_bootinfo_for_trade_users) | Strips non-allowed workspaces/icons/sidebar from bootinfo | Security |
| 4 | Property Setter | `tabProperty Setter` | Hides specific fields globally across all users | UX only |
| 5 | Report.roles | `tabReport` (roles child table) | Allows financial report execution for Accountant + Manager | Security |
| 6 | Workflow | `tabWorkflow` | Enforces Manager approval gate on SO, PO, Payment Entry | Business control |
| 7 | doc_events validate hook | Python (check_credit_limit) | Blocks SO save when customer exceeds credit limit | Business rule |
| 8 | Client JS + CSS | trade_mvp.js / trade_mvp.css | Hides Help and Explore nav items | UX only |

**Layers 1, 3, and 5 are the true security boundaries.** Every other layer is either a UX
improvement or a business rule that operates within the permission envelope.

A user with zero JavaScript and direct API access (e.g., via curl) is still constrained by
Layers 1, 5, and the credit limit hook. A user with a browser and devtools can bypass Layers
2, 4, 6, 7, and 8 locally, but the server will still enforce Layers 1, 3, and 5.
