# Worklog — Build 4A.1 FACE+CANT Frozen Technical Parity Closure

| Field | Value |
|-------|-------|
| Task | BUILD4A_1_FACE_CANT_FROZEN_TECHNICAL_PARITY_CLOSURE |
| Owner GO | `GO_BUILD4A_1_ONLY` |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `23c1713` |
| End HEAD | see commit `fix(execution): preserve face-cant interface outputs in frozen preview` |
| Initial | `BUILD4A_1_IN_PROGRESS` |
| Final | `BUILD4A_1_FACE_CANT_PARITY_COMPLETE_WITH_GUARDS` |

## Objective

Close divergence between Build 3 live ProductAggregate authority (FACE+CANT adhesive×1 bonding×1) and Build 4A frozen modular graph preview (semantic OK, technical missing). Consume technical truth — do not invent outputs.

## Root cause

1. **Thin Aggregate fixture** (`_seed_volumetric_v2_fixture`): child `TPL-VOLUM-ALUMINIU_v1` omitted `MAT-ADEZIV-CANT-LITERE` and `RETURN_PROFILE_FACE_BONDING` present in production seed.
2. **Preview source gap**: `build_frozen_component_scope` called `build_for_workspace` which filters from **workspace payload only**. Freeze ActiveScope already compiles workspace + `quote_input`, but Aggregate was not re-filtered with that compiled scope.
3. **Task rule ownership**: dossier map tagged `return_face_bonding` → `asamblare` (inactive in FACE+CANT subset), so bonding task rules dropped after filter. Production op code `RETURN_PROFILE_FACE_BONDING` was unmapped.

Not: composition exclusion false-negative, parent suppression, or frozen-graph inventing materials.

## Chosen fix (Strategy A + B)

| Strategy | Change |
|----------|--------|
| A | After Aggregate build in `build_frozen_component_scope`, re-apply `filter_aggregate_by_active_scope` with compiled ActiveScope from quote_input |
| B | Enrich **inline test fixture** (not global seed) with production interface rows + bonding task rule; upsert helper for stale fixtures |
| Task map | Prefer JSON `mini_module_code`; map bonding → `modelare_cant` |

Forbidden strategies avoided: no hardcoded adhesive in frozen graph, no semantic→material invent, no formula/CPP/schema/seed_sync changes.

## Files changed

- `backend/services/quote_snapshot_component_scope_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/tests/test_product_aggregate_volumetric_v2.py`
- `backend/tests/test_frozen_modular_graph_build4a.py`
- This worklog

## Scenario matrix

| Assertion | Full/legacy | FACE | CANT | FACE+CANT |
|-----------|-------------|------|------|-----------|
| Interface marker | n/a / legacy | false | false | true |
| Adhesive count | ≥1 | 0 | 0 | **1** |
| Bonding op count | ≥1 | 0 | 0 | **1** |
| Bonding task rule | present | absent | absent | **1** |
| Frozen assertions | pass | pass | pass | pass |

## Provenance (FACE+CANT)

| Output | Physical source | Semantic owner | Module |
|--------|-----------------|----------------|--------|
| `MAT-ADEZIV-CANT-LITERE` | Child aluminum template materials | interface FACE+CANT | `modelare_cant` |
| `RETURN_PROFILE_FACE_BONDING` | Child aluminum operations | interface FACE+CANT | `modelare_cant` |
| Task `return_face_bonding` | Dossier task_rules | interface / modelare_cant | `modelare_cant` |

## Tests

```
pytest tests/test_frozen_modular_graph_build4a.py
      tests/test_product_aggregate_volumetric_v2.py::test_aggregate_compiles_dossier_task_rules_for_execution_plan
      tests/test_active_scope_snapshot_freeze.py
      tests/test_product_aggregate_active_scope_filter.py
      tests/test_intake_v6_build3_subset_isolation.py
→ 47 passed
```

No-write: snapshot row counts unchanged on live preview; frozen graph `no_write=True`.

## Hash note

FACE+CANT Aggregate / frozen-graph hashes may change vs Build 4A when prior payload lacked adhesive/bonding. That is **correction of incomplete technical input**, not nondeterminism. Full/FACE/CANT hashes remain stable for the same inputs.

## Remaining guards

1. `filter_aggregate_by_active_scope` still fail-opens to full-product keep-all when `scope.errors` (pre-existing).
2. Two V6 official snapshot tests in `test_quote_snapshot_component_scope.py` fail pre-existing (payload validation / BLOCKED) — not introduced here.
3. `test_aggregate_includes_dossier_components` fails pre-existing (Aggregate build does not emit dossier identity components without filter enrich).
4. Production dossier seeds without JSON `mini_module_code` rely on priced_op → `modelare_cant` map.

## Exclusions

No Build 4B/4C/4D. No snapshot/Order/ExecutionPlan/task persistence. No global seed_sync. No schema/migration. No formula/CPP changes.

## Next step

Owner review. Then separate GO for Build 4C read-only Execution preview (preferred) or 4B disposable persistence. Not materialization.

## Commit

Exact-path isolated commit only.

## STOP
