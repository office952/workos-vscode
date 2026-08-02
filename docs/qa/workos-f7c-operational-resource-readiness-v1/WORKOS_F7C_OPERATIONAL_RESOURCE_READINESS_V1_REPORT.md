# WORKOS F7C — Operational Resource Readiness (read-only)

## Verdict

```text
INTERNAL GATE = GO (Lead)
APPROACH = read-only ORR allow-list ∩ machines registry
F7C = PASS_WITH_WARNINGS
FIXTURE = 880811 / plan 22 (5 operational tasks)
REGRESSION FIXTURE = 973019 / plan 21 (18 operational tasks)
DB WRITES = ZERO (snapshot sha256 unchanged, execution_plan.updated_at unchanged)
MATERIALIZATION GATE = CLOSED (pilot_gate_open=False, LIVE_DEC009_STATUS=A)
SESSIONS / ASSIGNMENTS CREATED = ZERO
PUSH = NOT EXECUTED
```

## Scope

Single canonical read-only service + Pydantic schema for:

```text
OperationalTask -> WorkcenterRequirement -> ResourceRequirementMode
  -> CompatibleMachineCandidates -> ResourceReadinessResult
```

Composes **existing** truth only — no parallel registry, no invented enum:

- `operation_resource_requirements` (ORR) — `allowed_resource_codes` / `allowed_workcenter_codes` / `default_resource_code`
- `machines` registry — `resource_kind` (machine | tool | work_area) / `is_active` / `is_available`
- `data/operational_workcenters.py` — canonical workcenter code identity

## Files changed

| File | Change |
|------|--------|
| `backend/schemas/operational_resource_readiness.py` | **New.** Pydantic schema — statuses, modes, candidate + result models. |
| `backend/services/operational_resource_readiness_service.py` | **New.** `build_operational_resource_readiness(db, order_id)` — the single read model builder. |
| `backend/routers/execution_plan_v2.py` | Extended existing execution plan-v2 namespace with one new `GET` route (no new router file). |
| `backend/tests/test_operational_resource_readiness.py` | **New.** 14 tests (unit + integration + HTTP). |
| `frontend/src/api/execution.ts` | Added `OperationalResourceReadinessResponse` types + `executionApi.getOperationalResourceReadiness(orderId)`. |
| `frontend/src/components/execution-result/resourceReadinessDisplay.ts` | **New.** Pure Romanian label/tone mapping (no computation). |
| `frontend/src/components/execution-result/resourceReadinessDisplay.test.ts` | **New.** Logic-only test (pattern: `executionResultWorkspace.test.ts`). |
| `frontend/src/components/execution-result/ResourceReadinessPanel.tsx` | **New.** Compact read-only table, no Assign/Schedule/Start controls. |
| `frontend/src/pages/ExecutionDetail.tsx` | Inserted `<ResourceReadinessPanel>` after `BlockersPanel`, before `WorkPanel` (only when `has_plan`). |

## API

```text
GET /api/v1/execution/plan-v2/from-order/{order_id}/resource-readiness
```

- Extends the existing `execution_plan_v2` router (same file as `materialization-audit` and `employee-eligibility`) — no duplicate namespace.
- Zero DB writes. Stable ordering (task order mirrors `operational_tasks[]` in the materialized envelope). Idempotent — two consecutive GETs return byte-identical JSON given unchanged plan/registry state.
- Auth: `require_permission("execution.plan_generate")`, same as sibling read endpoints on this router.

## Readiness matrix — 880811 / plan 22 (5 operational tasks)

| # | Operation | Workcenter (registry status) | `resource_requirement_mode` | Compatible machines | `status` |
|---|-----------|-------------------------------|------------------------------|----------------------|----------|
| 1 | `face_cnc_cut` | `WC_CNC_ROUTING` (resolved) | `orr_allowlist` | `MCH-CNC-4020` (default) | `ready_with_warnings` |
| 2 | `side_forming` | `WC_LETTER_FORMING` (resolved) | `orr_allowlist` | `MCH-CNC-CANT-LITERE` (default) | `ready_with_warnings` |
| 3 | `return_face_bonding` | `WC_METAL_FAB` (resolved) | `orr_allowlist` | `MCH-WELD-STEEL`, `MCH-WELD-ALU` (+ work area `WA-WELD-TABLE`, no default) | `ready_with_warnings` |
| 4 | `painting` | `WC_ASSEMBLY` (resolved) | `workcenter_only` | none (work areas: `WA-ASSEMBLY-01`, `WA-ASSEMBLY-02`) | `workcenter_only` |
| 5 | `packaging_letters` | `WC_ASSEMBLY` (resolved) | `workcenter_only` | none (work areas: `WA-ASSEMBLY-01`, `WA-ASSEMBLY-02`) | `workcenter_only` |

Top-level: `ready=0`, `warning_count=5` (all 5 tasks carry `PLANNING_MINUTES_SOURCE_MISSING`), `blocked=0`.

Live capture: [`live-880811-resource-readiness.json`](./live-880811-resource-readiness.json).

**Honesty note on task 3 (`return_face_bonding`):** ORR allows two welding tools and one work area with **no `default_resource_code`**. Both tools are active and compatible, so this is reported `ready_with_warnings` (warning = missing planning minutes), never `machine_required_but_none_compatible` — a compatible candidate genuinely exists; the absence of a *default* is not a blocker.

## Regression fixture — 973019 / plan 21 (18 operational tasks, protected baseline)

Ran the same GET against the larger protected golden-pilot eligibility fixture to confirm the service scales past the 5-task shape without guessing: `operational_task_count=18`, `ready=0`, `warning_count=18`, `blocked=0`. Live capture: [`live-973019-resource-readiness.json`](./live-973019-resource-readiness.json).

## Owner-mandatory test cases — all covered

| Case | Test |
|------|------|
| `WC_CNC_ROUTING` resolves canonically | `test_wc_cnc_routing_resolves_canonically` |
| `WC_CNC` does not silently pass as canonical | `test_wc_cnc_non_canonical_does_not_silently_pass` |
| Unknown workcenter → warning, not a guessed mapping | `test_unknown_workcenter_warns_without_guessing` |
| Empty workcenter → `missing_workcenter`, no guess | `test_empty_workcenter_is_missing_workcenter` |
| Missing ORR mapping → `unknown_resource_policy` | `test_missing_orr_mapping_is_unknown_resource_policy` |
| Ambiguous ORR (2 allowed workcenters) → `ambiguous_mapping` | `test_ambiguous_workcenter_mapping` |
| Machine required, none compatible (all inactive) → not falsely `ready` | `test_machine_required_but_none_compatible` |
| Default resource inactive → `machine_unavailable` | `test_machine_unavailable_when_default_resource_inactive` |
| Work-area-only ORR → `workcenter_only`, never `machine_required_but_none_compatible` | `test_workcenter_only_not_falsely_blocked_for_missing_machine` |
| Empty `allowed_resource_codes` → `workcenter_only` | `test_no_resource_codes_is_workcenter_only` |
| Full 5-task materialized fixture matches Stage A matrix | `test_f7c_five_task_fixture_matches_stage_a_readiness_matrix` (also asserts zero reality rows, zero plan drift, unchanged commercial total, closed gate before/after) |
| GET creates no assignments/sessions, idempotent, HTTP 200 shape | `test_endpoint_resource_readiness_returns_ok` |
| Plan not found / not yet materialized | `test_plan_not_found`, `test_blocked_not_materialized` |

**Result: 14/14 passed.** Regression subset run alongside (`test_dec009_materialize_gate`, `test_employee_eligibility_read_model`, `test_execution_plan_v2_materialize`, `test_execution_plan_v2_preview`, `test_execution_plan_v2_persist`, `test_f7a_product_linked_task_contract_enrichment`, `test_f7a1_pre_materialization_truth_gap`): **144/145 passed** — the 1 failure (`test_no_migration_needed_for_step_9_3_3`) is a pre-existing, unrelated migration-filename assertion (confirmed red on a clean stash of this branch before any F7C edit).

## Runtime proof (live :8000 / :3000)

- Backend `GET /health` → 200; frontend `GET /` → 200 (frontend dev server had to be restarted via `scripts/dev-detached.ps1` mid-session after it dropped — backend was untouched, no port was killed, per the live-stack rule).
- `GET .../880811/resource-readiness` → 200, matches the matrix above.
- `GET .../973019/resource-readiness` → 200, 18 tasks, no crash.
- Before/after `orders.snapshot_v2_json` SHA-256 and `execution_plan.updated_at` for **both** orders are byte-identical across the GET calls (see table below) — zero side effects.
- `evaluate_materialize_authorization(order_id=880811, plan_id=22)` → `pilot_gate_open=False`, `allowed=False`, `LIVE_DEC009_STATUS='A'` — gate unchanged and closed, before and after.

| Order | snapshot sha256 (before = after) | execution_plan.updated_at (before = after) |
|-------|-----------------------------------|---------------------------------------------|
| 880811 | `a59b6c447d9e6afb484bae9415e85041e12fc73bf5bb20a7cf2a089bd393738b` | `2026-08-03 00:06:15.946013` |
| 973019 | `2d412e6e1234ae44a4bf00f023375b2a454d4bc82ee2d41cb9c63df12611703e` | `2026-08-02 16:48:17.965225` |

## UI evidence

Screenshot: [`screenshots/f7c-01-execution-880811-resource-readiness-panel.png`](./screenshots/f7c-01-execution-880811-resource-readiness-panel.png) — route `/execution/880811`.

**Honest UI opinion:** the new "Pregătire resurse" section sits exactly where specified (after "Necesită atenție", before "Lucru în execuție"), reads as a plain fact table with no interactive controls, and its two visible states ("Pregătit (cu atenționări)" amber, "Doar punct de lucru (fără utilaj)" amber) are visually indistinguishable in tone from each other — both use the same warning color today because neither task in this fixture is truly blocked. The `danger`-toned states (`missing_workcenter`, `unknown_resource_policy`, `machine_required_but_none_compatible`, etc.) exist in the mapping and are unit-tested but were **not** visually exercised in this live fixture, since none of the 5 (or 18) real tasks trigger them. This is honest, not a gap: the fixtures genuinely don't have a blocked resource case today.

## Frontend tests / CI

- `pnpm run lint` → clean (0 errors).
- `pnpm run build` → succeeds.
- New logic-only tests (`resourceReadinessDisplay.test.ts`, 3 tests) → pass in isolation and inside `pnpm run test:ci`.
- Full `pnpm run test:ci` run: 4 pre-existing failures in `src/pages/MaterializedOpsGraph.test.tsx` (unrelated file, not touched by F7C) — confirmed red on a clean stash of this branch before any F7C edit, so this is pre-existing debt, not a regression introduced here.

## Boundaries respected

- No `POST materialize` call issued outside of test-only bypass fixtures (autouse `_UNIT_TEST_BYPASS`, same pattern as existing F7A/F7B tests).
- No mutation of `operational_tasks[]` / `planned_tasks[]` / snapshots.
- No `machine_code` written onto any operational task row.
- No Pricing / CostEngine / sessions / assignment / employee-eligibility writes.
- No SVG/DWG, no fake machines invented — `MCH-*` / `WA-*` codes seeded in tests mirror the real dev.db rows inspected at Stage A.
- No push executed.

## Remaining Owner decisions (unresolved truths, explicit)

1. **No formal `machine_required | machine_optional | workcenter_only` enum exists in the registry.** `resource_requirement_mode` is derived (never invented) from `allowed_resource_codes` + `machines.resource_kind`. If the Owner later adds a formal ORR field for this, the derivation in `operational_resource_readiness_service.py` should be replaced with a direct read, not merged silently.
2. **DEC-006 (planning minutes) is still open.** Every task in both fixtures carries `PLANNING_MINUTES_SOURCE_MISSING` because `estimated_minutes` is null upstream — this surface reports it as a warning (never invents a value), consistent with the capacity-warning-is-not-a-commercial-blocker rule.
3. **`maintenance_conflict` status is defined but unreachable** — no maintenance-window data source exists yet in the registry. Kept in the enum for schema completeness per Owner spec; will only ever fire once such a source exists.
4. **`machine_optional_no_candidate` is also currently unreachable** with today's registry truth (every `workcenter_only` case has zero `allowed_resource_codes` of kind `machine`/`tool` by definition, so there is no "optional machine, no candidate" state distinct from `workcenter_only` yet). Documented as a gap, not silently collapsed into another status.
