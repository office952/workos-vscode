# BUILD — Work Intake V2 Routing and TPL Input Completion

**Date:** 2026-06-09  
**Branch:** `fix/work-intake-v2-routing-and-tpl-inputs`  
**Base:** `feature/tpl-volumetric-quote-flow-readiness` @ `bc0ef3a`

---

## Owner issues addressed

| # | Issue | Fix |
|---|-------|-----|
| 1 | Template area (`aria șablonului`) not auto-calculating | `computeMountingTemplateAreaM2()` from `width_mm × height_mm`; auto-display + persist in V2 production stage |
| 2 | Missing Forex 10 mm back chamfer checkbox | `work-intake-v2-forex-back-chamfer` in `V2ProductionStage`; persists `back_bevel_enabled` / `backing_chamfer` |
| 3 | `/intake/:id` still shows old form | `IntakeLegacyRoute` redirects volumetric intakes → `/intake-v2/:id`; UI links updated |
| 4 | WI “Creează Ofertă Draft” dead click / error | `createDraftQuoteFromIntake` handles 409 duplicate → opens existing quote; controlled inline error |

**Decision: PASS**

---

## Root cause

| Area | Cause |
|------|-------|
| Route | `/intake/:id` routed directly to `IntakeDetail` (legacy Product001 workspace) for volumetric intakes |
| Draft button | Backend 409 on duplicate draft returned `null` with only `alert()`; no navigation to existing quote |
| Template area | V2 used manual number input; QuoteWizard had suggest helper but intake stage did not |
| Chamfer | Field existed in `product_spec_json` / legacy editor only; not wired in WorkIntake V2 production stage |

---

## Files changed

- `frontend/src/pages/IntakeLegacyRoute.tsx` (new)
- `frontend/src/pages/IntakeLegacyRoute.test.tsx` (new)
- `frontend/src/App.tsx`
- `frontend/src/lib/mountingTemplateArea.ts` (new)
- `frontend/src/lib/mountingTemplateArea.test.ts` (new)
- `frontend/src/lib/dataStore.ts`
- `frontend/src/pages/WorkIntake.tsx`
- `frontend/src/pages/WorkIntake.draftQuote.test.tsx` (new)
- `frontend/src/components/workos/workIntakeV2/stages/V2ProductionStage.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2OperationalHeader.tsx`
- `frontend/src/pages/WorkIntakeV2.tsx`
- `frontend/src/pages/ClientWorkspace.tsx`
- `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx`

---

## Validation

| Gate | Result |
|------|--------|
| Backend `test_quote_price_intake_linkage` + `test_volumetric_execution_dispatch` | 6/6 PASS |
| Typecheck | PASS |
| Lint | PASS |
| Build | PASS |
| Vitest (focused) | 52/52 PASS |
| Playwright `work-intake-v2-to-quote-finish-display.spec.ts` | PASS |

---

## Browser smoke (local :3000 / :8000)

| Route | Result |
|-------|--------|
| `/intake` | PASS — list loads |
| `/intake/IR-MQ51B998` | PASS — redirects to V2 (no legacy form) |
| `/intake-v2/IR-MQ51B998` | PASS — WorkIntake V2 flow |
| `/quotes` | PASS |
| `/inventory/pricing` | PASS |
| `/product-system` | PASS — TPL-VOLUMETRIC-LETTERS active |

---

## SVG upload button root-cause and stabilization

### Binary visible-input test (Phase 3)

| Step | Result |
|------|--------|
| Hidden `sr-only` input in DOM | PASS |
| `onChange` → `handleFilePick` → `analyzeSvgVectorFile` | PASS (Vitest + CDP on `:3000`) |
| UI layers / parse status after selection | PASS |
| Autosave path (`onVectorUploadStart` / `scheduleAutoSave`) | PASS (Vitest autosave cases) |

**Conclusion:** Handler/parsing chain is sound. The regression was in the browse trigger layer and a failed two-step UI attempt (visible native input + separate „Încarcă fișierul” submit), not in SVG analysis.

### Root cause

1. **Committed browse path** used `className="hidden"` (`display:none`) on the file input. Programmatic `input.click()` from a custom button is unreliable with fully hidden inputs in some Windows browser contexts.
2. **Failed interim fix** replaced the single-click flow with a two-step pick-then-upload form (`work-intake-v2-upload-button`, staging refs, window-focus sync). Users clicked „Alege SVG de pe calculator” but the running UI no longer exposed that control; drag & drop still worked because it bypassed the broken browse layer.
3. **Stale spec updates** in the old `handleFilePick` closed over `spec` instead of functional `onSpecChange`, risking lost vector metadata during concurrent autosave refresh.

### Final implementation (`V2SvgStage.tsx`)

- **Button** `work-intake-v2-file-button`: „Alege SVG de pe calculator” → synchronous `fileInputRef.current.click()`.
- **Input** `work-intake-v2-file-input`: `sr-only` (visually hidden, still in layout tree), disabled only when `readOnly`.
- **No** `showOpenFilePicker`, **no** `htmlFor`/`label` mapping, **no** overlay input, **no** `pickingFile` / „Se deschide…” state.
- **`processingFile`** (label „Se analizează…”) starts only after a file is selected; cancel leaves UI normal with no error.
- **`onChange`** resets `input.value` after pick so the same file can be re-selected.
- **Drag & drop** calls `handleFilePick` directly (unchanged semantics).
- **`onVectorUploadStart` / `onVectorUploadEnd`** guard autosave merge during upload.

### Tests run

| Gate | Result |
|------|--------|
| Typecheck | PASS |
| Lint | PASS |
| Vitest `WorkIntakeV2Flow.test.tsx` | 47/47 PASS |
| Build | PASS |
| Playwright e2e | Not re-run in this pass (local `:3000` CDP proof used instead) |

### Manual browser proof (`http://127.0.0.1:3000/intake-v2/IR-MQ51B998`)

| Check | Result |
|-------|--------|
| Button shows „Alege SVG de pe calculator” (not two-step UI) | PASS |
| Button click → `input.click()` (CDP spy, count=1) | PASS |
| SVG selection → analysis → layers visible | PASS (`browser-proof.svg`) |
| No stuck „Se deschide…” / „Se încarcă…” on idle | PASS |
| No upload error on cancel/empty change | PASS (Vitest) |
| Drag & drop still parses immediately | PASS (Vitest) |

### Remaining limitations

- OS file dialog open itself cannot be asserted in headless automation; browse chain is proven via `input.click()` spy + `setInputFiles`/CDP `DataTransfer` on the hidden input.
- `openVectorFilePicker.ts` was never present on this branch; no helper removal required.

---

## Deferred

- CNC pass summary UI (3 + 2 treceri) — field persisted only; no new pricing engine
- Non-volumetric intakes still use legacy `IntakeDetail` at `/intake/:id` (by design)
- Pricing UI “7 lipsă” for generic aliases + operation rates (unchanged)

---

## Boundary confirmation

No origin/main, PR #3, app-layout, CostEngine, production migration/seed, DB reset, or scratch commits.

---

## Server-backed SVG upload (2026-06-09)

### Why client staging was abandoned

Owner manual proof on `/intake-v2/IR-MQ51B998` and `/intake-v2/IR-MQ6AB0JG` showed:

- Windows file dialog opens and selection reaches handlers.
- Client `pendingFile` staging remained unreliable (dedupe/triple-listener races).
- UI kept showing persisted `browser-proof.svg` / `lleexxaa.svg` instead of newly selected files.

Decision: official Work Intake V2 SVG flow is **server-backed upload + analysis**.

### Endpoint (canonical)

`POST /api/v1/entities/intake_requests/by-code/{intake_code}/svg-upload-and-analyze`

- Defined in `backend/routers/intake_requests.py`
- Frontend client: `frontend/src/lib/workIntakeV2/svgUploadApi.ts`
- Legacy router `backend/routers/intake_svg_upload.py` removed — single canonical route only
- `multipart/form-data` field: `file`
- Validates `.svg` / `image/svg+xml`, size cap (`SvgMetricsService` limit), UTF-8 text
- Stores under `backend/storage/intake_svg_uploads/{intake_code}/` (gitignored)
- Analyzes via `SvgLayerAnalysisService` + maps to flat `product_spec_json.vector_*`
- Persists merged spec to `intake_requests.product_spec_json`

### Fields updated

`vector_file_name`, `vector_file_selected_at`, `vector_file_size_bytes`, `vector_file_mime`, `vector_file_extension`, `vector_file_source=server_upload`, `vector_file_present`, `vector_parse_status`, `vector_svg_viewbox`, `vector_svg_width/height`, `vector_detected_layer_count`, `vector_detected_layers`, `vector_detected_layers_summary`, `svg_layer_mappings`, `vector_analysis_status`, `vector_svg_analyzed`, `vector_metrics_source=svg_analysis`, `intake_input_pathway=vector`

### Frontend behavior

- `V2SvgStage`: file pick → immediate POST → progress UI → apply returned `product_spec_json` + `onIntakeRefresh`
- Persistent success feedback after `ok: true`: `SVG analizat și salvat: <filename>` + `Ultima analiză: <timestamp>`
- Removed client `pendingFile` staging and separate **Analizează SVG** button from official flow
- Dev: `vite.config.ts` disables MGX source locator / atoms by default so file picker clicks work in local dev

### Tests

- Backend: `backend/tests/test_work_intake_svg_upload.py` (6 tests)
- Frontend: `WorkIntakeV2Flow.test.tsx` mocks `uploadIntakeSvgAndAnalyze`

### Owner proof

**PASS (agent audit 2026-06-09)** — POST 200 on `IR-MQ51B998`, filename updates, persistent success message + timestamp, same-file re-upload shows feedback, hard refresh coherent. Owner re-confirmation still recommended before merge.

### Gitignore

```
backend/storage/intake_svg_uploads/
backend/.debug_uploads/
```
