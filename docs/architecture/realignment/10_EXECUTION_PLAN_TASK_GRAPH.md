# ExecutionPlan — Task Graph & Operational Scheduling

**Version:** 1.0.2  
**Status:** Target architecture + **Step 9 preview + persist draft VALIDATED_WITH_GUARDS** (2026-06-30)  
**Step:** 9 — preview **VALIDATED**; persist draft **VALIDATED_WITH_GUARDS**; materialize/sessions **BLOCKED**

---

## 1. Rolul sistemului

ExecutionPlan transformă **graful tehnic înghețat** (din Order snapshot / ProductDefinition processes) în **taskuri operaționale reale**: ordine, dependențe, paralelizare, asignare, resurse, utilaje, pregătire execuție.

**Regulă:** ExecutionPlan vine **după** Quote/Order. Nu generează prețul clientului. Nu decide produsul. Nu inventează taskuri din catalog paralel.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Taskuri reale** | tasks_json persisted |
| **Ordine / dependencies** | DAG operational |
| **Paralelizare** | Concurrent tasks where allowed |
| **Asignare** | Employee, team, workcenter |
| **Resurse / utilaje** | Machine assignment |
| **Pregătire execuție** | Plan state, approval gates |
| **Estimated duration (planning)** | For capacity — **not commercial price** |
| **Linkage** | order_id, snapshot ref |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial client |
| CommercialPriceProposal |
| Regula de ofertă / markup |
| EstimatedInternalCost recalculation |
| ProfitabilityAnalysis final |
| ProductDefinition compilation (reads frozen) |
| Intake workspace mutation |
| Minute reale (ExecutionActuals) |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Order snapshot | snapshot_line_items, product_definition |
| Frozen processes[] | From priced/accepted quote path |
| Operational registry | Skills, workcenters (partial today) |
| Machines/utilaje | Capability matching |
| Template task_rules | **Reference only** — not parallel driver |

**API (canonical V2 path):**

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/execution/plan-v2/preview/{order_id}` | Read-only preview from `orders.snapshot_v2_json` |
| `POST /api/v1/execution/plan-v2/from-order/{order_id}` | Persist one `execution_plan` draft row |
| `POST /api/v1/execution/plan-v2/materialize-tasks/{order_id}` | Materialize operational_tasks — **BLOCKED / NEEDS OWNER GO** |

**Legacy (V1):** `POST /execution/plan/from-order/{id}` — blocked for V2 orders (`EXECUTION_PLAN_V2_REQUIRED`)

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| execution_plan.tasks_json | Operator UI, Employee Mobile |
| Task instances | Start/stop sessions |
| Plan vs actual baseline | ExecutionActuals comparison |
| Capacity load | Scheduling views |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Operational task list | **ExecutionPlan** post-order |
| Product structure | Order snapshot — **upstream frozen** |
| Task preview (Intake) | **NOT** truth — ephemeral |
| V3 operation catalog | **DEVIATED** — parallel source |
| dossier task_rules | Documentation — **not** driver |

---

## 7. Conexiuni cu celelalte sisteme

```
Quote/Order snapshot (product_definition.processes)
    ↓
ExecutionPlan (THIS)
    ↓
ExecutionActuals (task start/stop, real minutes)
    ↓
ProfitabilityAnalysis (time estimated vs real)
```

| Sistem | Relație |
|--------|---------|
| ProductDefinition | Source processes — frozen at order |
| Cost Engine | **NO** task generation |
| Intake task-preview | Preview only — label clearly |
| HR/Pontaj | Assignment eligibility — not commercial |
| Machines | Feasibility + assignment |

**Regulă critică:** Taskurile vin din ProductDefinition/ProductAggregate graph — **not** CostEngine, **not** V3 catalog.

---

## 8. Reguli owner obligatorii

1. No task creation from parallel catalog in production path.
2. Plan after order — not before accept (except dry-run previews labeled).
3. Estimated minutes in plan = capacity — **not** client billing.
4. produce_order fallback when processes empty — **fix** — not acceptable target.
5. Explicit approval before plan activation — governance.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| 3 task sources | V3 catalog, dossier rules, product_definition | `DEAD_PIECE` |
| produce_order fallback | Empty processes collapse | `HIGH_RISK_DEVIATED` |
| Layer-1 only | Multi-layer processes lost | `NEEDS_OWNER_DECISION` |
| Intake task-preview | ~13 ops — not order snapshot | `MISLEADING_UI` |
| can_generate_tasks: false | Dry-run blocked | OK if labeled preview |
| No execution_plan at convert | Separate step | Documented |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Single source | Order snapshot product_definition.processes |
| Dependency resolution | From technical graph |
| No catalog parallel | Deprecate V3 for production |
| Planning time | Separate from commercial |
| Hardening Step 9 | order_id ↔ plan ↔ sessions clear |

### Runtime — Execution Plan V2 envelope (VALIDATED 2026-06-30)

**Status:** **VALIDATED** on controlled QA fixture (`order_id=88001`, `plan_id=1`). Full Step 9 hardening still **NEEDS OWNER GO**.

| Rule | Runtime behavior |
|------|------------------|
| V2 envelope | `tasks_json` contains `planned_tasks[]` and `operational_tasks[]` |
| `planned_tasks[]` | **Informative / design intent** — not operational source after materialize |
| `operational_tasks[]` | **Operational source** after materialize |
| Parser | `execution_plan_task_parser.py` — **no fallback** to `planned_tasks[]` for operational reads |
| `v2_not_materialized` | Blocks mutating paths — readiness guard → **422** |
| `v2_operational_ready` | Allows plan mutations per existing lifecycle |
| Materialize | `materialize_execution_plan_v2_operational_tasks` — sets `execution_tasks_created=true` |
| Materialize ≠ sessions | Materialize does **not** create ExecutionReality rows or task sessions |
| `execution_tasks_created` | Means operational task materialization — **not** ExecutionReality/session start |

**UI (validated):** ExecutionDetail badge `Operational tasks ready`; OperatorProductionBlueprintPanel chip; OperationalReports plan metrics.

**Worklogs:** `2026-06-30_controlled_fixture_and_reqa_v2_readiness.md`, `2026-06-30_step_9_3_6_operational_reality_review_audit.md`

### Runtime — Step 9 preview + persist draft from Order snapshot V2 (VALIDATED_WITH_GUARDS 2026-06-30)

**Status:** Preview **VALIDATED** (`8dd67e9`); persist draft **VALIDATED_WITH_GUARDS** (`b12889c`).

| Rule | Runtime behavior |
|------|------------------|
| Source | `orders.snapshot_v2_json` — technical snapshots only; commercial/internal in `ignored_pricing_sources` |
| Preview | **No DB writes**; `no_write=true`; READINESS_GATE dossier rules excluded from operational candidates |
| Persist draft | Exactly **one** `execution_plan` row; **no** `execution_tasks` table writes; **no** sessions |
| Idempotency | Second persist → `status=already_exists`, HTTP **200**, no duplicate row |
| Forbidden | `/price`, CostEngine, QuoteOrchestrator |

**Live evidence (order `88002`, snapshot `QSN2-2026-0003` / `id=3`):**

| Field | Value |
|-------|-------|
| Preview status | `partial_missing_planning_minutes` |
| Task candidates | **12** planned tasks, **17** operations |
| Persist plan | `execution_plan.id=2` |
| `source_quote_snapshot_v2_id` | **3** |
| `plan_source` | `order_snapshot_v2` |
| `tasks_json` | Present — draft envelope with `planned_tasks[]` |
| Side effects | **No** execution_tasks; **no** sessions; **no** Employee Mobile |

**Guard:** HTTP POST persist returned **422** against stale running backend (pre-READINESS_GATE fix); service-level persist with current code **PASS**. Restart backend before HTTP verification.

**Tests:** **107 pytest** (persist suite); preview suite **156 passed** with Step 8/9 scoped run.

**Worklogs:** `2026-06-30_step9_order_snapshot_to_execution_plan_audit_skeleton.md`, `2026-06-30_step9_persist_draft_execution_plan.md`

**Not validated / blocked:** `materialize-tasks`; operational_tasks envelope on live order; task sessions (Step 11+).

### Runtime — Step 9 materialization audit-only (VALIDATED 2026-06-30)

**Status:** Read-only audit **VALIDATED** — GET endpoints; **no** POST materialize on live order.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/execution/plan-v2/{execution_plan_id}/materialization-audit` | Dry-run mapping audit by plan id |
| `GET /api/v1/execution/plan-v2/from-order/{order_id}/materialization-audit` | Same audit by order id |

| Rule | Behavior |
|------|----------|
| Mode | `audit_only` — **no DB writes** |
| `materialization_status` | `blocked_needs_owner_go` — POST materialize not exercised |
| Dry-run | Uses `materialize_operational_tasks_from_v2_envelope()` without persist |
| Source | `execution_plan.tasks_json` `planned_tasks[]` (not live repricing) |
| Non-operational | READINESS_GATE + excluded dossier rules surfaced separately |
| Actual materialize | `POST .../materialize-tasks/{order_id}` — **BLOCKED / NEEDS OWNER GO** |

**Live evidence (plan `id=2`, order `88002`):** dry_run `ready_with_warnings`; **12** materializable candidates; **1** non-operational (READINESS_GATE); **no** `operational_tasks[]` in envelope yet.

**Worklog:** `2026-06-30_step9_materialization_audit_only.md`

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Generate plan from Intake workspace directly (production) |
| Generate tasks from Cost Engine output |
| Use dossier task_rules as runtime driver without snapshot |
| Plan modifies commercial price |
| Plan invents tasks not in product graph |
| Silent produce_order fallback |
| Materialize creates sessions or starts tasks | **Forbidden** — validated: materialize does not |
| Parser fallback to `planned_tasks[]` for operational reads | **Forbidden** — validated: no fallback |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Order → plan | All active modules → tasks |
| Same graph as aggregate | Traceable task codes |
| No catalog bypass | Production path clean |
| Preview labeled | Intake dry-run ≠ real plan |
| Actuals linkage | Each task session → plan task |
