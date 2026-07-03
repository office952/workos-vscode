# Roadmap Steps 7G → 12

**Version:** 1.0.8  
**Status:** Target roadmap + **runtime progress** (sync 2026-06-30 after Step 9 persist draft validation)  
**Related:** `WORKOS_REALIGNMENT_MASTER_PLAN.md`, `WORKOS_FULL_SYSTEM_REALITY_AUDIT_ACCEPTANCE.md`  
**Branch:** `feature/step-7g-commercial-price-proposal` — HEAD `b12889c` (Step 9 persist draft)

---

## 1. Rolul documentului

Definește **secvența acceptată** de implementare — fiecare step cu scope, interdicții, GO requirement. Marchează explicit **IMPLEMENTED**, **VALIDATED**, **PLANNED**, **NOT STARTED**, **WATCH**.

---

## 2. Context — unde suntem acum (2026-06-30)

| Milestone | Status |
|-----------|--------|
| Full System Reality Audit | **DONE** — verdict HIGH_RISK_DEVIATED |
| Step 7F / 7F.1 / realignment docs | **DONE** (docs) |
| Execution Plan V2 operational readiness | **VALIDATED** — QA order `88001` |
| Step 9.3.6 Operational Reality Review Audit | **PASS_WITH_GUARDS** |
| Step 10 Actuals/Profitability Hardening Audit | **PASS_WITH_GUARDS** |
| Step 10 ProfitabilityAnalysis Implementation Plan | **PASS_WITH_GUARDS** |
| **Slice 10.1** Order financial immutability guard | **IMPLEMENTED + VALIDATED** — individual (`90ba918`); batch (`453932f`) |
| **Slice 10.2 + 10.3** ProfitabilityAnalysis read-only MVP GET | **IMPLEMENTED + VALIDATED** (`45255a1`) |
| **Slice 10.4** Minimal read-only panel on ExecutionDetail | **IMPLEMENTED** (`378b42b`) — no dedicated profitability route |
| **Step 8** Dual quote snapshot | **VALIDATED_WITH_GUARDS** — live chain **VALIDATED**: freeze → pricing review from snapshot V2 → owner approval → accept → convert; snapshot `QSN2-2026-0003`, order `88002`; convert creates **no** execution_plan/tasks |
| **Step 9 preview** | **VALIDATED** — `POST .../execution/plan-v2/preview/88002`; `partial_missing_planning_minutes`; 12 task candidates; `no_write=true`; **156 pytest** (preview suite) |
| **Step 9 persist draft** | **VALIDATED_WITH_GUARDS** — plan `id=2` for order `88002`; `source_quote_snapshot_v2_id=3`; `tasks_json` 12 tasks / 17 ops; idempotency `already_exists`; **107 pytest** persist suite; **no** execution_tasks/sessions |
| **Step 10 overall** | **PARTIAL** — complete post-job truth **DEFERRED**; actual margin $ **DEFERRED** |
| Step 7G runtime (full commercial path) | **NOT STARTED** — preview services only |
| Steps 7H–12 (remaining commercial/cleanup) | **NOT STARTED** — NEEDS OWNER GO |

**Pas curent:** Step 9 preview + persist draft **VALIDATED_WITH_GUARDS** on order `88002` → next: **HTTP persist QA after backend restart**; **materialize operational_tasks** audit only with **separate owner GO**; **7I** registry separation; **Step 11** labels. Task materialization and sessions remain **BLOCKED**.

**Worklogs:** `docs/worklog/realignment/` — see `2026-06-30_step9_persist_draft_execution_plan.md`, `2026-06-30_docs_sync_after_step9_persist_draft.md`.

---

## 3. Step sequence

```
7F / 7F.1 / realignment docs  ✅ (documentation)
    ↓ GO owner
7G  CommercialPriceProposal (read-only preview)
    ↓ GO owner
7H  EstimatedInternalCost non-hourly
    ↓ GO owner
7I  Pricing Registry separation (UI tabs + classification)
    ↓ GO owner
8   Quote snapshot dual (VALIDATED_WITH_GUARDS — live chain VALIDATED)
    ↓ owner GO received for Step 9 preview + persist draft
9   ExecutionPlan V2 from Order snapshot V2 (PARTIAL — preview + persist draft VALIDATED_WITH_GUARDS)
    ├─ 9 preview read-only     ✅ VALIDATED (`8dd67e9`)
    ├─ 9 persist draft         ✅ VALIDATED_WITH_GUARDS (`b12889c`) — plan id=2, order 88002
    ├─ 9 materialize tasks     ⏳ BLOCKED / NEEDS OWNER GO
    └─ 9 sessions / actuals    ⏳ Step 11+ — NOT STARTED
    ↓ GO owner
10  ProfitabilityAnalysis (PARTIAL — MVP read-only only)
    ├─ 10.1 Order financial immutability guard  ✅ IMPLEMENTED + VALIDATED (individual + batch)
    ├─ 10.2+10.3 Read-only MVP GET               ✅ IMPLEMENTED + VALIDATED
    ├─ 10.4 Minimal panel on ExecutionDetail     ✅ IMPLEMENTED (no dedicated route)
    └─ Complete post-job truth / actual margin $ ⏳ DEFERRED — OWNER_DECISION
    ↓ GO owner
11  UI labels / deprecation (NO redesign)
    ↓ GO owner
12  Dead pieces cleanup (owner decision each piece)
```

**Dependencies:**

- Step 8 requires 7G + 7H outputs
- Step 10 requires 8 + 9
- Step 11 can parallel partial with 7I/8 but no misleading UI left official
- Step 12 **last** — never before canonical path works

---

## 4. Step details

### Step 7G — CommercialPriceProposal (read-only)

| | |
|-|-|
| **Scop** | Model + schema + preview **separat** de `/price` |
| **Input** | Intake V6 + ProductAggregate + reguli comerciale (inițial config/hardcoded read-only) |
| **Output** | commercial_lines[], total, provenance, blockers |
| **Interzis** | DB quote write; reprice; modify `/price`; UI redesign |
| **Doc** | [05_COMMERCIAL_PRICE_PROPOSAL.md](./05_COMMERCIAL_PRICE_PROPOSAL.md) |
| **GO** | **Required** |

### Step 7H — EstimatedInternalCost non-hourly

| | |
|-|-|
| **Scop** | Separă cost intern de preț comercial în engine |
| **Acțiuni** | Elimină per_hour ca basis pre-quote; ml/mp/buc/fix |
| **Păstrează** | Time pentru actuals/capacity — non-blocking commercial |
| **Interzis** | CE rewrite ad-hoc; cost-plus commercial |
| **Doc** | [06_ESTIMATED_INTERNAL_COST.md](./06_ESTIMATED_INTERNAL_COST.md), [07_COST_ENGINE_REALIGNMENT.md](./07_COST_ENGINE_REALIGNMENT.md) |
| **GO** | **Required** |

### Step 7I — Pricing Registry separation

| | |
|-|-|
| **Scop** | Tab-uri: Material / Commercial Rules / Internal Cost / Capacity / Analytics |
| **Acțiuni** | Classify entries; relabel rate_per_hour |
| **Interzis** | Registry edit for readiness without commercial design |
| **Doc** | [08_PRICING_REGISTRY_SEPARATION.md](./08_PRICING_REGISTRY_SEPARATION.md) |
| **GO** | **Required** |

### Step 8 — Quote snapshot dual (**VALIDATED_WITH_GUARDS**)

| | |
|-|-|
| **Scop** | Snapshot: commercial_price + estimated_internal_cost + warnings + owner_decisions; accept linkage via `quotes.accepted_snapshot_v2_id`; convert copies accepted snapshot into `orders.snapshot_v2_json` |
| **Interzis** | final = total_cost × margin universal; Intake preview as official; `/price`; CostEngine; QuoteOrchestrator; order/plan/task on freeze or accept |
| **Doc** | [09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md](./09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md) |
| **Preview runtime** | **VALIDATED** — `POST .../quote-snapshot-v2/preview/{template}` |
| **Freeze runtime (live)** | **VALIDATED** — persist on paper QA + dev bridge; snapshot `QSN2-2026-0003`, `status=frozen` |
| **Pricing review (IV6)** | **VALIDATED** — from snapshot V2 `commercial_total` when quote columns unpriced; **no** `/price`/CE/QO |
| **Owner approval** | **VALIDATED** — live on quote 1 |
| **Accept** | **VALIDATED** — live + **126 pytest**; `confirm_owner_decisions_acknowledged` for partial readiness |
| **Convert** | **VALIDATED** — order `88002`, `quote_snapshot_v2_id=3`, dual snapshots in `snapshot_v2_json` |
| **Execution side effects** | **None** — `execution_plan` count unchanged; no execution_tasks |
| **GO** | Step 8 chain validated on safe data; guards remain for partial readiness and owner decisions |

Step 8 can move from **PARTIAL_WITH_GUARDS** to **VALIDATED_WITH_GUARDS**. Live chain validated: freeze snapshot V2 → complete pricing review from snapshot V2 commercial total → owner approval → accept quote → convert to order snapshot V2.

### Step 9 — ExecutionPlan V2 from Order snapshot V2 (**PARTIAL — VALIDATED_WITH_GUARDS**)

| | |
|-|-|
| **Scop** | Preview + persist **draft** execution plan from `orders.snapshot_v2_json` — **not** execution runtime |
| **Interzis** | `/price`; CostEngine; QuoteOrchestrator; execution_tasks rows; task sessions; Employee Mobile; materialize without owner GO |
| **Doc** | [10_EXECUTION_PLAN_TASK_GRAPH.md](./10_EXECUTION_PLAN_TASK_GRAPH.md), [11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md](./11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md) |
| **Preview** | **VALIDATED** — `POST .../execution/plan-v2/preview/{order_id}`; order `88002`; status `partial_missing_planning_minutes`; 12 task candidates / 17 operations; `no_write=true`; READINESS_GATE excluded; commit `8dd67e9` |
| **Persist draft** | **VALIDATED_WITH_GUARDS** — `POST .../execution/plan-v2/from-order/88002`; plan `id=2`; `source_quote_snapshot_v2_id=3`; `plan_source=order_snapshot_v2`; `tasks_json` present; **no** execution_tasks; idempotency `already_exists`; commit `b12889c`; **107 pytest** |
| **HTTP runtime QA** | **PENDING** — live POST hit stale backend (pre-READINESS_GATE fix); service-level persist **PASS**; restart backend before HTTP verification |
| **Materialize** | **BLOCKED / NEEDS OWNER GO** — `POST .../plan-v2/materialize-tasks/{order_id}` not exercised on live order |
| **Sessions / Step 11** | **NOT STARTED** — Employee Mobile final-final |
| **GO** | Preview + persist draft validated; materialize and sessions require **separate owner GO** |

### Step 10 — ProfitabilityAnalysis (**PARTIAL**)

| | |
|-|-|
| **Scop (target)** | Quoted vs estimated vs actual; per-unit effective price; recommendations — **full loop deferred** |
| **Scop (MVP today)** | Read-only GET + minimal ExecutionDetail panel — **no write-back**, **no actual margin $** |
| **Interzis** | Retroactive quote change; pre-offer blocker; CostEngine; QuoteOrchestrator; `/price`; write-back |
| **Doc** | [16_PROFITABILITY_ANALYSIS.md](./16_PROFITABILITY_ANALYSIS.md) |
| **10.1** | Order financial PUT guard (individual + batch) — **IMPLEMENTED + VALIDATED** (`90ba918`, `453932f`) |
| **10.2+10.3** | Read-only MVP GET — **IMPLEMENTED + VALIDATED** |
| **10.4** | Minimal read-only panel on `ExecutionDetail` — **IMPLEMENTED** (`378b42b`); **no dedicated route/dashboard** |
| **Deferred** | Complete post-job truth; `actual_total_cost` / `actual_margin_*` until HR/inventory costing — **OWNER_DECISION** |
| **GO** | **Required** for HR/inventory actual costing and any commercial recommendation automation |
| **MITIGATED** | Batch `PUT /orders/batch` financial bypass — was **WATCH** after 10.1; closed `453932f` |

### Step 11 — UI labels / deprecation

| | |
|-|-|
| **Scop** | Claritate — preview vs official vs internal vs legacy |
| **Interzis** | Layout redesign; CSS overhaul |
| **Doc** | [17_UI_NAVIGATION_AND_LABELING_POLICY.md](./17_UI_NAVIGATION_AND_LABELING_POLICY.md) |
| **GO** | **Required** |

### Step 12 — Dead pieces cleanup

| | |
|-|-|
| **Scop** | Remove/archive classified DEAD after canonical path proven |
| **Interzis** | Auto-delete; cleanup before 7G–11 |
| **Doc** | [19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md](./19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md) |
| **GO** | **Required per piece** |

---

## 5. Frozen until realigned (do not extend)

| Path / operation |
|------------------|
| `POST /api/v1/entities/quotes/price` |
| `POST /api/v1/entities/quotes/{id}/price` |
| QuoteOrchestrator._apply_commercial |
| Cost Engine per_hour pre-quote commercial use |
| workcenter_rates as commercial blocker |
| Pricing Registry as unified quote hub |
| Intake live offer as official quote |
| Settings CE hourly fallback |
| Markup as universal commercial model |
| **Quote 4 reprice** |
| **Step 7E.2 apply** |

---

## 6. Protected foundations (preserve)

- Intake V6 product truth
- ProductDefinition / ProductAggregate
- ExecutionReality / task sessions
- HR / Pontaj
- Material Registry unit_cost

---

## 7. Owner decisions still open (UNKNOWN)

| Question | Impact |
|----------|--------|
| Debitare spate commercial: ml vs m² | CommercialPriceProposal rules |
| Duplicate lateral dossier vs module | Aggregate dedup |
| Employee internal cost in ProfitabilityAnalysis | Step 10 formula |
| External montaj/subcontract line model | Commercial + HUB boundary |
| Feature flag /price during transition | Governance |
| Full App.tsx route legacy map | Step 11 |
| Exact 7G pilot scope: hardcoded rules vs registry first | 7G implementation |

---

## 8. Success metrics (post-12)

| Metric | Target |
|--------|--------|
| Commercial lines | All volumetric zones with mp/ml/buc/set rules |
| No hourly commercial | Grep + behavior clean |
| Dual snapshot | 100% new quotes post-Step 8 |
| Task single source | Order snapshot processes only |
| Profitability | Available per closed order |
| MISLEADING_UI | Zero unlabeled preview-as-official |
| Dead pieces | Classified; DEAD removed with owner OK |

---

## 9. Alignment score context

Documentation captures **target architecture** aligned with owner direction. Runtime remains deviated until 7G–12 executed.

| Area | Doc coverage | Runtime alignment |
|------|--------------|-------------------|
| Product flow | High | Partial — aggregate good, CE/quote deviated |
| Commercial pricing | Documented target | **Deviated** — cost-plus |
| Internal cost | Documented target | **Deviated** — per_hour |
| Execution actuals | Documented | **Good** — V2 readiness **VALIDATED** |
| Order financial immutability | Documented | **IMPLEMENTED + VALIDATED** — individual + batch (`90ba918`, `453932f`) |
| Dual quote snapshot (Step 8) | Documented | **VALIDATED_WITH_GUARDS** — order `88002`, snapshot `QSN2-2026-0003`; convert creates no plan/tasks |
| Step 9 preview + persist draft | Documented | **VALIDATED_WITH_GUARDS** — plan `id=2`, `source_quote_snapshot_v2_id=3`; materialize/sessions **BLOCKED** |
| Profitability | Documented target | **PARTIAL** — MVP GET + minimal panel **VALIDATED**; complete post-job truth **DEFERRED**; actual margin $ null |

---

## 10. Forbidden for agents (recap)

No runtime, no /price, no Quote 4 reprice, no order/task creation, no DB, no UI, no registry edits, no CE/Orchestrator rewrite, no cleanup — **until owner GO on scoped step**.

---

## 11. Acceptance criteria for roadmap doc

| Criteriu | OK |
|----------|-----|
| All steps 7G–12 defined | ✅ |
| GO gates explicit | ✅ |
| Dependencies clear | ✅ |
| Frozen paths listed | ✅ |
| UNKNOWN questions listed | ✅ |
| No implementation claimed | ✅ |
