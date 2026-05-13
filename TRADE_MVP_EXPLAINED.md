# Trade MVP — Complete Technical Reference
### From Frappe Framework Basics to Full Customisation

---

## Table of Contents

1. [What is Frappe Framework?](#1-what-is-frappe-framework)
2. [What is ERPNext?](#2-what-is-erpnext)
3. [The Bench — How Everything is Organised](#3-the-bench)
4. [Core Frappe Concepts](#4-core-frappe-concepts)
   - 4.1 DocType
   - 4.2 Document
   - 4.3 Hooks
   - 4.4 Fixtures
   - 4.5 Roles and Permissions
   - 4.6 Workspaces
   - 4.7 Workflows
   - 4.8 Boot Session
   - 4.9 Property Setters
   - 4.10 Module Profiles
5. [The trade_mvp App](#5-the-trade_mvp-app)
6. [Category 1 — Default ERP Settings Used](#6-default-erp-settings-used)
7. [Category 2 — Customisations Made](#7-customisations-made)
   - 7.1 App Scaffolding (hooks.py)
   - 7.2 Custom Roles (Fixtures)
   - 7.3 Custom Fields (Fixtures)
   - 7.4 Approval Workflows (Fixtures)
   - 7.5 Install-time Setup (setup.py)
   - 7.6 Runtime Boot Filter
   - 7.7 Credit Limit Enforcement
   - 7.8 Frontend Customisation
   - 7.9 Workspaces
   - 7.10 Demo Data
8. [How Everything Connects — End-to-End Flow](#8-how-everything-connects)
9. [File Reference Map](#9-file-reference-map)

---

## 1. What is Frappe Framework?

Frappe is a full-stack, open-source web application framework built in Python (backend) and JavaScript (frontend). It was created specifically to make building business applications fast — think of it as a framework that combines a database ORM, a REST API layer, a UI renderer, and a permission system all in one.

### Key ideas in Frappe

**Everything is a DocType.** A DocType is Frappe's equivalent of a database table combined with a form definition. When you define a DocType, Frappe:
- Creates the actual MariaDB table automatically
- Generates a REST API for it (`/api/resource/DocType Name`)
- Renders a form UI for it in the browser
- Applies permissions to it

**The desk.** When you log in to a Frappe app, you see the "desk" — a single-page React-like web application. All navigation, forms, lists, and reports are rendered inside the desk without page reloads.

**Python + JavaScript, side by side.** Business logic lives in Python on the server. The desk UI is JavaScript. Frappe provides a clean bridge: `frappe.call()` in JS hits a whitelisted Python function on the server.

**MariaDB as the database.** All DocType data is stored in MariaDB. Table names follow the pattern `` `tabDocType Name` `` (e.g., `` `tabSales Order` ``).

---

## 2. What is ERPNext?

ERPNext is a complete ERP (Enterprise Resource Planning) application built on top of Frappe. It adds hundreds of pre-built DocTypes covering:

- **CRM** — Leads, Opportunities
- **Sales** — Quotations, Sales Orders, Delivery Notes, Sales Invoices
- **Purchasing** — Purchase Orders, Purchase Receipts, Purchase Invoices
- **Stock** — Warehouses, Items, Stock Entries
- **Accounts** — Payment Entries, General Ledger, Financial Statements
- **HR, Payroll, Manufacturing, Projects, Assets** — and more

ERPNext is the base. trade_mvp sits on top of ERPNext and shapes it into a focused import/export trading tool.

---

## 3. The Bench

The **bench** is Frappe's project management CLI tool. It manages apps, sites, processes, and dependencies.

### Folder structure of this bench

```
/home/manu/Desktop/frappe_mvp/          ← bench root
│
├── apps/                               ← source code for every installed app
│   ├── frappe/                         ← the framework itself
│   ├── erpnext/                        ← the ERP application
│   ├── india_compliance/               ← GST/Indian tax compliance
│   └── trade_mvp/                      ← our custom app (this repo)
│
├── sites/
│   └── frappe_mvp.localhost/           ← one site (one MariaDB database)
│       ├── site_config.json            ← DB credentials, site settings
│       └── public/                     ← uploaded files, assets
│
├── config/
│   ├── redis_cache.conf                ← Redis on port 13001 (cache)
│   └── redis_queue.conf                ← Redis on port 11001 (background jobs)
│
├── env/                                ← Python 3.14 virtualenv
├── Procfile                            ← process definitions (web, socketio, workers)
└── setup_bench.sh                      ← provisioning script
```

### Key bench commands

```bash
bench start                             # starts all processes (web, workers, Redis)
bench install-app trade_mvp             # installs an app on the site
bench migrate                           # applies schema changes and patches
bench export-fixtures                   # exports fixture records to JSON files
bench execute trade_mvp.demo.create_demo_data   # run any Python function
bench clear-cache                       # flush Redis cache
```

### How the web server works

`Procfile` starts a Gunicorn process on port 8001. Every HTTP request goes through Frappe's router, which maps URLs to Python controllers. The desk (frontend) is a compiled JS/CSS bundle served as static files.

---

## 4. Core Frappe Concepts

### 4.1 DocType

A DocType is the single most important concept in Frappe. It defines:

1. **The database table** — each field becomes a column (or a child table)
2. **The form UI** — field order, labels, fieldtypes (Data, Link, Currency, Table, etc.)
3. **Permissions** — which roles can read, write, create, delete, submit, cancel, amend
4. **Hooks** — which Python functions to call on validate, before_insert, on_submit, etc.

#### Example: the Sales Order DocType

The Sales Order DocType exists in ERPNext. It has ~100 fields: customer, transaction date, delivery date, items table, taxes table, total, grand_total, and many more. When a user opens a Sales Order form in the browser, Frappe reads the DocType definition and renders the form dynamically — no hand-written HTML needed.

#### Submitted documents

Some DocTypes are **submittable** (Sales Order, Invoice, Payment Entry). A submitted document has `docstatus = 1` and is immutable — it can only be cancelled. This is important for accounting integrity.

#### Child DocTypes

A DocType can have child tables (e.g., the "Items" table inside a Sales Order). Each child table is its own DocType with a `parent` field pointing back to the parent record.

### 4.2 Document

A Document is one record in a DocType — the equivalent of a database row plus all its child table rows. In Python:

```python
doc = frappe.get_doc("Sales Order", "SO-0001")
doc.customer    # field value
doc.items       # list of child row objects
doc.save()      # write back to DB
doc.submit()    # change docstatus to 1
```

### 4.3 Hooks

`hooks.py` is the app's registration file. It tells Frappe: "when X happens, call my function Y." Hooks make Frappe extensible without modifying core code.

The hooks that trade_mvp uses:

| Hook | When it fires | What trade_mvp does |
|---|---|---|
| `after_install` | Once, when the app is installed | Runs the entire setup: permissions, workspaces, field hiding |
| `boot_session` | Every time any user logs in | Filters the navigation data sent to that user |
| `doc_events` | When a specific DocType event fires | Enforces credit limit on Sales Order save |
| `app_include_js` | Every desk page load | Injects trade_mvp.js |
| `app_include_css` | Every desk page load | Injects trade_mvp.css |
| `fixtures` | On `bench export-fixtures` / `sync_fixtures` | Declares which records are managed as code |

### 4.4 Fixtures

Fixtures are database records that are stored as JSON files and managed alongside your code in version control. Instead of manually creating Roles or Custom Fields through the UI and hoping someone doesn't delete them, you define them in JSON. Frappe's `sync_fixtures()` function reads those JSON files and upserts the records into the database.

**Why this matters:** Without fixtures, configuration lives only in the database. If you reinstall or deploy to a new server, that configuration is lost. Fixtures make configuration reproducible.

```python
# hooks.py
fixtures = [
    {"dt": "Role",           "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field",   "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Pending Approval", "Approved", "Rejected"]]]},
    {"dt": "Workflow",       "filters": [["name", "like", "Trade%"]]},
]
```

Each entry says: "export all records of this DocType matching these filters into a JSON file."

### 4.5 Roles and Permissions

Frappe has a layered permission system.

**Roles** are named groups (e.g., "Accounts User", "Stock User"). A user is assigned one or more roles.

**DocPerm** records say: "Role X can do [read, write, create, delete, submit, cancel, amend] on DocType Y."

There are two kinds:
- **Standard DocPerm** — stored inside the DocType definition itself. Ships with ERPNext.
- **Custom DocPerm** — stored in a separate `tabCustom DocPerm` table. Overrides without touching core.

trade_mvp uses Custom DocPerm exclusively — it never modifies ERPNext's built-in permissions.

**The permission check (simplified):**
When a user tries to open a Sales Order, Frappe checks: does this user have any role that has `read = 1` on "Sales Order" in DocPerm or Custom DocPerm? If yes, allow. If no, raise PermissionError.

### 4.6 Workspaces

A Workspace is a top-level navigation page in the Frappe desk. Think of it as a dashboard/home page for a functional area.

Each Workspace has:
- **Links section** — shortcut cards to DocTypes, Reports, Dashboards
- **Charts** — embedded chart widgets
- **Number Cards** — KPI tiles (e.g., "Annual Sales")
- **Sidebar items** — the left navigation panel when you're inside that workspace

ERPNext ships with ~20 workspaces: Accounts, Stock, Selling, Buying, CRM, Manufacturing, Projects, etc.

Workspaces are stored in the `tabWorkspace` table and in JSON files under the app's `workspace/` directory.

**How Frappe decides what to show:**

At login, `boot.py` calls `load_desktop_data()` which populates the `bootinfo` object with:
1. `workspaces["pages"]` — the list of workspaces for the icon home screen
2. `workspace_sidebar_item` — the left-nav content per workspace
3. `app_data` — the app-switcher tiles (e.g., "ERPNext", "Frappe")
4. `desktop_icons` — the actual icon tiles (populated separately, cached in Redis)

The client JS receives this bootinfo blob and renders the desk accordingly.

### 4.7 Workflows

A Workflow attaches a state machine to any DocType. Instead of a document simply being Draft/Submitted/Cancelled, it can have intermediate states with approval gates.

**Components:**
- **Workflow State** — a named state (Draft, Pending Approval, Approved, Rejected) with a visual style
- **Workflow** — bound to a DocType; defines states and transitions
- **Transition** — "from state A, action X moves to state B, only allowed by Role R"

When a workflow is active on a DocType:
- The document gets a `workflow_state` field
- The form shows action buttons based on which transitions the current user's role can trigger
- `doc_status` is set by the target state definition (0=Draft, 1=Submitted)

### 4.8 Boot Session

The `boot_session` hook fires during login, before the desk loads. It receives a `bootinfo` object — a large dict of everything the client needs to bootstrap the UI (user info, workspaces, permissions, installed apps, etc.).

Your hook function can read and modify `bootinfo` freely. Whatever you return in `bootinfo` is what the client receives. This is the mechanism trade_mvp uses to show each user only the workspaces relevant to their role.

### 4.9 Property Setters

A Property Setter is a database record that overrides a specific property of a specific field on a DocType — without editing the DocType definition itself.

For example: `{"doc_type": "Customer", "field_name": "loyalty_program", "property": "hidden", "value": "1"}` makes the `loyalty_program` field invisible on the Customer form, globally, for all users.

This is the right way to hide fields in ERPNext: you don't modify the Customer DocType source code, you create a Property Setter record.

### 4.10 Module Profiles

A Module Profile is a list of ERPNext modules to **block** for users assigned that profile. When a user has a module profile, the blocked modules disappear from their desk — no workspaces, no navigation links, nothing from those modules shows.

Modules in ERPNext correspond roughly to functional areas: "Accounts", "Stock", "Selling", "CRM", etc.

trade_mvp uses this as a coarse first filter: block all 28 standard ERPNext modules, so none of the default ERPNext navigation leaks through.

---

## 5. The trade_mvp App

trade_mvp is a custom Frappe app that transforms a full ERPNext installation into a focused import/export trading tool. It does not build new DocTypes from scratch — instead, it takes ERPNext's existing DocTypes (Sales Order, Invoice, etc.) and:

1. Creates 5 trade-specific roles
2. Grants those roles exactly the permissions they need (no more)
3. Hides irrelevant fields to reduce form complexity
4. Adds trade-specific fields (port of loading, LC number, credit limit)
5. Creates 6 role-scoped navigation workspaces
6. Enforces approval workflows on key documents
7. Enforces credit limits on Sales Orders

The result: a trade executive sees only their pipeline and orders. An accountant sees only finance. A warehouse person sees only stock movements. None of them can reach manufacturing, HR, payroll, or any other ERPNext module they don't need.

### App location

```
apps/trade_mvp/
└── trade_mvp/                  ← Python package (same name as app)
    ├── hooks.py                ← app registration
    ├── setup.py                ← all setup and business logic
    ├── demo.py                 ← demo data creation
    ├── fixtures/               ← JSON records managed as code
    │   ├── role.json
    │   ├── custom_field.json
    │   ├── workflow_state.json
    │   └── workflow.json
    ├── public/
    │   ├── js/trade_mvp.js     ← client-side customisation
    │   └── css/trade_mvp.css   ← client-side styles
    ├── tests/
    │   └── test_credit_limit.py
    └── trade_mvp/              ← inner module (app name convention)
        └── workspace/          ← 6 workspace JSON definitions
            ├── pipeline/
            ├── sales/
            ├── purchasing/
            ├── warehouse/
            ├── finance/
            └── asset_register/
```

---

## 6. Default ERP Settings Used

These are standard Frappe/ERPNext capabilities that trade_mvp uses as-is, without modification.

### 6.1 Standard DocTypes

All the transactional and master DocTypes come from ERPNext. trade_mvp does not create any new DocTypes — it works with what ERPNext already provides.

#### CRM
| DocType | What it represents |
|---|---|
| Lead | A potential customer who has shown interest |
| Opportunity | A qualified lead with a specific deal in progress |
| Contact | A named person linked to customers/suppliers |
| Address | Physical or billing address linked to any party |

#### Sales Cycle
| DocType | Stage in the cycle |
|---|---|
| Quotation | Price offer sent to a potential customer |
| Sales Order | Confirmed order from a customer |
| Delivery Note | Record of goods shipped to the customer |
| Sales Invoice | Bill sent to the customer; creates an accounting entry |

#### Purchase Cycle
| DocType | Stage in the cycle |
|---|---|
| Purchase Order | Confirmed order placed with a supplier |
| Purchase Receipt | Record of goods received from the supplier |
| Purchase Invoice | Bill received from the supplier; creates an accounting entry |

#### Finance
| DocType | Purpose |
|---|---|
| Payment Entry | Records payment made or received; settles invoices |
| Bank Account | Links to the company's actual bank account |

#### Asset Management
| DocType | Purpose |
|---|---|
| Asset | A fixed asset (machinery, vehicle, equipment) |
| Asset Category | Groups assets for depreciation settings |
| Asset Movement | Records physical movement of an asset between locations |

#### Stock
| DocType | Purpose |
|---|---|
| Stock Entry | Internal material movement (receipt, transfer, issue) |
| Item | A product or service that can be bought or sold |
| Warehouse | A physical or logical storage location |

### 6.2 The Standard Permission System

trade_mvp uses Frappe's Custom DocPerm table. The system already exists — trade_mvp just populates it with the right role/doctype combinations.

### 6.3 The Workspace and Boot System

The workspace rendering, sidebar, desktop icons, and boot session infrastructure all come from Frappe. trade_mvp plugs into it via the `boot_session` hook.

### 6.4 The Workflow Engine

The workflow engine (state machine, action buttons, state field) is built into Frappe. trade_mvp only provides the workflow definitions as fixture JSON.

### 6.5 Financial Reports

ERPNext ships ~50 financial reports. trade_mvp grants access to 15 of them for Accountant and Manager roles. The reports themselves are not modified.

---

## 7. Customisations Made

### 7.1 App Scaffolding — `hooks.py`

```
apps/trade_mvp/trade_mvp/hooks.py
```

This file is the entry point Frappe reads when the app is installed. It registers everything:

```python
app_name        = "trade_mvp"
app_title       = "Trade MVP"
app_description = "Import/export trading app built on ERPNext"

# Inject into every desk page
app_include_js  = "/assets/trade_mvp/js/trade_mvp.js"
app_include_css = "/assets/trade_mvp/css/trade_mvp.css"

# Run once on install
after_install   = "trade_mvp.setup.after_install"

# Run every time a user logs in
boot_session    = "trade_mvp.setup.filter_bootinfo_for_trade_users"

# Run every time a Sales Order is validated/saved
doc_events = {
    "Sales Order": {
        "validate": "trade_mvp.setup.check_credit_limit"
    }
}

# Records managed as version-controlled JSON
fixtures = [
    {"dt": "Role",           "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field",   "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Pending Approval", "Approved", "Rejected"]]]},
    {"dt": "Workflow",       "filters": [["name", "like", "Trade%"]]},
]
```

---

### 7.2 Custom Roles — `fixtures/role.json`

5 roles are defined. `desk_access = 1` means the role grants access to the desk (the web UI) — without this, users with only this role would be locked to the portal/website, not the admin desk.

```json
[
  {"name": "Trade - Sales Executive",    "desk_access": 1},
  {"name": "Trade - Purchase Executive", "desk_access": 1},
  {"name": "Trade - Warehouse Staff",    "desk_access": 1},
  {"name": "Trade - Accountant",         "desk_access": 1},
  {"name": "Trade - Manager",            "desk_access": 1}
]
```

**Role design rationale:**

| Role | Functional scope |
|---|---|
| Trade - Sales Executive | CRM pipeline, quotations, orders |
| Trade - Purchase Executive | Procurement only |
| Trade - Warehouse Staff | Physical stock movement only |
| Trade - Accountant | Invoices, payments, assets |
| Trade - Manager | Everything — oversight and approvals |

---

### 7.3 Custom Fields — `fixtures/custom_field.json`

Custom fields extend existing DocTypes without touching ERPNext source code. Frappe stores them in `` `tabCustom Field` `` and injects them into the form at runtime.

10 fields across 4 DocTypes, all tagged `"module": "Trade MVP"` so the fixtures filter picks them up.

#### Trade-specific shipping fields (9 fields)

Added to Sales Order, Purchase Order, and Quotation — all three transactional documents that involve shipment.

| Field | Label | Purpose |
|---|---|---|
| `port_of_loading` | Port of Loading | Origin port for the shipment |
| `port_of_discharge` | Port of Discharge | Destination port |
| `lc_number` | LC Number | Letter of Credit reference number |

These fields are positioned after the `incoterm` field (International Commercial Terms — already in ERPNext) because they are logically related to shipping terms.

#### Credit limit field (1 field)

Added to the Customer DocType:

| Field | Label | Type | Default | Note |
|---|---|---|---|---|
| `trade_credit_limit` | Credit Limit | Currency | 0 | 0 means unlimited |

This field is what the `check_credit_limit` function reads. Storing it on Customer (rather than in a separate DocType) keeps the data model simple.

---

### 7.4 Approval Workflows — `fixtures/workflow.json`

Three workflows, one for each key financial transaction. All follow the same 4-state, 4-transition pattern.

#### Workflow States (`fixtures/workflow_state.json`)

| State | Style (badge colour) |
|---|---|
| Draft | (default/grey) |
| Pending Approval | Warning (yellow) |
| Approved | Success (green) |
| Rejected | Danger (red) |

#### Trade SO Approval (Sales Order)

```
States:
  Draft            → doc_status=0, editable by: Trade - Sales Executive
  Pending Approval → doc_status=0, editable by: Trade - Manager
  Approved         → doc_status=1, editable by: Trade - Manager
  Rejected         → doc_status=0, editable by: Trade - Sales Executive

Transitions:
  Draft            --[Submit for Approval]--> Pending Approval  (Sales Executive)
  Pending Approval --[Approve]-------------> Approved           (Manager)
  Pending Approval --[Reject]--------------> Rejected           (Manager)
  Rejected         --[Resubmit]------------> Pending Approval   (Sales Executive)
```

**What this achieves:** A sales executive cannot submit (lock) a Sales Order on their own. They must route it to the manager for approval. Only after approval does the document reach `doc_status=1` (submitted/immutable).

#### Trade PO Approval (Purchase Order)

Same pattern — Purchase Executive initiates, Manager approves.

#### Trade Payment Approval (Payment Entry)

Same pattern — Accountant initiates, Manager approves. Prevents payments being made without management sign-off.

---

### 7.5 Install-time Setup — `setup.py`

Everything in this file runs once when `bench install-app trade_mvp` is executed. The entry point is `after_install()`.

#### Execution sequence

```
after_install()
│
├── 1. sync_fixtures("trade_mvp")
│       Pushes the JSON fixtures (roles, fields, workflows) into the database.
│       Must run FIRST because later steps reference the Role records.
│
├── 2. hide_default_workspaces()
│       SQL UPDATE: sets is_hidden=1 on all ERPNext workspaces.
│       The 6 trade workspaces are excluded from this UPDATE.
│
├── 3. setup_permissions()
│       Creates Custom DocPerm rows for all 5 roles across ~20 DocTypes.
│       Also grants read-only access to 50+ master/reference DocTypes.
│
├── 4. setup_report_permissions()
│       Grants 15 financial reports to Accountant and Manager roles.
│
├── 5. setup_module_profiles()
│       Creates the "Trade User" Module Profile blocking 28 modules.
│
├── 6. setup_property_setters()
│       Hides ~60 fields across 12 DocTypes using Property Setter records.
│
├── 7. setup_workspace_sidebars()
│       Populates Workspace Sidebar records with the correct navigation items.
│
├── 8. create_workspace_sidebar_for_workspaces() [Frappe built-in]
│
├── 9. create_desktop_icons_from_workspace() [Frappe built-in]
│
├── 10. SQL fix: UPDATE tabWorkspace SET module='' WHERE name IN (trade workspaces)
│       Clears the module field so Frappe doesn't apply the allow_modules check.
│
├── 11. SQL fix: UPDATE tabWorkspace Sidebar SET module=NULL WHERE title IN (...)
│       Same fix for sidebar records.
│
└── 12. frappe.cache.flushall()
        Clears Redis so stale data doesn't persist.
```

#### Step 2: Hiding default workspaces

```python
# setup.py:399
def hide_default_workspaces():
    placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
    frappe.db.sql(
        f"UPDATE `tabWorkspace` SET is_hidden = 1 "
        f"WHERE name NOT IN ({placeholders}) AND name != 'Workspace'",
        TRADE_WORKSPACES,
    )
```

All ~20 stock ERPNext workspaces (Accounts, Stock, Selling, etc.) are hidden in a single SQL statement. Only the 6 trade workspaces survive.

#### Step 3: Permissions

```python
# setup.py:446
def setup_permissions():
    for role, perms in TRADE_PERMISSIONS.items():
        for (doctype, read, write, create, delete, submit, cancel, amend) in perms:
            _upsert_perm(doctype, role, {...})

    # Also grant read-only on all reference/master DocTypes
    for doctype in TRADE_READ_REFS:
        for role in TRADE_ROLES:
            _upsert_perm(doctype, role, read_only)
```

`_upsert_perm` checks whether a Custom DocPerm row already exists for that role+doctype combination. If it does, it updates it. If not, it inserts a new one. This makes the function idempotent — safe to run multiple times.

**Full permission matrix:**

| DocType | Sales Exec | Purchase Exec | Warehouse | Accountant | Manager |
|---|---|---|---|---|---|
| Lead | RWC | — | — | — | RWCD |
| Opportunity | RWC | — | — | — | RWCD |
| Quotation | RWC+SCA | — | — | — | RWCD+SCA |
| Sales Order | RWC+SCA | R | R | R | RWCD+SCA |
| Purchase Order | R | RWC+SCA | R | R | RWCD+SCA |
| Purchase Receipt | — | R | RWC+SCA | R | RWCD+SCA |
| Delivery Note | R | — | RWC+SCA | R | RWCD+SCA |
| Sales Invoice | R | — | — | RWC+SCA | RWCD+SCA |
| Purchase Invoice | — | R | — | RWC+SCA | RWCD+SCA |
| Payment Entry | — | — | — | RWC+SCA | RWCD+SCA |
| Customer | RWC | R | R | R | RWCD |
| Supplier | R | RWC | R | R | RWCD |
| Item | R | R | R | R | RWCD |
| Asset | — | — | — | RWC+SCA | RWCD+SCA |

R=Read, W=Write, C=Create, D=Delete, S=Submit, Ca=Cancel, A=Amend

**Why read-only on master DocTypes (TRADE_READ_REFS)?**

When a user opens a Sales Order form, the form tries to read linked records: Territory, Customer Group, Price List, Currency, UOM, Cost Center, Account, etc. If the user's role doesn't have at least `read = 1` on these DocTypes, Frappe throws a PermissionError and the form breaks. The 50+ entries in `TRADE_READ_REFS` ensure every trade role can read all the link targets that appear in transactional forms.

#### Step 4: Report permissions

```python
# setup.py:467
def setup_report_permissions():
    finance_roles = ["Trade - Accountant", "Trade - Manager"]
    for report_name in FINANCE_REPORTS:
        doc = frappe.get_doc("Report", report_name)
        for role in finance_roles:
            if role not in existing_roles:
                doc.append("roles", {"role": role})
        doc.save(ignore_permissions=True)
```

ERPNext's financial reports (General Ledger, Trial Balance, etc.) are restricted by default to "Accounts User" and "Accounts Manager" roles. This step adds the trade roles to the `Report.roles` child table so they can run those reports.

15 reports granted: General Ledger, Trial Balance, Profit and Loss Statement, Balance Sheet, Cash Flow, Accounts Receivable, Accounts Receivable Summary, Accounts Payable, Accounts Payable Summary, Customer Ledger Summary, Supplier Ledger Summary, Gross Profit, Sales Invoice Trends, Purchase Invoice Trends, Bank Reconciliation Statement.

#### Step 5: Module Profile

```python
# setup.py:483
def setup_module_profiles():
    if frappe.db.exists("Module Profile", "Trade User"):
        return
    profile = frappe.new_doc("Module Profile")
    profile.module_profile_name = "Trade User"
    for module in BLOCK_MODULES:
        profile.append("block_modules", {"module": module})
    profile.insert(ignore_permissions=True)
```

Creates one Module Profile called "Trade User" that blocks 28 modules:

```
Accounts, Stock, Selling, Buying, CRM,
Manufacturing, Projects, HR, Payroll, Assets,
Support, Quality Management, Subcontracting,
ERPNext Integrations, Regional,
Build, Integrations, Website,
Core, Email, Automation, Desk, Custom,
Geo, Printing, Workflow
```

**Why block all of these?** Without this, a trade user could navigate to the ERPNext Accounts module and see the full accounts workspace, or go to HR and see payroll. Blocking all standard modules ensures the user only sees what's in the 6 trade workspaces.

This profile needs to be assigned to each trade user (done at user creation in demo.py or manually in the UI).

#### Step 6: Property Setters (field hiding)

```python
# setup.py:493
def setup_property_setters():
    for doctype, fields in HIDE_FIELDS.items():
        for fieldname in fields:
            _safe_hide_field(doctype, fieldname)

def _safe_hide_field(doctype, fieldname):
    # Check field exists before creating setter (avoids errors on schema mismatches)
    if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
        return
    # Upsert the Property Setter record
    frappe.make_property_setter({
        "doctype": doctype, "fieldname": fieldname,
        "property": "hidden", "value": "1", "property_type": "Check",
    })
```

Fields hidden per DocType:

| DocType | Hidden fields | Reason |
|---|---|---|
| Customer | loyalty_program, loyalty_program_tier, sales_team, default_sales_partner, default_commission_rate, account_manager, market_segment, language, customer_details, industry, website, lead_name | Loyalty programs and sales commissions are not used in trade |
| Supplier | default_bank_account, payment_terms, represents_company, is_transporter, language, website, supplier_details, warn_rfqs, warn_pos, prevent_rfqs, prevent_pos | Transporter and RFQ warning features not needed |
| Item | brand, shelf_life_in_days, end_of_life, has_serial_no, has_batch_no, has_variants, is_sub_contracted_item, reorder_levels, inspection_required_before_purchase, inspection_required_before_delivery, quality_inspection_template, is_fixed_asset, auto_create_assets | Serialisation, batch tracking, quality inspection not used |
| Quotation | order_type, language, auto_repeat, utm_source, utm_campaign, utm_medium, utm_content, referral_sales_partner | UTM tracking and marketing attribution not relevant |
| Sales Order | utm_source/campaign/medium/content, commission_rate, total_commission, sales_team, auto_repeat, skip_delivery_note, is_internal_customer, represents_company, dispatch_address_name, dispatch_address, cost_center | Commissions, internal trading, cost centre allocation not needed |
| Purchase Order | buying_price_list, price_list_currency, supplier_warehouse, auto_repeat, is_subcontracted, order_confirmation_no/date | Subcontracting not used |
| Delivery Note | lr_no/date, vehicle_no, driver_name, transporter, transporter_name, instructions, commission_rate, sales_team, is_internal_customer, language, letter_head | Transporter-specific fields not needed |
| Purchase Receipt | rejected_warehouse, supplier_delivery_note, is_subcontracted, supplier_warehouse, language, letter_head | Subcontracting not used |
| Sales Invoice | project, commission_rate, total_commission, loyalty_program, sales_partner, sales_team, utm fields, language, letter_head | Same pattern |
| Purchase Invoice | project, language, letter_head, is_subcontracted, supplier_warehouse | Simplified |
| Payment Entry | project, cost_center, letter_head, print_heading, auto_repeat | Simplified |
| Asset | next_depreciation_date, default_finance_book, booked_fixed_asset | Depreciation scheduling simplified |

#### Steps 7–9: Workspace and sidebar wiring

```python
# setup.py:407
def setup_workspace_sidebars():
    for ws_name, items in SIDEBAR_ITEMS.items():
        doc = frappe.get_doc("Workspace Sidebar", ws_name)
        doc.set("items", [])
        for label, item_type, link_to in items:
            if item_type == "Section Break":
                doc.append("items", {"type": "Section Break", "collapsible": 1, "label": label})
            else:
                doc.append("items", {"type": "Link", "link_type": item_type, "link_to": link_to, ...})
        doc.save(ignore_permissions=True)
```

Then Frappe's own `create_workspace_sidebar_for_workspaces()` and `create_desktop_icons_from_workspace()` are called to generate the sidebar records and desktop icon records from the workspace JSON definitions.

#### Steps 10–11: The module field fix

```python
# setup.py:386
frappe.db.sql(
    "UPDATE `tabWorkspace` SET module = '' WHERE name IN (...)", TRADE_WORKSPACES
)
frappe.db.sql(
    "UPDATE `tabWorkspace Sidebar` SET module = NULL WHERE title IN (...)", TRADE_WORKSPACES
)
```

**Why is this needed?** When Frappe renders a workspace, it checks `workspace.module` against the user's `allow_modules` list. `allow_modules` is built from DocTypes installed in the app. Since trade_mvp has no DocTypes of its own, "Trade MVP" never appears in `allow_modules`. If `module` is set to "Trade MVP", every trade workspace would be silently excluded.

Setting `module` to empty string (or NULL for sidebar) makes Frappe skip the `allow_modules` check entirely for those records — they are always included.

---

### 7.6 Runtime Boot Filter — `filter_bootinfo_for_trade_users`

```
apps/trade_mvp/trade_mvp/setup.py:520
```

This function fires on every user login, after Frappe has assembled the full bootinfo object.

```python
def filter_bootinfo_for_trade_users(bootinfo):
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return                                      # don't filter admin

    user_trade_roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "role": ["in", TRADE_ROLES]},
        pluck="role",
    )
    if not user_trade_roles:
        return                                      # not a trade user, don't filter

    # compute the set of workspaces this user is allowed to see
    allowed = set()
    for role in user_trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))

    _filter_workspaces(bootinfo, allowed)           # workspace icon screen
    _filter_desktop_icons(bootinfo, allowed)        # desktop icon tiles (Redis-cached)
    _filter_sidebar(bootinfo, allowed)              # left nav sidebar
    _filter_app_data(bootinfo)                      # app-switcher (only trade_mvp)
```

**Role → workspace mapping:**

| Role | Allowed workspaces |
|---|---|
| Trade - Sales Executive | Pipeline, Sales |
| Trade - Purchase Executive | Purchasing |
| Trade - Warehouse Staff | Warehouse |
| Trade - Accountant | Finance, Asset Register |
| Trade - Manager | Pipeline, Sales, Purchasing, Warehouse, Finance, Asset Register |

**Why filter at boot_session if we already have Module Profile and workspace hiding?**

Defence in depth. The Module Profile blocks modules but doesn't prevent the workspace list from leaking. The `is_hidden` flag on workspaces is a DB default, but any user could potentially have it overridden. The `boot_session` filter is the definitive runtime gate — it strips the data from the payload before the client ever receives it. Even if the Redis desktop_icons cache was built before permissions were applied (a known Frappe quirk), the boot_session hook strips it clean on every login.

**The four bootinfo structures filtered:**

```python
# 1. workspace pages (icon grid on home screen)
bootinfo.workspaces["pages"] = [p for p in pages if p.get("title") in allowed]

# 2. desktop icons (cached separately in Redis — must be filtered here)
bootinfo.desktop_icons = [
    icon for icon in bootinfo.desktop_icons
    if icon.get("module_name") in allowed or icon.get("label") in allowed
]

# 3. sidebar items (left nav)
bootinfo.workspace_sidebar_item = {
    k: v for k, v in bootinfo.workspace_sidebar_item.items()
    if k.lower() in lower_allowed
}

# 4. app data (app switcher — show only trade_mvp, not ERPNext/Frappe)
bootinfo.app_data = [a for a in bootinfo.app_data if a.get("name") == "trade_mvp"]
```

---

### 7.7 Credit Limit Enforcement — `check_credit_limit`

```
apps/trade_mvp/trade_mvp/setup.py:580
Hook: doc_events → Sales Order → validate
```

Every time a Sales Order is saved or submitted, this function runs.

```python
def check_credit_limit(doc, method=None):
    if not doc.customer:
        return                                      # no customer yet, skip

    credit_limit = frappe.db.get_value(
        "Customer", doc.customer, "trade_credit_limit"
    ) or 0
    if not credit_limit:
        return                                      # 0 = unlimited, skip

    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSales Invoice`
        WHERE customer = %s
          AND docstatus = 1
          AND outstanding_amount > 0
    """, doc.customer)[0][0] or 0

    if float(outstanding) + float(doc.grand_total or 0) > float(credit_limit):
        frappe.throw(
            f"Customer {doc.customer} has exceeded their credit limit of "
            f"{frappe.format_value(credit_limit, {'fieldtype': 'Currency'})}. "
            f"Outstanding: {frappe.format_value(float(outstanding), {'fieldtype': 'Currency'})}."
        )
```

**Logic:**

1. Read `trade_credit_limit` from the Customer record (the custom field added in §7.3)
2. If `0`, skip — unlimited credit
3. Query all submitted Sales Invoices for this customer with remaining outstanding amounts
4. If `outstanding + this order's grand_total > credit_limit` → hard block with a user-visible error

`frappe.throw()` raises an exception that Frappe catches and displays as a red error dialog in the UI. The save is prevented.

**Test coverage** — `tests/test_credit_limit.py` covers 5 scenarios:
- `credit_limit = 0` → unlimited, must pass
- `outstanding < limit` → must pass
- `outstanding + order > limit` → must throw
- No customer on document → must skip entirely (no DB calls)
- `outstanding == limit` exactly → must pass (strictly greater than, not equal)

---

### 7.8 Frontend Customisation

#### `public/js/trade_mvp.js`

Injected into every desk page for every user (the `app_include_js` hook injects globally). The script checks whether the current user is a trade user before doing anything.

```javascript
frappe.provide("trade_mvp");

frappe.ready(function () {
    const tradeRoles = [
        "Trade - Sales Executive", "Trade - Purchase Executive",
        "Trade - Warehouse Staff", "Trade - Accountant", "Trade - Manager",
    ];

    const isTradeUser = tradeRoles.some(r => frappe.user_roles.includes(r));
    if (!isTradeUser) return;

    document.body.classList.add("trade-minimal");

    frappe.after_ajax(function () {
        $('[data-label="Help"]').closest(".nav-item").hide();
        $('[data-label="Explore"]').closest(".nav-item").hide();
    });
});
```

`frappe.user_roles` is an array of role names for the current user, available in the browser because it's included in the bootinfo payload.

`frappe.after_ajax()` defers execution until the initial AJAX calls complete — this ensures the navbar DOM has rendered before the jQuery selectors run.

The `body.trade-minimal` class is the hook used by the CSS file.

#### `public/css/trade_mvp.css`

```css
body.trade-minimal .navbar-help,
body.trade-minimal [data-label="Help"],
body.trade-minimal [data-label="Explore"] {
    display: none !important;
}
```

CSS-level reinforcement of the same hiding. The `!important` ensures it wins over any framework style that might override it. Targeting three selectors covers different Frappe versions that use different HTML structures for the help button.

**Why both JS and CSS?** The JS `hide()` is immediate and jQuery-specific. The CSS is a permanent stylesheet rule — if Frappe re-renders the navbar (which happens on some navigation events), the CSS rule still applies without needing JS to re-run.

---

### 7.9 Workspaces

6 workspace JSON files, stored at:
```
trade_mvp/trade_mvp/workspace/<name>/<name>.json
```

All share these properties:
- `"module": ""` — empty, so the allow_modules check is skipped
- `"app": "trade_mvp"` — links the workspace to this app
- `"public": 1` — visible to all users (role filtering happens at boot_session)
- `"roles": []` — no role restriction at the Workspace level (handled by boot filter)

#### Pipeline (sequence_id: 1)

Icon: `crm`

Links: Lead, Opportunity (CRM section) · Customer, Contact (Masters section)

Dashboard widgets: "Incoming Leads" chart, "Opportunity Trends" chart, "New Lead (Last 1 Month)" number card, "Open Opportunity" number card, "Won Opportunity (Last 1 Month)" number card

#### Sales (sequence_id: 2)

Icon: `sell`

Links: Quotation, Sales Order, Sales Invoice (Orders section) · Item (Catalogue section)

Dashboard widgets: "Sales Order Trends" chart, "Top Customers" chart, "Annual Sales" number card, "Sales Orders to Deliver" number card, "Sales Orders to Bill" number card

#### Purchasing (sequence_id: 3)

Icon: `buying`

Links: Purchase Order, Purchase Receipt, Purchase Invoice (Orders section) · Supplier, Item (Masters section)

Sidebar: Dashboard (Buying), Purchase Order, Purchase Receipt, Purchase Invoice, Supplier, Item

#### Warehouse (sequence_id: 4)

Icon: `stock`

Links: Purchase Receipt, Delivery Note, Stock Entry (Transactions section) · Item, Warehouse (Masters section)

#### Finance (sequence_id: 5)

Icon: `accounts`

The richest workspace. Sidebar has 30 items across 8 sections:

| Section | Items |
|---|---|
| Invoices | Sales Invoice, Purchase Invoice |
| Payments | Payment Entry |
| Banking | Bank Account |
| Financial Statements | General Ledger, Trial Balance, Profit and Loss Statement, Balance Sheet, Cash Flow |
| Receivables | Accounts Receivable, Accounts Receivable Summary, Customer Ledger Summary |
| Payables | Accounts Payable, Accounts Payable Summary, Supplier Ledger Summary |
| Analysis | Gross Profit, Sales Invoice Trends, Purchase Invoice Trends, Payment Period Based On Invoice Date, Bank Reconciliation Statement |

#### Asset Register (sequence_id: 6)

Icon: `asset`

Links: Asset, Asset Category, Asset Movement

---

### 7.10 Demo Data — `demo.py`

Not run automatically on install. Invoked manually:

```bash
bench execute trade_mvp.demo.create_demo_data
```

Creates a complete demo environment:

**Users (password: `Trade@1234`):**

| Email | Role | Name |
|---|---|---|
| sales@trade.local | Trade - Sales Executive | Sarah Sales |
| purchase@trade.local | Trade - Purchase Executive | Peter Purchase |
| warehouse@trade.local | Trade - Warehouse Staff | Wes Warehouse |
| accounts@trade.local | Trade - Accountant | Anna Accounts |
| manager@trade.local | Trade - Manager | Mike Manager |

**Items:**

| Code | Name | UOM | HSN Code |
|---|---|---|---|
| ELEC-001 | Electronics Component | Nos | 999900 |
| TEXT-001 | Industrial Textile | Meter | 999900 |
| CHEM-001 | Chemical Raw Material | Kg | 999900 |
| MACH-001 | Machinery Part | Nos | 999900 |
| CONS-001 | Consumer Goods | Nos | 999900 |

**Customers:**

| Name | Credit Limit |
|---|---|
| Alpha Imports Ltd | ₹1,00,000 |
| Beta Trading Co | ₹75,000 |
| Gamma Distributors | 0 (unlimited) |

**Suppliers:**

| Name | Country |
|---|---|
| XYZ Exports | China |
| ABC Manufacturing | Germany |
| Global Sourcing LLC | United Arab Emirates |

Each creation function uses `frappe.db.exists()` before inserting — the demo data creation is idempotent (safe to run multiple times without creating duplicates).

---

## 8. How Everything Connects — End-to-End Flow

### What happens when a user logs in

```
1. Browser hits /login → enters credentials
2. Frappe authenticates against MariaDB (tabUser)
3. frappe/boot.py: get_bootinfo() is called
   ├── Loads user info, roles, permissions
   ├── load_desktop_data() → populates workspaces, sidebar, desktop_icons, app_data
   └── Runs boot_session hooks
4. boot_session: filter_bootinfo_for_trade_users(bootinfo) runs
   ├── Detects trade roles on the user
   ├── Computes allowed workspaces from ROLE_WORKSPACES
   └── Strips all non-allowed data from bootinfo
5. bootinfo JSON is sent to the browser
6. app_include_js injects trade_mvp.js → adds body.trade-minimal, hides Help/Explore
7. app_include_css injects trade_mvp.css → CSS reinforcement
8. Desk renders — user sees only their 1–6 allowed workspaces
```

### What happens when a Sales Executive creates an order

```
1. User opens Pipeline workspace → clicks Sales Order in sidebar
2. Frappe checks Custom DocPerm: Trade - Sales Executive has read=1 on Sales Order ✓
3. User fills the form (custom fields port_of_loading, port_of_discharge, lc_number visible)
4. User clicks Save → doc.validate fires
5. check_credit_limit() runs:
   ├── Reads Customer.trade_credit_limit (custom field)
   ├── Queries outstanding Sales Invoices for this customer
   └── If over limit → frappe.throw() → save blocked with error dialog
6. If under limit → document saved with workflow_state = "Draft"
7. User clicks "Submit for Approval" (workflow transition button)
   └── workflow_state → "Pending Approval"
8. Manager logs in → sees the Sales Order in Pending Approval state
9. Manager clicks "Approve"
   └── workflow_state → "Approved", docstatus → 1 (submitted/immutable)
```

### What happens when an Accountant runs a report

```
1. Accountant opens Finance workspace
2. Left sidebar shows: General Ledger, Trial Balance, Balance Sheet, etc.
3. User clicks "General Ledger"
4. Frappe checks Report.roles: Trade - Accountant is in the list ✓
   (added by setup_report_permissions() during install)
5. Report runs — reads from tabGL Entry, tabAccount, etc.
6. All master DocTypes (Account, Cost Center, etc.) are readable
   (added by setup_permissions() via TRADE_READ_REFS)
7. Report renders with data
```

---

## 9. File Reference Map

| File | Purpose | Key functions/data |
|---|---|---|
| `trade_mvp/hooks.py` | App registration | `after_install`, `boot_session`, `doc_events`, `fixtures` |
| `trade_mvp/setup.py` | All setup + business logic | `after_install`, `hide_default_workspaces`, `setup_permissions`, `setup_report_permissions`, `setup_module_profiles`, `setup_property_setters`, `setup_workspace_sidebars`, `filter_bootinfo_for_trade_users`, `check_credit_limit` |
| `trade_mvp/setup.py` (constants) | Configuration | `TRADE_ROLES`, `TRADE_WORKSPACES`, `ROLE_WORKSPACES`, `SIDEBAR_ITEMS`, `TRADE_PERMISSIONS`, `TRADE_READ_REFS`, `FINANCE_REPORTS`, `BLOCK_MODULES`, `HIDE_FIELDS` |
| `trade_mvp/demo.py` | Demo data | `create_demo_data`, users, items, customers, suppliers |
| `trade_mvp/fixtures/role.json` | 5 trade roles | desk_access = 1 |
| `trade_mvp/fixtures/custom_field.json` | 10 custom fields | port_of_loading/discharge/lc_number on SO/PO/Quotation; trade_credit_limit on Customer |
| `trade_mvp/fixtures/workflow_state.json` | 4 workflow states | Draft, Pending Approval, Approved, Rejected |
| `trade_mvp/fixtures/workflow.json` | 3 approval workflows | Trade SO Approval, Trade PO Approval, Trade Payment Approval |
| `trade_mvp/public/js/trade_mvp.js` | Client customisation | body.trade-minimal class, hide Help/Explore nav |
| `trade_mvp/public/css/trade_mvp.css` | Client styles | CSS enforcement of nav hiding |
| `trade_mvp/tests/test_credit_limit.py` | Unit tests | 5 credit limit scenarios |
| `trade_mvp/trade_mvp/workspace/pipeline/pipeline.json` | Pipeline workspace | Lead, Opportunity, Customer, Contact |
| `trade_mvp/trade_mvp/workspace/sales/sales.json` | Sales workspace | Quotation, Sales Order, Sales Invoice, Item |
| `trade_mvp/trade_mvp/workspace/purchasing/purchasing.json` | Purchasing workspace | PO, Purchase Receipt, Purchase Invoice, Supplier, Item |
| `trade_mvp/trade_mvp/workspace/warehouse/warehouse.json` | Warehouse workspace | Purchase Receipt, Delivery Note, Stock Entry, Item, Warehouse |
| `trade_mvp/trade_mvp/workspace/finance/finance.json` | Finance workspace | Invoices, Payments, Banking, 15 reports |
| `trade_mvp/trade_mvp/workspace/asset_register/asset_register.json` | Asset Register workspace | Asset, Asset Category, Asset Movement |
