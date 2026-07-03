# BUILD — INTAKE_V3_CONFIRMED_PRODUCTION_MODEL_REVIEW_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `e4b9766`  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Operator explicitly confirms production model counts from raw SVG analysis. No auto-confirmation from raw analysis. HUB reference: **18 letters / 27 cut contours / 9 inner holes** (holes are not separate letters).

### In scope

- `GET .../production-model/review-candidate`
- `POST .../production-model/confirm`
- `intake_v3_production_model_review_service.py`
- `IntakeV3ProductionModelReviewPanel` UI
- Payload: `confirmed_production_model`, `production_model_status`, timestamps
- Tests + docs

### Out of scope

- Finish per letter/group
- Quote / order / execution / inventory / CostEngine
- Intake V2 / Employee Mobile
- DB migration
- Full geometric letter/contour mapping from SVG paths

---

## Payload audit (post-SVG upload)

| Field | Location | Notes |
|-------|----------|-------|
| `vector_asset` | workspace payload | file hash, viewBox, upload_status |
| `raw_svg_analysis` | workspace payload | paths, colors, warnings — **not production truth** |
| `raw_analysis_status` | workspace payload | `analyzed` after upload |
| `confirmed_production_model` | workspace payload | **only set via confirm endpoint** |
| `production_model_status` | workspace payload | `confirmed` after operator confirm |
| Blocker without confirm | readiness | `UNCONFIRMED_LETTER_MODEL` |

Raw analysis is **never deleted** on confirm. Confirmed model is a separate object with operator-entered counts and synthetic placeholder letter/contour scaffolding for existing vector validation.

---

## Endpoints

```http
GET  /api/v1/intake-v3/workspaces/{id}/production-model/review-candidate
POST /api/v1/intake-v3/workspaces/{id}/production-model/confirm
```

### Review candidate (read-only)

Built from `raw_svg_analysis`:
- `suggested_cut_contour_count` ← `closed_contour_count`
- `suggested_inner_hole_count` ← `estimated_inner_hole_count`
- `suggested_letter_count` ← null (no auto letter detection in this build)
- `confirmed: false`

Returns 400 if `raw_svg_analysis` missing.

### Confirm (write)

Request:
```json
{
  "letter_count": 18,
  "cut_contour_count": 27,
  "inner_hole_count": 9,
  "ignored_object_ids": [],
  "operator_notes": "...",
  "confirmed": true
}
```

Validation:
- `letter_count > 0`
- `cut_contour_count >= letter_count`
- `inner_hole_count >= 0`
- `confirmed === true`
- raw analysis must exist
- archived workspace → 400

Warnings (non-blocking):
- `COUNT_SUM_MISMATCH` when `letter_count + inner_hole_count != cut_contour_count`
- `CONFIRM_WITHOUT_OPERATOR_NOTES` when mismatch without notes

---

## Raw vs confirmed boundary

| | Raw SVG analysis | Confirmed production model |
|--|------------------|----------------------------|
| Source | automatic from upload | operator POST confirm |
| Purpose | diagnostic | production truth (counts) |
| `confirmation_status` | n/a | `confirmed` only after explicit action |
| Removed on confirm? | **No** | N/A |

---

## HUB example (18 / 27 / 9)

Valid: 18 letters + 9 inner holes = 27 cut contours. Holes assigned to first 9 letters in placeholder geometry; not counted as letters.

---

## Files changed

### Created

- `backend/services/intake_v3_production_model_review_service.py`
- `backend/tests/test_intake_v3_production_model_review.py`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionModelReviewPanel.tsx`
- `docs/qa/BUILD_INTAKE_V3_CONFIRMED_PRODUCTION_MODEL_REVIEW_FOUNDATION.md`

### Modified

- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `frontend/src/lib/intakeV3/api.ts`, `contracts.ts`, `flowState.ts`, `blockerMessages.ts`
- `frontend/src/pages/IntakeV3App.tsx`, `IntakeV3App.test.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3CommandBar.tsx`
- `frontend/src/lib/intakeV3/flowState.test.ts`
- `docs/intake-v3/00_STATUS.md`, `02`, `04`, `06`, `07`

---

## Tests

| Suite | Result |
|-------|--------|
| Backend targeted (40) | **40 passed** |
| Backend regression (53) | **53 passed** |
| Frontend (45) | **45 passed** |

---

## No side effects

Verified: no quote/order/execution IDs; `preview_only` and `inventory_mutation_allowed` remain safe.

---

## Pending next build

**Finish per letter/group assignment** (separate prompt).

---

## Recommended commit message

```text
feat(intake-v3): add confirmed production model review foundation
```
