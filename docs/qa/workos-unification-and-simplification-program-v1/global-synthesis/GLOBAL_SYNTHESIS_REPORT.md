# WorkOS global synthesis / simplification plan V1

| Field | Value |
|-------|--------|
| Task | `WORKOS_GLOBAL_SYNTHESIS_AND_SIMPLIFICATION_PLAN_V1` |
| Date | 2026-08-14 |
| Baseline | `4018cf271cee156b8014f19c7928f7fd781cefa3` local = remote |
| AHEAD / BEHIND | 0 / 0 |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` ON |
| Implementation | NO |
| Product-code changes | 0 |
| Owner DB mutations | 0 |

```text
VERDICT = PASS
GLOBAL_SYNTHESIS_STATUS = COMPLETE
CURRENT_WORKOS_MODEL = PARTIAL
TARGET_WORKOS_MODEL = DEFINED
IMPLEMENTATION_RECOMMENDED_NOW = NO
BIG_BANG_REWRITE_REQUIRED = NO
NEXT_TASK = NOT_AUTHORIZED
```

This is the conversion of Waves 1–5 into one product direction. It is **not** another findings dump and **not** an implementation GO.

Companion files in this folder are SoT for matrices, routes, IA, backlog, and waves.

---

## What is WorkOS now?

A **production-cost laboratory / reference** that already contains three real spines:

1. **Commercial sold-work** — Cerere → Intake V6 → Quote → frozen Order snapshot
2. **Compiler** — Product System (design-time) → ProductDefinition (no page) → ProductAggregate
3. **Execution** — frozen graph → ExecutionPlan → operational tasks → MachineRun / actuals

Wrapped in an AppShell that still teaches **implementation history**: FLUX Produse in the commercial strip, three action UIs, audit pages in everyday nav, and mock/demo surfaces that look official.

It is **not** one coherent commercial journey, **not** one production action home, **not** a live DMS/HR-dossier product, and **not** a second commercial price engine.

## What should remain?

- Cereri, Intake V6, Oferte, Comenzi (sold-work spine)
- Product System as **admin catalog** (not Lucrări)
- ProductDefinition as compiler preview **without a dedicated page**
- ProductAggregate as runtime composition (API / V6, not a shop noun)
- Atelier as canonical **monitor**
- `/operator` and `/tablet` as **ACTIVE_COMPAT** action surfaces until Owner picks a canonical action home
- employee-app-v2 as specialized mobile
- Employee master, pontaj, payments, advances as **separate truths**
- Inventory, pricing registry, machines, suppliers
- Settings (VAT/FX + CostEngine)
- `/modules` (map) and `/governance` (policy) — accuracy PARTIAL
- Reports as **live operational projection**, never sold money

## What should be simplified?

- Commercial teaching: remove Produse from FLUX; label V6 money as preview; fix readiness chip
- Identity display: one primary work id; IR/IV6/numeric ids in disclosure
- EUR/RON as labeled projections, not two authorities
- Role homes: less audit-stack as the only story
- `/operator` unbounded list (paginate/filter — later, after action-home decision)
- Product System chrome: planned shells hidden; TPL/compiler nouns demoted
- Light/dark: shared primitives last, not first

## What should be merged?

**Almost nothing at the write layer.**

| Candidate | Disposition |
|-----------|-------------|
| Colaboratori + Inventory Furnizori | SAME_TRUTH — keep both pages until Owner; do not merge writes |
| Atelier + /operator + /tablet | SAME_TRUTH projections — do **not** merge UIs |
| Payment + advance + labor | VALID_SEPARATE — never merge |
| Pontaj + session | VALID_SEPARATE — never merge |
| Utilaje + MachineRun | VALID_SEPARATE — never merge |
| Pricing registry + snapshot | VALID_SEPARATE — never merge |
| Reports + snapshot | SAME_TRUTH projection — label, do not merge pages |

TRUE_DUPLICATE_TRUTH after reclass = **0**.

## What should be demoted to admin/audit?

- `/execution/ops-graph`
- `/execution/reality-review`
- `/reports/operational`
- Product System blueprint dossier / output-blocks preview
- `/dashboard` as everyday work entry (keep as admin Control)
- `/modules` and `/governance` stay admin; add freeze honesty

## What should be labeled as placeholder / demo?

- `/documents` = MOCK
- `/employees-records` = DEMO dossier on real employee identity
- Settings Societate profile = mock
- Inventory Automatizare = mock
- Product System planned sections = FUTURE / unwired
- `/demo/*` = lab DEMO

## What should be hidden until real?

Recommended (Owner still decides OD-2 / OD-3):

- Documents leave primary Relații
- Planned Product System shells leave everyday catalog
- Evidență HR may stay labeled DEMO or hide if noise

## What should be removed later?

**Nav routes: REMOVE_CANDIDATE = 0.**

Only proven file-only orphan: `MaterialPriceRegistry.tsx` (unwired). `/operator` and `/tablet` are **not** dead.

## In what order can we change it without breaking the system?

```text
S1 labels + FLUX honesty
 → S2 mock/demo honesty
 → S3 nav grouping (no write merges)
 → S4 leak reduction (display only)
 → S5 Product System chrome
 → S6 action-home (blocked on Owner OD-6)
 → S7 modules/governance
 → S8 visual tokens
```

Never: rewrite the app, new shell, new backend, simultaneous nav+domain+schema, invent a ProductDefinition page, unfreeze by accident.

---

## Answers to the ten synthesis questions

1. **True Level-1 systems (7):** Commercial sold-work; Compiler; Execution; People ops; Resource registries; Settings; Governance/map. Do not revive 12+9.
2. **Only projections / admin / audit / compat / placeholders / demos / compiler internals:** Atelier, Dashboard, clients 360, `/operator`/`/tablet`, ops-graph, reality-review, `/modules` verifyRoute, Documents, Evidență HR, planned PS, ProductDefinition (no page), ProductAggregate (API grain).
3. **Same truth, multiple UIs:** suppliers (two pages); tasks (Atelier / operator / tablet / mobile); employee names (master + records); V6 preview vs quote vs reports vs snapshot (sold = snapshot).
4. **Must stay separate:** payment ≠ advance ≠ labor; pontaj ≠ session; catalog ≠ MachineRun; IR ≠ IV6; pricing registry ≠ snapshot; commercial line ≠ WC ≠ operator card.
5. **Technical leak:** FLUX Produse; WC_* titles; English Shop Floor; TPL / Product Compiler as the PS story; JOB-* / numeric execution ids as primary.
6. **Wrong workflow teaching:** Lucrări = Cereri → **Produse** → Oferte. Real path is Cerere → Intake V6 → Ofertă → Comandă.
7. **History accumulation:** three action UIs; `/employee-app` v1 sibling; `/demo/*`; planned PS workshops; Documents hub; dual supplier doors.
8. **Wrong nav group:** Plăți/Avansuri under Management; Ops-Graph under Producție; Product System under Lucrări; Documents under Relații.
9. **Look more official than they are:** Documents, Evidență HR, planned PS, Settings Societate, reports “revenue” without live-projection label.
10. **Cosmetic vs architecture:** light sidebar / page-local cards = cosmetic (P3). FLUX + preview-as-offer + readiness chip = architecture risk (P0). Monitor≠action and RBAC MIXED = real, but not “fix in S1”.

---

## Finding disposition (Waves 1–5)

No major finding disappears. Status: CARRIED · MERGED · SUPERSEDED · RETRACTED · DEFERRED.

| Wave finding | Disposition | Lands in |
|--------------|-------------|----------|
| W1 incomplete day-mode | CARRIED | GS-22 / S8 |
| W1 admin home = audit stack | CARRIED | IA Acasă; S3 |
| W1 sales home strongest | CARRIED | keep `/quotes` home |
| W1 WC keys + Shop Floor English | CARRIED | GS-15 / S4 |
| W1 role projection works | CARRIED | keep role homes |
| W1 hardcoded page-local cards | CARRIED | principle 10 / S8 |
| W2 C1 IR vs IV6 | CARRIED | GS-07; D-IR-IV6 |
| W2 C2 EUR vs RON | CARRIED | GS-08; D-EUR-RON |
| W2 C3 1 vs 19 clients | CARRIED | GS-14 |
| W2 C4 readiness chip | CARRIED | GS-03 P0 |
| W2 C5 FLUX Produse | CARRIED | GS-01 P0; OD-1 |
| W2 C6 quote→client dead end | DEFERRED | GS-24 P3 |
| W2 V6 “OFERTĂ CLIENT” rail | CARRIED | GS-02 P0 |
| W2 `/intake-v4` FE residue | CARRIED | LEGACY_UNUSED; GS-25 P3 |
| W3 monitor ≠ action | CARRIED | OD-6; S6 DEFER |
| W3 `/operator` 234 tasks | CARRIED | GS-16; depends OD-6 |
| W3 W3-C1/C4 92400 vs 973024 | RETRACTED | FALSE_POSITIVE |
| W3 W3-C3 assigned · Neatribuit | RETRACTED | FALSE_POSITIVE |
| W3 COMPAT operator/tablet | CARRIED | ACTIVE_COMPAT; do not remove |
| W3 grain inequality | CARRIED | principle 6 |
| W3 W3-C5 status vocab split | CARRIED | VALID_SEPARATE; do not unify enums |
| W3 mutating STATE_NOT_REACHED (6) | DEFERRED | not a simplification P0; needs fixtures + Owner GO |
| W4 PS = design-time | CARRIED | target model |
| W4 PD no page | CARRIED | OD-5 = no page |
| W4 PA→973024 proven | CARRIED | compiler spine |
| W4 W4-C2 stale gov products | CARRIED | GS-13; OD-8 |
| W4 W4-C3 two doc hierarchies | CARRIED | S7 |
| W4 W4-C4 premount drift | DEFERRED | OD-9; do not activate |
| W4 W4-C5 freeze omitted | CARRIED | GS-12 |
| W4 W4-C6 confirm vs frozen | CARRIED | fixture DEFINITION_DRIFT; no unfreeze |
| W4 W4-C7 = C5 | MERGED | GS-01 |
| W4 U12 12+9 | RETRACTED | Level-1 = 7 |
| W4 planned PS shells | CARRIED | GS-11 |
| W5 W5-C1 pontaj MIXED | DEFERRED | OD-11; not S1 |
| W5 W5-C2 records demo | CARRIED | GS-06; OD-3 |
| W5 W5-C3 suppliers | CARRIED | GS-20; OD-4 |
| W5 W5-C4 documents MOCK | CARRIED | GS-05; OD-2 |
| W5 W5-C5 reports live money | CARRIED | GS-04; OD-7 |
| W5 W5-C6 three labor languages | CARRIED | VALID_SEPARATE |
| W5 W5-C7 utilaje vs MachineRun | CARRIED | GS-21 |
| W5 records SNR (no `<a>`) | SUPERSEDED | gap closure; protocol §1.2 |

---

## Recommended commercial model (one)

```text
Cerere → configurare în Intake V6 → Ofertă → Comandă înghețată
```

Product System = **Configurare / Admin**. Not a Lucrări step.

## Recommended Product System role

| Audience | Sees |
|----------|------|
| Normal users | Nothing named Product System in everyday work; they configure in Intake |
| Admins | Live catalog + structure that is actually wired |
| Compiler terms | Disappear from sales/operator chrome; stay in Sistem / API |
| Planned/unwired | Hide or FUTURE label |
| ProductDefinition | **No dedicated human page** |

## Recommended execution UX

| Role | Surface |
|------|---------|
| Canonical monitor | Atelier (`/shop-floor`) |
| De-facto action today | `/operator` (compat) + `/tablet` (compat) |
| Specialized mobile | `/employee-app-v2` |
| Audit | Ops-Graph, Reality Review |
| Canonical action later | Owner OD-6 only — do not invent a fourth portal |

## Recommended HR / supplier / documents / reports

| Topic | Target |
|-------|--------|
| Employees | KEEP master |
| Attendance | KEEP; ≠ session |
| Payments / Advances | KEEP separate; MOVE nav to Oameni |
| Employee Records | LABEL_DEMO / HIDE_UNTIL_REAL |
| Suppliers | one entity; both pages justified until OD-4 |
| Documents | REMOVE_FROM_PRIMARY_NAV (recommended) |
| Reports | MANAGEMENT live projection; never frozen sold |

## Modules / governance

| Route | Target |
|-------|--------|
| `/modules` | System map + runtime capabilities + freeze banner |
| `/governance` | Ownership, boundaries, gates, prohibited scope, SoT policy |
| Stale | products tab vs live catalog |
| Missing | freeze ON |
| Noise | two documentation hierarchies; “active spine” copy |

Do not rewrite now.

---

## Visual / UX target (not Figma)

- Operational **tables** for lists; **cards** for one decision
- One H1 that matches nav; one primary CTA; Romanian status
- Technical detail behind “Detalii sistem” / audit routes
- Empty = empty, mock, or blocked — never invented completeness
- Sales: money + readiness. Operator: current work. Admin: map + gaps
- Light/dark from shared primitives (S8), not page-local patches

---

## Target architecture (text)

```text
COMMERCIAL     Cerere ──► Intake V6 ──► Quote ──► Order snapshot
                    │                      │
COMPILER       Product System / PD / PA ───┘   (admin language)
                    │
EXECUTION      ExecutionPlan ──► tasks ──► Atelier (watch)
                                         ──► /operator /tablet (compat action)
                                         ──► employee-app-v2 (specialized)
PEOPLE         Employee master ──► Pontaj │ Plăți │ Avansuri
               Evidență HR = demo until real
RESOURCES      Inventory │ Pricing registry │ Machines │ Suppliers
MANAGEMENT     Reports (live projection) │ Dashboard (admin)
GOVERNANCE     /modules = map + freeze   │ /governance = ownership + gates
```

No new runtime systems.

---

## Final required report

```text
VERDICT = PASS
GLOBAL_SYNTHESIS_STATUS = COMPLETE
CURRENT_WORKOS_MODEL = PARTIAL
TARGET_WORKOS_MODEL = DEFINED
LEVEL_1_SYSTEMS_FINAL = 7
CORE_SPINES_FINAL = 3
COMMERCIAL = Cerere → Intake V6 → Quote → Order snapshot
COMPILER = Product System → ProductDefinition (no page) → ProductAggregate
EXECUTION = Frozen graph → ExecutionPlan → tasks → MachineRun / actuals
LATERAL_BELTS_FINAL = People · Resources · Settings · Documents(mock) · Reports(projection)
CORE_PROJECTIONS_FINAL = Atelier · Dashboard · /operator · /tablet · employee-app-v2
CORE_WORKFLOW_ROUTE_COUNT = 5
ADMIN_CONFIGURATION_ROUTE_COUNT = 6
MANAGEMENT_ROUTE_COUNT = 6
AUDIT_ONLY_ROUTE_COUNT = 5
COMPATIBILITY_ROUTE_COUNT = 4
DEMO_ROUTE_COUNT = 2
PLACEHOLDER_ROUTE_COUNT = 1
REMOVE_CANDIDATE_COUNT = 0
TRUE_DUPLICATE_TRUTH_COUNT = 0
SAME_TRUTH_DIFFERENT_PROJECTION_COUNT = 8
VALID_SEPARATE_TRUTHS_COUNT = 11
FALSE_POSITIVE_DUPLICATE_COUNT = 3
P0_COUNT = 3
P1_COUNT = 8
P2_COUNT = 8
P3_COUNT = 6
IMPLEMENTATION_WAVES_PROPOSED = 8
TOP_10_SIMPLIFICATION_PRIORITIES =
1. Remove Produse from commercial FLUX (GS-01)
2. Label V6 money as preview, not offer (GS-02)
3. Align readiness chip with V6 confirm (GS-03)
4. Label reports as live operational projection (GS-04)
5. Documents mock out of primary nav (GS-05)
6. Evidență HR stays DEMO (GS-06)
7. Hide planned Product System shells (GS-11)
8. Freeze banner on /modules and /governance (GS-12)
9. Move Plăți/Avansuri under Oameni (GS-09)
10. Demote Ops-Graph / Reality Review to Sistem (GS-10)
OWNER_DECISIONS_REQUIRED = 12 (see OWNER_DECISION_REGISTER.md)
BIG_BANG_REWRITE_REQUIRED = NO
IMPLEMENTATION_RECOMMENDED_NOW = NO
FIRST_RECOMMENDED_IMPLEMENTATION_WAVE = S1
WHY_FIRST = Stops Lucrări from teaching Product System as the commercial path
CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON
PRODUCT_CODE_CHANGES = 0
OWNER_DEV_DB_MUTATIONS = 0
IMPLEMENTATION = NO
CLEANUP = NO
UNFREEZE = NO
COMMIT = NO
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```

## Mandatory roadmap checkpoint

```text
Metoda de lucru si logica abordarii = ce-plan organization; read-only lanes; single ORCH writer; independent REV; no /lfg; no /ce-work
Multitasking used = YES
Parallel research lanes = commercial · execution · compiler · HR/resources/IA
Canonical writer = ORCH
Consistency reviewer = REV (GLOBAL_CONSISTENCY_REVIEW.md)
Cross-wave synthesis = YES
Wave 1 accounted = YES
Wave 2 accounted = YES
Wave 3 accounted = YES
Wave 4 accounted = YES
Wave 5 accounted = YES
Impact Harta sistemelor = Level-1 stays 7; 12+9 stays retracted
Impact Guvernanța sistemului = /modules map vs /governance policy; freeze missing (GS-12)
Dead Pieces Check = nav REMOVE_CANDIDATE = 0; file-only MaterialPriceRegistry
Overengineering Check = no new frameworks, portals, registries, tasking systems
Roadmap awareness = 9/10
Cât sunt în direcția stabilită = 100%
Forbidden Scope respected = YES
```
