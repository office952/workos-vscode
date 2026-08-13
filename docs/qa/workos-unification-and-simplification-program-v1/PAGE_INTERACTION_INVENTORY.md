# Page interaction inventory

Do not measure audit size by route count. A route is complete only when this inventory is reconciled with runtime traversal **and** full scroll exhaustion.

Status: `RECONCILED` · `PARTIAL` · `NOT_TRAVERSED`

---

## AppShell chrome

| Class | Inventory | Runtime |
|-------|-----------|---------|
| tabs / subtabs | none | RECONCILED — none |
| drawers | narrow nav drawer | STATE_NOT_REACHED at 1440 (mobile-only) |
| popovers | user menu | RECONCILED — opened; role label visible (`admin` / `sales` / `operator` Preview) |
| contextual menus | Deconectare | RECONCILED — visible, not clicked (would destroy session) |
| internal links | `SHELL_NAV_SECTIONS` per role | RECONCILED — every visible edge followed once (92 YES) |
| secondary actions | nav collapse; theme toggle; search; bell | RECONCILED — collapse + theme used; search present; bell not opened (no badge count) |
| role-dependent surfaces | entire sidebar | RECONCILED — admin full IA; sales thin (no Atelier/HR/admin); operator Producție+Resurse only |
| nested scroll | `workos-shell-nav` | RECONCILED — admin max=624, 2 segments, BOTTOM_REACHED=YES. sales/operator nav fits (no nested scroller) |

---

## `/dashboard` — Control producție

| Class | Inventory | Runtime |
|-------|-----------|---------|
| tabs / subtabs | none | RECONCILED — none |
| accordions | honesty banner; “Am înțeles — pliază Gap”; risks expand | PARTIAL — Gap fold control present; risks expand NOT_APPLICABLE (0 delivery risks) |
| drawers / modals | none | RECONCILED — none |
| internal links | Cerere Nouă; Oferte; Comenzi; Execuție; Atelier; Rapoarte; Deschide Execuție; Vezi Atelier; gap Deschide | RECONCILED as destinations via nav graph / quick actions observed; mutating create not executed |
| primary CTAs | Cerere Nouă | Observed; not executed (would open intake workspace) |
| filters / tables | none | RECONCILED |
| scroll | `main.overflow-auto` | **PASS** — 3 segments, 0→1299/1299, both themes |

Hardcoded-UI: page-local KPI cards (labels missing on first fold — only ACTUAL/PROXY/DERIVAT chips). Honesty banners are page-local, not `AlertBanner`/`PageShell`. `CapacityNotice` / `BoundaryBadge` used in places. Breadcrumb “FLUX EXECUȚIE” stacks Control producție after Atelier — operator-confusing on the admin home.

---

## `/quotes` — Oferte

| Class | Inventory | Runtime |
|-------|-----------|---------|
| tabs / subtabs | Toate / Ciornă / Tarifat / Acceptat | RECONCILED — all four exhausted |
| accordions | Detalii tehnice — readiness / politică backend | RECONCILED — present on page |
| expandable cards | quote card → detail pane | RECONCILED — first card selected (`quote-selected` scroll PASS) |
| drawers | none | RECONCILED |
| modals | QuoteSendDialog; QuoteRevisionDialog | STATE_NOT_REACHED for submit; send-like control on V6 detail is disabled (`Trimite în ofertare`) |
| filters | search; status chips | RECONCILED |
| tables with row actions | card list, not DataTableWrapper | RECONCILED — page-local cards |
| primary CTAs | + Ofertă nouă | Observed; not executed |
| secondary | accept / reject / convert | STATE_NOT_REACHED (mutating) |
| scroll | `main.overflow-auto` | **PASS** — default 7 segs 0→4440; Ciornă 2/488; Tarifat 2/640; Acceptat 5/2464; selected 7/4389 |

Hardcoded-UI: list+detail is page-local, not `DataTableWrapper`. KPI money tiles are page-local. Status chips mix token + hardcoded blue/emerald. “% Adaos 50%” on every card is commercial chrome, not a shared primitive.

---

## `/shop-floor` — Atelier

| Class | Inventory | Runtime |
|-------|-----------|---------|
| tabs / subtabs | none | RECONCILED |
| accordions | none | RECONCILED |
| expandable cards | workcenter cards (CNC_ROUTING, LETTER_FORMING, …) | RECONCILED — visible on scroll |
| drawers / modals | none on landing | RECONCILED |
| internal links | Acțiune task; Stații (next-step banner) | Observed; followed via nav graph |
| filters | implicit workcenter grouping | RECONCILED |
| tables | per-card job/queue fragments | RECONCILED — page-local, not DataTableWrapper |
| primary CTAs | none on landing | RECONCILED |
| scroll | `main.overflow-auto` | **PASS** — 3 segments, 0→818/818, admin + operator, both themes |

Hardcoded-UI: workcenter keys leak (`CNC_ROUTING`, `METAL_FAB`, `LETTER_FORMING`). `SourceBadge` is shared. Connection chip uses raw emerald/slate classes. H1 “Atelier” matches nav — good. English breadcrumb “Shop Floor” vs Romanian H1.

Reconciliation verdict: Wave 1 homes = **RECONCILED** for non-mutating journey. Mutating quote/dashboard create paths remain `STATE_NOT_REACHED` by charter.
