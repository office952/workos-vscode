# Worklog — Product Process Resolver Live Aggregate Bridge

| Field | Value |
|-------|-------|
| Task | `PRODUCT_PROCESS_RESOLVER_LIVE_AGGREGATE_BRIDGE` |
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `baec7a9` |
| End HEAD | (see commit) |
| Initial | `PRODUCT_PROCESS_LIVE_AGGREGATE_BRIDGE_IN_PROGRESS` |
| Final | `PRODUCT_PROCESS_LIVE_AGGREGATE_BRIDGE_COMPLETE_WITH_GUARDS` |

## Active path (before → after)

**Before:** `ProductAggregateService.build` → dossier `task_rules_json` → `_build_task_contract` (sequence-ish, no process DAG).

**After:** same compile for BOM/ops → `apply_modular_process_graph_to_aggregate` → pure resolver → **replace** letters `task_contract` (no dossier concat). Workspace compose re-applies with `finish_setup` payload; preserves `linked_segment:` logo rules.

## Alternatives

| Variant | Decision |
|---------|----------|
| A Direct in AggregateService | Used as call site |
| B Workspace compiler only | Also used for workspace re-resolve |
| C Separate adapter | **Chosen** — `product_process_resolve_input_adapter` + bridge apply |
| D Existing extension point | None suitable; mini-modules are not process DAG |

Why: smallest coupling, testable, identity-gated, zero-write, scalable to next product via contract registry later.

## Identity gate

`normalize_template_code(canonical) == normalize_template_code(TPL-VOLUMETRIC-LETTERS_v2)` via `resolve_template_identity`. No display-name matching.

## Files

Created:
- `backend/services/product_process_resolve_input_adapter.py`
- `backend/tests/test_product_process_live_aggregate_bridge.py`
- this worklog

Modified:
- `backend/services/product_process_aggregate_bridge.py` — live apply + snapshot-from-aggregate
- `backend/services/product_aggregate_service.py` — hook + `process_bridge_payload`
- `backend/services/product_aggregate_workspace_composition_service.py` — end-of-compose re-bridge
- `backend/schemas/product_aggregate.py` — observability fields on task_contract
- `backend/tests/test_product_aggregate_volumetric_v2.py` — expect modular graph

## Tests

```
pytest tests/test_product_process_live_aggregate_bridge.py
     tests/test_product_process_contract_resolver.py
     tests/test_frozen_modular_graph_build4a.py
     tests/test_execution_preview_from_frozen_build4c.py
     tests/test_product_aggregate_volumetric_v2.py::test_aggregate_compiles_modular_process_graph_for_execution_plan
→ 108 passed

logo task_rules compose: PASS
```

## Guards remaining

1. Intake fields for cable/corner/screws still optional mapping — missing → defaults/blockers as documented
2. Not wired into CPP (by design)
3. Pre-existing: some volumetric component tests expect dossier components Aggregate no longer sources
4. Logo workspace component-set equality tests flaky/pre-existing vs active scope

## Next safe step

**Option 1 — OWNER REVIEW OF LIVE AGGREGATE BRIDGE**

## STOP
