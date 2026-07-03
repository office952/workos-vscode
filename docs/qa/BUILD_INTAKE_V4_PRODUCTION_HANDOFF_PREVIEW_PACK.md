# BUILD_INTAKE_V4_PRODUCTION_HANDOFF_PREVIEW_PACK

**Date:** 2026-06-22  
**Status:** PASS (scoped read-only production handoff preview)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `335f12f506aebcb907d8debda72015c27e146b8e`  
**Commit:** none (awaiting user confirmation)

---

## Purpose

Expose a **read-only** production handoff preview for Intake V4 Review: material jobs, operation groups, task seed preview, blockers/warnings — without ExecutionTask, stock consumption, or order mutation.

---

## Working tree before (off-scope dirty — do NOT include in commit)

V2/V3 operator workspace, AuthContext, `tmp/`, untracked E2E off-scope, atoms docs — unchanged.

---

## Files modified (in-scope)

| File | Change |
|------|--------|
| `backend/schemas/intake_v4.py` | Production handoff preview response models |
| `backend/services/intake_v4_production_handoff_preview_service.py` | **New** — preview builder |
| `backend/services/intake_v4_workspace_service.py` | `get_production_handoff_preview_for_workspace` |
| `backend/routers/intake_v4_workspaces.py` | GET endpoint |
| `backend/tests/test_intake_v4_production_handoff_preview.py` | **New** — contract + blockers tests |
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | Types + API client |
| `frontend/src/components/workos/intake-v4/IntakeV4ProductionHandoffPreviewPanel.tsx` | **New** — Review panel |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Load + render preview |
| `docs/qa/BUILD_INTAKE_V4_PRODUCTION_HANDOFF_PREVIEW_PACK.md` | This document |

**Not touched:** CostEngine, ExecutionTask creation, inventory, Orders, Employee Mobile, V2/V3 dirty, ACM/bond.

---

## API contract

### `GET /api/v1/intake-v4/workspaces/{id}/production-handoff-preview`

Read-only. Does **not** mutate workspace, orders, inventory, or execution tables.

Top-level fields:

| Field | Value |
|-------|--------|
| `handoff_mode` | `"preview_only"` |
| `stock_consumption` | `false` |
| `creates_execution_tasks` | `false` |
| `creates_stock_reservations` | `false` |
| `quote_estimate_only` | `true` |

Returns blockers/warnings instead of HTTP 422 when setup incomplete (unlike material-breakdown/pricing endpoints).

---

## Material jobs

Derived from `intake_v4_material_breakdown` rows (nesting precision + BLK-18 pricing metadata):

| job_key | Source material_key | Role |
|---------|-------------------|------|
| `face_plexiglas_cutting` | `plexiglas_face` | face |
| `forex_backing_cutting` | `forex_backing` | backing |
| `oracal_vinyl_cutting` | `face_vinyl` | face |
| `print_vinyl_artwork` | `letter_face_print_vinyl` | face |
| `laminate_vinyl_artwork` | `letter_face_laminated_vinyl` | face |
| `return_profile_material` | `return_material` | return |
| `led_modules_install` | `led_modules` | electrical |
| `psu_electrical` | `led_psu` | electrical |

Each job: `creates_stock_reservation=false`, `quote_estimate_only=true`, carries `quantity_basis` + `confidence` from breakdown.

---

## Operation groups (volumetric)

| group_key | Title | Station hint |
|-----------|-------|--------------|
| `cnc_cutting` | CNC / debitare față & spate | cnc_router |
| `vinyl_print_finish` | Colantare / print față | workbench |
| `return_forming` | Modelare cant | return_forming_machine |
| `return_bonding` | Lipire cant la fețe | assembly_bench |
| `led_electrical` | Montaj LED / electric | electrical_bench |
| `assembly` | Asamblare litere | assembly_bench |
| `preflight_qc` | Verificare / pregătire montaj | graphics_workstation |

Groups activate when related V3 catalog operations are active and/or material jobs exist.

---

## Task seed preview

Built from V3 operation catalog via existing `build_v4_task_preview_response`, enriched with:

- `task_key`, `station_hint`, `role_hint`
- `source_material_jobs` links
- `depends_on` from catalog
- `creates_execution_task=false` always
- Note: „Preview seed — nu creează ExecutionTask.”

---

## Blockers / warnings

**Blockers (examples):** `unsupported_template`, `layer_roles_incomplete`, `missing_svg_analysis_json`, `finish_setup_not_confirmed`, analysis boundary codes.

**Warnings (examples):** `missing_psu_config`, `missing_return_depth`, material breakdown warnings (`sheet_nesting_prorated_fallback`, `roll_nesting_color_split_missing`, …), `missing_pricing_registry_row`.

---

## Quote estimate vs production execution

| Layer | This build |
|-------|------------|
| Material qty | From V4 breakdown (nesting/geometry quote estimate) |
| Material jobs | Preview labels only — no reservations |
| Operations | Catalog seeds — no ExecutionTask |
| Commercial total | QuoteWizard / CostEngine (unchanged) |
| Stock | Not consumed |

---

## What this build does NOT do

- Create ExecutionTask / ExecutionPlan / WorkSession
- Modify orders or production status
- Stock consumption or reservations
- Sheet leftovers / warehouse allocation
- DXF/export, Employee Mobile, ACM/bond activation
- CostEngine or Pricing changes

---

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_production_handoff_preview.py tests/test_intake_v4_material_breakdown.py -q
```

**Result:** `24 passed`

Frontend Vitest: omitted — new panel is presentational; no existing V4 Review step test harness.

E2E: not run (follow-up; not PASS blocker).

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| Read-only preview | ✅ |
| No ExecutionTask / stock | ✅ |
| Material jobs from breakdown | ✅ |
| Operation groups logical | ✅ |
| Blockers clear | ✅ |
| UI preview-only copy | ✅ |
| Backend tests pass | ✅ |
| V2/V3 untouched | ✅ |

---

## Recommendation

**Recommend commit** (scoped files only):

```
feat(intake-v4): add read-only production handoff preview for review step
```

---

## Follow-ups

1. E2E: Review shows handoff preview counts after analysis persist.
2. Emit `derivedPartKind` on nesting placements (from nesting precision pack).
3. Optional Confirm step panel reuse.
4. Wire material jobs → operation groups with richer dependency graph when ExecutionTask creation build lands.
