## TASK

VECTOR_LOGO_FACE_BASE_MATERIAL_AND_FINISH_STATE_SYNC_FIX_V1

## HEAD before work

- `117d273`

## Safety state

- `git status -sb`: clean tracked worktree; no staged files
- `git diff --cached --name-only`: empty
- `git status --short --untracked-files=no`: empty
- `git diff --check`: clean before edits

## Root cause

- Persisted `artwork_finishes` rows could carry contradictory state, e.g.:
  - `execution_type = print_laminate`
  - `face_personalization_method = none_raw_plexi`
  - `material_code = null`
- UI header/card summary and combobox were reading different state signals:
  - [frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx)
  - [frontend/src/components/workos/intake-v6/artworkCardPresentation.ts](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/artworkCardPresentation.ts)
- Backend material breakdown used global `face_finish_type` fallback for artwork/logo-only pricing when no letter groups existed, leaking letter-face rows into logo pricing:
  - [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py)

## Files changed

- [frontend/src/lib/svgArtworkContracts.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/svgArtworkContracts.ts)
- [frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts)
- [frontend/src/components/workos/intake-v6/artworkCardPresentation.ts](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/artworkCardPresentation.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx)
- [frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx)
- [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py)
- [backend/tests/test_intake_v4_material_breakdown.py](c:/Users/offic/workos_app_vs/backend/tests/test_intake_v4_material_breakdown.py)
- [docs/worklog/realignment/2026-07-07_vector_logo_face_base_material_finish_state_sync_fix_v1.md](c:/Users/offic/workos_app_vs/docs/worklog/realignment/2026-07-07_vector_logo_face_base_material_finish_state_sync_fix_v1.md)

## What changed

- Frontend now normalizes stale `artwork_finishes` payload rows into coherent canonical states for:
  - raw / `none_raw_plexi`
  - `oracal_641`
  - `oracal_8500`
  - `print_laminate`
- Raw mode now clears stale print/oracal fields and uses explicit raw execution/color state.
- UI header/card summary and combobox now agree even when loading old mixed payloads.
- Backend artwork/logo pricing no longer uses global letter-face finish fallback when the workspace is artwork/logo-only.
- Backend now adds logo/artwork-specific Oracal material rows and application rows for `cut_vinyl` / `translucent_vinyl`.

## Tests run

- `Set-Location "c:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q -k "artwork_raw_skips_global_oracal_face_fallback or artwork_oracal_641_adds_logo_specific_vinyl_and_application or artwork_oracal_8500_adds_logo_specific_vinyl_and_application or artwork_print_laminate_adds_logo_specific_rows or artwork_finish_totals_are_additive_relative_to_raw"`
  - PASS
- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx --reporter=verbose`
  - PASS
- `git diff --check`
  - PASS

## Runtime verification

- Workspace identified from runtime payload/logs:
  - `e4d42fed-a159-4cff-b22b-9979b9574ddb`
  - file `cerc100cm.svg`
- Route checked:
  - `http://127.0.0.1:3000/intake-v6/e4d42fed-a159-4cff-b22b-9979b9574ddb/operator`
- Read-only backend replay against the real workspace payload confirmed:
  - raw / `none_raw_plexi`: base plexiglas present, no logo print/lamination rows, no wrong global `Vinil față Oracal 651`
  - `oracal_641`: base plexiglas present, `Vinil față Oracal 641 — Logo 1` present, logo application service present
  - `oracal_8500`: base plexiglas present, `Vinil față Oracal 8500 — Logo 1` present, logo application service present
  - `print_laminate`: base plexiglas present, logo print + lamination + application rows present
- Direct browser mutation/save was intentionally avoided.

## Forbidden scope confirmation

- No Pricing Registry rewrite
- No Quote/Order changes
- No Execution changes
- No ProductAggregate / TaskGraph / ExecutionPlan changes
- No DB / seed / migration work
- No Logo root activation
- No ACP root activation
- No Image Analyzer runtime changes

## Remaining gaps

- The persisted workspace payload stays stale until the operator re-saves finish state; this fix normalizes UI read-state and backend calculation paths, but does not perform an automatic DB migration/repair.
- The generic base row label is still `Plexiglas 3 mm / față litere` in the current breakdown path even for logo-only artwork scenarios; pricing semantics are corrected, but naming remains broader than the exact component identity.