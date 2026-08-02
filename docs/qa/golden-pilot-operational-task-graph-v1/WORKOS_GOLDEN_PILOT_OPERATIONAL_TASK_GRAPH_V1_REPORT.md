# WORKOS â€” Golden Pilot Operational Task Graph V1

**Stamp:** PASS WITH WARNINGS
**Date:** 2026-08-02
**Canonical repo:** `C:\w\psiso`
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`
**Prior tip (pushed):** `1144e091` â€” Ship read-only material planning hints
**This build commit:** local only â€” `Materialize golden pilot operational task graph`

---

## 1. Repo / runtime gate

| Signal | Value |
|--------|-------|
| Active worktree | `C:\w\psiso` (contains `1144e091` + validated runtime) |
| Stale checkout | `C:\Users\offic\workos_app_vs` â€” detached `82a713e0`; do not use |
| Remote | `office952/workos-vscode.git` |
| Runtime | backend `:8000`, frontend `:3000`, DB `backend/dev.db` |
| Stash | `stash@{0}: wip-employee-unrelated` â€” intact |

`1144e091` audited and pushed separately earlier in this GO; local = remote = `1144e091` at start of build (0/0).

---

## 2. Root cause â€” `blocked_missing_task_rules`

1. Modular process bridge on `hard_blocked` cleared letters `task_rules` to `[]` (`letters_task_rules_cleared_on_block`).
2. EP V2 preview hard-fails when `aggregate.task_contract.task_rules` is empty.
3. Secondary: dossier extract ignored `"tasks"` key (now also accepts `"tasks"`).

**Fix:** on hard block, keep dossier letters rules (`letters_task_rules_dossier_fallback_on_block`); map missing priced ops; classify `ANALYZE_SVG` non-operational; finish-aware + alias collapse; real DAG from `depends_on_process_ids`.

---

## 3. Decisions implemented

| DEC | Result |
|-----|--------|
| DEC-003 RETURN | Module `RETURN_PROFILE_*` collapsed when parent priced op present |
| DEC-004 PAINTING | Module `PAINTING` collapsed when parent `painting` present |
| DEC-005 Workcenter | Resolved from aggregate op / PD role only; null+gap if missing (no invent) |
| DEC-006 Minutes | `estimated_minutes=null` + `PLANNING_MINUTES_SOURCE_REQUIRED` warning OK |
| DEC-007 DAG | Process-graph edges; catalog fallback only when deps empty; cycle fail-closed |
| DEC-009 | `True_CONDITIONAL` â€” materialize only `973015/17`; protected orders forbidden |

---

## 4. Fixture

| Field | Value |
|-------|-------|
| workspace | `IV6-GPTG-*` / `b3f3b2cf-â€¦` |
| quote_id | 15 |
| order_id | **973015** |
| order_code | `ORD-IV6-V2-1785672021-15` |
| plan_id | **17** |
| path | freeze QuoteSnapshotV2 â†’ pricing review â†’ owner approval â†’ accept â†’ convert â†’ EP persist â†’ audit â†’ materialize |
| task_rules | 19 (dossier fallback on modular block; modular-shaped codes preserved) |
| planned_tasks | **18** (ANALYZE_SVG excluded; RETURN aliases collapsed) |
| dependencies | **24** edges, acyclic |
| operational_tasks | **18** after materialize |
| sessions / actuals | **0 / 0** |

---

## 5. Materialization

| Check | Result |
|-------|--------|
| `blocked_missing_task_rules` | **0** |
| Audit dry_run | `ready_with_warnings` (minutes / readiness-gate excluded) |
| Auth | `True_CONDITIONAL` allowed for 973015/17 only |
| POST materialize | success â€” `execution_tasks_created=true`, activation_hash set |
| 2nd materialize | **409** `operational_tasks_already_materialized` (safe idempotency) |
| Inventory / `/price` | not called |
| Protected 92401 / 973012 / 973013 | snapshot + `tasks_json` hashes **unchanged** |

---

## 6. UI

**URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=973015`

| Screenshot | Path |
|------------|------|
| Full page | `screenshots/01-973015-full-page.png` |
| Dependency list | `screenshots/02-973015-dependency-graph.png` |

**Honest opinion:** Page correctly shows Operational Plan with 18 materialized pending tasks, real DAG in DEPENDS, materials section collapsed/secondary, sessions/actuals 0. Gap tags for null WC/minutes are honest. DEC-009 banner still mixes â€œfurther POST blockedâ€ with already-materialized envelope â€” slightly noisy after conditional authorize, but not corruptive. No new page required.

---

## 7. Tests run

**Green:** `test_golden_pilot_task_contract_dag`, `test_dec009_materialize_gate`, `test_product_process_live_aggregate_bridge`, `test_execution_plan_v2_preview`, `test_execution_plan_v2_materialize`.

**Not run:** full pytest / full frontend suite.

---

## 8. Files changed (product)

- `backend/services/product_process_aggregate_bridge.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/execution_plan_v2_preview_service.py`
- `backend/services/task_dependency_rules_service.py`
- `backend/services/dec009_materialize_gate.py`
- `backend/data/product_process/catalogs.py`
- `backend/tests/test_dec009_materialize_gate.py`
- `backend/tests/test_golden_pilot_task_contract_dag.py`
- QA + worklog under `docs/qa/golden-pilot-operational-task-graph-v1/` and `docs/worklog/realignment/`

---

## 9. Warnings / next

**Warnings (acceptable):** null planning minutes; null workcenters (no canonical WC on many ops); modular resolver still blocked â†’ dossier fallback; live uvicorn may still show stale DEC-009 identity until restart; accept-blocker bypass used for SVG/layer completeness (same pattern as materials RO fixture).

**Next Owner GO:** workcenter registry fill for volumetric priced ops; planning minutes source (not from `/price`); optional restart + re-stamp DEC-009 UI copy for True_CONDITIONAL; extend finish-aware paint-only / vinyl-only live fixtures.
