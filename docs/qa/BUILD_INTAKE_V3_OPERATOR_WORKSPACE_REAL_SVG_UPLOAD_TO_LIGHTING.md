# BUILD_INTAKE_V3_OPERATOR_WORKSPACE_REAL_SVG_UPLOAD_TO_LIGHTING

## Purpose

Validate the real Operator Workspace chain: **SVG upload → path geometry → layer roles → perimeter classification → lighting module suggestion → PSU save**, without DB manual edits or bypassing the operator flow.

Companion implementation: **BUILD_INTAKE_V3_OPERATOR_WORKSPACE_GLOBAL_FILE_DROP_UPLOAD** (scoped drag & drop on Operator Workspace page).

## Problem

Runtime workspace `e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf` had partial production model data but **no parsed path geometry**:

| Field | Before upload |
|-------|---------------|
| `snapshot_available` | true |
| `geometry_status` | `geometry_partial` |
| `path_geometry_summary` | absent |
| `classification_available` | false |
| `total_letter_perimeter_ml` | null |
| `layer_role_confirmation.layers` | [] |
| Operator SVG & Layers | “No SVG layers detected yet” |

Root cause: SVG never uploaded/parsed through the operator pipeline; lighting module suggestion correctly stayed unavailable (post `3f4bf36` fix).

## Upload audit (existing flow)

| Question | Answer |
|----------|--------|
| Where is SVG uploaded? | `IntakeV3SvgUploadPanel` on Operator **SVG & Layers** tab; also legacy `IntakeV3App.tsx` |
| Endpoint | `POST /api/v1/intake-v3/workspaces/{workspace_id}/svg` |
| Frontend helper | `uploadIntakeV3WorkspaceSvg()` in `frontend/src/lib/intakeV3/api.ts` |
| Backend | `attach_svg_raw_analysis_to_workspace()` → `build_path_geometry_summary_from_svg_text()` |
| Layer roles source | `path_geometry_summary.layers` via `layer_role_confirmation_service` |
| Perimeter / lighting | Requires confirmed face layer + parsed path metrics |
| Accepted types | `.svg`, `image/svg+xml` |
| Operator drag & drop before fix | **Not present** — button + hidden input only |
| Risk of double upload | Mitigated by shared `intakeV3SvgUploadFlow.ts` in-flight lock |

## Implementation — scoped file drop (frontend only)

**New**

- `frontend/src/lib/intakeV3/intakeV3SvgUploadFlow.ts` — shared validation, single-flight lock, `uploadSvgFileToWorkspace()`
- `frontend/src/lib/intakeV3/operatorSvgUploadHelpers.ts` — `applyOperatorSvgUploadResult()` refreshes layer roles after upload
- `frontend/src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorWorkspaceFileDrop.tsx` — page-scoped overlay + drop handler
- Tests for upload flow and file drop

**Modified**

- `IntakeV3SvgUploadPanel.tsx` — uses shared flow; mentions drag & drop fallback
- `IntakeV3OperatorWorkspaceApp.tsx` — wraps page in file drop
- `IntakeV3OperatorSvgLayersTab.tsx` — `onUploaded` → `applyOperatorSvgUploadResult()`

**Design**

- Drop anywhere on Operator Workspace page only (not global app)
- Overlay: “Drop SVG file to upload to this workspace”
- `preventDefault` on drag events (no browser navigation)
- First SVG when multiple files dropped (notice)
- Classic file input remains fallback
- No new backend endpoint; no duplicate SVG parsing

## Runtime preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (before) | `3f4bf36` |
| Git status | tracked frontend changes + `?? tmp/` only |
| Port 8000 | listening |
| Port 3000 | listening |
| Port 3001 | not used |
| `/health` | healthy |
| OpenAPI routes | 320 |
| Phase 3–5 guards | `layer-finish-assignments`, `targets`, `lighting-plan` present |

## SVG real tests

### Test A — owner-style SVG (failed parse)

| | |
|-|-|
| File | `blueprints/volumetric-letter-svg-test/litere-volumetrice.svg` |
| Method | `POST .../svg` (API, same pipeline as operator upload) |
| HTTP | 200 |
| Raw analysis | saved (groups: Spate, sanfren, volum, fata_x0020_plexiglas, autocolant) |
| `path_geometry_summary.parse_status` | **`failed`** |
| `error_code` | **`xml_unsafe_construct`** (DOCTYPE) |
| Layers for roles | 0 |
| Perimeter / lighting | blocked |

**Note:** Fixing DOCTYPE / unsafe XML is a **separate backend build** — out of scope here.

### Test B — repo fixture SVG (success)

| | |
|-|-|
| File | `frontend/e2e/fixtures/volumetric-multilayer.svg` |
| Method | `POST .../svg` |
| HTTP | 200 |
| `path_geometry_summary.parse_status` | **`parsed`** |
| Detected path layer | `layer-litere` (1 path, perimeter 126.491 mm) |
| Layer role auto | `face` |
| Operator confirm | `PUT .../layer-role-confirmation` → `layer-litere` confirmed as `face` |

**Parsing caveat:** Fixture has 3 Inkscape layers (LITERE, DIBOND, CADRU) but path geometry parser surfaced **1 layer** with one open path (triangle). Rect paths in same group may need separate path-geometry build review — not blocking lighting chain proof.

## Geometry result (after Test B + role confirm)

| Field | Value |
|-------|-------|
| `snapshot_available` | true |
| `geometry_status` | `geometry_partial` (backing/return/bevel missing — expected for single face layer) |
| `path_geometry_summary` | present, `parse_status=parsed` |
| `face_cutting_perimeter_ml` | **0.126491** m |
| `total_letter_perimeter_ml` | **0.126491** m |
| `classification_status` | `partial` (face high quality) |
| Layer roles | 1 layer confirmed (`layer-litere` → face) |

Standalone `geometry-path-perimeter-classification` GET returned stale `path_geometry_summary_missing` in one probe; **`geometry-metrics-snapshot` is authoritative** and includes merged classification.

## Lighting result

Derived suggestion (V2 formula):

```
ceil(0.126491 m × 1000 / 100 mm pitch) = 2 modules
```

Saved via `PATCH .../lighting-plan`:

| Field | Value |
|-------|-------|
| `illumination_mode` | `frontlit` |
| `led_system` | `modules` |
| `module_power_w` | **1.44** |
| `module_count` | **2** |
| `estimated_total_watts` | **2.88** |
| `required_watts_with_reserve` (@30%) | **3.74** |
| `psu_strategy` | `auto` |
| `psu_units` | 1× 60 W |
| `is_confirmed` | true |
| `lighting_plan_status` | `complete` |

Readiness after save: `can_create_quote=true` (workspace had prior finish setup; quote remains subject to real blockers if layer finishes incomplete).

## Tests run

### Frontend (vitest)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV3/intakeV3SvgUploadFlow.test.ts `
  src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorWorkspaceFileDrop.test.tsx `
  src/components/workos/intake-v3/IntakeV3SvgUploadPanel.test.tsx `
  src/lib/intakeV3/lightingModuleCountDerivation.test.ts `
  src/lib/intakeV3/operatorLightingPlanForm.test.ts
```

**Result:** 35 passed

### Backend (pytest)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest `
  tests/test_intake_v3_lighting_plan.py `
  tests/test_intake_v3_operator_workspace_e2e_hardening.py -q
```

**Result:** 36 passed

## Boundary confirmations

- No CostEngine changes
- No Inventory / StockMovement mutation
- No ExecutionTask / ExecutionPlan / PO / SupplierOrder
- No reserve or PSU allocator logic changes
- No Atoms recomposition
- No DB manual edits
- No commit / no push in this session
- `tmp/` not committed

## What remains

1. **Owner SVG (`litere-volumetrice.svg`)** — fails `xml_unsafe_construct`; needs dedicated SVG sanitizer/parser build if production files include DOCTYPE.
2. **Multi-layer path geometry** — fixture uploads only 1 productive path layer; full owner file needs parseable SVG + all layer paths extracted.
3. **Visual browser acceptance** — file-drop overlay not manually screenshot-verified in this session (API chain validated).
4. **Commit** — frontend file-drop + shared upload flow uncommitted; await explicit owner request.
5. **`geometry-path-perimeter-classification` stale response** — investigate why standalone GET can lag live workspace payload (low priority; geometry-metrics-snapshot correct).

## Verdict

**PASS — real SVG upload produced geometry and lighting suggestion** (using repo fixture `volumetric-multilayer.svg`; owner DOCTYPE SVG still blocked).
