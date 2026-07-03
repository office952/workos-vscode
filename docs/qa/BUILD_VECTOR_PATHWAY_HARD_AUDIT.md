# BUILD: Vector Pathway Hard Audit

**Date:** 2026-06-07  
**Branch:** `master`  
**HEAD (baseline):** `62a0bf7`  
**Fix status:** local working tree (uncommitted at audit close)

---

## 1. Exact tested intake/code

| Intake | URL | Workspace | Pathway UI | Notes |
|--------|-----|-----------|------------|-------|
| **IR-MQ3C869E** | `http://127.0.0.1:3000/intake/IR-MQ3C869E` | volumetric modular (`litere_volumetrice`) | Yes — vector / manual / quick_estimate | Primary SVG bug reproduction |
| **IR-MQ3E7K2V** | `http://127.0.0.1:3000/intake/IR-MQ3E7K2V` | **generic unresolved** (`product_family` empty) | **No** | User screenshot intake — SVG pathway **not testable** until “Alege tip lucrare” → Litere volumetrice |
| **WI-SMOKE-P001** | `http://127.0.0.1:3000/intake/WI-SMOKE-P001` | volumetric (smoke baseline) | Yes | Cost baseline only — no SVG pick cycle |

**Test SVG A:** `C:\Users\offic\Desktop\lleexxaa.svg` (also `backend/validation_input/lleexxaa.svg`)  
**Test SVG B:** `backend/validation_input/TPL-VOLUMETRIC-LETTERS_vetro_litere.svg` (served as `/vetro_litere.svg` for browser fetch)

---

## 2. Reproduction table — before fix (`HEAD` `62a0bf7`, no local fix)

Observed on volumetric intake when UI opened on **derived vector** (vector file hints present, `intake_input_pathway` sometimes stale `manual`) and parent `initialSpec` refetched during/after SVG pick:

| moment | expected pathway | actual visual tab | spec.intake_input_pathway (API) | filename | layers | issue |
|--------|------------------|-------------------|----------------------------------|----------|--------|-------|
| Load (stale manual + vector file) | vector (derived) | **vector** (derived) | `manual` or `vector` | prior file | prior | UI derived from file hints |
| Click “Din fișier vector” | vector | vector | — | — | — | OK after explicit click |
| After SVG pick (no explicit click first) | vector | **manual** (intermittent) | `manual` (stale) | updated | detected | **BUG — tab switches to Specificații manuale** |
| After Apply | vector | manual (if already switched) | — | — | — | Fast-ask panel hidden |
| After Save + Refresh | vector | manual (persisted wrong tab) | `manual` or mixed | saved | saved | Parent sync won race |

**Root mechanism:** `localPathwayChoiceRef` was `null` until explicit card click; `initialSpec` sync called `setPathway(derivePathwayFromSpec(synced))` and could downgrade to `manual` while operator was in vector fast-ask flow.

**IR-MQ3E7K2V:** No pathway selector — operator sees “Alege tip lucrare”. This is routing, not the vector-tab bug.

---

## 3. Pathway writer audit

| file | function/component | writes pathway? | can overwrite vector? | evidence | fix needed |
|------|-------------------|-----------------|-------------------------|----------|------------|
| `Product001IntakeSpecEditor.tsx` | `handlePathwayChange` | yes | only on user click | sets `localPathwayChoiceRef` | — |
| `Product001IntakeSpecEditor.tsx` | `handleVectorFileAttach` | yes → vector | no | `preservePathwayForVectorMetadata` | — |
| `Product001IntakeSpecEditor.tsx` | `handleVectorFastAskApply` | yes → vector | no | `mapVectorFastAskToProductSpec` | — |
| `Product001IntakeSpecEditor.tsx` | `initialSpec` sync `useEffect` | yes via `setPathway` | **yes** when ref null | L318–323 `derivePathwayFromSpec(synced)` | **FIXED** |
| `Product001IntakeSpecEditor.tsx` | `handleSave` | via payload | clears refs post-save | depends on `spec` state | hardened sync |
| `volumetricIntakePathway.ts` | `derivePathwayFromSpec` | infer only | returns manual if no hints | used by parent sync | seed ref |
| `volumetricIntakePathway.ts` | `preservePathwayForVectorMetadata` | yes → vector | no | used by file mappers | — |
| `vectorFileSelection.ts` | `mapVectorFilePickToProductSpec` | yes | no | preserves vector | — |
| `mapSvgVectorAnalysisToSpec.ts` | `mapSvgVectorAnalysisToProductSpec` | yes | was missing on parse-fail | now `preservePathwayForVectorMetadata` | **FIXED** |
| `volumetricVectorFastAskMapping.ts` | `mapVectorFastAskToProductSpec` | yes → vector | no | explicit `vector` | — |
| `intakeVolumetricSpec.ts` | `normalizeVolumetricIntakeSpecForSave` | pass-through | drops if unset | preserves when canonical | — |
| `backend/validators/intake_product_spec.py` | validator | pass-through | no | enum filter | — |
| `VectorIntakeFastAskPanel.tsx` | `applyFileMetadata` | no | stale layers on bad parse | clears layers on fail | **FIXED** |

### Answers to specific questions

1. **Writers:** 6 frontend write sites + backend validator pass-through.  
2. **After SVG select:** `handleVectorFileAttach` → `mapVectorFilePickToProductSpec` / `mapSvgVectorAnalysisToProductSpec`.  
3. **After analysis:** same chain; parse-fail now preserves vector.  
4. **After Apply:** `mapVectorFastAskToProductSpec`.  
5. **After Save/refetch:** API stores payload; parent `initialSpec` sync — **was the race surface**.  
6. **UI id mismatch:** No.  
7. **Default manual after file:** Parent sync with `localPathwayChoiceRef === null`.  
8. **Derived from section visibility:** No.  
9. **Parent initialSpec overwrite:** **Yes — root cause.**  
10. **Backend dropping pathway:** No.  
11. **Stale manual stronger than vector file:** `derivePathwayFromSpec` prefers vector hints, but sync ran before ref seeded.  
12. **Race file pick vs analysis:** Yes — concurrent parent refresh during async parse.

---

## 4. Data audit — IR-MQ3C869E

| field | before session (API) | after SVG A (`lleexxaa.svg`) | after SVG B (`vetro_litere.svg`) | after Apply | after Save | after Refresh |
|-------|----------------------|------------------------------|----------------------------------|-------------|------------|---------------|
| `intake_input_pathway` | `vector` | `vector` (local) | `vector` (local) | `vector` | **`vector`** | **`vector`** |
| `vector_file_name` | `lleexxaa.svg` | `lleexxaa.svg` | `vetro_litere.svg` | `vetro_litere.svg` | **`vetro_litere.svg`** | **`vetro_litere.svg`** |
| `vector_svg_analyzed` | `true` | `true` | `true` | `true` | `true` | `true` |
| `vector_detected_layer_count` | `3` | `2` (re-parse) | `1` | `1` | **`1`** | **`1`** |
| `vector_file_selected_at` | prior timestamp | updated on pick | updated on pick | — | **`2026-06-07T08:43:45.748Z`** | persisted |

No fake geometry written. No quote/order created.

---

## 5. Root cause (one sentence)

**When the UI opened on a derived vector pathway without seeding `localPathwayChoiceRef`, a parent `initialSpec` refetch during or after SVG selection re-ran `setPathway(derivePathwayFromSpec(synced))` with `localPathwayChoiceRef === null`, downgrading the visible tab to Specificații manuale even though the operator was in the vector fast-ask flow.**

---

## 6. Fix summary

1. **`seedLocalPathwayChoice()`** — seed `localPathwayChoiceRef` when derived pathway is `vector` on mount.  
2. **`localVectorFileAtRef`** — seed from `initialSpec.vector_file_selected_at`.  
3. **`initialSpec` sync** — if local pathway lock is `vector`, force `intake_input_pathway: vector` even when `keepLocalVector` is false.  
4. **`mapSvgVectorAnalysisToSpec`** — preserve vector pathway on parse failure.  
5. **`VectorIntakeFastAskPanel`** — clear stale layer UI when new file parse fails.

No pricing, CostEngine, routing contract, or quote/order changes.

---

## 7. Files changed (uncommitted)

| File | Change |
|------|--------|
| `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` | Seed pathway ref; hardened parent sync |
| `frontend/src/components/workos/Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | Regression tests for stale parent sync |
| `frontend/src/components/workos/VectorIntakeFastAskPanel.tsx` | Clear stale layers on failed parse |
| `frontend/src/lib/mapSvgVectorAnalysisToSpec.ts` | Preserve vector on parse-fail |
| `docs/qa/BUILD_VECTOR_PATHWAY_HARD_AUDIT.md` | This audit |

---

## 8. Tests / lint

| Check | Result |
|-------|--------|
| `volumetricIntakePathway.test.ts` | 9 passed |
| `vectorFileSelection.test.ts` | 7 passed |
| `Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | 14 passed |
| **Total** | **30 passed** |
| ESLint (changed files) | 0 errors, 1 pre-existing warning (`useEffect` deps in `VectorIntakeFastAskPanel`) |
| WI-SMOKE simulate-cost API | **844.41 EUR**, `status=simulated`, `persisted=false` |

---

## 9. Browser validation after fix — IR-MQ3C869E

Full cycle executed live on `http://127.0.0.1:3000/intake/IR-MQ3C869E` with fix code running in Vite dev server.

| step | visual tab | spec pathway (API when saved) | filename | layer count | pass/fail |
|------|------------|-------------------------------|----------|-------------|-----------|
| Load | vector | vector | lleexxaa.svg | 3 | PASS |
| Click vector | vector | — | lleexxaa.svg | 3 | PASS |
| SVG A (`lleexxaa.svg`) | **vector** | — | lleexxaa.svg | 2 | PASS |
| SVG B (`vetro_litere.svg`) | **vector** | — | vetro_litere.svg | 1 | PASS |
| Apply | **vector** | — | vetro_litere.svg | 1 | PASS |
| Save | **vector** | **vector** | vetro_litere.svg | 1 | PASS |
| Refresh | **vector** | **vector** | vetro_litere.svg | 1 | PASS |

Screenshot after save: `vector-pathway-save-vetro_litere.png` (browser capture) — vector pathway active, `vetro_litere.svg` attached, fast-ask panel visible.

Manual and quick_estimate pathways: covered by existing unit tests (unchanged).  
`/quotes` → Ofertă nouă → generic QuoteWizard: not re-tested this session (no routing changes).

---

## 10. Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| intakes | 19 | 19 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

---

## 11. WI-SMOKE-P001 baseline

`POST /api/v1/product-system/simulate-cost` with dossier `BASE_QUOTE_INPUT` (4800×600×60, 2.88 m², 18 m perimeter, 9 letters):

**844.41 EUR** — unchanged.

---

## 12. Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] No fake geometry calculated
- [x] SVG layer detection preserved
- [x] Manual flow preserved (tests)
- [x] Quick estimate flow preserved (tests)
- [x] Vector Studio preserved
- [x] WI-SMOKE-P001 baseline preserved (844.41 EUR)

---

## 13. Commit hash

**None** — fix and audit doc are in working tree, not committed at audit close.

---

## 14. Final git status

```
 M frontend/src/components/workos/Product001IntakeSpecEditor.tsx
 M frontend/src/components/workos/Product001IntakeSpecEditor.vectorFastAsk.test.tsx
 M frontend/src/components/workos/VectorIntakeFastAskPanel.tsx
 M frontend/src/lib/mapSvgVectorAnalysisToSpec.ts
?? docs/qa/BUILD_VECTOR_PATHWAY_HARD_AUDIT.md
```

---

## 15. PASS / FAIL

**PASS** — on volumetric modular intake `IR-MQ3C869E`, selecting SVG A (`lleexxaa.svg`) and SVG B (`vetro_litere.svg`) does **not** switch away from **Din fișier vector** through pick → apply → save → refresh (live browser evidence above).

**Not applicable / expected:** `IR-MQ3E7K2V` (generic unresolved) has no vector pathway UI until work type is chosen — this is correct routing, not a regression of the vector-tab bug.
