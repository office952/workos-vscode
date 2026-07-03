# BUILD — INTAKE_V3_SVG_UPLOAD_AND_RAW_ANALYSIS_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `f776eaf`  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Add real SVG upload to Intake V3 **draft workspaces** with safe validation and **raw SVG analysis** persisted in workspace payload. Preview regenerates after upload. Operator sees objects/paths/colors/warnings — **no automatic Confirmed Production Model**.

### In scope

- `POST /api/v1/intake-v3/workspaces/{workspace_id}/svg` (multipart)
- `intake_v3_svg_analysis_service.py` — stdlib `xml.etree` parse
- Payload fields: `vector_asset`, `raw_svg_analysis`, `raw_analysis_status`
- UI: `IntakeV3SvgUploadPanel`, `IntakeV3RawSvgAnalysisPanel`
- Backend + frontend tests
- Docs update

### Out of scope (boundary)

- Quote / order / execution plan / inventory
- CostEngine, pricing formulas
- Employee Mobile, Intake V2
- Confirmed Production Model auto-confirmation
- Disk storage for SVG (payload JSON only)
- DB migration

---

## Upload / API pattern audit

| Aspect | Choice | Avoided |
|--------|--------|---------|
| Backend multipart | FastAPI `UploadFile` + `File(...)` — same as Work Intake V2 | New storage layer |
| Size limit | `_MAX_SVG_BYTES` = **500_000** from `svg_metrics_service` | Ad-hoc 5 MB without convention |
| Filename | `sanitize_upload_filename()` from `work_intake_svg_spec_mapper` | Raw client filenames |
| Persistence | Workspace `payload_json` only | `storage/intake_svg_uploads/` disk writes |
| Frontend | `FormData`, no manual `Content-Type` | Base64 JSON embed |
| MIME | Reject if content-type set and not `svg` / `octet-stream` | Strict magic-byte sniffing |

---

## Endpoint

```http
POST /api/v1/intake-v3/workspaces/{workspace_id}/svg
Content-Type: multipart/form-data
file: <SVG>
```

**Response:** `IntakeV3SvgUploadResponse` — `workspace`, `preview`, `raw_svg_analysis`, `warnings`.

**Errors:**

| Case | Status | Code |
|------|--------|------|
| Workspace not found | 404 | — |
| Archived workspace | 400 | `workspace_archived` |
| Non-`.svg` filename | 422 | `invalid_svg` |
| Empty / non-UTF-8 / not `<svg` | 422 | `invalid_svg` |
| Too large | 422 | `svg_too_large` |
| `<script>` | 422 | `svg_scripts_forbidden` |
| External `href`/`xlink:href` http(s) | 422 | `svg_external_references` |
| Invalid XML | 422 | `invalid_svg_xml` |

**External refs:** reject only attribute-level `href`/`xlink:href` pointing to `http(s)://`. `xmlns="http://..."` is allowed (SVG namespace).

---

## Parser / validator safety

- **No** script execution, network, external resource loading
- **No** third-party SVG parser with JS
- Pre-parse reject: `<script>`, external hrefs
- Post-parse: `xml.etree.ElementTree.fromstring`
- Raw facts only — no geometry confirmation

---

## Raw analysis fields (`RawSvgAnalysis`)

| Field | Notes |
|-------|-------|
| `file_name`, `file_size_bytes` | From upload |
| `svg_width`, `svg_height`, `view_box` | Root `<svg>` attrs |
| `path_count`, `open_path_count`, `closed_contour_count` | `<path>` + `Z/z` in `d` |
| `polygon_count`, `rect_count`, `raw_object_count` | Shape counts |
| `estimated_inner_hole_count` | Heuristic from group ids / closed paths |
| `detected_groups` | `<g id="...">` |
| `detected_color_count` | fill / stroke / inline style |
| `raw_objects` | Up to 50 path summaries |
| `warnings` | String codes (see below) |
| `confidence` | 0.1–1.0 derived from warnings |

### Warning codes (raw analysis)

`MISSING_VIEW_BOX`, `MISSING_WIDTH_HEIGHT`, `TEXT_NOT_CONVERTED_TO_PATHS`, `RASTER_IMAGE_EMBEDDED`, `TOO_MANY_PATHS`, `UNKNOWN_UNITS`

---

## RawSvgAnalysis ≠ ConfirmedProductionModel

- Upload sets `raw_analysis_status = "analyzed"`
- **`confirmed_production_model` is never written** by upload path
- Readiness keeps `UNCONFIRMED_LETTER_MODEL` until operator confirms in a future build
- UI boundary copy: *"Operator confirmation is still required before this becomes a production model."*

---

## Files changed

### Created

- `backend/services/intake_v3_svg_analysis_service.py`
- `backend/tests/test_intake_v3_svg_upload_analysis.py`
- `frontend/src/components/workos/intake-v3/IntakeV3SvgUploadPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3RawSvgAnalysisPanel.tsx`
- `docs/qa/BUILD_INTAKE_V3_SVG_UPLOAD_AND_RAW_ANALYSIS_FOUNDATION.md`

### Modified

- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/lib/intakeV3/contracts.ts`
- `frontend/src/lib/intakeV3/flowState.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3CommandBar.tsx`
- `frontend/src/pages/IntakeV3App.tsx`
- `frontend/src/pages/IntakeV3App.test.tsx`
- `frontend/src/lib/intakeV3/flowState.test.ts`
- `docs/intake-v3/00_STATUS.md`, `02`, `04`, `06`, `07`

---

## Tests

### Backend targeted

```text
31 passed
tests/test_intake_v3_svg_upload_analysis.py (9)
tests/test_intake_v3_workspace_field_editor.py
tests/test_intake_v3_workspace_persistence.py
```

### Backend regression

```text
53 passed
tests/test_intake_v3_preview_endpoint.py
tests/test_intake_v3_workspace_preview_service.py
tests/test_intake_v3_vector_and_letter_model.py
tests/test_intake_v3_finish_and_material_workflow.py
tests/test_volumetric_execution_task_order.py
```

### Frontend targeted

```text
37 passed
src/pages/IntakeV3App.test.tsx (31)
src/lib/intakeV3/flowState.test.ts (6)
```

---

## No side effects (verified)

- No quote / order / execution plan IDs on workspace response
- `inventory_mutation_allowed` stays false
- `production_handoff.preview_only` stays true
- Real action buttons remain disabled in UI

---

## Pending next build

**`INTAKE_V3_CONFIRMED_PRODUCTION_MODEL_REVIEW`** — operator review/confirm letter model from raw analysis (separate prompt; not in this build).

---

## Recommended commit message

```text
feat(intake-v3): add SVG upload and raw analysis foundation
```
