# BUILD: Volumetric Vector Intake Fast Ask Flow

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `5bc2b3c`

## Problem

Selecting **„Din fișier vector”** showed the same manual specification form immediately. Operators had to scroll through all sections without a vector-first entry step.

## Root cause

`intake_input_pathway === "vector"` only controlled section visibility via `isIntakeSectionVisible()` — no dedicated fast-ask layer before the full `Product001IntakeSpecEditor`.

Secondary bug fixed during QA: `deriveFastAskFromSpec()` passed `letterDepth: undefined` into the fast-ask panel init, overwriting the default 60 mm depth and preventing depth prefill on apply.

## New flow

1. Operator selects **Din fișier vector**
2. **Vector Intake Fast Ask** panel appears first (file + quick questions)
3. Full form sections stay gated until **Aplică în specificație** (legacy smoke rows with file + depth + geometry/finish skip the gate)
4. Safe fields map into `product_spec_json`
5. Full form sections unlock with prefilled values highlighted
6. Operator reviews and **Salvează specificația**

## Fast ask questions

| Step | Question | Options |
|------|----------|---------|
| A | Fișier vector | upload + filename + quality notes |
| B | Layere aliniate? | Da / Nu / Nu știu + notes |
| C | Față colantată? | Plexi / Oracal / Print+laminare / Nu știu |
| D | Cant/lateral | Aluminiu / RAL / Oracal / Alt / Nu știu |
| E | Adâncime | 30/60/80/100/custom mm |
| F | Iluminare | Halo / față / mixt / fără / nu știu |

## Prefill mapping

| Fast ask answer | product_spec_json field(s) | Auto-calc? |
|-----------------|------------------------------|------------|
| vectorFileName | `vector_file_name`, `vector_file_present`, `vector_file_type`, `vector_analysis_status` | No geometry |
| layer aligned | `vector_layer_alignment_status`, `vector_layer_mapping_status`, `vector_manual_review_approved` | No |
| plexi visible | `face_finish_type: "none"` | No |
| oracal colored | `face_finish_type: "oracal_651"` | No |
| print laminated | `face_finish_type: "printed_laminated_vinyl"` | No |
| cant RAL | `volume_finish: "paint_after_face_miter_bond"` | No |
| cant Oracal | `volume_finish: "oracal_651_before_forming"` | No |
| depth 60 | `depth_mm`, `return_depth_mm` | No |
| lighting halo | `illumination_type: "halo"` | No |
| apply timestamp | `vector_fast_ask_applied_at` | Metadata only |

**Not auto-calculated:** `letter_face_area_m2`, `letter_perimeter_m`, `letter_count`, `width_mm`, `height_mm`.

## Save behavior

- Apply updates local editor state only until operator saves
- **Salvează specificația** persists via existing `normalizeIntakeProductSpecForSave`
- Message: „Date aplicate în formular. Verifică și salvează specificația.”
- Pathway change shows warning; does not erase data

## Tests & lint

- `volumetricVectorFastAskMapping.test.ts` — 11 tests PASS
- `VectorIntakeFastAskPanel.test.tsx` — 3 tests PASS
- `Product001IntakeSpecEditor.vectorFastAsk.test.tsx` — 5 tests PASS
- `volumetricIntakePathway.test.ts` — 7 tests PASS
- ESLint on changed frontend files — PASS

## Browser validation (2026-06-07)

| Step | Result |
|------|--------|
| IR-MQ3C869E — select vector pathway | Fast ask panel shown; full form gated |
| Enter file + answers + Apply | Sections unlocked; vector file in Vector Studio |
| Save + refresh | `litere_test.svg`, aligned layers, finishes persist |
| WI-SMOKE-P001 — Simulare ofertă | **844,41 EUR** total unchanged |
| /quotes — Ofertă nouă | Generic quotes list; 7 quotes |

## Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 15 | 15 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

## Confirmations

- No pricing / CostEngine / quote calc changes
- `Product001IntakeSpecEditor` contract preserved (additive UI layer)
- Manual + quick estimate flows unchanged
- Vector Studio section preserved
- No fake geometry without parser
- No quote/order created during validation
