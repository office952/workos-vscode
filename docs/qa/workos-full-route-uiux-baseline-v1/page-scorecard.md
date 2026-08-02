# WorkOS Full Route UI/UX Baseline V1 — Page Scorecard

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Status | **PASS WITH WARNINGS** |
| Scoring | 0–5 per page (honest, not inflated) |
| Evidence | Screenshots under `screenshots/**` + U1/U2 JSON (`themeClass: light` on U2) |
| Scale | See §1 |

Companion: [`route-inventory.md`](./route-inventory.md) · [`WORKOS_FULL_ROUTE_UIUX_BASELINE_V1_REPORT.md`](./WORKOS_FULL_ROUTE_UIUX_BASELINE_V1_REPORT.md)

---

## 1. Score scale

| Score | Meaning |
|------:|---------|
| 0 | Broken / blank / wrong product |
| 1 | Opens but unusable for intended operator |
| 2 | Partial usefulness; heavy jargon, confusion, or missing role fit |
| 3 | Usable by experts; clear gaps for shop-floor / day-mode / RO language |
| 4 | Solid for intended role; minor polish left |
| 5 | Production-ready IA + UI for intended role (rare in this baseline) |

Dimensions inside justification: **clarity**, **language honesty**, **role fit**, **day-mode chrome**, **actionability**.

---

## 2. Shell / operations

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| App shell chrome | `shell/00-app-shell-chrome.png` | **2** | IA readable but EN/RO mix, “(registry)” in nav, ops surfaces overloaded; day-mode sidebar often reads darker/cooler than content |
| `/dashboard` Control Tower | `shell/01-dashboard-control-tower.png` | **3** | Real KPIs + gap honesty (ACTUAL/PROXY/DERIVAT); banner + audit chrome dense; English search + mixed jargon |
| `/shop-floor` | `core-flow/02-shop-floor.png` | **3** | Live board works; WC keys like `CNC_ROUTING` / `METAL_FAB` leak internal codes; overlaps Control Tower/Execuție |
| `/operator` | `core-flow/11-operator-view.png`, `people-execution/02-operator.png` | **3** | Distinct queue surface; H1 “Operator View” English; role visibility not gated |
| `/tablet` | `people-execution/03-tablet.png` | **3** | Clear station picker (“Atelier — Stații de lucru”) |
| `/tablet/cnc` | `people-execution/03b-tablet-station.png` | **3** | Drill works; deeper task route not scored |
| `/execution` | `core-flow/08-execution.png` | **3** | Spine entry OK; competes with Shop Floor/Ops-Graph |
| `/execution/:order_id` | `core-flow/08b-*.png`, `08c-*.png` | **3** | Detail present for fixture orders; density high |
| `/execution/ops-graph` | `core-flow/09-ops-graph.png` | **3** | Powerful expert surface; heavy EN/tech (“envelope”, “materialized_pending_execution”); **KEEP** — assignment UI emerging Track F, not redesigned here |
| `/execution/reality-review` | `core-flow/10-execution-reality-review.png` | **2** | Audit-oriented; not shop-floor primary; ADMIN lean |

---

## 3. Commercial spine

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| `/intake` | `core-flow/03-work-intake.png` | **3** | Core spine; “Work Intake” English in RO nav |
| `/intake-v6/…/operator` | `core-flow/04-*.png`, `management-admin/08-*.png` | **3** | Active operator flow; redirects to workspace; still mixed chrome |
| `/product-system/products` | `core-flow/05-product-system-products.png` | **3** | Primary PS path visible; laboratory depth remains |
| `/product-system/components` | `core-flow/05b-*.png`, `management-admin/11-*.png` | **2** | Planned section — honest placeholder energy |
| `/quotes` | `core-flow/06-quotes-oferte.png` | **3** | List usable; commercial spine intact |
| `/orders` | `core-flow/07-orders-comenzi.png` | **3** | Same |
| `/clients` | `registries-support/04-clients.png` | **3** | List OK; workspace deep-link not opened (warning) |
| `/documents` | `registries-support/06-documents.png` | **2** | H1 “Document Center” vs sidebar “Documente” |

---

## 4. Registries / resources

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| `/inventory` | `registries-support/02-inventory.png` | **3** | Functional registry UI; OC coupling not operator-simple |
| `/inventory/pricing` | `registries-support/03-pricing.png` | **2** | H1 “Pricing Registry”; nav exposes “(registry)” — internal term |
| `/pricing` redirect | `registries-support/07-pricing-redirect.png` | **n/a** | Alias only — scored via destination |
| `/utilaje` | `registries-support/01-utilaje.png` | **2** | H1 “Utilaje (registry)” — jargon in title |
| `/colaboratori` | `registries-support/05-colaboratori.png` | **3** | Straightforward list |
| `/reports` | `management-admin/01-reports.png` | **3** | RO title OK |
| `/reports/operational` | `management-admin/02-reports-operational.png` | **2** | H1 “Operational Reports” English |

---

## 5. People / attendance / money

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| `/employees` | `people-execution/01-employees.png` | **3** | Clear RO H1 |
| `/personal` redirect | `people-execution/09-personal-redirect.png` | **n/a** | Lands on employees |
| `/employees-records` | `people-execution/06-employees-records.png` | **3** | HR list; should be role-gated |
| `/attendance` | `people-execution/04-attendance.png` | **3** | Usable; nav “Pontaj (registry intern)” |
| `/attendance/effects` | `people-execution/05-attendance-effects.png` | **2** | Secondary; admin/HR |
| `/employee-payments` | `people-execution/07-employee-payments.png` | **2** | Sensitive; visible in full admin nav |
| `/employee-advances` | `people-execution/08-employee-advances.png` | **2** | Same |

---

## 6. Employee Mobile (out of scope for change)

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| `/employee-app` | `people-execution/10-employee-app.png` | **2** | Standalone dark UI; technical EN error banner (`operational_tasks[]`); **DEFER** product change |
| `/employee-app-v2` | `people-execution/11-employee-app-v2.png` | **2** | Cleaner RO tiles; plan/task empty-state honesty; still not shell-integrated; **DEFER** |

---

## 7. Management / admin / lab

| Route | Screenshot | Score | Justification |
|-------|------------|------:|---------------|
| `/modules` | `management-admin/03-modules.png` | **2** | System map — admin |
| `/governance` | `management-admin/04-governance.png` | **2** | Admin |
| `/settings` | `management-admin/05-settings.png` | **3** | Expected admin home |
| `/demo/commercial-spine` | `management-admin/06-*.png` | **1** | Internal demo — should not be primary nav story |
| `/demo/volumetric-letter-preview` | `management-admin/07-*.png` | **1** | QA demo |
| `/product-system/blueprint-dossier` | `management-admin/09-*.png` | **2** | Expert studio; ADMIN_ONLY lean |
| `/product-system/output-blocks-preview` | `management-admin/10-*.png` | **2** | Preview/lab |

---

## 8. Aggregates (captured pages only)

| Cohort | Pages scored | Mean (approx.) | Read |
|--------|-------------:|---------------:|------|
| Shell + ops spine | 10 | ~2.9 | Expert-usable, IA crowded |
| Commercial | 8 | ~2.9 | Spine alive; labels inconsistent |
| Registries | 6 | ~2.5 | “Registry” exposure hurts |
| People / money | 7 | ~2.6 | Needs role hide |
| Employee Mobile | 2 | 2.0 | Deferred |
| Admin / demo / lab | 7 | ~1.9 | Hide/ADMIN |

**Overall UI/UX readiness (captured product surface):** ~**2.5 / 5** — usable laboratory + staging ops tool, not yet a coherent day-mode Romanian operator product.

Unopened parametric routes are **not** scored as 0; they remain **coverage gaps** (see inventory warnings).
