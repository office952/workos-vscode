# UI Navigation & Labeling Policy

**Version:** 1.0.2  
**Status:** Target architecture + **owner visual verification policy** (sync 2026-06-30 after Slice 10.2 + 10.3)  
**Step:** 11 — NEEDS OWNER GO (labels only — **no redesign**)  
**Related:** `WORKOS_UI_POLISH_STRATEGY.md`, `.cursor/rules/workos-ui-governance.mdc`

---

## 1. Rolul sistemului

Politica UI definește **cum etichetăm** suprafețele WorkOS — ce este operational, read-only, preview, registry, analytics, legacy/mock/dead, source of truth — fără redesign de layout în acest roadmap step.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Label taxonomy** | Standard tags per surface type |
| **Navigation honesty** | Routes reflect real capability |
| **Warning visibility** | Blockers/confidence shown not hidden |
| **Separation labels** | Commercial vs internal vs actual |
| **Legacy markers** | Deprecated paths labeled |
| **Mock/demo markers** | Non-production surfaces |
| **Source of truth badges** | Which screen owns which truth |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Layout redesign |
| CSS/theme overhaul |
| New feature implementation |
| CommercialPriceProposal engine |
| Runtime behavior changes (Step 11 = labels/deprecation markers) |
| HUB UI (future) |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Architecture realignment docs | This folder |
| Audit findings | MISLEADING_UI tags |
| Legacy cleanup policy | doc 19 classifications |
| Owner GO | Step 11 scope approval |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| UI label spec | Frontend implementers (future Step 11) |
| Badge component policy | Consistent operator experience |
| Deprecation notices | Legacy routes |
| Operator training clarity | Reduced false confidence |

---

## 6. Source of truth — surface types

| Label | Meaning | Examples |
|-------|---------|----------|
| **Operational** | Real production workflow | Intake V6 confirm, Order convert, Task start/stop |
| **Read-only truth** | Display canonical data — no fake edit | Aggregate BOM preview (7D) |
| **Preview** | Ephemeral — not official | Intake live offer, material breakdown, pricing-input-preview |
| **Registry** | Admin configuration | Pricing.tsx, ProductSystem.tsx, Inventory |
| **Analytics** | Post-job / statistics | ProfitabilityAnalysis MVP panel (read-only), capacity |
| **Legacy/mock/dead** | Not production path | DocumentCenter mock, Intake v3/v4 detail |
| **Source of truth** | Badge on Intake V6 workspace, Order snapshot | Explicit |

---

## 7. Conexiuni cu celelalte sisteme

```
Every UI surface maps to one backend truth model:

Intake V6 UI          → product truth (not commercial official)
Intake live calc      → preview internal/commercial — NOT official quote
Aggregate BOM panel   → EstimatedInternalCost readiness — read-only
Pricing.tsx           → Registry — separated tabs (7I)
QuoteWizard           → official only post-snapshot (Step 8)
ProductSystem UI      → template registry — comp_auto_1 misleading today
Task preview panels   → preview — NOT ExecutionPlan
Employee Mobile       → ExecutionActuals input
```

---

## 8. Reguli owner obligatorii

### Interzis în UI (target)

| Interzis | De ce |
|----------|-------|
| UI sugerează preț final când e doar preview | Intake ~6324 vs grand_total=0 |
| UI sugerează taskuri reale când sunt demo | Task preview ≠ plan |
| UI ascunde warnings | Fail-closed philosophy |
| UI amestecă CostEngine intern cu preț comercial | Mixed-risk paths |
| UI sugerează clientului ore × tarif | Owner law |
| `rate_per_hour` labeled „tarif client” | Misleading |

### Step 11 target labels (from master plan)

| Label RO | Pentru |
|----------|--------|
| mock / demo | DocumentCenter, ModuleChain events |
| read-only | Cost BOM preview, governance |
| estimare internă | Live calc Intake, BOM |
| propunere comercială | 7G preview |
| ofertă oficială | Snapshot post-Step 8 only |
| legacy | intake v3/v4 detail, IntakeDetail |

**No redesign** — only clarity.

### Owner visual verification rule (mandatory for UI/QA tasks)

Any task that modifies or verifies UI must document in the final report / worklog:

| Field | Required |
|-------|----------|
| URL | Concrete path, e.g. `http://127.0.0.1:3000/execution/88001` |
| Page / tab / section | Where to look |
| IDs | `order_id`, `job_id`, `plan_id`, `task_id` as applicable |
| Element | Badge, chip, metric, label |
| Expected text/value | Exact expected string or number |
| Click path | Short steps to reach the surface |
| `dev.db` data | Fixture/order required |
| No dedicated UI | State explicitly — e.g. Slice 10.1: **API/tests only** |

**Slice 10.1:** No new UI. Owner verifies guard via `backend/tests/test_orders_update_immutability.py`. Browser smoke only on existing surfaces:

- `http://127.0.0.1:3000/execution/88001` — readiness `Operational tasks ready`
- `http://127.0.0.1:3000/reports/operational` — plan metrics `2` / `0`

**Slice 10.2 + 10.3 (API):** Owner verifies read-only profitability endpoint:

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:8000/api/v1/profitability-analysis/order/88001` |
| Expected status | `estimated_only` |
| Expected commercial | `1500.0` RON |
| Expected internal | `620.0` |
| Expected margin | `880.0` / ~`58.67%` |
| Guard flags | `retroactive_change_allowed: false`, `write_back_performed: false` |
| Missing order | `GET .../order/99999999` → **404** `order_not_found` |
| Legacy order | `GET .../order/1` → **200** `unsupported_legacy_order` |
| Tests | `backend/tests/test_profitability_analysis.py` (+ immutability regression) |

**Slice 10.4 (minimal UI — no dedicated route):** Panel on existing **ExecutionDetail** only. **Not** a profitability dashboard or new nav item.

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:3000/execution/88001` |
| Page | ExecutionDetail |
| Section | **Profitability analysis** (below Observabilitate / Alerte) |
| `order_id` | `88001` |
| Expected status label | `Estimated only` |
| Expected commercial | `1500.00 RON` |
| Expected internal | `620.00 RON` |
| Expected margin | `880.00 RON` / `58.67%` |
| Actuals | `Actuals not recorded yet` / actual cost `not available` — **not final profit** |
| Read-only guardrail | Text: read-only / no write-back (if shown) |
| Must NOT show | Reprice/save buttons; “final profit”; dedicated profitability route |
| API backing | Same values as `GET /api/v1/profitability-analysis/order/88001` |
| Smoke | `http://127.0.0.1:3000/reports/operational` — **no** profitability panel there |

**Step 10 is PARTIAL:** complete post-job profitability truth and actual margin $ remain **DEFERRED** until HR/inventory costing (**OWNER_DECISION**). See [16_PROFITABILITY_ANALYSIS.md](./16_PROFITABILITY_ANALYSIS.md).

**Step 8 (dual quote snapshot — no browser UI):** Owner verifies API + DB only. **No new UI was introduced.**

| Field | Value |
|-------|-------|
| Preview URL | `POST http://127.0.0.1:8000/api/v1/product-system/quote-snapshot-v2/preview/TPL-VOLUMETRIC-LETTERS_v2` |
| Freeze URL | `POST http://127.0.0.1:8000/api/v1/product-system/quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS_v2` |
| Pricing review URL | `POST http://127.0.0.1:8000/api/v1/intake-v6/quotes/1/complete-pricing-review` |
| Owner approval URL | `POST http://127.0.0.1:8000/api/v1/intake-v6/quotes/1/owner-approval` |
| Accept URL | `POST http://127.0.0.1:8000/api/v1/intake-v6/quotes/1/accept` |
| Convert URL | `POST http://127.0.0.1:8000/api/v1/intake-v6/quotes/1/convert-to-order` |
| Live snapshot | `quote_snapshots_v2.id=3`, `QSN2-2026-0003`, `status=frozen` |
| Live quote | `quotes.id=1`, `accepted_snapshot_v2_id=3` |
| Live order | `orders.id=88002`, `quote_snapshot_v2_id=3`, `snapshot_v2_json` with commercial + internal snapshots |
| Execution (Step 8 convert) | Convert creates **no** execution_plan/tasks |
| Execution (Step 9 persist draft) | Plan `execution_plan.id=2`, `source_quote_snapshot_v2_id=3`, `tasks_json` draft — **no** execution_tasks, **no** sessions |
| Step 9 preview URL | `POST http://127.0.0.1:8000/api/v1/execution/plan-v2/preview/88002` |
| Step 9 persist URL | `POST http://127.0.0.1:8000/api/v1/execution/plan-v2/from-order/88002` (HTTP QA **pending backend restart**) |
| Tests | Step 8: **126 pytest**; Step 9 persist: **107 pytest** |
| Must NOT | Create execution_tasks or sessions on persist draft; call `/price`, CostEngine, QuoteOrchestrator |

**Step 8 overall:** **VALIDATED_WITH_GUARDS** — live freeze/pricing review/owner approval/accept/convert validated on safe IV6 path.

**Step 9 overall:** **PARTIAL — VALIDATED_WITH_GUARDS** — preview + persist draft validated on order `88002`; materialize and sessions **BLOCKED / NEEDS OWNER GO**; Employee Mobile **final-final**.

---

## 9. Riscuri actuale din audit

| Risc | Surface | Tag |
|------|---------|-----|
| Live offer looks official | IntakeV6LiveCalculationSummary | `MISLEADING_UI` |
| comp_auto_1 | ProductSystem.tsx | `MISLEADING_UI` |
| Pricing unified hub | Pricing.tsx | `MISLEADING_UI` |
| Dossier shown without audit label | ProductSystem | Partial — audit label exists |
| grand_total=0 unexplained | Quote commercial spine | `MISLEADING_UI` |
| Task preview as production | Intake review panels | `MISLEADING_UI` |
| WC rates as client tariff | Pricing registry columns | `MISLEADING_UI` |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Every price display | Tagged: preview / internal / commercial / official |
| Every task list | Tagged: preview / plan / actual |
| Registry pages | Tab labels per 7I separation |
| Legacy routes | Banner LEGACY_COMPATIBILITY |
| Warnings visible | Blockers not hidden |
| App.tsx routes | Honest naming — audit route list **NEEDS_OWNER_DECISION** for full map |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| UI redesign without GO + visual audit |
| Hide NOT_READY blockers |
| Show Intake preview as „Ofertă client” |
| Single „Total preț” without commercial/internal split post-Step 8 |
| Remove legacy labels without Step 12 owner decision |
| CSS/theme drive-by changes in Step 11 |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Label spec complete | All audit MISLEADING_UI surfaces listed |
| No hourly client implication | Pricing + quote screens |
| Preview ≠ official | Operator test comprehension |
| Legacy marked | v3/v4 paths |
| Step 11 scope respected | Labels only — no layout rewrite |
