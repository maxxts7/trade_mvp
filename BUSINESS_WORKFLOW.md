# Trade MVP — Business Workflow Guide

> Quotation to GL Entry: end-to-end flow for an import/export trading company built on ERPNext v16.

---

## Overview

Trade MVP is a simplified trading overlay on ERPNext. It does not replace ERPNext's accounting engine — it constrains and configures it for a small import/export business with five clearly separated roles, approval gates on every major transaction, and trade-finance fields (LC number, ports) on all commercial documents.

---

## Actors

| Role | User | Workspace(s) | What they own |
|---|---|---|---|
| Trade - Sales Executive | Sarah Sales | Pipeline, Sales | Leads, Opportunities, Quotations, Sales Orders |
| Trade - Purchase Executive | Peter Purchase | Purchasing | Purchase Orders |
| Trade - Warehouse Staff | Wes Warehouse | Warehouse | Purchase Receipts, Delivery Notes, Stock Entries |
| Trade - Accountant | Anna Accounts | Finance, Asset Register | Sales Invoices, Purchase Invoices, Payment Entries, Assets |
| Trade - Manager | Mike Manager | All 6 workspaces | Approves SO, PO, and Payment workflows; full read/write everywhere |

Default password for all demo users: `Trade@1234`

---

## Sales Cycle

```
Lead → Opportunity → Quotation → Sales Order → Delivery Note → Sales Invoice → Payment Entry
[CRM]    [CRM]        [Sales]      [Sales]        [Warehouse]     [Finance]       [Finance]
```

### 1. Lead (Sarah — Pipeline workspace)

Sarah logs a **Lead** when a potential buyer makes contact. Fields: company name, contact, source, estimated value. No financial impact.

### 2. Opportunity (Sarah — Pipeline workspace)

The Lead is qualified into an **Opportunity** once there is a real business requirement. Tracks expected revenue and close date. Still no financial impact.

### 3. Quotation (Sarah — Sales workspace)

Sarah raises a formal **Quotation** for the customer with line items, pricing, taxes, and incoterms.

**Trade-specific fields added by this app:**

| Field | Purpose |
|---|---|
| Port of Loading | Origin port where goods will be shipped from |
| Port of Discharge | Destination port at customer's end |
| LC Number | Letter of Credit reference — key for international trade finance |

On customer acceptance, the Quotation is converted to a Sales Order with one click.

### 4. Sales Order (Sarah → Mike — Sales workspace)

The Sales Order is the binding commercial commitment. Two things happen here specific to this app:

#### Credit Limit Check (on every Save/Validate)

`check_credit_limit()` in `setup.py` fires automatically:

```
outstanding_invoices (all unpaid SI for this customer)
  + current_order.grand_total
  > customer.trade_credit_limit
  → BLOCKED with error message
```

| Demo Customer | Credit Limit |
|---|---|
| Alpha Imports Ltd | ₹1,00,000 |
| Beta Trading Co | ₹75,000 |
| Gamma Distributors | Unlimited (0 = no check) |

#### Workflow: Trade SO Approval

```
Draft
  └─ [Sarah: Submit for Approval] ──▶ Pending Approval
                                           ├─ [Mike: Approve] ──▶ Approved  (docstatus = 1)
                                           └─ [Mike: Reject]  ──▶ Rejected
                                                                      └─ [Sarah: Resubmit] ──▶ Pending Approval
```

The Sales Order is only **submitted** (docstatus = 1) when Mike approves it. Only a submitted SO can trigger a Delivery Note or Sales Invoice.

### 5. Delivery Note (Wes — Warehouse workspace)

Wes creates a **Delivery Note** from the approved Sales Order when goods are physically dispatched.

**On submit — two ledger entries are created by ERPNext:**

| Ledger | Dr | Cr |
|---|---|---|
| Stock Ledger | — | Items removed from warehouse |
| GL Entry (perpetual inventory) | Cost of Goods Sold | Stock / Inventory Account |

### 6. Sales Invoice (Anna — Finance workspace)

Anna raises the **Sales Invoice** from the Sales Order or Delivery Note to bill the customer.

**On submit — GL Entries:**

| Account | Dr | Cr |
|---|---|---|
| Debtors / Receivable | Invoice amount | — |
| Sales Income | — | Invoice amount |
| Output GST (if applicable) | — | Tax amount |

This creates the **outstanding amount** tracked against the customer. The credit limit check on future Sales Orders will include this outstanding until it is cleared.

### 7. Payment Entry — Customer Receipt (Anna → Mike — Finance workspace)

Anna records the incoming payment from the customer and links it to the open Sales Invoice.

#### Workflow: Trade Payment Approval

```
Draft
  └─ [Anna: Submit for Approval] ──▶ Pending Approval
                                           ├─ [Mike: Approve] ──▶ Approved  (docstatus = 1)
                                           └─ [Mike: Reject]  ──▶ Rejected
                                                                      └─ [Anna: Resubmit] ──▶ Pending Approval
```

**On submit — GL Entries:**

| Account | Dr | Cr |
|---|---|---|
| Bank / Cash | Payment amount | — |
| Debtors / Receivable | — | Payment amount |

The outstanding on the Sales Invoice drops to zero. The customer's credit is freed.

---

## Purchase Cycle

```
Purchase Order → Purchase Receipt → Purchase Invoice → Payment Entry
  [Purchasing]     [Warehouse]         [Finance]           [Finance]
```

### 1. Purchase Order (Peter → Mike — Purchasing workspace)

Peter raises a **Purchase Order** to a supplier for stock replenishment.

**Trade-specific fields** (same as SO): Port of Loading, Port of Discharge, LC Number.

#### Workflow: Trade PO Approval

```
Draft
  └─ [Peter: Submit for Approval] ──▶ Pending Approval
                                           ├─ [Mike: Approve] ──▶ Approved  (docstatus = 1)
                                           └─ [Mike: Reject]  ──▶ Rejected
                                                                      └─ [Peter: Resubmit] ──▶ Pending Approval
```

Only an approved (submitted) PO can be used to create a Purchase Receipt.

**Demo suppliers:**

| Supplier | Country |
|---|---|
| XYZ Exports | China |
| ABC Manufacturing | Germany |
| Global Sourcing LLC | UAE |

### 2. Purchase Receipt (Wes — Warehouse workspace)

Wes creates a **Purchase Receipt** (Goods Receipt Note) when the physical shipment arrives.

**On submit — two ledger entries:**

| Ledger | Dr | Cr |
|---|---|---|
| Stock Ledger | — | Items added to warehouse |
| GL Entry (perpetual inventory) | Stock / Inventory Account | Stock Received But Not Billed (interim liability) |

The **Stock Received But Not Billed** account is a temporary holding account — goods are in the warehouse but no supplier invoice has been booked yet.

### 3. Purchase Invoice (Anna — Finance workspace)

Anna creates the **Purchase Invoice** when the supplier's bill arrives, linked to the PO or Purchase Receipt.

**On submit — GL Entries:**

| Account | Dr | Cr |
|---|---|---|
| Stock Received But Not Billed | SRBNB amount | — |
| Creditors / Payable | — | Invoice amount |
| Input GST (if applicable) | Tax amount | — |

The interim SRBNB liability is cleared and replaced with a real payable to the supplier.

### 4. Payment Entry — Supplier Payment (Anna → Mike — Finance workspace)

Anna creates the outgoing payment to the supplier, linked to the open Purchase Invoice.

Same **Trade Payment Approval** workflow as the customer receipt.

**On submit — GL Entries:**

| Account | Dr | Cr |
|---|---|---|
| Creditors / Payable | Payment amount | — |
| Bank / Cash | — | Payment amount |

The outstanding on the Purchase Invoice drops to zero.

---

## Asset Register

Anna manages the company's fixed assets (machinery, equipment) from the **Asset Register** workspace.

| Document | Purpose |
|---|---|
| Asset Category | Defines depreciation method and rate for a class of assets |
| Asset | Individual asset record with purchase value, location, depreciation schedule |
| Asset Movement | Transfers asset between locations/custodians |

ERPNext automatically posts **depreciation GL entries** on the scheduled date:

| Account | Dr | Cr |
|---|---|---|
| Depreciation Expense | Depreciation amount | — |
| Accumulated Depreciation | — | Depreciation amount |

---

## End-to-End Money Trail

A complete trade on ₹1,00,000 sale with ₹60,000 cost of goods:

```
Event                       Account                         Dr          Cr
─────────────────────────── ─────────────────────────────── ─────────── ───────────
Purchase Receipt submit     Stock / Inventory               60,000
                            Stock Received But Not Billed               60,000

Purchase Invoice submit     Stock Received But Not Billed   60,000
                            Creditors / Payable                         60,000

Supplier Payment submit     Creditors / Payable             60,000
                            Bank / Cash                                 60,000

Delivery Note submit        Cost of Goods Sold              60,000
                            Stock / Inventory                           60,000

Sales Invoice submit        Debtors / Receivable            1,00,000
                            Sales Income                                1,00,000

Customer Payment submit     Bank / Cash                     1,00,000
                            Debtors / Receivable                        1,00,000
─────────────────────────── ─────────────────────────────── ─────────── ───────────
Net result                  Bank                            +40,000
                            Gross Profit                    +40,000     ✓
```

---

## What the Custom App Adds

Trade MVP does not implement any accounting logic itself — ERPNext handles all ledger postings. The app's role is governance and simplification:

| Concern | Mechanism | Where defined |
|---|---|---|
| Role-scoped UI | `filter_bootinfo_for_trade_users()` filters workspaces, sidebar, desktop icons at login | `setup.py` |
| Credit limit | `check_credit_limit()` on Sales Order validate | `setup.py`, `hooks.py` |
| Trade finance fields | `port_of_loading`, `port_of_discharge`, `lc_number` on Quotation / SO / PO | `fixtures/custom_field.json` |
| Approval gates | 3 Frappe Workflows: Trade SO Approval, Trade PO Approval, Trade Payment Approval | `fixtures/workflow.json` |
| Simplified forms | ~60 fields hidden via Property Setter (commissions, loyalty, UTM, subcontracting…) | `setup.py → HIDE_FIELDS` |
| Module access | "Trade User" Module Profile blocks non-trade ERPNext modules | `setup.py → BLOCK_MODULES` |
| Permission model | Custom DocPerm rows give each role the minimum necessary permissions | `setup.py → TRADE_PERMISSIONS` |

---

## Approval Workflow Summary

All three workflows follow the same state machine. The only difference is the role that initiates and the document type:

```
          Initiator              Manager
          ─────────              ───────
SO        Sales Executive   ──▶  Manager approves/rejects
PO        Purchase Executive ──▶  Manager approves/rejects
Payment   Accountant        ──▶  Manager approves/rejects
```

No Sales Order ships, no Purchase Order is placed, and no payment leaves the bank without Mike's explicit approval.

---

## Document Linkage Map

```
Lead
 └─▶ Opportunity
       └─▶ Customer
             └─▶ Quotation
                   └─▶ Sales Order ──── [credit limit check] ──── Customer.trade_credit_limit
                         ├─▶ Delivery Note ──▶ Stock Ledger, GL (COGS)
                         └─▶ Sales Invoice ──▶ GL (Debtor + Income)
                                 └─▶ Payment Entry ──▶ GL (Bank + Debtor clearance)

Supplier
  └─▶ Purchase Order
        └─▶ Purchase Receipt ──▶ Stock Ledger, GL (SRBNB)
              └─▶ Purchase Invoice ──▶ GL (SRBNB clearance + Creditor)
                      └─▶ Payment Entry ──▶ GL (Bank + Creditor clearance)

Asset Category
  └─▶ Asset ──▶ Depreciation GL entries (scheduled)
        └─▶ Asset Movement
```
