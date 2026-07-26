# Worklog — Build 4C Execution Preview from Frozen Modular Graph

| Field | Value |
|-------|-------|
| Task | BUILD4C_EXECUTION_PREVIEW_FROM_FROZEN_GRAPH |
| Owner GO | explicit Build 4C only |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `8c98dae` |
| End HEAD | `46bfc9b` (`feat(execution): preview task graph from frozen modular snapshot`) |
| Initial | `BUILD4C_IN_PROGRESS` |
| Final | `BUILD4C_EXECUTION_PREVIEW_COMPLETE_WITH_GUARDS` |

## Objective

Read-only Execution preview V2 that consumes only the frozen modular graph (Build 4A / 4A.1). No ExecutionPlan persist, no task materialization, no live Product System recompile.

## Architecture

```
QuoteSnapshotV2 / OrderSnapshotV2
  → build_frozen_modular_graph_from_v2 (4A)
  → build_execution_preview_from_frozen_snapshot (4C)
  → ExecutionPreviewFromFrozen
```

Law: candidates ⊆ `task_contract.task_rules` only. Materials filtered by frozen scope exclusions. No CPP reprice. No role/machine invent.

## Endpoints (read-only)

| Method | Path | DB |
|--------|------|-----|
| POST | `/api/v1/execution/plan-v2/preview-from-frozen-snapshot` | none |
| GET | `/api/v1/execution/plan-v2/preview-from-frozen/{order_id}` | `db.get` Order only |

Distinct from write paths: `plan-v2/from-order`, `materialize-tasks`, V1 `plan/from-order`.

## Files changed

- `backend/schemas/execution_preview_from_frozen.py`
- `backend/services/execution_preview_from_frozen_graph_service.py`
- `backend/routers/execution_preview_from_frozen.py`
- `backend/tests/test_execution_preview_from_frozen_build4c.py`
- This worklog

## Scenario proof

| Scenario | Candidates | Bonding | Adhesive | Writes |
|----------|------------|---------|----------|--------|
| Full/legacy `active=[]` | task_rules | present | present | 0 |
| FACE | FACE only | 0 | 0 | 0 |
| CANT | CANT only | 0 | 0 | 0 |
| FACE+CANT | FACE+CANT+bond×1 | 1 | 1 | 0 |

Negative: `scope.errors` → `scope_invalid` + empty candidates; missing adhesive FACE+CANT → `blocked`; excluded mats do not leak; duplicate bonding → `blocked`.

## No-write

- Snapshot POST: no DB
- Order GET: one read
- QuoteSnapshotV2Record count unchanged on live preview compose
- Router AST: no commit/add/flush

## Remaining guards

1. Existing `POST …/plan-v2/preview/{order_id}` may still emit synthetic composition_graph tasks — Build 4C path does **not**; FE Generate Plan (V1) remains WRITE_RISK
2. Dependency graph is sequence-linear (not full rule-graph)
3. Role/machine hints empty until frozen contract carries them
4. Order 14 without V2 → compatibility shell, not modular invent

## Exclusions

No Build 4B, no Build 4D, no snapshot/Order/plan/task persistence, no schema/migration/seed, no Intake/PD/Aggregate/CPP edits.

## Tests

```
pytest tests/test_execution_preview_from_frozen_build4c.py
      tests/test_frozen_modular_graph_build4a.py
      tests/test_intake_v6_build3_subset_isolation.py
→ green
```

## Next step

Owner review. Then separate GO for Build 4B (disposable persist) or Build 4D (materialization). Prefer 4C acceptance before any write path.

## STOP
