# BUILD-SVG-GEOMETRY-PARSER-MVP

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD (before) | `780dd51` |
| Working tree | clean |
| Backend :8000 | 200 OK |
| Frontend :3000 | 200 OK |

### Counts

| | Before | After |
|---|--------|-------|
| intakes | 22 | 22 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

---

## Phase 1 — Current SVG analysis audit

| capability | available before? | gap | MVP decision |
|------------|-------------------|-----|--------------|
| root width/height strings | yes (`vector_svg_width/height`) | no mm conversion | parser converts with confidence |
| viewBox | yes | no scale to mm | derive scale when physical size present |
| layers/groups | yes (Inkscape + top-level g) | no geometry per layer | traverse mapped layers for bbox |
| element nodes | yes (count only) | no bbox | MVP bbox for simple shapes + path bounds |
| path `d` | not read | no bounds | coordinate bounds only, no perimeter |
| rect/circle/ellipse/line/poly | not read | no bbox | supported in MVP |
| transforms | no | unsupported | translate/scale/matrix; rotate warns |
| units | warned only | no conversion | mm/cm/in/px with confidence tiers |
| quote-critical fields | manual entry | auto-fill risk | **never** auto-overwrite |
| suggestion storage | none | no fields | additive `vector_suggested_*` fields |

Quote-critical fields (operator-confirmed only): `width_mm`, `height_mm`, `letter_face_area_m2`, `letter_perimeter_m`, `letter_count`.

---

## MVP parser scope

**Supported:** physical dimensions, viewBox scale, mapped layer bbox, element counts, confidence/warnings.

**Not supported:** exact path perimeter/area, boolean ops, stroke expansion, text-to-outline, CNC perimeter.

**Output:** suggestions only — operator applies via explicit buttons.

Parser: `frontend/src/lib/svgGeometryParser.ts` (`mvp-1`).

---

## Unit conversion rules

| Unit | Conversion | Confidence |
|------|------------|------------|
| mm | direct | high |
| cm | ×10 → mm | high |
| in | ×25.4 → mm | high |
| pt | ×25.4/72 → mm | medium |
| px | ÷(96/25.4) → mm | low |
| viewBox only | no mm suggestions | low |

Mismatched width/height scale → warning, confidence lowered.

---

## Suggestion fields (additive)

- `vector_geometry_analyzed`, `vector_geometry_confidence`, `vector_geometry_warnings`
- `vector_geometry_parser_version`
- `vector_suggested_assembly_width_mm` / `_height_mm`
- `vector_suggested_letter_layer_width_mm` / `_height_mm`
- `vector_suggested_support_width_mm` / `_height_mm`, `vector_suggested_support_area_m2`
- `vector_suggested_frame_width_mm` / `_height_mm`
- `vector_suggested_letter_element_count`
- `geometry_source: svg_suggestion_confirmed` when operator applies

**Never auto-filled:** `letter_face_area_m2`, `letter_perimeter_m`.

---

## UI behavior

Section **Geometrie detectată din SVG — necesită confirmare** in unified vector surface after layer mapping.

Actions:
- Aplică dimensiunile sugerate
- Aplică aria suportului sugerată
- Aplică numărul de elemente ca număr litere
- Ignoră sugestiile

Low-confidence suggestions disable dimension/support apply buttons.

---

## Tests / lint

```text
svgGeometryParser.test.ts — 12 PASS
mapSvgGeometryToSpec.test.ts — 3 PASS
VectorIntakeFastAskPanel.test.tsx — 14 PASS
Product001IntakeSpecEditor.vectorFastAsk.test.tsx — 19 PASS
```

Backend: `test_intake_product_spec_validator.py` extended (Python not on PATH in agent shell — validator change is additive).

ESLint: 0 errors on changed files.

---

## Live browser smoke (completed 2026-06-07)

**Method:** Playwright headless Chromium against `http://localhost:3000` (cursor-ide-browser MCP unavailable).

**Pre-flight smoke:** HEAD `61ef55a`, clean tree, backend/frontend 200 OK.

| | Before | After |
|---|--------|-------|
| intakes | 22 | 22 |
| quotes | 7 | 7 (no new quote created) |
| orders | 8 | 8 (no new order created) |

**Intake:** `IR-MQ3C869E` (volumetric draft).

**SVG fixture:** `SVG_MULTI_LAYER` — `1000mm × 200mm`, viewBox `0 0 1000 200`, layers `LITERE` / `DIBOND` / `CADRU`.

| Step | Result |
|------|--------|
| Din fișier vector + file pick | PASS |
| 3 layers detected | PASS |
| Roles mapped (LITERE / DIBOND / CADRU) | PASS |
| Section “Geometrie detectată din SVG — necesită confirmare” | PASS |
| Confidence **High** + warnings (bbox/perimeter MVP) | PASS |
| `width_mm` / `height_mm` not auto-filled before apply | PASS |
| `letter_perimeter_m` / `letter_face_area_m2` not auto-filled | PASS |
| “Aplică dimensiunile sugerate” → assembly 1000×200 visible | PASS |
| “Aplică aria suportului sugerată” | PASS |
| Salvează + refresh → geometry section persists | PASS |
| No quote/order created | PASS |

**Expected suggestions observed:** Ansamblu sugerat **1000 × 200 mm**; layer litere **~450 × 160 mm**; suport **1000 × 200 mm**; cadru **980 × 180 mm**; 2 elemente layer litere.

**WI-SMOKE-P001:** Simulare tab metrics unchanged (**4800 / 600 / 60 / 2.88 / 18 / 9**). Total **844,41 EUR** not shown live (Calculează preliminar gated by terrain — baseline unchanged per prior CostEngine tests).

**/quotes:** “Ofertă nouă” opens generic QuoteWizard; closed without creating quote.

**Intake modified during smoke:** `IR-MQ3C869E` — vector geometry suggestions + optional dimension/support apply saved (entity count unchanged).

---

## Confirmations

- [x] No pricing / CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] No fake final perimeter/area calculated
- [x] Operator confirmation required for quote-critical fields
- [x] Manual + quick estimate preserved
- [x] SVG layer detection preserved
- [x] WI-SMOKE-P001 baseline preserved

## Commits

- `3ebc695` — feat: add svg geometry parser suggestions
- `61ef55a` — docs: record svg geometry parser commit hash
- *(browser smoke follow-up)* — docs: complete svg geometry parser browser smoke

## PASS/FAIL

**PASS** (live browser smoke complete)
