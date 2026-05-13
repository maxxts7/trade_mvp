# Frappe v16 Desktop Icon Visibility — How It Works & How We Debugged It

## The Problem

After installing `trade_mvp`, logging in as any trade role user (e.g. `sales@trade.local`) showed a blank desktop — no workspace icons visible, despite the workspaces existing in the database.

---

## How Desktop Icon Visibility Works in Frappe v16

### Four separate data structures

When a user loads the desk, `get_bootinfo()` in `frappe/boot.py` populates four things that together control what the user sees:

| Structure | What it is | How it's built |
|---|---|---|
| `bootinfo.workspaces["pages"]` | List of workspace pages the user is allowed to see | `get_workspace_sidebar_items()` in `frappe/desk/desktop.py` |
| `bootinfo.workspace_sidebar_item` | Dict of sidebar content keyed by workspace name (lowercase) | `get_sidebar_items(allowed_pages)` in `frappe/boot.py` |
| `bootinfo.desktop_icons` | The actual icon tiles on the home screen | `get_desktop_icons(bootinfo)` in `frappe/desk/doctype/desktop_icon/desktop_icon.py` |
| `bootinfo.app_data` | App-switcher tiles (ERPNext, Framework, etc.) | Populated in `load_desktop_data()` |

They are populated in this order in `get_bootinfo()`:

```
load_desktop_data(bootinfo)        # → workspaces, workspace_sidebar_item, app_data
get_desktop_icons(bootinfo)        # → desktop_icons  (depends on sidebar being populated first)
boot_session hooks                 # → our filter_bootinfo_for_trade_users runs here
```

### Step 1 — `get_workspace_sidebar_items()` (which workspaces are visible)

`frappe/desk/desktop.py:381`

Queries all `Workspace` records with these SQL filters:
- `restrict_to_domain NOT IN [active_domains, None]`
- `module NOT IN blocked_modules`

Then for each matching workspace it instantiates `Workspace(page, minimal=True)`.

**Critical check in `Workspace.__init__()` (lines 42–48):**

```python
if (
    self.doc.module
    and self.doc.module not in self.allowed_modules
    and not self.workspace_manager
):
    raise frappe.PermissionError
```

`allowed_modules` is built from `user.allow_modules`, which Frappe derives from the set of DocTypes the user has read permission on — grouped by module. If the workspace's `module` field is set to a module that has no readable DocTypes, the workspace is silently excluded via `except frappe.PermissionError: pass`.

If zero workspaces pass, Frappe falls back to the `Welcome Workspace` as a safety net.

### Step 2 — `get_sidebar_items(allowed_pages)` (sidebar content)

`frappe/boot.py:543`

Iterates all `Workspace Sidebar` records. For each one, it checks:

```python
if (
    frappe.session.user == "Administrator"
    or sidebar_title == "My Workspaces"
    or not sidebar_doc.module           # ← passes if module is NULL/empty
    or sidebar_doc.module in sidebar_doc.user.allow_modules
):
```

For each item inside the sidebar it then calls `sidebar_doc.is_item_allowed(link_to, link_type, allowed_pages)`, which checks:
- `DocType` items: user can read it + not domain-restricted + `frappe.has_permission()`
- `Workspace` items: the workspace name is in `allowed_pages`
- `Report`, `Dashboard`, `URL`, `Help`: their own checks

The result is `bootinfo.workspace_sidebar_item`, a dict like:
```python
{
    "pipeline": {"label": "Pipeline", "items": [...]},
    "sales":    {"label": "Sales",    "items": [...]},
    ...
}
```

### Step 3 — `get_desktop_icons(bootinfo)` (the icon tiles)

`frappe/desk/doctype/desktop_icon/desktop_icon.py`

Fetches all `Desktop Icon` records, then calls `icon.is_permitted(bootinfo)` for each:

- **`icon_type == "Link"`** — checks `bootinfo.workspace_sidebar_item[label.lower()]` exists **and** its `items` list is non-empty. If the key is missing or items is empty → icon hidden.
- **`icon_type == "Folder"`** — always passes (no check).
- **`icon_type == "App"`** — checks `has_permission` hook if defined, otherwise passes.

Results are cached in Redis as `desktop_icons:{user}`. Stale cache shows wrong icons until `bench clear-cache`.

### Step 4 — `filter_bootinfo_for_trade_users(bootinfo)` (our hook)

`trade_mvp/setup.py`, registered as a `boot_session` hook.

Runs **after** `get_desktop_icons()` has already computed and cached its result. Filters all four structures down to the workspaces the user's trade role is allowed to see:

```python
allowed = set()
for role in user_trade_roles:
    allowed.update(ROLE_WORKSPACES.get(role, []))
```

Removes workspaces, icons, sidebar entries, and app tiles outside `allowed`.

---

## What Was Wrong

### Symptom

`get_workspace_sidebar_items()` returned `['Welcome Workspace']` for every trade user. Because `allowed_pages = ['Welcome Workspace']`, all trade sidebar item lists came back empty, so `is_permitted()` returned False for all trade Desktop Icons → blank screen.

### Root cause

All six workspace fixture JSONs had `"module": "Trade MVP"`. The app `trade_mvp` has no DocTypes, so "Trade MVP" is never added to `user.allow_modules`. When `Workspace.__init__()` checked:

```python
self.doc.module not in self.allowed_modules
# "Trade MVP" not in [] → True → raise PermissionError
```

Every trade workspace was silently dropped. Zero pages passed → fallback to Welcome Workspace.

---

## How We Debugged It

### 1. Confirmed the symptom in bench console

```python
frappe.set_user("sales@trade.local")
pages = get_workspace_sidebar_items()
# → ['Welcome Workspace']   ← wrong
```

### 2. Ruled out SQL filter

Checked the DB directly:

```sql
SELECT name, is_hidden, module, public FROM `tabWorkspace`
WHERE name IN ('Pipeline', 'Sales', ...);
-- All is_hidden=0, public=1 → not filtered by SQL
```

Checked user's blocked_modules:

```sql
SELECT * FROM `tabBlock Module` WHERE parent = 'sales@trade.local';
-- Empty → blocked_modules = ['Dummy Module'] only → 'Trade MVP' passes NOT IN check
```

### 3. Traced the code path

Read `get_workspace_sidebar_items()` carefully. The SQL query would return all 6 trade workspaces. But then `Workspace(page, True)` is called in a try/except. When a PermissionError is raised it silently skips the page.

Traced into `Workspace.__init__()` and found lines 42–48: the `allowed_modules` check. Confirmed "Trade MVP" is absent from `user.allow_modules` because the app has no DocTypes for the ORM to include.

### 4. Verified the allow_modules logic

```python
frappe.set_user("sales@trade.local")
user = frappe.get_user()
user.build_permissions()
print(user.allow_modules)
# → ['Selling', 'CRM', ...] — no 'Trade MVP'
```

### 5. Identified the fix

Setting `module = ""` (empty string) makes the check `if self.doc.module` evaluate to False — the whole `PermissionError` block is skipped. The workspace passes through.

The same `module` field on `Workspace Sidebar` records was already cleared to `NULL` for a related reason: `get_sidebar_items()` has an equivalent `module in allow_modules` gate.

---

## The Fix

### 1. Workspace fixture JSONs — clear the module field

In all six workspace JSON files under `trade_mvp/trade_mvp/workspace/`:

```json
"module": ""
```

(was `"Trade MVP"`)

### 2. Database — apply the same change live

```sql
UPDATE `tabWorkspace` SET module = '' WHERE name IN (
    'Pipeline', 'Sales', 'Purchasing', 'Warehouse', 'Finance', 'Asset Register'
);
```

### 3. `after_install()` — persist across reinstalls

```python
# trade_mvp/setup.py  after_install()

if TRADE_WORKSPACES:
    placeholders = ", ".join(["%s"] * len(TRADE_WORKSPACES))
    # Clear module on Workspace so the allow_modules PermissionError is not raised
    frappe.db.sql(
        f"UPDATE `tabWorkspace` SET module = '' WHERE name IN ({placeholders})",
        TRADE_WORKSPACES,
    )
    # Clear module on Workspace Sidebar so get_sidebar_items() includes them unconditionally
    frappe.db.sql(
        f"UPDATE `tabWorkspace Sidebar` SET module = NULL WHERE title IN ({placeholders})",
        TRADE_WORKSPACES,
    )
```

---

## Verification

After the fix, bench console confirmed:

```python
frappe.set_user("sales@trade.local")

pages = get_workspace_sidebar_items()
# → ['Pipeline', 'Sales', 'Purchasing', 'Warehouse', 'Finance', 'Asset Register'] ✓

sidebar = get_sidebar_items(allowed)
# → {'pipeline': {..., 'items': [...]}, 'sales': {..., 'items': [...]}, ...} ✓

icons = get_desktop_icons(bootinfo=bootinfo)
# → 10 icons including ERPNext, Framework, etc.

filter_bootinfo_for_trade_users(bootinfo)
# → ['Pipeline', 'Sales']  ← exactly what the sales role should see ✓
```

---

## Key Files Reference

| File | Relevance |
|---|---|
| `frappe/boot.py:60–61` | `load_desktop_data()`, `get_desktop_icons()` call order |
| `frappe/boot.py:543` | `get_sidebar_items()` — sidebar population and item permission checks |
| `frappe/desk/desktop.py:381` | `get_workspace_sidebar_items()` — workspace list |
| `frappe/desk/desktop.py:42–48` | `Workspace.__init__()` — the `allow_modules` gate that was blocking trade workspaces |
| `frappe/desk/doctype/desktop_icon/desktop_icon.py` | `get_desktop_icons()`, `is_permitted()` |
| `frappe/desk/doctype/workspace_sidebar/workspace_sidebar.py:81` | `is_item_allowed()` — per-item permission inside sidebar |
| `trade_mvp/setup.py` | `after_install()`, `filter_bootinfo_for_trade_users()`, `ROLE_WORKSPACES` |
