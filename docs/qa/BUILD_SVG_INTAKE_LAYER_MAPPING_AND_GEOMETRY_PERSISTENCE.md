# BUILD: SVG Intake Upload + Layer Mapping + Geometry Persistence

**Date:** 2026-06-04  
**Build status:** **PASS**  
**Base commit:** `4682fb97d48349319160a2660cd91c7e6196de32` (form flow audit)  
**This build commit:** not committed (per user rule)  
**Pre-flight:** Working tree was clean @ `4682fb9` before implementation

## Summary

Runtime implementation for **TPL-VOLUMETRIC-LETTERS** vector intake: client-side SVG parse visibility, detected layers/groups, letters-layer suggestion + operator confirmation, honest geometry estimates, persistence into `product_spec_json`, autosave on Apply/confirm boundaries, and precise readiness repair messages.

## Failure point addressed

On `/intake/:id` with pathway **vector**, selecting an SVG previously felt dead: no clear parse status, vague “Layer principal litere nemapat” / “Nu s-au extras metrici geometrice automat”, Fast-Ask **Apply** was local-only until manual Save, and readiness did not guide repair.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/svgIntakeFlow.ts` | **New** — parse UI status, letters-layer heuristics, repair messages |
| `frontend/src/lib/svgIntakeFlow.test.ts` | **New** — unit tests for heuristics/repair |
| `frontend/src/components/workos/VectorIntakeFastAskPanel.tsx` | Parse status banner, layer rows + bbox, primary letters section, confirm button |
| `frontend/src/components/workos/VectorIntakeFastAskPanel.test.tsx` | Extended tests |
| `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` | Autosave on Apply + confirm letters layer; wires new panel props |
| `frontend/src/lib/mapSvgVectorAnalysisToSpec.ts` | Primary letters layer + mapping confirmed timestamp |
| `frontend/src/lib/intakeProductSpec.ts` | New optional spec fields |
| `frontend/src/lib/intakeVolumetricSpec.ts` | Normalizer passes through new vector mapping fields |
| `frontend/src/lib/svgVectorAnalysis.ts` | `data-name` attribute for layer labels |
| `frontend/src/lib/intakeReadinessStages.ts` | Vector pathway repair items in `specMissing` |
| `frontend/src/lib/volumetricIntakeFormPrep.ts` | Letters-layer mapping in final-quote missing |
| `frontend/src/lib/vectorStudioPreview.ts` | Suppress false “no geometry” warning when estimate exists |
| `backend/validators/intake_product_spec.py` | Allowlist new vector mapping fields |
| `frontend/e2e/fixtures/volumetric-multilayer.svg` | **New** — LITERE / DIBOND / CADRU fixture |

## Parser behavior

- SVG read **client-side** on file pick (`analyzeSvgVectorFile`, `parseSvgGeometryFromFile`).
- Parse status shown: Neselectat / Se analizează / Analizat cu succes / Analizat cu avertismente / Analiză eșuată.
- Layer detection: `<g id>`, `inkscape:label`, `data-name`, top-level fallback.
- **No raw SVG** stored in `product_spec_json`.
- Area/perimeter remain **unsupported** (`PERIMETER_AREA_UNSUPPORTED_MSG`); bbox/dimensions shown as estimates only.

## UI behavior

- Filename + viewBox + layer/element counts after selection.
- Per-layer: name, id, element count, bbox (when geometry parse succeeds), role suggestion + manual override.
- **Layer principal litere:** auto-suggest (high/medium/low + reason), dropdown override, **Confirmă layer litere** → persists.
- Apply button: **Aplică și salvează** (calls `persistSpec` in editor).

## Persistence shape (`product_spec_json`)

Existing + new fields (minimal):

- `vector_file_name`, `vector_svg_analyzed`, `vector_parse_status`, `vector_svg_viewbox`, `vector_svg_width`, `vector_svg_height`
- `vector_detected_layers`, `vector_detected_layers_summary`, `svg_layer_mappings`
- `vector_primary_letters_layer_id`, `vector_primary_letters_layer_name`
- `vector_letters_layer_suggestion_confidence` (`high` \| `medium` \| `low`)
- `vector_layer_mapping_confirmed`, `vector_layer_mapping_confirmed_at`
- Geometry estimate fields via existing `mapSvgGeometryToSpec` (`vector_geometry_analyzed`, `vector_suggested_*`, `vector_geometry_confidence`, warnings)

## Readiness / repair

`buildVectorIntakeRepairMissing` adds actionable items for vector pathway:

- Încarcă/selectează SVG
- Confirmă layerul principal pentru litere
- Verifică dimensiunile extrase / completează manual
- Aplică răspunsurile rapide vector (Aplică și salvează)
- Confirmă maparea layerelor SVG

Integrated into `intakeReadinessStages` and `volumetricIntakeFormPrep`.

## Tests run

| Command | Result |
|---------|--------|
| `npm run lint` | PASS |
| `vitest run svgIntakeFlow.test.ts VectorIntakeFastAskPanel.test.tsx intakeReadinessStages.test.ts` | 38 passed |
| `vitest run svgVectorAnalysis.test.ts svgGeometryParser.test.ts intakeVolumetricSpec.test.ts volumetricIntakeFormPrep.test.ts` | 36 passed |
| Backend pytest | Not run — `python`/`py` unavailable in shell |

## Acceptance checklist

- [x] Working tree clean before build
- [x] Selecting SVG visibly changes the page
- [x] SVG text parsed client-side
- [x] Detected layers/groups shown
- [x] Suggested letters layer shown
- [x] Operator can manually choose/confirm layer principal litere
- [x] Geometry estimates shown honestly (bbox/dims; no fake area/perimeter)
- [x] Parser warnings visible
- [x] Mapping/geometry persisted into `product_spec_json`
- [x] Fast-Ask Apply / SVG confirm saves when it looks saved
- [x] Readiness blockers more precise
- [x] No CostEngine/Pricing/Execution changes
- [x] QA doc created

## Remaining gaps

- No dedicated Playwright E2E for full intake SVG flow (fixture added for future use).
- Backend validator unit tests not executed in this environment.
- Re-open intake does not re-run local file parse (relies on saved spec fields + `rehydrateLayersFromSpec`).
- DXF/DWG still manual-review only (by design).

## Next substantial build recommendation

**Stage 2 from audit:** Quote tab / simulation live refresh — after spec save, auto-refresh simulate readiness and surface geometry-derived line items without requiring tab switch or duplicate Save.

## Audit doc

No material plan change; audit remains source of truth at `docs/audits/WORKOS_FORM_FLOW_AUDIT_AND_FLUID_PROPOSAL.md`.
