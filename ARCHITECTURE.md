# Trade MVP — Architecture & Frappe Concepts from First Principles

This document explains how trade_mvp is built, starting from the very basics of what a web framework is and building up to every mechanism the app uses. No prior Frappe knowledge is assumed.

---

## Table of Contents

1. [What is a Web Framework?](#1-what-is-a-web-framework)
2. [What is Frappe?](#2-what-is-frappe)
3. [What is ERPNext?](#3-what-is-erpnext)
4. [What is a Frappe Bench?](#4-what-is-a-frappe-bench)
5. [What is a Frappe App?](#5-what-is-a-frappe-app)
6. [The DocType: Frappe's Core Building Block](#6-the-doctype-frappess-core-building-block)
7. [The hooks.py File — The App Registry](#7-the-hookspy-file--the-app-registry)
8. [Fixtures — Shipping Data With Your App](#8-fixtures--shipping-data-with-your-app)
9. [The after_install Hook — One-Time Setup](#9-the-after_install-hook--one-time-setup)
10. [Custom Fields — Non-Destructive Schema Extension](#10-custom-fields--non-destructive-schema-extension)
11. [Custom DocPerm — Overriding Permissions](#11-custom-docperm--overriding-permissions)
12. [Module Profile — Coarse Module Blocking](#12-module-profile--coarse-module-blocking)
13. [Property Setter — Runtime Field Metadata Overrides](#13-property-setter--runtime-field-metadata-overrides)
14. [Workflows — Approval State Machines](#14-workflows--approval-state-machines)
15. [Workspaces — The Desk Home Pages](#15-workspaces--the-desk-home-pages)
16. [Workspace Sidebar — The Left Navigation](#16-workspace-sidebar--the-left-navigation)
17. [Bootinfo — The Login Payload](#17-bootinfo--the-login-payload)
18. [The boot_session Hook — Per-Login Filtering](#18-the-boot_session-hook--per-login-filtering)
19. [The doc_events Hook — Document Lifecycle Callbacks](#19-the-doc_events-hook--document-lifecycle-callbacks)
20. [Frontend Assets — JS and CSS](#20-frontend-assets--js-and-css)
21. [The frappe.db API — Talking to the Database](#21-the-frappedb-api--talking-to-the-database)
22. [Demo Data — Seeding a Working Dataset](#22-demo-data--seeding-a-working-dataset)
23. [Tests — Unit Testing Without a Running Site](#23-tests--unit-testing-without-a-running-site)
24. [The Complete Install Flow](#24-the-complete-install-flow)
25. [The Complete Login Flow](#25-the-complete-login-flow)
26. [The Business Rules Summary](#26-the-business-rules-summary)

---

## 1. What is a Web Framework?

A web application receives HTTP requests from browsers, reads and writes to a database, and returns HTML or JSON responses. Doing this from scratch for every project means solving the same problems repeatedly: user authentication, session management, database access, form rendering, file uploads, permissions, email sending, caching, and so on.

A **web framework** is a pre-built solution to all of those common problems. You extend it — adding your specific business logic — rather than rebuilding the infrastructure.

Most frameworks let you define:
- **Data models** — what tables exist and what columns they have
- **Business logic** — what happens when data is created, changed, or deleted
- **UI** — how the data is displayed and edited
- **Permissions** — who can do what

---

## 2. What is Frappe?

Frappe is a full-stack Python web framework designed for building business applications. It goes further than most frameworks by making the data model itself a first-class, runtime-configurable concept called a **DocType**.

Key characteristics of Frappe:

**Everything is a DocType.** A DocType is both a database table schema and an auto-generated UI form. If you define a DocType called "Customer" with fields "name", "email", and "credit_limit", Frappe automatically creates the database table, generates the create/edit/list form in the browser, handles validation, manages permissions, and provides a REST API — all without writing any additional code.

**The desk is the application.** Frappe ships a single-page web application called "the desk" — a React-like JavaScript frontend that renders forms, lists, reports, and dashboards based on metadata fetched from the server. You don't write HTML pages; you define DocTypes and the UI generates itself.

**Apps extend Frappe.** Frappe itself is an app. You build additional apps on top of it. Each app can define new DocTypes, override existing ones, register hooks into the framework lifecycle, and add frontend assets. Multiple apps can be installed on the same site simultaneously.

**MariaDB + Redis.** Frappe uses MariaDB for its relational database (all DocType data) and Redis for session storage, caching, and background job queues.

**Python + JavaScript.** Server-side logic is Python. Client-side logic is JavaScript. Frappe provides APIs on both sides that mirror each other — `frappe.db.get_value()` in Python, `frappe.db.get_value()` in JavaScript.

---

## 3. What is ERPNext?

ERPNext is a full Enterprise Resource Planning system built as a Frappe app. It defines hundreds of DocTypes covering:

- **Selling** — Quotation, Sales Order, Delivery Note, Sales Invoice
- **Buying** — Purchase Order, Purchase Receipt, Purchase Invoice
- **Stock** — Item, Warehouse, Stock Entry
- **CRM** — Lead, Opportunity, Customer, Contact
- **Accounts** — Payment Entry, Bank Account, Journal Entry
- **Assets** — Asset, Asset Category, Asset Movement
- **HR, Payroll, Manufacturing, Projects, Support, Quality Management...**

ERPNext is enormous. A company typically only needs a fraction of its features. The challenge trade_mvp solves is: how do you install ERPNext and then present only the relevant subset to users of a trading company?

---

## 4. What is a Frappe Bench?

A **bench** is a directory on the server that contains everything needed to run one or more Frappe sites. Think of it as a self-contained deployment unit.

```
frappe_mvp/                ← the bench root
  apps/                    ← all installed app source code
    frappe/                ← the framework itself
    erpnext/               ← the ERP app
    india_compliance/      ← GST/Indian tax compliance
    trade_mvp/             ← our custom app
  sites/
    frappe_mvp.localhost/  ← a single site (its own MariaDB database)
      site_config.json     ← database credentials, Redis URLs, etc.
  env/                     ← Python virtualenv (all pip packages installed here)
  config/
    redis_cache.conf       ← Redis for caching (port 13001)
    redis_queue.conf       ← Redis for job queues (port 11001)
  Procfile                 ← defines all processes to run
```

The `Procfile` starts six processes simultaneously:
- **web** — a gunicorn Python server handling HTTP requests (port 8001)
- **socketio** — a Node.js server for real-time browser notifications
- **redis_cache** — caches DocType metadata, permissions, user data
- **redis_queue** — stores background job tasks
- **schedule** — runs scheduled jobs (hourly/daily tasks)
- **worker** — processes background jobs from the queue

You interact with the bench through the `bench` command-line tool: `bench start` to run all processes, `bench migrate` to apply database changes, `bench install-app` to add an app to a site.

---

## 5. What is a Frappe App?

A Frappe app is a Python package with a specific directory structure that the framework knows how to load. The app name must match its folder name and its top-level Python module name.

```
trade_mvp/                         ← repo / pip package root
  trade_mvp/                       ← Python module (import trade_mvp)
    hooks.py                       ← THE central registry
    modules.txt                    ← declares the app's module name
    __init__.py
    setup.py                       ← install logic + business logic
    demo.py                        ← demo data creation
    fixtures/                      ← JSON data shipped with the app
      role.json
      custom_field.json
      workflow.json
    public/                        ← static files → served at /assets/trade_mvp/
      js/trade_mvp.js
      css/trade_mvp.css
    trade_mvp/                     ← sub-module (the "Trade MVP" module)
      workspace/                   ← workspace configuration JSONs
        sales/sales.json
        pipeline/pipeline.json
        purchasing/purchasing.json
        warehouse/warehouse.json
        finance/finance.json
        asset_register/asset_register.json
    tests/
      test_credit_limit.py
    config/
      __init__.py
    patches/
      __init__.py
    templates/
      pages/__init__.py
```

`modules.txt` contains a single line: `Trade MVP`. This registers the module name with Frappe. A **module** in Frappe is a logical grouping of DocTypes. Since trade_mvp defines no new DocTypes (it only customises ERPNext's existing ones), the module is mostly a namespace.

---

## 6. The DocType: Frappe's Core Building Block

Before going further, you need to understand DocTypes because everything in Frappe is built on them.

**In traditional web development:** You define a database table in a migration file, write ORM model code, create HTML forms, write controller logic, and set up routes — all separately.

**In Frappe:** You define a DocType. One definition creates all of that simultaneously.

A DocType definition specifies:
- **Fields** — each field has a name, label, fieldtype (Data, Int, Currency, Link, Table, etc.), and properties (required, hidden, in_list_view, etc.)
- **Permissions** — which roles can read/write/create/delete/submit/cancel/amend
- **Controller** — optional Python class for custom logic
- **Properties** — is it submittable? Is it a single record (singleton)? Does it have naming rules?

When Frappe syncs a DocType:
1. It creates a MariaDB table `tab{DocType Name}` with one column per field
2. It stores the DocType definition in the `tabDocType` and `tabDocField` tables
3. The desk frontend automatically builds list views and form views from the metadata

**The Document object.** When you load a record from the database (`frappe.get_doc("Sales Order", "SO-0001")`), you get a Python object where every field is an attribute. `doc.customer`, `doc.grand_total`, `doc.items` (a child table) — all accessible directly. Saving the doc writes all fields back to the database and runs validation hooks.

**Submittable documents.** Some DocTypes are "submittable" — they have a `docstatus` field. `docstatus=0` means draft, `docstatus=1` means submitted (locked), `docstatus=2` means cancelled. Sales Orders, Invoices, and Payment Entries are submittable. Submitting posts ledger entries, creates accounting records, and locks the document from further edits.

**This is the foundation.** Everything else in Frappe — permissions, workflows, workspaces, property setters — is either modifying DocType metadata or hooking into the document lifecycle.

---

## 7. The hooks.py File — The App Registry

`hooks.py` is the most important file in any Frappe app. It is read by the framework on startup and used as a registry for everything the app wants to inject into the system.

Frappe loads `hooks.py` from every installed app and merges all the values together. When multiple apps register the same hook, they all run — in the order apps were installed.

Here is trade_mvp's complete `hooks.py` annotated:

```python
# App identity — used in the UI and app registry
app_name = "trade_mvp"
app_title = "Trade MVP"
app_publisher = "Trade"
app_description = "Import/export trading app built on ERPNext"
app_email = "admin@trade.local"
app_license = "MIT"

# Inject these files into EVERY page of the desk for ALL users of this site.
# Frappe adds <script src="..."> and <link rel="stylesheet" href="..."> tags.
app_include_js = "/assets/trade_mvp/js/trade_mvp.js"
app_include_css = "/assets/trade_mvp/css/trade_mvp.css"

# Run this Python function once, when the app is installed.
after_install = "trade_mvp.setup.after_install"

# Run this Python function on every user login (when bootinfo is assembled).
boot_session = "trade_mvp.setup.filter_bootinfo_for_trade_users"

# Run these Python functions when specific document events fire.
doc_events = {
    "Sales Order": {
        "validate": "trade_mvp.setup.check_credit_limit"
    }
}

# Define which database records belong to this app and should be exported/imported as fixtures.
fixtures = [
    {"dt": "Role",         "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field", "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow",     "filters": [["name", "like", "Trade%"]]},
]
```

Each key is a **hook point** — a named slot in Frappe's execution where apps can register code. The values are Python dotted-path strings, not function references. Frappe calls `frappe.get_attr("trade_mvp.setup.after_install")` at runtime to resolve the function.

---

## 8. Fixtures — Shipping Data With Your App

### The Problem

An app needs certain database records to exist to function. Trade MVP needs:
- 5 Role records (Trade - Sales Executive, etc.)
- 10 Custom Field records (the port/LC fields, credit limit)
- 3 Workflow records (SO/PO/Payment approval)

These are database rows, not code. How do you ship them with the app in a reproducible way?

### The Solution: Fixtures

Fixtures are JSON files in the `fixtures/` directory. Each file contains an array of objects, where each object is a complete DocType record. When `sync_fixtures(app)` runs, it reads these files and upserts the records into the database.

The `fixtures` key in `hooks.py` tells Frappe which records belong to this app:

```python
fixtures = [
    {"dt": "Role", "filters": [["name", "like", "Trade%"]]},
]
```

`dt` = the DocType name. `filters` = which records to include when *exporting* (running `bench export-fixtures`). During *import* (sync), Frappe reads the JSON file and upserts all records found in it.

**Export:** `bench export-fixtures --app trade_mvp` queries each fixture DocType with the given filters and writes the results to JSON. This is how you update the fixture files when you change records in the UI.

**Import/Sync:** `sync_fixtures("trade_mvp")` reads each JSON file, iterates the records, and for each one calls `frappe.get_doc(data).insert()` if it doesn't exist or updates it if it does. Fixtures are idempotent — safe to run multiple times.

### trade_mvp's Fixture Files

**`role.json`** — 5 Role records:
```json
[
  {"doctype": "Role", "name": "Trade - Sales Executive",    "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Purchase Executive", "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Warehouse Staff",    "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Accountant",         "desk_access": 1},
  {"doctype": "Role", "name": "Trade - Manager",            "desk_access": 1}
]
```

`desk_access: 1` means the role grants access to the Frappe desk UI (as opposed to portal-only access).

**`custom_field.json`** — 10 Custom Field records adding trade-specific fields to existing ERPNext DocTypes:
- `port_of_loading`, `port_of_discharge`, `lc_number` (Letter of Credit) on Sales Order, Purchase Order, and Quotation — logistics fields relevant to import/export
- `trade_credit_limit` on Customer — a Currency field used by the credit limit check

**`workflow.json`** — 3 Workflow records defining approval state machines for Sales Order, Purchase Order, and Payment Entry (covered in detail in section 14).

---

## 9. The after_install Hook — One-Time Setup

### What It Is

`after_install` is a function that runs exactly once: when you execute `bench install-app trade_mvp` on a site. It's the app's setup script — it creates all the configuration that makes trade_mvp work.

### Why It's Needed

Fixtures sync data records. But many things can't be expressed as simple fixture records:
- Hiding all of ERPNext's default workspaces requires running SQL
- Creating permissions requires iterating a Python data structure and inserting many rows
- Setting up module profiles and property setters requires calling Frappe's Python APIs

All of this happens in `after_install`.

### The Execution Order Problem

There's a subtle timing issue. `after_install` runs *before* Frappe's normal post-install fixture sync. But `setup_permissions()` creates permission rows that reference the Trade Role records — and those records only exist after `sync_fixtures()` puts them in the database.

The solution: call `sync_fixtures("trade_mvp")` manually at the very start of `after_install`, before anything else. The `frappe.flags.in_migrate = True` flag disables a workspace route-conflict validation that would otherwise error during sync.

```python
def after_install():
    from frappe.utils.fixtures import sync_fixtures
    frappe.flags.in_migrate = True
    try:
        sync_fixtures("trade_mvp")   # MUST run first — roles needed by setup_permissions
    finally:
        frappe.flags.in_migrate = False

    hide_default_workspaces()        # step 1: hide everything that's not ours
    setup_permissions()              # step 2: grant trade roles their permissions
    setup_module_profiles()          # step 3: block irrelevant ERPNext modules
    setup_property_setters()         # step 4: hide irrelevant form fields
    setup_workspace_sidebars()       # step 5: configure left-nav per workspace
    frappe.db.commit()

    create_workspace_sidebar_for_workspaces()
    create_desktop_icons_from_workspace()

    # Clear module= on trade workspaces to bypass the allow_modules check
    frappe.db.sql("UPDATE `tabWorkspace` SET module = '' WHERE name IN (...)")
    frappe.db.sql("UPDATE `tabWorkspace Sidebar` SET module = NULL WHERE title IN (...)")

    frappe.cache.flushall()          # clear Redis so stale cache doesn't serve old data
```

Each step is covered in its own section below.

---

## 10. Custom Fields — Non-Destructive Schema Extension

### The Problem

ERPNext ships with a Sales Order DocType that has many fields. You need to add trade-specific fields — port of loading, port of discharge, letter of credit number. How do you add these without modifying ERPNext's source code?

Modifying ERPNext source would be a nightmare: your changes would conflict on every ERPNext update, and git merges would be required forever.

### The Solution: Custom Fields

Frappe stores DocType field definitions in a database table called `tabDocField`. It also has a separate table `tabCustom Field`. When Frappe loads a DocType's metadata (`get_meta(doctype)`), it fetches records from both tables and merges them.

A `Custom Field` record specifies:
- `dt` — which DocType to add the field to
- `fieldname` — the column name in the database
- `label` — the display label in the form
- `fieldtype` — Data, Currency, Link, etc.
- `insert_after` — which existing field to place this field after
- `module` — which app owns this field (used for fixture filtering)

When you add a Custom Field, Frappe automatically adds the column to the underlying MariaDB table. No migration file needed — it happens at sync time.

### trade_mvp's Custom Fields

The `custom_field.json` fixture file creates 10 fields across 4 DocTypes:

| DocType | Field Name | Label | Type | Notes |
|---------|-----------|-------|------|-------|
| Sales Order | port_of_loading | Port of Loading | Data | After incoterm field |
| Sales Order | port_of_discharge | Port of Discharge | Data | After port_of_loading |
| Sales Order | lc_number | LC Number | Data | Letter of Credit |
| Purchase Order | port_of_loading | Port of Loading | Data | Same set |
| Purchase Order | port_of_discharge | Port of Discharge | Data | |
| Purchase Order | lc_number | LC Number | Data | |
| Quotation | port_of_loading | Port of Loading | Data | Same set |
| Quotation | port_of_discharge | Port of Discharge | Data | |
| Quotation | lc_number | LC Number | Data | |
| Customer | trade_credit_limit | Credit Limit | Currency | Default 0 = unlimited |

Once these Custom Fields exist, they are accessible on documents like any built-in field: `doc.trade_credit_limit`, `doc.port_of_loading`. The desk form renders them automatically.

---

## 11. Custom DocPerm — Overriding Permissions

### How Frappe Permissions Work

Frappe's permission system is role-based. Every DocType definition includes a `permissions` table (stored in `tabDocPerm`) that lists which roles have which access rights. A permission row specifies: role, permlevel, read, write, create, delete, submit, cancel, amend.

When a user tries to access a document, Frappe checks: does this user have any role that has the required permission for this DocType?

ERPNext's default permissions are broad — the "Accounts User" role can access Sales Invoices, the "Stock User" role can access Delivery Notes, etc. These are too permissive for trade_mvp's tightly scoped roles.

### The Solution: Custom DocPerm

`Custom DocPerm` is a parallel permission table stored in `tabCustom DocPerm`. The key rule: **if a DocType has any Custom DocPerm records, those replace (not supplement) the DocPerm records for permission checking**.

This means you can completely redefine who has access to a DocType. Trade MVP does exactly this — it creates Custom DocPerm rows for every role/doctype combination it cares about, establishing a clean permission slate.

### trade_mvp's Permission Structure

`TRADE_PERMISSIONS` in `setup.py` is a Python dict mapping each role to a list of (doctype, read, write, create, delete, submit, cancel, amend) tuples:

```python
TRADE_PERMISSIONS = {
    "Trade - Sales Executive": [
        ("Lead",           1, 1, 1, 0, 0, 0, 0),  # can create leads, no delete
        ("Quotation",      1, 1, 1, 0, 1, 1, 1),  # full cycle on quotations
        ("Sales Order",    1, 1, 1, 0, 1, 1, 1),  # full cycle on orders
        ("Purchase Order", 1, 0, 0, 0, 0, 0, 0),  # read-only visibility
        ...
    ],
    "Trade - Warehouse Staff": [
        ("Purchase Receipt", 1, 1, 1, 0, 1, 1, 1), # receives stock
        ("Delivery Note",    1, 1, 1, 0, 1, 1, 1), # ships stock
        ("Stock Entry",      1, 1, 1, 0, 1, 1, 1), # moves stock
        ("Sales Order",      1, 0, 0, 0, 0, 0, 0), # knows what to ship
        ("Purchase Order",   1, 0, 0, 0, 0, 0, 0), # knows what's incoming
        ...
    ],
    ...
}
```

The design principle: each role has full CRUD + submit/cancel/amend on the documents it owns, and read-only access on the documents it needs to see as context.

`setup_permissions()` iterates this structure and calls `frappe.new_doc("Custom DocPerm")` or `frappe.db.set_value("Custom DocPerm", ...)` for each entry. After inserting, it calls `frappe.clear_cache(doctype=doctype)` to invalidate the permission cache for that DocType.

---

## 12. Module Profile — Coarse Module Blocking

### The Problem

Even with tight Custom DocPerm restrictions, the ERPNext desk still shows the user many things they don't need: the Manufacturing workspace, HR workspace, Payroll, Quality Management, Support, and so on. Users could click into these, see "Permission Denied" errors, or just be confused by the irrelevant options.

A blunter tool is needed to hide entire modules at the UI level.

### What a Module Is in Frappe

In Frappe, a **module** is a named grouping of DocTypes. Every DocType belongs to a module (e.g. Sales Order belongs to the "Selling" module, Purchase Order to "Buying", etc.). Workspaces have a `module` field tying them to their module.

When the desk renders the navigation, it checks whether the current user's allowed modules include the workspace's module. If not, the workspace is hidden.

### Module Profile

A `Module Profile` is a database record with a name and a child table listing blocked modules. A user can be assigned to a Module Profile. When that user logs in, their `allow_modules` list (the inverse of their profile's blocked list) is computed. Workspaces tied to blocked modules are filtered out.

### trade_mvp's Use

`setup_module_profiles()` creates a single Module Profile named "Trade User":

```python
BLOCK_MODULES = [
    "Accounts", "Stock", "Selling", "Buying", "CRM",
    "Manufacturing", "Projects", "HR", "Payroll", "Assets",
    "Support", "Quality Management", "Subcontracting",
    "ERPNext Integrations", "Regional",
    "Build", "Integrations", "Website",
    "Core", "Email", "Automation", "Desk", "Custom",
    "Geo", "Printing", "Workflow",
]
```

This blocks 26 ERPNext/Frappe modules. Any workspace whose `module` field matches one of these is hidden for users assigned to this profile.

**The catch:** trade_mvp's own workspaces need `module = ""` (empty). Here's why: "Trade MVP" is not in any user's `allow_modules` list, so if the workspaces declared `module = "Trade MVP"`, they would be blocked too. Setting `module = ""` bypasses the allow_modules check entirely — a workspace with no module is always included. This is done via a raw SQL UPDATE in `after_install()` after the workspaces are created.

---

## 13. Property Setter — Runtime Field Metadata Overrides

### The Problem

ERPNext's forms contain many fields that trade users don't need. A Sales Order has `utm_source`, `utm_campaign`, `commission_rate`, `sales_team`, `is_internal_customer` — all irrelevant to a small trading company. A Customer form has `loyalty_program`, `account_manager`, `sales_partner`.

You need to hide these fields. But again, you can't modify ERPNext's source.

### What is a Property Setter?

Every field in a DocType has metadata: `hidden`, `required`, `label`, `options`, `default`, `read_only`, etc. These properties live in `tabDocField`. A `Property Setter` is a runtime override for any of these properties.

When Frappe builds a DocType's metadata object (`get_meta()`), it:
1. Loads the base field definitions from `tabDocField`
2. Loads all `Property Setter` records for that DocType
3. Applies each Property Setter: `field[property] = value`

So if a Property Setter says `{"doc_type": "Sales Order", "field_name": "utm_source", "property": "hidden", "value": "1"}`, then `utm_source` is hidden in every Sales Order form, for every user.

### trade_mvp's Property Setters

`HIDE_FIELDS` in `setup.py` lists fields to hide on 12 DocTypes:

```python
HIDE_FIELDS = {
    "Customer": [
        "lead_name", "account_manager", "industry", "website",
        "market_segment", "loyalty_program", "sales_team", ...
    ],
    "Sales Order": [
        "utm_source", "utm_campaign", "commission_rate",
        "sales_team", "is_internal_customer", "cost_center", ...
    ],
    "Item": [
        "has_serial_no", "has_batch_no", "has_variants",
        "is_sub_contracted_item", "quality_inspection_template", ...
    ],
    ...
}
```

`setup_property_setters()` iterates this dict and calls `_safe_hide_field(doctype, fieldname)` for each entry.

`_safe_hide_field()` first checks that the field actually exists in `tabDocField` — guarding against ERPNext version differences where a field might have been removed. Then it either creates a new Property Setter or updates the existing one:

```python
frappe.make_property_setter({
    "doctype": doctype,
    "doctype_or_field": "DocField",
    "fieldname": fieldname,
    "property": "hidden",
    "value": "1",
    "property_type": "Check",
})
```

The result: these fields still exist in the database (the column is still there), but they are invisible in every form view across the entire site.

---

## 14. Workflows — Approval State Machines

### The Problem

A Sales Executive creates a Sales Order. But the company doesn't want orders going out without manager approval. How do you enforce a review step before submission?

### What is a Workflow in Frappe?

A Frappe Workflow is a state machine attached to a DocType. It defines:
- **States** — named stages a document can be in, each with a `doc_status` (0=draft, 1=submitted, 2=cancelled)
- **Transitions** — arrows between states, each with an action name and a role that's allowed to trigger it
- **workflow_state_field** — a field on the document that stores the current state name

When a workflow is active on a DocType, Frappe intercepts every save and validates: is the user's role allowed to move from the current state to the requested state? If not, the save is rejected with an error.

States with `doc_status = 1` represent the "submitted" state — reaching that state submits the document and locks it.

### trade_mvp's Three Workflows

**Trade SO Approval** (Sales Order):

```
[Draft] ──"Submit for Approval" (Sales Executive)──→ [Pending Approval]
                                                            │
                          ┌─────────────────────────────────┤
                          ↓                                 ↓
                      [Approved]                       [Rejected]
                    (doc_status=1)               (can be resubmitted by
                   (Manager approves)             Sales Executive)
```

The Sales Executive creates the order, fills in all fields, then clicks "Submit for Approval". This moves the state to "Pending Approval". The Manager then sees it in their queue and either clicks "Approve" (which submits the document, making it legally binding) or "Reject" (which sends it back to the Sales Executive for revision).

**Trade PO Approval** (Purchase Order): Identical structure, with Purchase Executive in place of Sales Executive.

**Trade Payment Approval** (Payment Entry): Identical structure, with Accountant in place of Sales Executive.

All three workflows have:
- `is_active: 1` — the workflow is enforced
- `override_status: 0` — Frappe's normal submit button still works alongside workflow actions
- `send_email_alert: 0` — no email notifications (can be enabled later)

The workflow transitions are stored in the `workflow.json` fixture, so they're installed automatically with the app.

---

## 15. Workspaces — The Desk Home Pages

### What is a Workspace?

In Frappe v16, the home screen of the desk shows a grid of workspace tiles. Clicking a tile opens a "workspace" — a configurable dashboard page with:
- A left sidebar for navigation
- A content area with charts, number cards, and quick-access link cards

Each workspace is a `Workspace` DocType record stored in the database, but the initial records are defined as JSON files in the app and synced during install.

### The Workspace JSON Structure

Here's the Sales workspace as an example:

```json
{
  "doctype": "Workspace",
  "name": "Sales",
  "title": "Sales",
  "module": "",
  "app": "trade_mvp",
  "icon": "sell",
  "is_hidden": 0,
  "public": 1,
  "sequence_id": 2.0,
  "content": "[{...charts and number cards...}]",
  "links": [
    {"type": "Card Break", "label": "Orders"},
    {"type": "Link", "label": "Quotation",    "link_type": "DocType", "link_to": "Quotation",    "onboard": 1},
    {"type": "Link", "label": "Sales Order",  "link_type": "DocType", "link_to": "Sales Order",  "onboard": 1},
    {"type": "Link", "label": "Sales Invoice","link_type": "DocType", "link_to": "Sales Invoice", "onboard": 1},
    {"type": "Card Break", "label": "Catalogue"},
    {"type": "Link", "label": "Item",         "link_type": "DocType", "link_to": "Item",         "onboard": 1}
  ]
}
```

Key fields:

| Field | Value | Meaning |
|-------|-------|---------|
| `module` | `""` | Empty — bypasses the allow_modules check |
| `app` | `"trade_mvp"` | Associates this workspace with our app |
| `public` | `1` | Visible to all users (role filtering happens in boot hook) |
| `is_hidden` | `0` | Not hidden — only the default ERPNext workspaces are hidden |
| `sequence_id` | `2.0` | Display order on the home screen |
| `roles` | `[]` | No baked-in role restriction — handled in boot_session hook |
| `content` | JSON string | Widget layout — charts and number cards |
| `links` | Array | Quick-access cards in the workspace body |

The `links` array uses `Card Break` rows as section headers and `Link` rows as clickable items. `link_type` can be `"DocType"` (opens the list view), `"Report"`, `"Dashboard"`, or `"Page"`. `onboard: 1` marks a link as part of the onboarding checklist.

### The Six Workspaces

| Workspace | sequence | Users | Contents |
|-----------|----------|-------|----------|
| Pipeline | 1 | Sales Executive, Manager | Leads, Opportunities, Customers, Contacts |
| Sales | 2 | Sales Executive, Manager | Quotations, Sales Orders, Sales Invoice, Items |
| Purchasing | 3 | Purchase Executive, Manager | Purchase Orders, Receipts, Invoices, Suppliers |
| Warehouse | 4 | Warehouse Staff, Manager | Purchase Receipts, Delivery Notes, Stock Entries |
| Finance | 5 | Accountant, Manager | Sales/Purchase Invoices, Payment Entry, Bank Account |
| Asset Register | 6 | Accountant, Manager | Assets, Asset Categories, Asset Movements |

### Hiding Default Workspaces

`hide_default_workspaces()` runs a single SQL UPDATE:

```sql
UPDATE `tabWorkspace`
SET is_hidden = 1
WHERE name NOT IN ('Pipeline','Sales','Purchasing','Warehouse','Finance','Asset Register')
AND name != 'Workspace'
```

This hides ERPNext's built-in workspaces (Accounts, Buying, Selling, Stock, etc.) so they don't appear on the home screen. Trade users only see the six trade workspaces.

---

## 16. Workspace Sidebar — The Left Navigation

### What is the Sidebar?

Each workspace has a left sidebar showing a structured navigation menu — section headers and links to DocTypes, reports, and dashboards. In Frappe v16, this sidebar is stored in a separate DocType: `Workspace Sidebar`. Each Workspace Sidebar record has a `items` child table.

### Item Types

A sidebar item can be:
- **Section Break** — a visual header that groups items below it. Has `type: "Section Break"`, `collapsible: 1` (can be collapsed).
- **Link** — a clickable item. Has `type: "Link"`, `link_type` (DocType/Dashboard/Report), `link_to` (the target name), `child: 1`, `indent: 1` (renders indented under the section).

### trade_mvp's Sidebar Configuration

`SIDEBAR_ITEMS` in `setup.py` defines the sidebar content for each workspace:

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
    ...
}
```

`setup_workspace_sidebars()` iterates this dict, fetches each `Workspace Sidebar` record, clears its items, and re-appends them from the `SIDEBAR_ITEMS` definition. This runs inside `after_install()`.

---

## 17. Bootinfo — The Login Payload

### What is Bootinfo?

When a user successfully logs into the Frappe desk, the browser does not immediately fetch data for each workspace, sidebar, and icon separately. Instead, Frappe assembles a single large JSON object called **bootinfo** and sends it all at once.

Bootinfo contains everything the browser needs to initialize the entire desk UI:

- User profile (name, email, roles, language, time zone)
- All workspace definitions
- All sidebar items for every workspace
- Desktop icons
- App data (the app switcher)
- System settings (date format, currency, etc.)
- Translations
- Print format definitions
- And many other settings

This single HTTP response is why the desk loads fast after login — no round trips needed for navigation.

### The Four Structures Trade MVP Cares About

```
bootinfo
  ├── workspaces
  │     └── pages[]          ← workspace tiles on home screen
  ├── workspace_sidebar_item ← dict: workspace_name → sidebar items
  ├── desktop_icons[]        ← icon list for the desktop (legacy + v16)
  └── app_data[]             ← app switcher tiles
```

All four need to be filtered for trade users, because all four independently contribute to the UI. Filtering only one would leave leakage paths — e.g. if you filter workspaces but not desktop_icons, the old desktop icon for "Accounting" would still appear.

### How Bootinfo Is Assembled

In `frappe/boot.py`, `get_bootinfo()` runs on every login:

```python
def get_bootinfo():
    bootinfo = frappe._dict()
    get_user(bootinfo)                          # loads user profile and roles
    load_desktop_data(bootinfo)                 # loads workspaces, sidebar, app_data
    bootinfo.desktop_icons = get_desktop_icons(bootinfo=bootinfo)  # loads/caches icons
    ...
    for method in hooks.boot_session or []:     # calls trade_mvp's filter hook
        frappe.get_attr(method)(bootinfo)
    return bootinfo
```

The `boot_session` hooks run *after* all the data is assembled, so by the time trade_mvp's filter runs, all four structures are already populated and ready to be filtered in-place.

---

## 18. The boot_session Hook — Per-Login Filtering

### What It Does

`filter_bootinfo_for_trade_users(bootinfo)` is called on every user login. It checks whether the user has any Trade role, and if so, filters the bootinfo to only include the workspaces that role is allowed to see.

### The Logic

```python
def filter_bootinfo_for_trade_users(bootinfo):
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return  # don't filter system users

    # Which trade roles does this user have?
    user_trade_roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "role": ["in", TRADE_ROLES]},
        pluck="role",
    )
    if not user_trade_roles:
        return  # not a trade user — don't filter anything

    # Compute the union of all allowed workspaces across all trade roles
    allowed = set()
    for role in user_trade_roles:
        allowed.update(ROLE_WORKSPACES.get(role, []))

    # Filter all four bootinfo structures
    _filter_workspaces(bootinfo, allowed)
    _filter_desktop_icons(bootinfo, allowed)
    _filter_sidebar(bootinfo, allowed)
    _filter_app_data(bootinfo)
```

The role-to-workspace mapping:

```python
ROLE_WORKSPACES = {
    "Trade - Sales Executive":    ["Pipeline", "Sales"],
    "Trade - Purchase Executive": ["Purchasing"],
    "Trade - Warehouse Staff":    ["Warehouse"],
    "Trade - Accountant":         ["Finance", "Asset Register"],
    "Trade - Manager":            all six workspaces,
}
```

A user with multiple roles gets the union. A manager sees everything. A sales executive sees only Pipeline and Sales.

### The Four Sub-Filters

**`_filter_workspaces`** — removes workspace page records not in `allowed`:
```python
bootinfo.workspaces["pages"] = [p for p in pages if p.get("title") in allowed]
```

**`_filter_desktop_icons`** — removes icon records not matching allowed workspaces:
```python
bootinfo.desktop_icons = [
    icon for icon in bootinfo.desktop_icons
    if icon.get("module_name") in allowed or icon.get("label") in allowed
]
```

**`_filter_sidebar`** — removes sidebar entries for non-allowed workspaces (keys are lowercased):
```python
lower_allowed = {w.lower() for w in allowed}
bootinfo.workspace_sidebar_item = {
    k: v for k, v in bootinfo.workspace_sidebar_item.items()
    if k.lower() in lower_allowed
}
```

**`_filter_app_data`** — removes all app tiles except trade_mvp from the app switcher:
```python
bootinfo.app_data = [a for a in bootinfo.app_data if a.get("name") == "trade_mvp"]
```

### Why Server-Side Filtering Matters

The permission system (Custom DocPerm) protects data access. But without bootinfo filtering, the desk UI would still show links to ERPNext modules the user doesn't need — they'd get "Permission Denied" errors everywhere, which is a bad UX. Bootinfo filtering removes those options from the UI before the user ever sees them.

---

## 19. The doc_events Hook — Document Lifecycle Callbacks

### The Document Lifecycle

Every time a Frappe document is saved, submitted, cancelled, or deleted, it goes through a lifecycle with named events. Before saving: `before_validate`, `validate`. After saving: `on_update`, `after_insert`. On submit: `on_submit`. On cancel: `on_cancel`. On delete: `before_delete`, `on_trash`.

At each event, Frappe calls:
1. The method of the same name on the document's controller class (if it has one)
2. Every function registered under that event in `doc_events` across all installed apps

This is how you add behavior to an existing DocType without modifying its controller.

### trade_mvp's Credit Limit Check

```python
doc_events = {
    "Sales Order": {
        "validate": "trade_mvp.setup.check_credit_limit"
    }
}
```

This tells Frappe: whenever a Sales Order is validated (which happens on every save and submit), call `trade_mvp.setup.check_credit_limit(doc, method)`.

### The Business Rule

A customer has a credit limit (`trade_credit_limit`). The sum of their outstanding (unpaid) sales invoices plus the new order total must not exceed that limit. If it does, the order is blocked.

```python
def check_credit_limit(doc, method=None):
    if not doc.customer:
        return  # no customer set yet — skip

    credit_limit = frappe.db.get_value("Customer", doc.customer, "trade_credit_limit") or 0
    if not credit_limit:
        return  # 0 means unlimited credit — skip

    # Sum all outstanding (unpaid) submitted invoices for this customer
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

`frappe.throw()` raises a `frappe.ValidationError`, which Frappe catches and returns as an HTTP error response with a user-friendly message. The save is aborted. The user sees a red error banner.

`frappe.format_value()` formats a number as currency using the site's locale settings (symbol, decimal separator, etc.).

**Design decisions:**
- `credit_limit = 0` means unlimited — allows customers with no credit restriction without requiring a special flag
- The check is on `validate` not `on_submit` — blocks the order at creation time, not just at submission
- Uses `docstatus = 1 AND outstanding_amount > 0` — only counts submitted, unpaid invoices

---

## 20. Frontend Assets — JS and CSS

### How Assets Get Loaded

The `app_include_js` and `app_include_css` hooks tell Frappe to inject the app's static assets into every page served by the desk. When the Frappe web server builds an HTML response, it iterates all installed apps' hooks and adds `<script>` and `<link>` tags for each registered asset.

Files in `apps/trade_mvp/trade_mvp/public/` are served at `/assets/trade_mvp/`. So `public/js/trade_mvp.js` becomes `/assets/trade_mvp/js/trade_mvp.js`.

### trade_mvp.js

```javascript
frappe.provide("trade_mvp");  // creates the trade_mvp namespace on the frappe object

frappe.ready(function () {
    const tradeRoles = [
        "Trade - Sales Executive",
        "Trade - Purchase Executive",
        "Trade - Warehouse Staff",
        "Trade - Accountant",
        "Trade - Manager",
    ];

    // frappe.user_roles comes from bootinfo — the server-sent role list
    const isTradeUser = tradeRoles.some((r) => frappe.user_roles.includes(r));
    if (!isTradeUser) return;

    // Add a CSS class to body to scope our CSS rules
    document.body.classList.add("trade-minimal");

    // frappe.after_ajax runs after every AJAX navigation
    // (Frappe desk is a SPA — navigating doesn't reload the page)
    frappe.after_ajax(function () {
        $('[data-label="Help"]').closest(".nav-item").hide();
        $('[data-label="Explore"]').closest(".nav-item").hide();
    });
});
```

**`frappe.provide(namespace)`** — creates a nested namespace on the `frappe` global object, used for organizing custom JavaScript code.

**`frappe.ready(fn)`** — equivalent to `$(document).ready()`, runs when the Frappe desk has initialized.

**`frappe.user_roles`** — the array of role names for the current user, populated from bootinfo when the page loads.

**`frappe.after_ajax(fn)`** — Frappe's SPA router fires this callback after every page navigation. Since navigating between pages doesn't reload the DOM, this is needed to re-apply DOM manipulations after each navigation.

### trade_mvp.css

```css
body.trade-minimal .navbar-help,
body.trade-minimal [data-label="Help"],
body.trade-minimal [data-label="Explore"] {
    display: none !important;
}
```

The `.trade-minimal` class is added to `<body>` by the JS above. This CSS then hides the Help and Explore navigation items for trade users. Using `!important` overrides any inline styles Frappe might set on these elements.

### Why Both JS and CSS?

The JS hides elements dynamically after each navigation (catching items that render after the initial page load). The CSS provides instant hiding before JS runs, preventing a flash where the items briefly appear. Together they're more robust than either alone.

---

## 21. The frappe.db API — Talking to the Database

Frappe provides a database abstraction layer used throughout `setup.py`. Understanding these API calls is essential for reading the code.

### Reading Data

```python
# Fetch a single field value from a single record
credit_limit = frappe.db.get_value("Customer", "Alpha Imports Ltd", "trade_credit_limit")
# → single value or None

# Fetch multiple records, returning a specific field as a flat list
roles = frappe.db.get_all(
    "Has Role",
    filters={"parent": user, "role": ["in", TRADE_ROLES]},
    pluck="role",
)
# → ["Trade - Sales Executive", "Trade - Manager"]

# Check if a record exists
if frappe.db.exists("Module Profile", "Trade User"):
    ...
# → returns name if exists, None if not

# Raw SQL with parameterized values (use %s for parameters, never f-strings with user data)
result = frappe.db.sql("""
    SELECT COALESCE(SUM(outstanding_amount), 0)
    FROM `tabSales Invoice`
    WHERE customer = %s AND docstatus = 1
""", customer_name)
# → [[value]] — always returns list of lists
```

### Writing Data

```python
# Create a new document in memory, then insert into DB
doc = frappe.new_doc("Custom DocPerm")
doc.parent = "Sales Order"
doc.role = "Trade - Sales Executive"
doc.read = 1
doc.write = 1
doc.insert(ignore_permissions=True)  # skips permission check — used in setup/install contexts

# Update a single field on an existing record (direct SQL UPDATE, no validation)
frappe.db.set_value("Custom DocPerm", "existing-name", {"read": 1, "write": 1})

# Fetch and modify an existing document (runs full validation on save)
doc = frappe.get_doc("Workspace Sidebar", "Sales")
doc.set("items", [])
doc.append("items", {"label": "Quotation", "type": "Link", ...})
doc.save(ignore_permissions=True)
```

### Cache Management

Frappe caches DocType metadata (field definitions, permissions, etc.) in Redis. When you modify these, you must invalidate the cache:

```python
frappe.clear_cache(doctype="Sales Order")  # clear cache for one doctype
frappe.cache.flushall()                     # flush ALL Redis cache (use sparingly)
```

After `after_install()` finishes, `frappe.cache.flushall()` ensures that no stale cached data will be served to the first users who log in.

### Table Naming Convention

All DocType data lives in tables named `tab` + DocType name. Spaces become spaces in the table name:
- `tabSales Order` ← Sales Order records
- `tabWorkspace` ← Workspace records
- `tabCustom DocPerm` ← Custom permission rows
- `tabHas Role` ← User-role assignments

When writing raw SQL, always use backtick-quoted table names to handle spaces correctly.

---

## 22. Demo Data — Seeding a Working Dataset

`demo.py` creates a minimal but realistic dataset to demonstrate the app. It is not called automatically — you run it manually: `bench execute trade_mvp.demo.create_demo_data`.

### Users

Five users, one per role, with a fixed password `Trade@1234`:

| Email | Role | Name |
|-------|------|------|
| sales@trade.local | Trade - Sales Executive | Sarah Sales |
| purchase@trade.local | Trade - Purchase Executive | Peter Purchase |
| warehouse@trade.local | Trade - Warehouse Staff | Wes Warehouse |
| accounts@trade.local | Trade - Accountant | Anna Accounts |
| manager@trade.local | Trade - Manager | Mike Manager |

`user.add_roles(role_name)` is the Frappe API for assigning roles. `send_welcome_email = 0` prevents the system from trying to send email during setup.

### Items

Five inventory items representing different product categories:

| Code | Name | Unit |
|------|------|------|
| ELEC-001 | Electronics Component | Nos |
| TEXT-001 | Industrial Textile | Meter |
| CHEM-001 | Chemical Raw Material | Kg |
| MACH-001 | Machinery Part | Nos |
| CONS-001 | Consumer Goods | Nos |

`gst_hsn_code` is required by india_compliance (GST harmonised system nomenclature code).

### Customers

Three customers demonstrating different credit situations:

| Customer | Credit Limit | Scenario |
|---------|-------------|---------|
| Alpha Imports Ltd | 100,000 | Medium limit |
| Beta Trading Co | 75,000 | Lower limit |
| Gamma Distributors | 0 | Unlimited credit |

`trade_credit_limit = 0` triggers the unlimited-credit path in `check_credit_limit()`.

### Suppliers

Three suppliers from different countries representing an import trading company's typical sourcing geography:

| Supplier | Country |
|---------|---------|
| XYZ Exports | China |
| ABC Manufacturing | Germany |
| Global Sourcing LLC | United Arab Emirates |

All demo data functions check `frappe.db.exists()` before creating, so the function is safe to run multiple times — existing records are skipped, not duplicated.

---

## 23. Tests — Unit Testing Without a Running Site

### The Challenge

`check_credit_limit` in `setup.py` imports `frappe` and calls `frappe.db.get_value()`, `frappe.db.sql()`, and `frappe.throw()`. Normally these require a running Frappe site with a MariaDB database. But we want fast, isolated unit tests.

### The Solution: Mocking frappe Before Import

The test file installs a `MagicMock` as the `frappe` module into `sys.modules` before `trade_mvp.setup` is ever imported. Python's import machinery checks `sys.modules` first, so when `setup.py` does `import frappe`, it gets the mock instead of the real thing.

```python
import sys
from unittest.mock import MagicMock

def _make_frappe_mock():
    mock_frappe = MagicMock()
    sys.modules["frappe"] = mock_frappe
    for sub in ("frappe.utils", "frappe.model", "frappe.model.document"):
        sys.modules.setdefault(sub, MagicMock())
    return mock_frappe

_frappe_mock = _make_frappe_mock()  # must run before any import of trade_mvp.setup
```

### The Tests

Each test controls what the mock returns and asserts what was called:

```python
def test_over_limit_throws(self):
    _frappe_mock.db.get_value.return_value = 50_000   # credit limit = 50k
    _frappe_mock.db.sql.return_value = [[40_000]]     # outstanding = 40k
    _frappe_mock.throw.side_effect = Exception("blocked")

    with self.assertRaises(Exception):
        check_credit_limit(self._make_so("CUST-001", 20_000))  # 40k + 20k > 50k

    _frappe_mock.throw.assert_called_once()  # must have called frappe.throw
```

The five test cases cover:
1. `credit_limit = 0` → unlimited, no throw
2. Outstanding + total within limit → no throw
3. Outstanding + total over limit → throws
4. `doc.customer = None` → skip entirely, `db.get_value` never called
5. Outstanding exactly equal to limit → no throw (boundary case)

---

## 24. The Complete Install Flow

When `bench install-app trade_mvp` runs on the site, here is the exact sequence of events:

```
bench install-app trade_mvp
│
├── Frappe registers the app in site_config (apps list)
├── Frappe runs bench migrate (applies any schema changes)
│
└── Frappe calls after_install() from hooks.py
    │
    ├── 1. sync_fixtures("trade_mvp")
    │      ├── Reads fixtures/role.json → upserts 5 Role records
    │      ├── Reads fixtures/custom_field.json → upserts 10 Custom Field records
    │      │      └── Frappe adds columns to tabSales Order, tabCustomer, etc.
    │      └── Reads fixtures/workflow.json → upserts 3 Workflow records
    │
    ├── 2. hide_default_workspaces()
    │      └── SQL: UPDATE tabWorkspace SET is_hidden=1 WHERE name NOT IN (trade workspaces)
    │
    ├── 3. setup_permissions()
    │      └── For each (role, doctype) in TRADE_PERMISSIONS:
    │             INSERT or UPDATE tabCustom DocPerm row
    │             frappe.clear_cache(doctype=...)
    │
    ├── 4. setup_module_profiles()
    │      └── INSERT "Trade User" Module Profile with 26 blocked modules
    │
    ├── 5. setup_property_setters()
    │      └── For each (doctype, fieldname) in HIDE_FIELDS:
    │             INSERT tabProperty Setter with hidden=1
    │
    ├── 6. setup_workspace_sidebars()
    │      └── For each workspace in SIDEBAR_ITEMS:
    │             Load Workspace Sidebar record
    │             Clear existing items
    │             Append items from SIDEBAR_ITEMS definition
    │             doc.save()
    │
    ├── 7. frappe.db.commit()
    │
    ├── 8. create_workspace_sidebar_for_workspaces()
    │      └── Creates Workspace Sidebar records for any workspaces that lack them
    │
    ├── 9. create_desktop_icons_from_workspace()
    │      └── Creates Desktop Icon records for each workspace
    │
    ├── 10. SQL: UPDATE tabWorkspace SET module='' WHERE name IN (trade workspaces)
    │          (bypasses allow_modules check — see section 12)
    │
    ├── 11. SQL: UPDATE tabWorkspace Sidebar SET module=NULL WHERE title IN (trade workspaces)
    │
    └── 12. frappe.cache.flushall()
           └── Clears all Redis cache so no stale data is served
```

After this, optionally:
```
bench execute trade_mvp.demo.create_demo_data
└── Creates 5 users + 5 items + 3 customers + 3 suppliers
```

---

## 25. The Complete Login Flow

When a trade user opens the browser and logs in:

```
Browser → POST /api/method/login
│
└── Frappe authenticates credentials, creates session
    │
    └── Browser → GET /api/method/frappe.client.get_boot
        │
        └── frappe/boot.py: get_bootinfo()
            │
            ├── get_user(bootinfo)
            │    └── Loads user profile, roles, module profile
            │         (computes allow_modules from "Trade User" Module Profile)
            │
            ├── load_desktop_data(bootinfo)
            │    ├── Loads workspace records (filtered by allow_modules — but
            │    │    trade workspaces have module="" so they always pass)
            │    ├── Loads workspace_sidebar_item dict (same filter logic)
            │    └── Loads app_data (all installed apps)
            │
            ├── get_desktop_icons(bootinfo)
            │    └── Returns cached or freshly built list of desktop icons
            │         (cached in Redis as desktop_icons:{user})
            │
            ├── [... many other bootinfo fields assembled ...]
            │
            └── boot_session hook: filter_bootinfo_for_trade_users(bootinfo)
                 │
                 ├── Queries Has Role → gets user's trade roles
                 ├── Computes allowed workspaces from ROLE_WORKSPACES
                 ├── _filter_workspaces() → removes non-allowed workspace pages
                 ├── _filter_desktop_icons() → removes non-allowed icons
                 ├── _filter_sidebar() → removes non-allowed sidebar entries
                 └── _filter_app_data() → keeps only trade_mvp in app switcher

Boot JSON sent to browser (contains only trade workspaces, no ERPNext clutter)
│
Browser renders desk:
├── trade_mvp.js runs → detects trade role → adds .trade-minimal to body
├── trade_mvp.css hides Help + Explore nav items
└── Home screen shows only Pipeline/Sales (or role-appropriate subset) tiles
```

---

## 26. The Business Rules Summary

Trade MVP implements a complete access control and business rule system for a trading company:

### Access Control (who can see and do what)

| Role | Workspaces | Key Capabilities |
|------|-----------|-----------------|
| Sales Executive | Pipeline, Sales | Create leads/opportunities, manage quotations and sales orders, read-only on invoices |
| Purchase Executive | Purchasing | Create and submit purchase orders, read-only on invoices and sales |
| Warehouse Staff | Warehouse | Receive and ship stock (Purchase Receipts, Delivery Notes, Stock Entries), read-only on orders |
| Accountant | Finance, Asset Register | Create and submit invoices and payments, manage assets |
| Manager | All six | Full create/edit/delete/submit across all documents |

### Approval Workflows (who must approve what)

| Document | Created By | Approved By |
|---------|-----------|-------------|
| Sales Order | Sales Executive | Manager |
| Purchase Order | Purchase Executive | Manager |
| Payment Entry | Accountant | Manager |

### Business Rules (automatic enforcement)

| Rule | Trigger | Enforcement |
|------|---------|-------------|
| Credit limit | Every Sales Order save | `check_credit_limit()` via doc_events validate hook |
| Approval required | Submit attempt on SO/PO/Payment | Workflow state machine blocks direct submission |

### UI Simplification (what's hidden from view)

- 25+ ERPNext modules hidden via Module Profile
- All default ERPNext workspaces hidden (is_hidden = 1)
- 100+ fields hidden across 12 DocTypes via Property Setter
- Help and Explore nav items hidden via JS/CSS for trade users
- App switcher shows only trade_mvp (bootinfo filter)

---

*This document covers every mechanism in the trade_mvp codebase. Each concept builds on the previous: DocTypes are the foundation, hooks.py is the registry, fixtures ship the data, after_install creates the configuration, and boot_session + doc_events provide the runtime behaviour.*
