# BUILD — INTAKE_V3_VECTOR_AND_LETTER_MODEL

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD at build:** `d78bc4d`  
**Verdict:** PASS

---

## Purpose

Implement testable foundation for Intake V3 vector & letter model:

```text
RawSvgAnalysis → Review → ConfirmedProductionModel → ReadinessReport
```

Separate system detection from operator-confirmed production truth. HUB 18/27/9 as mandatory test case.

---

## Files created

| Path |
|------|
| `backend/services/intake_v3_vector_model_service.py` |
| `backend/tests/test_intake_v3_vector_and_letter_model.py` |
| `docs/qa/BUILD_INTAKE_V3_VECTOR_AND_LETTER_MODEL.md` |

## Files modified

| Path |
|------|
| `backend/data_models/intake_v3_contracts.py` |
| `backend/schemas/intake_v3.py` |
| `backend/services/intake_v3_readiness_service.py` |
| `frontend/src/lib/intakeV3/contracts.ts` |
| `docs/intake-v3/00_STATUS.md` |
| `docs/intake-v3/06_BUILD_ROADMAP.md` |
| `docs/intake-v3/07_DECISIONS_LOG.md` |
| `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/02_VECTOR_AND_LETTER_MODEL.md` |

---

## Contracts extended

| Contract | Changes |
|----------|---------|
| `RawSvgObject` | new — detected raw vector object |
| `RawSvgAnalysis` | + `raw_objects[]` |
| `LetterGroup` | new |
| `LetterItem` | + `outer_contour_ids`, `inner_hole_ids`, `group_id`, `sequence_index` |
| `CutContourItem` | + `source_object_id`, `sequence_index` |
| `ConfirmedProductionModel` | + `source_raw_analysis_id`, `operator_notes` |
| `VectorModelValidationResult` | new |
| Blocker codes | +5 vector blockers |
| Warning codes | +6 vector warnings |

---

## Service

`intake_v3_vector_model_service.py`:

- `summarize_raw_svg_analysis()`
- `build_confirmed_production_model()`
- `validate_confirmed_production_model()`

Pure/in-memory — no DB, no SVG parser.

---

## Readiness changes

`evaluate_intake_v3_readiness()` now:

- delegates vector validation when model is confirmed;
- maps vector blockers (except duplicate `UNCONFIRMED`) to readiness blockers;
- maps vector warnings including `RAW_CONFIRMED_LETTER_COUNT_MISMATCH`;
- preserves existing finish/dimension blockers.

---

## Frontend

`contracts.ts` — types mirrored + helpers:

- `isConfirmedProductionModelReady()`
- `summarizeLetterContourCounts()`
- `VECTOR_MODEL_WARNING_CODES`

No React, no routes, no UI.

---

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_architecture_contracts.py -q
# 26 passed

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
# 22 passed
```

---

## PASS criteria met

- Raw vs confirmed separated ✅
- HUB 18/27/9 passes ✅
- Holes not letters ✅
- Raw mismatch = warning only when confirmed coherent ✅
- Unconfirmed blocks readiness ✅
- Cut count mismatch blocks ✅
- Inner hole without parent blocks ✅
- Ignored objects excluded from cut count ✅
- No UI / DB / execution / pricing changes ✅

---

## Not implemented

- Full SVG parser
- Visual editor / Assisted Interpretation UI
- Nesting
- CNC file generation
- PricingInput adapter
- ProductionHandoff adapter runtime
- DB persistence

---

## Boundary

No commit in agent phase. No push.

---

## Next build

`INTAKE_V3_FINISH_AND_MATERIAL_WORKFLOW` per [06_BUILD_ROADMAP.md](../intake-v3/06_BUILD_ROADMAP.md).
