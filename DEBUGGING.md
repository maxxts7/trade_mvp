# Debugging Log — Trade MVP

Three bugs were hit in sequence. Each one exposed a different Frappe subsystem.
This document records the root cause, the investigation path, and the fix for each,
along with a detailed explanation of the underlying Frappe concept.

---

## Bug 1 — Sidebar invisible after adding dashboard content

### Symptom
After editing `setup.py` to add `SIDEBAR_ITEMS` (including Dashboard links) and
running setup, the left-hand navigation panel inside workspace pages was completely
blank for trade users.

### Investigation

**Step 1 — Check the DB state**

```sql
SELECT name, title, module
FROM `tabWorkspace Sidebar`
WHERE title IN ('Pipeline','Sales','Purchasing','Warehouse','Finance','Asset Register');
```

Result: all six records existed, but `module` was set to ERPNext module names
(`CRM`, `Selling`, `Buying`, `Stock`, `Accounts`, `Assets`).

**Step 2 — Trace the filter**

`frappe/boot.py:167` builds `bootinfo.workspace_sidebar_item` by calling
`get_sidebar_items(allowed_pages)`. Inside that function (`boot.py:543`):

```python
workspace_sidebars = frappe.get_all("Workspace Sidebar", ...)

for sidebar in workspace_sidebars:
    sidebar_doc = frappe.get_doc("Workspace Sidebar", sidebar_title)
    if (
        frappe.session.user == "Administrator"
        or sidebar_title == "My Workspaces"
        or not sidebar_doc.module          # ← NULL passes this check
        or sidebar_doc.module in sidebar_doc.user.allow_modules
    ):
        sidebar_items[sidebar_title.lower()] = { ... }
```

The check `sidebar_doc.module in sidebar_doc.user.allow_modules` failed because
the "Trade User" Module Profile blocks `Selling`, `CRM`, `Buying`, etc.
The `not sidebar_doc.module` branch (NULL/empty passes) was the intended escape hatch,
but `module` was NOT NULL.

**Step 3 — Trace how the module field got set**

`setup_workspace_sidebars()` calls `doc.save()` on each `Workspace Sidebar`.
`Workspace Sidebar.before_save()` always calls `set_module()`:

```python
def set_module(self):
    if not self.module:
        self.module = self.get_module_from_items()
```

`get_module_from_items()` inspects every sidebar item, calls
`frappe.get_doc(item.link_type, item.link_to).module` to find the most common module,
and writes it back. Items like `Quotation` → module `Selling`, `Lead` → module `CRM`.
So every save of a sidebar doc auto-populates `module` with an ERPNext module name,
overwriting the NULL we needed.

The SQL in `after_install()` that was supposed to clear this
(`UPDATE tabWorkspace Sidebar SET module = NULL ...`) ran before the sidebar records
existed (they were created by `create_workspace_sidebar_for_workspaces()` later),
so it had no effect.

### Fix

Direct SQL on the live DB, then flush cache:

```sql
UPDATE `tabWorkspace Sidebar`
SET module = NULL
WHERE title IN ('Pipeline','Sales','Purchasing','Warehouse','Finance','Asset Register');
```

```bash
bench --site frappe_mvp.localhost clear-cache
```

The permanent fix in `after_install()` is: call the module-clearing SQL **after**
`create_workspace_sidebar_for_workspaces()`, not before.

---

### Frappe Concept: Workspace Sidebar & the module field

In Frappe v16 the left-nav panel within a workspace is driven by a separate DocType
called **Workspace Sidebar**. It is distinct from the `Workspace` record itself.

**Data flow at login:**

```
boot.py:get_bootinfo()
  → load_desktop_data(bootinfo)
      → get_workspace_sidebar_items()       → bootinfo.workspaces["pages"]
      → get_sidebar_items(allowed_pages)    → bootinfo.workspace_sidebar_item
  → boot_session hooks fire
      → filter_bootinfo_for_trade_users()   → strips to role-allowed workspaces
```

**The module gate in `get_sidebar_items()`:**

```python
if (
    user == "Administrator"
    or sidebar_title == "My Workspaces"
    or not sidebar_doc.module          # empty/NULL → always shown
    or sidebar_doc.module in user.allow_modules
):
    sidebar_items[sidebar_title.lower()] = { ... }
```

If `module` is set to an ERPNext module name that is blocked in the user's
Module Profile, the entire sidebar entry is excluded and the panel is blank.
Setting `module = NULL` (or `""`) makes the sidebar unconditionally included,
which is correct for Trade workspaces that span multiple ERPNext modules.

**The `before_save` trap:**

`Workspace Sidebar.before_save()` calls `set_module()` which re-derives the module
from the items' DocType modules. This means:
- Any `doc.save()` call will overwrite a manually-set NULL.
- Direct SQL is required to set `module = NULL` durably.
- Alternatively, items can be "URL" type (excluded from the module scan) to prevent
  auto-derivation, but the SQL approach is simpler.

**The `is_item_allowed` per-item check:**

Even after the sidebar entry passes the outer gate, each item is individually
filtered by `sidebar_doc.is_item_allowed(link_to, link_type, allowed_workspaces)`:

| link_type  | Rule |
|------------|------|
| `DocType`  | `link_to in can_read AND link_to in restricted_doctypes AND has_permission(link_to)` |
| `Dashboard`| always `True` |
| `Workspace`| `link_to in allowed_workspaces` |
| `Page`     | `link_to in allowed_pages` |
| `Report`   | `link_to in allowed_reports` |

For DocType items: `can_read` is populated by `UserPermissions.build_permissions()`
and cached under the Redis key `user_perm_can_read` — first populated by the
`Workspace` class during `get_workspace_sidebar_items()`, then re-used by
`WorkspaceSidebar` (which has a broken `get_can_read_items()` that doesn't return
the list, relying on the prior cache fill).

`restricted_doctypes` comes from `frappe.cache.get_value("domain_restricted_doctypes")` —
this is the list of all doctypes accessible under active domains. With no domains
restricted, it contains every doctype, so all items with correct read permission pass.

---

## Bug 2 — "does not have doctype access via role permission for document Workflow State"

### Symptom
After fixing the sidebar, clicking a Sales Order produced:
> User sales@trade.local does not have doctype access via role permission for document Workflow State

### Investigation

**Step 1 — Find the throw site**

`frappe/permissions.py:171`:
```python
if not perm:
    push_perm_check_log(
        _("User {0} does not have doctype access via role permission for document {1}")
        .format(frappe.bold(user), frappe.bold(_(doctype))), debug=debug
    )
```

**Step 2 — Find what triggers `has_permission("Workflow State")`**

`frappe/desk/form/meta.py:210`:
```python
def load_workflows(self):
    workflow_name = self.get_workflow()
    workflow_docs = []
    if workflow_name and frappe.db.exists("Workflow", workflow_name):
        workflow = frappe.get_doc("Workflow", workflow_name)          # ← checks perm
        workflow_docs.append(workflow)
        workflow_docs.extend(
            frappe.get_doc("Workflow State", d.state)                 # ← checks perm
            for d in workflow.get("states")
        )
    self.set("__workflow_docs", workflow_docs)
```

`load_workflows()` is called when loading the form metadata for any doctype that has
an active workflow. For Sales Order → "Trade SO Approval" workflow is active →
`frappe.get_doc("Workflow", "Trade SO Approval")` and
`frappe.get_doc("Workflow State", "Draft")` are called.
`frappe.get_doc` checks permissions before returning.

**Step 3 — Check existing permissions**

```sql
SELECT parent, role, `read`
FROM `tabDocPerm`
WHERE parent IN ('Workflow', 'Workflow State')
ORDER BY parent, role;
```

Result:
```
Workflow        System Manager   1
Workflow State  Desk User        0
Workflow State  System Manager   1
```

Trade roles had zero entries (no Custom DocPerm, and the built-in rows gave them
nothing). `has_permission("Workflow State", "read", user="sales@trade.local")` → False.

### Fix

Added to `TRADE_PERMISSIONS` in `setup.py` for all five Trade roles:
```python
("Workflow",       1, 0, 0, 0, 0, 0, 0),   # read-only
("Workflow State", 1, 0, 0, 0, 0, 0, 0),   # read-only
```

Applied immediately by running `setup_permissions()` on the live DB, then cleared cache.

---

### Frappe Concept: Custom DocPerm and the permission resolution order

Frappe has two permission tables:

| Table | Source | Priority |
|-------|--------|----------|
| `tabDocPerm` | Built into the DocType JSON (app code) | Lower |
| `tabCustom DocPerm` | Stored in DB, created by apps or admins | Higher — **replaces** built-in perms |

**Critical rule:** Once ANY `Custom DocPerm` row exists for a doctype, Frappe uses
**only** Custom DocPerm rows for that doctype and ignores all built-in `DocPerm`.
This is checked in `frappe/permissions.py:get_valid_perms()`:

```python
custom_perms = get_perms_for(roles, "Custom DocPerm")
doctypes_with_custom_perms = get_doctypes_with_custom_docperms()

# If doctype has custom perms, only custom perms apply
if doctype in doctypes_with_custom_perms:
    return custom_perms
else:
    return builtin_perms
```

Consequence: if you add a Custom DocPerm row for `Sales Order` for one role, you
**must** also add rows for every other role that needs access — the built-in rows no
longer apply for `Sales Order` at all. `setup_permissions()` handles this by
inserting rows for all five Trade roles for every doctype they need.

**The seven permission bits:**
```python
(doctype, read, write, create, delete, submit, cancel, amend)
```
- `read` — can see the document
- `write` — can edit saved documents
- `create` — can create new documents
- `delete` — can delete documents
- `submit` — can submit (docstatus 0→1)
- `cancel` — can cancel (docstatus 1→2)
- `amend` — can amend a cancelled document (creates a new copy)

`submit/cancel/amend` are only meaningful for submittable documents
(`is_submittable = 1` in the DocType definition). For non-submittable types like
`Workflow State` or `Customer`, only read/write/create/delete matter.

**Why `Workflow` and `Workflow State` need explicit read perms:**

Core configuration doctypes in Frappe (`Workflow`, `Workflow State`,
`DocType`, `DocField`, etc.) default to `System Manager` only. Any custom role needs
an explicit Custom DocPerm entry. Trade roles are not System Managers, so they need
their own rows even for purely read-only access to framework configuration documents.

---

## Bug 3 — "Workflow State Draft not found"

### Symptom
Even after fixing permissions, Sales Order still failed:
> Not found — Workflow State Draft not found

### Investigation

**Step 1 — Check what Workflow State records exist**

```sql
SELECT name, style FROM `tabWorkflow State` ORDER BY name;
```

Result:
```
Approved   Success
Pending
Rejected   Danger
```

The records "Draft" and "Pending Approval" did not exist.

**Step 2 — Trace the 404**

`meta.py:219` calls `frappe.get_doc("Workflow State", d.state)` for each state in the
workflow. "Trade SO Approval" has four states: `Draft`, `Pending Approval`, `Approved`,
`Rejected`. `frappe.get_doc("Workflow State", "Draft")` → record not found → 404.

**Step 3 — Understand why they were missing**

The Trade workflow fixture (`fixtures/workflow.json`) creates `Workflow` records that
reference state names like `"state": "Draft"`. But `Workflow State` is a **separate
DocType** with its own records. The workflow fixture does not auto-create
`Workflow State` records — they must exist independently.

The DB only had the three states that happen to be default ERPNext records
(`Approved`, `Pending`, `Rejected`). `Draft` and `Pending Approval` were never
created because no fixture covered them.

### Fix

**Live DB:** Direct SQL insert:
```sql
INSERT IGNORE INTO `tabWorkflow State`
  (name, workflow_state_name, style, docstatus, idx, owner, creation, modified, modified_by)
VALUES
  ('Draft',           'Draft',           '',        0, 0, 'Administrator', NOW(), NOW(), 'Administrator'),
  ('Pending Approval','Pending Approval','Warning',  0, 0, 'Administrator', NOW(), NOW(), 'Administrator');
```

**Fixture:** Created `fixtures/workflow_state.json`:
```json
[
  {"doctype": "Workflow State", "name": "Draft",            "style": ""},
  {"doctype": "Workflow State", "name": "Pending Approval", "style": "Warning"},
  {"doctype": "Workflow State", "name": "Approved",         "style": "Success"},
  {"doctype": "Workflow State", "name": "Rejected",         "style": "Danger"}
]
```

Added to `hooks.py` **before** the Workflow fixture (correct order — states must
exist before workflows reference them):
```python
fixtures = [
    {"dt": "Role",           "filters": [["name", "like", "Trade%"]]},
    {"dt": "Custom Field",   "filters": [["module", "=", "Trade MVP"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft","Pending Approval","Approved","Rejected"]]]},
    {"dt": "Workflow",       "filters": [["name", "like", "Trade%"]]},
]
```

---

### Frappe Concept: Fixtures — what they are and how they work

**What fixtures are:**

Fixtures are JSON files in `{app}/fixtures/` that capture the state of specific
DocType records and sync them into any site where the app is installed. They are the
standard way to ship "seed data" that an app depends on: roles, custom fields,
workflows, print formats, etc.

**Fixture lifecycle:**

```
bench export-fixtures         →  reads DB, writes JSON files
sync_fixtures(app)            →  reads JSON files, upserts into DB
bench migrate                 →  calls sync_fixtures for all apps
after_install hook            →  typically calls sync_fixtures manually first
```

**How `hooks.py` defines what to fixture:**

```python
fixtures = [
    # Simple form: fixture the entire doctype
    "Role",

    # Dict form: fixture only rows matching filters
    {"dt": "Workflow",       "filters": [["name", "like", "Trade%"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft","Pending Approval"]]]},
]
```

`export-fixtures` uses the filters to SELECT which rows to write to JSON.
`sync_fixtures` reads every JSON file in `fixtures/` and upserts all records in it,
regardless of filters — the filter is only used for export scoping.

**Fixture sync order matters:**

Fixtures are imported in filename alphabetical order by default:
`custom_field.json` → `role.json` → `workflow.json` → `workflow_state.json`

Since `Workflow` records reference `Workflow State` names, `workflow_state.json` must
be synced **before** `workflow.json`. The alphabetical ordering `workflow.json` <
`workflow_state.json` means `workflow_state` comes AFTER `workflow` — which is wrong.

The safe fix is to rename: e.g. `z_workflow.json` to push it last, or to call
`sync_fixtures` with explicit ordering in `after_install()`. Alternatively, ensure
the `Workflow State` import is idempotent (using `INSERT IGNORE` / upsert) so a
second pass on workflow re-validation still works.

In the trade_mvp app, `after_install()` calls `sync_fixtures("trade_mvp")` once
which processes files alphabetically. With the current filenames:
```
custom_field.json     ← 1st
role.json             ← 2nd
workflow.json         ← 3rd   (references Draft, Pending Approval)
workflow_state.json   ← 4th   (creates Draft, Pending Approval)
```
The workflow imports before the states it references. This does not cause an install
error because Frappe's workflow validation is deferred, but it means the states are
not in place when the workflow is first synced.

**Recommended fix:** rename to `workflow_state.json` → `a_workflow_state.json`
(or prefix numerically: `01_role.json`, `02_workflow_state.json`, `03_workflow.json`)
to enforce the correct order.

---

## Summary table

| Bug | Frappe subsystem | Root cause | Fix |
|-----|-----------------|------------|-----|
| Sidebar invisible | Workspace Sidebar / Module Profile | `set_module()` in `before_save` auto-set `module` to a blocked ERPNext module name | `UPDATE tabWorkspace Sidebar SET module = NULL` + cache clear |
| Workflow State permission error | Custom DocPerm / `has_permission` | `Workflow` and `Workflow State` have only `System Manager` read perm; Trade roles had no entries | Added `("Workflow", 1,0,0,0,0,0,0)` and `("Workflow State", 1,0,0,0,0,0,0)` to all five roles in `TRADE_PERMISSIONS` |
| Workflow State Draft not found | Fixtures / DocType data integrity | `Workflow State` is an independent DocType; "Draft" and "Pending Approval" records were never created | Created records in DB; added `workflow_state.json` fixture to `hooks.py` before `workflow.json` |

---

## Key files touched

| File | What changed |
|------|-------------|
| `trade_mvp/setup.py` | Added `Workflow` + `Workflow State` read perms to all five `TRADE_PERMISSIONS` entries |
| `trade_mvp/hooks.py` | Added `Workflow State` fixture entry (before `Workflow`) |
| `trade_mvp/fixtures/workflow_state.json` | New file — four state records: Draft, Pending Approval, Approved, Rejected |
| Live DB: `tabWorkspace Sidebar` | `module` set to NULL on six trade workspace rows |
| Live DB: `tabCustom DocPerm` | Ten new rows: Workflow + Workflow State, all five roles, read=1 |
| Live DB: `tabWorkflow State` | Two new rows: Draft and Pending Approval |
