# Intake V6 Finish Truth Persistence V1 (W1-L-FINISH)

Verdict: **W1_FINISH_PASS_COMMITTED** (pending commit hash)

## Lane reservation

| Field | Value |
|-------|-------|
| Task | W1-L-FINISH — `INTAKE_V6_FINISH_TRUTH_PERSISTENCE_V1` |
| Start HEAD | `bee4cfe` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Lane | finish truth persist path only |

### Canonical truths

- `finish_setup.finish_target` — job-level finish zone target
- `finish_setup.artwork_finishes[].print_required` — row-level explicit boolean
- `finish_setup.artwork_finishes[].lamination_required` — row-level explicit boolean
- `finish_setup.confirmed` + row `confirmed` — confirmation anchor (unchanged)

### Contracts / services

- `normalize_intake_v4_finish_setup` (V6 alias `normalize_intake_v6_finish_setup`)
- `save_finish_setup_for_intake_v6_workspace`
- `artwork_finish_runtime_boolean_state`
- `build_form_system_runtime_capture_read_model`
- `apply_readiness_spine_to_pricing_preview`

### Likely files

- `backend/services/intake_v4_finish_truth_service.py`
- `backend/tests/test_intake_v4_finish_truth.py`
- `backend/tests/test_finish_target_runtime_capture.py`
- `backend/tests/test_intake_v6_finish_truth_persistence.py`

### Downstream consumers

- Runtime capture overlay (`finish.finish_target`, `finish.print_required`, `finish.lamination_required`)
- Pricing preview readiness spine
- Quote handoff policy (via capture blockers)
- Product Truth promotion planner (reads persisted booleans; no runtime inference)

### Collision risks

- Shares `finish_setup` writer with cant/return and mounting — mounting spine preserved
- No parallel edits to `finish_setup` readiness spine from W1-L-SPINE

### Integration point

- Existing `PUT /api/v1/intake-v6/workspaces/{id}/finish-setup` autosave path

## Root cause

UI persisted operator `execution_type` and zone-implied finish configuration but did **not** persist canonical fields required by runtime capture:

- `finish_target` never written by frontend
- `print_required` / `lamination_required` never written on artwork rows

Runtime capture correctly remained fail-closed (`FINISH_TARGET_MISSING`, `PRINT_REQUIRED_UNKNOWN`, `LAMINATION_REQUIRED_UNKNOWN`) while UI showed configured finish state.

## Chosen implementation

Backend persist normalization hydrates canonical finish truth from operator selections at save time (same pattern as mounting_scope / mounting_solution hydration):

1. `derive_finish_target_from_zones` — active face/cant/artwork/back zones → `finish_target` (`all` when multiple)
2. `derive_artwork_*_from_execution` — map decisive `execution_type` → row booleans
3. Re-normalize clears stale booleans when `execution_type` returns to `needs_decision` or changes parent mode

No frontend duplicate persistence, no runtime inference at read, no DB migration.

## Validation

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_finish_truth.py tests/test_intake_v6_finish_truth_persistence.py tests/test_finish_target_runtime_capture.py tests/test_intake_v6_canonical_readiness_spine.py tests/test_form_system_runtime_capture_read_model.py -q
```

Result: **51 passed**

## Live runtime (IR-MRJS4VIK / workspace `80570a4a-a806-4305-a39c-b34a72092694`)

| Check | Before (W1-INT-01) | After |
|-------|-------------------|-------|
| `finish_target` | missing | `all` |
| artwork `print_required` | missing | `true` per print_laminate row |
| artwork `lamination_required` | missing | `true` per print_laminate row |
| capture finish blockers | FINISH_TARGET_MISSING, PRINT/LAMINATION unknown | none |
| pricing `is_ready_for_quote` | false (finish blockers) | true |
| mounting spine | green | green (unchanged) |
| handoff | blocked (non-finish blockers remain) | no finish capture blockers |

Persisted readiness snapshot: `workspace.readiness_status` = `ready_for_quote_preview` — **EXPECTED_PERSIST_SNAPSHOT** (non-blocking; handoff/pricing use live spine).

## UI evidence

- Route: `/intake-v6/80570a4a-a806-4305-a39c-b34a72092694/operator` step 2 Finisaje
- Screenshot: `page-2026-07-14T00-03-41-559Z.png` — Logo rows show Print + laminare; live calc lists print/lamination material lines
- Remaining blockers: unclassified vector, missing tariff rates, cant depth contract (W1-L-CANT scope)

## Next allowed task

`W1-L-CANT` — cant/return finish contract (TE2E-006)
