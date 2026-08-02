# Wave 4 desktop route matrix

Scope is major AppShell route families, grouped where a detail route shares the same purpose. “Authority” means the backend/domain authority; UI never becomes the truth owner.

| Route | Primary user / decision | Canonical truth and write authority | Role exposure | Plan / actual and commercial / internal clarity | Blockers / runtime completeness | Day / dark and audit evidence |
|---|---|---|---|---|---|---|
| `/dashboard` | Manager prioritises operational risk | Dashboard read model; only local acknowledgement | all roles, role-projected | Gap labels are honest but audit-heavy; no commercial decision | Data gaps can dominate first fold | Shell day verified; page visual 3/5 |
| `/execution` | Manager/admin selects order to run | Execution dashboard/read model; no list write | manager, admin, sales | Planned execution is visible; actuals live in detail | Competes with Shop Floor/Operator | U2 continuity proof; 3/5 visual, 3/5 functional |
| `/execution/:id` | Manager/operator runs plan and sees reality | Plan/reality APIs; backend owns plan generate, start/end and stock deduction | execution visible to manager/admin/sales; actions require runtime permission | Strong planned-vs-actual minutes; commercial/estimated/actual cost are explicitly separated | Actual-cost job closure is incomplete until policy/material/capture gates pass | U2/F3 code evidence; no fresh U4 console probe |
| `/execution/ops-graph` | Manager/admin examines dependencies and assignment | Materialized operational graph; controlled assignment authority remains backend | manager/admin nav only | Operational, not commercial; actual status is technical | Expert vocabulary, Track F ownership | Captured baseline, 3/5 |
| `/execution/reality-review` | Manager/admin audits data quality | Reality review read model | deep link; manager/admin intended | Actual-quality audit, not execution action | Not an operator primary surface | Captured baseline, 2/5 visual |
| `/shop-floor` | Floor lead triages work centres | Live machine/task status; task actions route elsewhere | operator/manager/admin | Operational view; not commercial | Internal WC codes, overlapping homes | U2 warnings: dark islands; 3/5 |
| `/operator` | Operator starts/completes/blocks task | Backend operator-task truth | operator/manager/admin | Actual task execution; not commercial | Compatibility visual density; fresh console not captured | Historical duplicate-key warning closed; 3/5 |
| `/tablet/*` | Shop-floor operator chooses station and task | Backend station/task truth | operator/manager/admin | Task status, no commercial detail | Deep task route not freshly audited | Baseline 3/5 |
| `/intake`, `/:id` | Sales/admin turns request into quote-ready work | Intake backend; backend guards state changes | sales/manager/admin | Commercial request intent; product truth must be confirmed | Legacy detail route and V6 split | U1 proof; list 4V/3F |
| `/intake-v6/*` | Specialist configures active intake workspace | Versioned intake/product-truth contracts; operator confirmation | DEV/tooling entry; direct route | Product truth precedes commercial handoff | Separate specialist experience; no broad desktop polish claim | Existing audit only; 3/5 |
| `/product-system/products/*` | Product admin/commercial inspects templates | Frozen Product System reference; no silent confirmation | sales/manager/admin | Product structure, explicitly not client price | Reference freeze and laboratory depth | U3 4V/3F top surface |
| PS structure/planned/admin pages | Product admin researches reference structure | Frozen reference/docs; no new product truth authority | mostly direct/DEV paths | Internal/reference, not commercial | Placeholder/planned pages and jargon | 1–2F, not a Wave 4 candidate |
| `/quotes/*` | Sales/admin prices, accepts and converts | Quotes API/readiness backend | sales/manager/admin | Commercial truth clear; internal cost is permissioned | Card/KPI amount mismatch; deep detail capture brittle | U1 4V/3F |
| `/orders/*` | Commercial/ops lead prepares execution | Frozen order snapshot; backend plan generation | sales/manager/admin | Commercial accepted state then execution; no reprice | Detail coverage incomplete | U1 4V/3F |
| `/inventory` | Operator/manager handles stock | Inventory ledger/movements; protected writes | operator/manager/admin/sales read | Internal stock, never quote-price source | Protected truth surface | 3V/3F |
| `/inventory/pricing` | Admin maintains pricing policy | Pricing backend/rates; protected | admin nav | Separates material, commercial and internal meanings | Pre-existing maximum-update-depth test failure | U3 story improved; 3V/2F |
| `/utilaje` | Ops checks capacity/feasibility | Equipment registry | operator/manager/admin | Capacity is feasibility, not client price | Registry jargon/diagnostics | 3V/3F |
| `/clients`, `/documents`, `/colaboratori` | Sales/admin manages relationships/artifacts | respective backend records | sales/manager/admin (collaborators manager/admin) | Commercial context; weak details discoverability | Client deep link unproven; documents naming conflict | 2–3V/2–3F |
| People/attendance/payments/advances | HR/manager/admin decisions | HR/payroll records; sensitive writes | role-projected, payments/advances restricted | Internal only; never commercial | Need robust privacy/role review; detail discoverability | 2–3V/3F |
| `/reports*` | Manager assesses business | Reporting read models | sales/manager/admin; profit manager/admin | Profit may be unavailable honestly | Operational subroute is technical | 3V/2F |
| `/settings`, `/governance`, `/modules` | Admin configures/audits system | Config/governance docs and backend | admin | Internal administrative truth | Not daily operations | 2–3V/2–3F |
| `/demo/*` and aliases | Developer/QA compatibility | no product authority | DEV only / direct links | Explicitly non-production | Must stay hidden from production narrative | 1–2V, not scored as functional work |

## Cross-route conclusions

1. The commercial spine is legible through Orders, but the post-order truth is scattered across execution detail, dashboards, stock, a new actual-profitability read model, and a labelled legacy panel.
2. The Execution Detail already holds the strongest evidence: backend-refreshed plan and task reality, unavailable-values-not-zero discipline, and a management-only actual-profitability read panel.
3. It is nevertheless visually overloaded. Wave 4 should shape and sequence the closure decision without inventing a job-close action, actual cost, or commercial recomputation.
