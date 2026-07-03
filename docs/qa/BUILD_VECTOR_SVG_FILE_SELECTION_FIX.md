# BUILD: Vector SVG File Selection Fix

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `af6b811`

## User-reported issue

Selecting SVG files in **Din fișier vector** did not work reliably — file not selectable/visible/attached.

## Root cause

1. **Weak file picker UX** — native `<input type="file">` was small and easy to miss; no dedicated CTA.
2. **Incomplete `accept`** — only extensions (`.svg,.dxf,...`) without `image/svg+xml`; some Windows/Electron pickers filter SVG poorly.
3. **Metadata-only gap** — picking a file only updated local `vectorFileName` text; no immediate sync to `product_spec_json`, no MIME/size/extension fields.
4. **Backend ALLOWED_KEYS** — new metadata fields from fast ask were stripped on API save (fixed additively).

## Chosen scope: metadata-only

- No binary upload endpoint exists for intake vector files.
- Operator selects file → UI stores safe metadata (name, extension, MIME, size, timestamp, `vector_file_source: local_manual`).
- Tooltip/info: binary storage will connect when backend endpoint is available.
- **No geometry parsing** from SVG in this build.

## Accepted file types

| Extension | Notes |
|-----------|--------|
| `.svg` | Required; `image/svg+xml` + extension accept |
| `.dxf` | Reference / manual review |
| `.dwg` | Reference / manual review |
| `.eps`, `.ai`, `.pdf` | Reference only |

SVG with **empty MIME** is accepted when filename ends with `.svg`.

## Persistence fields

| Field | Purpose |
|-------|---------|
| `vector_file_present` | true when attached |
| `vector_file_name` | Display + Vector Studio |
| `vector_file_type` | svg/dxf/dwg/other |
| `vector_file_mime` | MIME hint |
| `vector_file_size_bytes` | Size at selection |
| `vector_file_extension` | Extension |
| `vector_file_selected_at` | ISO timestamp |
| `vector_file_source` | `local_manual` |

## Tests & lint

- `vectorFileSelection.test.ts` — 7 PASS
- `VectorIntakeFastAskPanel.test.tsx` — 8 PASS
- `Product001IntakeSpecEditor.vectorFastAsk.test.tsx` — 6 PASS
- ESLint changed frontend files — PASS

## Browser validation (2026-06-07)

| Step | Result |
|------|--------|
| IR-MQ3C869E vector pathway | **Selectează fișier vector** button visible |
| Prior save | `litere_test.svg` persists in fast ask + Vector Studio |
| WI-SMOKE-P001 simulation | **844,41 EUR** (verified in prior session; unchanged) |
| /quotes | 7 quotes; Ofertă nouă present |

## Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 15 | 15 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

## Confirmations

- No pricing / CostEngine changes
- No quote/order created
- No Reference Catalogs started
- No fake geometry from SVG
- Product001IntakeSpecEditor contract preserved (additive callbacks/fields)
- Manual + quick estimate flows preserved
- Vector Studio preserved

## Pre-flight note

`docs/qa/BUILD_INTAKE_DETAIL_ROUTING_AND_BLANK_PAGE_FIX.md` remains locally modified from a prior task — **not included** in this commit.
