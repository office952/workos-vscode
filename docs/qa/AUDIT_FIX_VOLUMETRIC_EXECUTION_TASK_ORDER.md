# AUDIT/FIX — Volumetric Execution Task Order Alignment

**Date:** 2026-06-17  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `059e48f` — `feat(intake-v3): add commercial and handoff adapters`  
**Verdict:** **PASS** (gap confirmed and fixed locally)

## Purpose

Align runtime volumetric execution plan task order/dependencies with owner rules documented in Intake V3 / ProductSystem — without touching CostEngine, pricing adapters, inventory, UI, or DB schema.

## Pre-flight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `059e48f` |
| Git status | tracked changes from this fix + `?? tmp/` |

## Phase 1 — Audit findings

### Task generation source (runtime)

| Concern | Service / layer |
|---------|-----------------|
| Conditional include/filter | `backend/services/volumetric_conditional_plan_tasks_service.py` |
| Vinyl inject + taxonomy | same + `volumetric_face_vinyl_service.py` + `volumetric_finish_assignment_service.py` |
| Base dependency rules | `backend/services/task_dependency_rules_service.py` |
| Volumetric vinyl/assembly deps | `apply_dynamic_volumetric_vinyl_plan_dependencies`, `apply_dynamic_volumetric_assembly_dependencies` |
| Finalize hook | `finalize_volumetric_plan_dependencies` (called from `backend/routers/execution.py`) |
| Display labels | `backend/services/volumetric_execution_dispatch.py` |

Intake V3 `intake_v3_production_handoff_adapter.py` is **preview-only** (`non_executable=true`) — not runtime execution source.

### Confirmed gaps (before fix)

1. **Face vinyl too early** — `vinyl_application` depended on `face_cnc_cut` and appeared before `return_face_bonding` / `assembly_letters`. Owner rule: final face colantare **after assembly** (and after return painting when painted).
2. **Return painting list order** — `painting` task remained before `assembly_letters` in plan list (deps not enforced post-assembly).
3. **Packaging label** — runtime used `Ambalare / predare`; owner prefers stretch-wrap colet wording. PSU colet note missing on packaging instructions.
4. **Return vinyl** — already correct (workbench vinyl before `side_forming`).
5. **LED before assembly** — already correct via `task_dependency_rules_service.py`.
6. **No shared support source mounting** — runtime does **not** generate `electrical_source_mounting`; `electrical_letters` is per-letter cablare/test only. No fix required.
7. **Return painted Intake V3 vs runtime** — Intake V3 uses `return_finish_type=painted`; runtime uses `volume_finish=paint_after_face_miter_bond` (`is_cant_ral_paint_enabled`). Painted branch fix applied for runtime signal only.

### Test coverage before fix

- Partial order tests in `test_volumetric_finish_assignment_normalization.py` asserted **incorrect** face-vinyl-before-bonding order.
- `test_volumetric_conditional_plan_tasks.py` covered filtering/illumination/packaging policy but not owner post-assembly vinyl order.
- Intake V3 handoff adapter tests cover preview seeds only.

## Phase 2 — Fix applied

### Files changed

| File | Change |
|------|--------|
| `backend/services/volumetric_conditional_plan_tasks_service.py` | Face vinyl deps after assembly/painting; strip vinyl from bonding deps; painting after assembly; reposition painting/face vinyl in list; packaging taxonomy + PSU colet note; QC after face vinyl when present |
| `backend/services/volumetric_execution_dispatch.py` | Align painting/packaging Romanian labels |
| `backend/tests/test_volumetric_finish_assignment_normalization.py` | Update order/dependency assertions; extend fixture plan with assembly/qc |
| `backend/tests/test_volumetric_execution_task_order.py` | **New** targeted owner-rule tests |

### Rules enforced (runtime)

- `return_vinyl_application` before `side_forming` when return wrapped.
- `return_face_bonding` depends on `face_cnc_cut` + `side_forming` only (not face vinyl).
- `assembly_letters` depends on bonding/back/LED path (unchanged).
- `painting` depends on `assembly_letters` when active (`volume_finish=paint_after_face_miter_bond`).
- `vinyl_application` depends on `painting` if present, else `assembly_letters`.
- `qc_letters` depends on face vinyl or painting when those tasks are active.
- `packaging_letters` display + instructions: stretch wrap colet; include PSU watts when illuminated.
- No `electrical_source_mounting` task introduced.

### Runtime support: return painted

| Signal | Supported |
|--------|-----------|
| `volume_finish=paint_after_face_miter_bond` + `paint_tube_count` | **Yes** — painting after assembly |
| Intake V3 `return_finish_type=painted` alone | **No** — contract-only until mapped into runtime quote_input |

## Tests

### Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_execution_task_order.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_production_handoff_adapter.py tests/test_intake_v3_pricing_input_adapter.py tests/test_intake_v3_finish_and_material_workflow.py -q
```

### Results (2026-06-17)

| Suite | Result |
|-------|--------|
| `test_volumetric_execution_task_order.py` | 9 passed |
| `test_volumetric_finish_assignment_normalization.py` + `test_volumetric_conditional_plan_tasks.py` | 54 passed |
| Full packet regression (71 tests) | **71 passed** |

## Boundary confirmation

- No CostEngine / pricing formulas / commercial markup changes
- No Inventory / StockMovement changes
- No DB schema / migrations / `dev.db` changes
- No UI / Employee Mobile runtime changes
- No Intake V3 adapter logic changes (preview seeds unchanged)
- No hardcoded employee names
- No commit / push

## Limitations / open questions

1. `mounting_template_cnc_cut` still exists for forex template orders — distinct from shared-support source mounting; not in no-shared-support illuminated default path.
2. Intake V3 `return_finish_type=painted` needs explicit mapping into runtime `volume_finish` when V3 becomes execution source.
3. QC remains `internal_only`; owner final operator task is packaging/stretch-wrap — QC dependency chain updated but QC not removed.

## Recommended commit message

```
fix(volumetric): align execution task order with owner finish rules

Move face vinyl and return painting after assembly, keep return vinyl
before side forming, and document PSU colet on final packaging task.
```
