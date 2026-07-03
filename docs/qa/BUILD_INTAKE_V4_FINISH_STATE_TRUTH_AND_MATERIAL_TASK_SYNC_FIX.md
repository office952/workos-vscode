# BUILD_INTAKE_V4_FINISH_STATE_TRUTH_AND_MATERIAL_TASK_SYNC_FIX

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (before commit) | `fe9b39d9206796a1dfe286b6e9db3d74267edd0f` |
| Build date | 2026-06-22 |

## Purpose

Align **UI finish selections → persisted payload → material breakdown → task dry-run** so Oracal/print/laminare/cant wrapped are not shown when per-layer truth is: față fără finisaj, cant aluminiu standard, artwork „Decizie ulterioară”.

## Root cause

| # | Layer | Finding |
|---|-------|---------|
| 1 | Material breakdown | Used **global stale** `face_finish_type` / `return_finish_type` for vinyl gate and return label; ignored per-group `none` / `standard_aluminum` when letter groups exist |
| 2 | Roll nesting | Added `face_vinyl` whenever roll nesting data existed if global face was Oracal — **no per-group gate** |
| 3 | Artwork print | Print/laminare rows fired on persisted `printed_vinyl_on_face` instead of skipping `needs_decision` |
| 4 | Persist / globals | Job-level globals stayed `oracal_651` / `oracal_wrapped` while per-group face was `none`; return/artwork not always synced on save |
| 5 | UI refetch | Breakdown / dry-run panels refetched only on `analysisIdentityKey`, not on finish identity change after save |

## Fix (scoped)

### Backend

- `backend/services/intake_v4_finish_truth_service.py` — per-layer finish resolution + `normalize_intake_v4_finish_setup`
- `backend/services/intake_v4_material_breakdown_service.py` — gate vinyl/print on groups; effective return label/depth; `artwork_execution_pending` warning
- `backend/services/intake_v4_workspace_service.py` — normalize finish on save

### Frontend

- `frontend/src/lib/intakeV4/intakeV4FinishPayloadSync.ts` — sync globals from layers before save; `finishSetupIdentityKey` for refetch
- `frontend/src/lib/intakeV4/intakeV4LetterGroups.ts` — derive defaults: face `none`, return `standard_aluminum`
- `frontend/src/lib/intakeV4/intakeV4ReturnCantBridge.ts` — default return `standard_aluminum`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` — sync on save; refetch panels on finish identity change; task preview reads persisted groups when layers exist

## Real workspace retest — IV4-46499080 (PASS post re-save)

Retestul pe IV4-46499080 a fost validat pe dev DB după re-save echivalent setărilor owner. Flow-ul real așteptat este: owner/operator apasă **Salvează finisaje** în UI, apoi hard refresh/review.

### Payload truth post re-save

| Field | Value |
|-------|-------|
| Global `face_finish_type` | `none` |
| Global `return_finish_type` | `standard_aluminum` |
| L2 / L3 | face `none`, cant `standard_aluminum`, 60 mm |
| L1 artwork | `needs_decision`, cant `standard_aluminum`, 60 mm |

### Material lines

| Line | Result |
|------|--------|
| Plexiglas / față litere | **0.5834 m²** ✓ |
| Vinil față | **absent** ✓ |
| Print față L1 | **absent** ✓ |
| Laminare print L1 | **absent** ✓ |
| Cant / return | **`standard_aluminum` · 60 mm** · 13.62 ml ✓ |
| Oracal cant | **absent** ✓ |
| Module LED | **55 buc** ✓ |
| PSU | **2 buc** ✓ |
| Forex/backing | **absent**, fără material inventat ✓ |

### Task activation

| Task | Result |
|------|--------|
| `oracal_vinyl_cutting` / `face_vinyl_application` | inactive (absent din dry-run) ✓ |
| `print_artwork` / `laminate_print` | inactive ✓ |
| `return_vinyl_application_workbench` | inactive (`inactive_by_finish_or_context`) ✓ |
| `return_side_forming` / `return_face_bonding` | active ✓ |
| `led_module_install` / `psu_electrical_wiring` | active ✓ |
| `letter_assembly` | active, provisional ✓ |

### Warnings / safety

- `artwork_execution_pending` — **intenționat** pentru L1 Decizie ulterioară ✓
- `can_generate_real_tasks=false` ✓
- **Fără** ExecutionPlan ✓
- **Fără** `tasks_json` ✓
- **Fără** consum stoc ✓

## Tests at commit basis

```
test_intake_v4_material_breakdown.py + test_intake_v4_finish_truth.py + test_intake_v4_task_generation_dry_run.py → 38 passed
test_tpl_volumetric_operation_keys_alignment.py → 22 passed (run separately)
frontend finish sync vitest (intakeV4FinishPayloadSync.test.ts) → 2 passed
```

## Boundary

- No ExecutionPlan / `tasks_json` writes
- No CostEngine / Pricing Registry changes
- No V2/V3 dirty paths
- No nesting footprint fix in this commit (separate build)

## Verdict

| Scope | Verdict |
|-------|---------|
| Finish state truth sync | **PASS scoped** |
| Commit | **Approved** |
