# BUILD — SVG Layer Detection & Filename State Fix

**Date:** 2026-06-07  
**Branch:** `master`  
**Base commits:** `37ba4ae`, `af6b811`, `5bc2b3c`  
**Implementation commit:** `e1f2914`  
**Browser smoke doc commit:** `13d2e4e`

## User-reported issue

After selecting an SVG in volumetric vector intake:

- Some dimensions appeared to update (fast-ask depth/finish local state).
- Displayed filename did not always update when selecting a second SVG.
- No SVG layer analysis — operator expected a message like “Am identificat N layere…”.

## Filename state root cause

`VectorIntakeFastAskPanel` initialized file metadata from `initialAnswers` only on mount. Parent `Product001IntakeSpecEditor` passes `initialAnswers={deriveFastAskFromSpec(spec)}` on every render. After save/refresh or when parent spec updated asynchronously, local file picks could be overwritten or the selected-file chip could drift from `answers.vectorFileName` because there was no guarded sync from parent `vector_file_selected_at`.

**Fix:** Track `localFilePickAtRef` so newer local picks win; sync file metadata from parent only when external `vector_file_selected_at` is newer or equal; clear file input after each pick; pass analysis through `onFileAttach` so parent `spec.vector_file_name` updates immediately (Vector Studio reads the same source).

## SVG parser scope

**Module:** `frontend/src/lib/svgVectorAnalysis.ts`

- FileReader text read only — no raw SVG stored in `product_spec_json`.
- DOMParser parse; script tags rejected/stripped.
- Extracts: width, height, viewBox, top-level groups, Inkscape layers (`inkscape:groupmode="layer"`, `inkscape:label`), `id`, `<title>`, element counts.
- Warnings: no layers, embedded raster, missing viewBox, unit hints.
- **Does not:** calculate perimeter/area/letter count, execute scripts, inject SVG into DOM, trust external refs.

## Layer role suggestion rules

**Module:** `frontend/src/lib/svgLayerRoleSuggestion.ts`

| Pattern in layer name | Suggested role |
|----------------------|----------------|
| litere, letters, volumetric | Litere volumetrice |
| fata, face, front | Față litere |
| cant, lateral, side | Cant / lateral |
| dibond, acm, backing, suport | Suport Dibond / ACM |
| cadru, frame, metal, teava | Cadru metalic |
| ghid, cote, reference | Ghidaj / cotă / referință |
| ignore, ascuns | De ignorat |
| otherwise | Necunoscut (operator must map) |

Suggestions shown as “Sugestie” — never auto-finalized.

## Persistence (`product_spec_json`)

Additive fields:

- `vector_svg_analyzed`, `vector_svg_width`, `vector_svg_height`, `vector_svg_viewbox`
- `vector_detected_layer_count`, `vector_detected_layers[]`
- `vector_layer_mapping_confirmed`, `vector_layer_analysis_warnings`
- Existing `vector_detected_layers_summary`, `svg_layer_mappings` updated on apply when roles map cleanly

Backend `ALLOWED_KEYS` extended in `backend/validators/intake_product_spec.py`.

## Tests / lint

| Suite | Result |
|-------|--------|
| Vitest (37 tests across 5 files) | **PASS** |
| ESLint (changed frontend files) | **PASS** |
| `test_intake_product_spec_validator.py` | Added — not executed (Python unavailable in agent shell) |

## Browser validation (Phase 10 — completed 2026-06-07)

**Environment:** Backend started with `APP_ENV=development` (avoids `release.json` staging safety block). Frontend `:3000` healthy.

**Intake:** `IR-MQ3C869E` (draft volumetric — not WI-SMOKE-P001).

| step | expected | actual | result |
|------|----------|--------|--------|
| Open volumetric intake | Workspace loads | IR-MQ3C869E spec tab | PASS |
| Select SVG A (`smoke_layers_a.svg`) | Filename A immediately | `smoke_layers_a.svg`, 2 layere | PASS |
| Select SVG B (`smoke_layers_b.svg`) | Filename B replaces A | `smoke_layers_b.svg`, 3 layere | PASS |
| Layer names shown | LITERE, DIBOND, CADRU | All visible with element counts | PASS |
| Safe suggestions | Only when names match | Sugestii for LITERE/DIBOND/CADRU | PASS |
| Manual role mapping | Litere / Dibond / Cadru | Comboboxes confirmed | PASS |
| Apply fast ask | Full editor remains | All sections + Vector Studio open | PASS |
| Save | Persists metadata | API: `vector_file_name=smoke_layers_b.svg`, `vector_svg_analyzed=true`, `layers=3` | PASS |
| Refresh | Filename + layers persist | UI shows 3 layere, roles, `smoke_layers_b.svg` | PASS |
| No fake geometry | No area/perimeter invented | `letter_face_area_m2` / `letter_perimeter_m` empty on IR-MQ3C869E | PASS |
| WI-SMOKE-P001 regression | Baseline values | 4800 / 600 / 60 / 2.88 / 18 / 9 | PASS |
| WI-SMOKE simulation | 844,41 EUR | **844,41 EUR** after Calculează preliminar | PASS |
| /quotes “Ofertă nouă” | Generic QuoteWizard | Wizard opened (client + template); cancelled | PASS |
| No quote/order created | Counts unchanged | intakes 15, quotes 7, orders 8 | PASS |

## Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 15 | 15 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

## Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created in tests
- [x] No Reference Catalogs started
- [x] No fake geometry calculated
- [x] Raw SVG not stored
- [x] Product001IntakeSpecEditor contract preserved
- [x] Manual / quick estimate / Vector Studio paths untouched
