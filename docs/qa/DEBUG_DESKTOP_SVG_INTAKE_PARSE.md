# DEBUG: Desktop SVG upload parse proof (TPL-VOLUMETRIC-LETTERS)

**Date:** 2026-06-04  
**Status:** Root cause identified + fixes applied (uncommitted)

## Proof summary (answers to primary questions)

| # | Question | Answer |
|---|----------|--------|
| 1 | File input receives `File`? | **Yes** — hidden `input[type=file]` wired via `handleFileInputChange` → `handleFilePick` |
| 2 | `FileReader.readAsText` called? | **Yes** — via `readSvgFileAsText` in `analyzeSvgVectorFile`; also `file.text()` cached in panel |
| 3 | First 200 chars of fixture SVG? | `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg"...` |
| 4 | Parser called with text? | **Yes** — `parseSvgVectorText(fileName, text)` after read |
| 5 | Parser return (fixture)? | `parse_ok: true`, **3 layers** (LITERE, DIBOND, CADRU), viewBox `0 0 300 120` |
| 6 | Parse failure UI? | **Was broken** — `applyFileMetadata` cleared `analysisError` after failed parse; **fixed** |
| 7 | Result in component state? | **Yes** — `svgAnalysis`, `detectedLayers`, parse status banner |
| 8 | Persisted to `product_spec_json`? | **On file pick** via `onFileAttach` → `mapSvgVectorAnalysisToProductSpec` + `persistSpec`; **was missing role heuristics on persist** — **fixed** |
| 9 | Why “Layer principal litere nemapat”? | **Two causes:** (a) operator typed filename only — no file read; (b) review warnings read **persisted spec** while local parse succeeded — stale warnings shown |

## Root causes

### A. Filename-only path (most common operator mistake)
Typing in “Nume fișier” without clicking **Selectează fișier vector** saves metadata only (`attached_unanalyzed`). No parser run. UI now shows explicit hint (`vector-filename-only-hint`).

### B. Stale review warnings
`reviewSummary.warnings` from `buildVectorStudioInfo(spec, …)` reflected saved `product_spec_json`, not live parse. Local parse could succeed while review still showed “Layer principal litere nemapat”. Fixed with `filterVectorReviewWarningsForLocalParse`.

### C. Persist without role heuristics
`onFileAttach` received raw parser output before `applySuggestedLayerRoles`, so `svg_layer_mappings` could omit letters layer for ambiguous names. Fixed: persist analysis with roles applied.

### D. Geometry skipped for all-unknown roles
`runGeometryParse` returned early if every layer `confirmed_role === unknown`. Fixed: fallback to `suggestPrimaryLettersLayer` for bbox estimates.

### E. Parse errors hidden
`applyFileMetadata` reset `analysisError` after `handleFilePick` set it. Fixed.

## Files changed

- `frontend/src/components/workos/VectorIntakeFastAskPanel.tsx`
- `frontend/src/lib/svgIntakeFlow.ts`
- `frontend/src/lib/svgIntakeFlow.test.ts`
- `frontend/src/components/workos/VectorIntakeFastAskPanel.desktopSvgParse.test.tsx` (new)

## How to upload now

1. Open intake → pathway **Din fișier vector**
2. Click **Selectează fișier vector** (do not only type filename)
3. Choose `.svg` from Desktop
4. Expect: parse status banner, layer count, layer list, letters layer suggestion
5. Click **Confirmă layer litere** then **Aplică și salvează** (or rely on autosave on pick/confirm)

## UI after successful SVG select

- Status analiză: Analizat cu succes / Analizat cu avertismente
- Fișier + viewBox + layer/element counts
- Mapare layere (3 rows for fixture)
- Layer principal litere — suggestion + dropdown + confirm
- Geometry suggestions (bbox mm) when units allow
- Stale “nemapat” hidden when local letters layer detected

## Tests run

- `npm run lint` — PASS
- `VectorIntakeFastAskPanel.desktopSvgParse.test.tsx` — 5 passed
- `svgIntakeFlow.test.ts` — 10 passed
- `VectorIntakeFastAskPanel.test.tsx` — 18 passed

## Corel / Illustrator limitations

- Flat SVG (paths only, no `<g>`) → parse_ok but **0 layers**; manual mapping required
- Layer names like “Layer 1” → roles `unknown` until operator selects
- DOCTYPE / external entities → rejected by sanitizer
- Area/perimeter still not auto-estimated (by design)
