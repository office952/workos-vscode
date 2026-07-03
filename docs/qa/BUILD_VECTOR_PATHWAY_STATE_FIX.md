# BUILD — Vector Pathway State Fix

**Date:** 2026-06-07  
**Branch:** `master`  
**Base commits:** `af6b811`, `37ba4ae`, `e1f2914`, `e5bd6d8`

## User-reported bug

When the operator selects **Din fișier vector** and picks an SVG, the UI jumped to **Specificații manuale** — the vector fast-ask / layer detection flow disappeared as if the build had not run.

## Reproduction (before fix)

1. Open volumetric intake (e.g. `IR-MQ3C869E`).
2. Select **Din fișier vector**.
3. Pick an SVG file.
4. **Observed:** pathway tab switched to manual; `intake_input_pathway` often missing from save payload; reload could open manual despite vector file metadata.

## Root cause

| source | issue |
|--------|--------|
| `mapVectorFilePickToProductSpec` | Did not set `intake_input_pathway: "vector"` on file attach |
| `mapSvgVectorAnalysisToProductSpec` | Did not preserve vector pathway after analysis merge |
| `handleVectorFileAttach` | Updated `spec` only — local `pathway` UI state not forced to vector |
| `derivePathwayFromSpec` | Stored `manual` took precedence over `vector_file_name` (stale manual default after vector flow) |
| `Product001IntakeSpecEditor` `useEffect` | Parent `initialSpec` sync could reset pathway before save when local vector picks were newer |

## Canonical pathway values

Persisted on `product_spec_json.intake_input_pathway`:

| value | UI label |
|-------|----------|
| `vector` | Din fișier vector |
| `manual` | Specificații manuale |
| `quick_estimate` | Estimare rapidă |

Constants: `INTAKE_INPUT_PATHWAY_VECTOR`, `INTAKE_INPUT_PATHWAY_MANUAL`, `INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE` in `frontend/src/lib/volumetricIntakePathway.ts`.

Helper: `preservePathwayForVectorMetadata()` — sets vector pathway on vector metadata merges unless quick estimate is active.

## Fix summary

1. **Mapping:** `mapVectorFilePickToProductSpec` and `mapSvgVectorAnalysisToProductSpec` call `preservePathwayForVectorMetadata`.
2. **Editor:** `handleVectorFileAttach` / `handleVectorFastAskApply` set `pathway` UI + refs; `useEffect` merge keeps local vector file picks when parent spec is stale.
3. **Derive:** `derivePathwayFromSpec` prefers vector file hints over stale stored `manual`.
4. **Tests:** pathway preservation across file pick, apply, save, reload scenarios.

No pricing, CostEngine, quote, or geometry changes.

## Tests / lint

| Suite | Result |
|-------|--------|
| `volumetricIntakePathway.test.ts` | **PASS** (9) |
| `vectorFileSelection.test.ts` | **PASS** (7) |
| `Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | **PASS** (11) |
| `volumetricVectorFastAskMapping.test.ts` | **PASS** (11) |
| `intakeVolumetricSpec.test.ts` | **PASS** (13) |
| ESLint (changed frontend files) | **PASS** |

## Browser validation (2026-06-07)

**Environment:** `APP_ENV=development`, backend `:8000`, frontend `:3000`.

**Intake:** `IR-MQ3C869E`

| step | expected | actual | result |
|------|----------|--------|--------|
| Select Din fișier vector | Vector panel | Fast ask visible | PASS |
| Pick SVG A | Stay vector, filename A | `pathway_smoke_a.svg`, 2 layere, vector tab active | PASS |
| Pick SVG B | Stay vector, filename B | `pathway_smoke_b.svg`, 3 layere, vector tab active | PASS |
| Apply + Save + Refresh | Vector pathway + layers persist | `intake_input_pathway=vector`, filename/layers in DB + UI | PASS |
| No fake geometry | No area/perimeter invented | `letter_face_area_m2` / `letter_perimeter_m` null | PASS |
| Manual pathway switch | Manual sections, no fast ask | Works | PASS |
| Quick estimate switch | Sections 1–2 only | Works | PASS |
| WI-SMOKE-P001 | 4800/600/60/2.88/18/9, 844,41 EUR | Confirmed live | PASS |

## Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 16 | 16 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

## Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] No fake geometry calculated
- [x] SVG layer detection preserved
- [x] Manual flow preserved
- [x] Quick estimate flow preserved
- [x] Vector Studio preserved
- [x] WI-SMOKE-P001 baseline preserved (844,41 EUR)
