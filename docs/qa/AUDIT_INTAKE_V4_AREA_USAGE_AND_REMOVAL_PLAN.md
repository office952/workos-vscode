# AUDIT — Intake V4 Area Usage and Removal Plan

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `e719846f15b7f0b7103e143313311b5a4742cfd2`  
**Scope:** Audit only — no backend, CostEngine, or ProductSystem changes in this build.  
**Resumes:** worker `af4498e1` (incomplete — doc missing until this run).

**Related completed work (other workers):**
- Cant UI cleanup + simple UI (`IntakeV4EdgeCantReviewCard`, cost formula, `Detalii cant` layers)
- Print + laminare dedupe fix in `intakeV4LiveMaterialsUsedDisplay.ts` (`sumPrintLaminateCoverage`)
- **Phase A frontend finalization:** [`BUILD_INTAKE_V4_REVIEW_PHASE_A_FRONTEND_FINALIZATION.md`](./BUILD_INTAKE_V4_REVIEW_PHASE_A_FRONTEND_FINALIZATION.md)

---

## Executive summary

**Owner direction:** Remove intermediate area variants from the main operator Review form. Keep dimensions, vector perimeter, cant perimeter, LED perimeter, and **final material quantities** (including m² where the priced unit is m²). Do not show competing footprint sources (`eligible_area_floor`, placement face, face union bbox, layout shelf, etc.) in the primary workflow.

**Main question — can we remove area from the main form without breaking calculations?**

| Level | Verdict | Notes |
|-------|---------|-------|
| 1. UI principal | **DA** — scoatem ariile intermediare | `IntakeV4OperatorGeometrySummaryCard` already shows only L×H + perimetru vectorial. Rămân de eliminat/mutat: `IntakeV4GeometryPanel` (Suprafață față/emblemă), `IntakeV4SheetFootprintOverridePanel`, candidați arie în `IntakeV4SheetQuoteReviewPanel`. |
| 2. Calcul live | **PARȚIAL** | Fără surse de arie / footprint. **Păstrăm** cantități finale pe materiale (Plexi 1.264 m², Oracal 1.611 m², Print + laminare X m² acoperire) — acestea sunt output breakdown, nu „5 variante de arie”. |
| 3. Materiale folosite | **PARȚIAL** | La fel ca Calcul live: cantități finale pe material, etichetă `acoperire` pentru print. **Nu** afișa candidați footprint. |
| 4. Material breakdown detaliat | **PARȚIAL** | Rândurile materiale în m² rămân (sunt cantitatea ofertată). Zona „Verificare footprint material” + lista candidați → **mutare în debug/QA collapsed** sau eliminare din flux operator. |
| 5. Backend internal | **NU** — păstrăm | `face_area_m2`, nesting footprint, eligible floor, footprint override sunt necesare pentru qty Plexi/Forex/Oracal/print. |
| 6. Quote final / CostEngine | **NU** — păstrăm | `quote_input.letter_face_area_m2` / `front_face_area_m2` sunt gate obligatorii (`volumetric_quote_ready_policy`). Intake V4 breakdown nu este încă `is_applied_to_quote` pentru footprint. |

**Verdict ferm:** Eliminarea ariei din **UI principal** este sigură pentru calcule — backend continuă să deriveze m² intern. Riscul este **doar UX/confuzie**, nu ruptură de preț, dacă footprint panel este ascuns fără a șterge payload-ul `sheet_quote_override` din workspace.

---

## Classification legend (A–E)

| Class | Meaning | UI action |
|-------|---------|-----------|
| **A** | Necesar intern (backend, quote_input, nesting, persist) | Nu afișa în UI principal; poate rămâne în API/payload |
| **B** | Necesar doar ca **cantitate finală material** (m² preț) | Afișare permisă ca **o singură cifră per material**, nu ca sursă/geometrie |
| **C** | Debug / audit / QA | Collapsed accordion, owner review, tests — nu operator principal |
| **D** | De eliminat din UI principal | Footprint variants, eligible vs placement vs bbox, geometry panel areas |
| **E** | Riscant / greșit (sau a fost) | Print+laminare dublat (fixat frontend); nesting sub eligible înainte de floor (fixat backend) |

---

## Full area usage map

| # | Location | Field / label | Class | Used for | Removable from main UI? | Risk if removed from UI |
|---|----------|---------------|-------|----------|-------------------------|-------------------------|
| 1 | `IntakeV4OperatorGeometrySummaryCard` | Lățime, Înălțime, Perimetru total vectorial | — (perimetru, nu arie) | Operator orientation | N/A — **keep** | — |
| 2 | `IntakeV4GeometryPanel` (`variant="advanced"`) | Suprafață față, Suprafață emblemă | **D** | Display quote geometry | **Da** | None — duplicate of breakdown qty context |
| 3 | `IntakeV4GeometryPanel` | Cant perimetru (quote geometry) | **C** | Debug vs operator cant card | Collapse with panel | Operator uses `EdgeCantReviewCard` |
| 4 | `IntakeV4SheetFootprintOverridePanel` | Aria pieselor eligibile, Face union bbox, Layout auto shelf, Manual Corel | **D** | Operator selects footprint source | **Da** (mutare debug) | Plexi/Forex qty unchanged until save + `useForQuoteEstimate` |
| 5 | `IntakeV4SheetQuoteReviewPanel` | Arie selectată pentru review, sursă calcul | **C/D** | Internal sheet quote review | **Da** from main | Breakdown still uses default floor without override |
| 6 | `IntakeV4SheetQuoteReviewPanel` (accordion) | eligible, placement, nesting shelf, recommended auto | **C** | Owner/QA comparison | **Da** | None |
| 7 | `IntakeV4MaterialBreakdownPanel` | Plexiglas / Forex rows (m²) | **B** | Material qty + price | **Nu** — final qty | Hides material truth |
| 8 | `IntakeV4MaterialBreakdownPanel` | Oracal face / cant wrap (m²) | **B** | Vinyl area pricing | **Nu** as row qty | — |
| 9 | `IntakeV4MaterialBreakdownPanel` | Print / laminare rows (m²) | **B** | Print cost basis | **Nu** in full breakdown | — |
| 10 | `IntakeV4LiveCalculationSummary` → Materiale folosite | Plexi, Oracal, Print+laminare (m²) | **B** | Compact material qty | **Nu** — owner wants final qty | — |
| 11 | `intakeV4LiveMaterialsUsedDisplay` | `sumPrintLaminateCoverage` | **B** | Deduped graphic coverage | **Keep** | Was **E** before fix |
| 12 | `IntakeV4EdgeCantReviewCard` | Perimetru cant (m) | — | Cant cost | **Keep** — no m² | — |
| 13 | `IntakeV4ReviewLightingSection` (main) | Perimetru iluminare (m) | — | LED module density along perimeter | **Keep** | — |
| 14 | `IntakeV4ReviewLightingSection` (accordion) | Outbox emblemă m², densitate module/m² | **C** | Emblem LED area rule | **Da** from main | Emblem modules still computed |
| 15 | `IntakeV4ReviewBackingSelect` / emblem copy | „60 module LED / m² pe aria outbox” | **C** | Help text | Collapse | — |
| 16 | `IntakeV4PricingInputPanel` | Suprafață față | **C** | Quote handoff preview | Hidden from Review | — |
| 17 | `intakeV4QuoteGeometry.ts` | `face_area_m2`, `artwork_area_m2` | **A** | Sync to workspace / quote_input | N/A (logic) | Break quote readiness if removed from backend |
| 18 | `intakeV4LetterGroups.ts` | `face_area_m2` per group | **A** | Breakdown per-group vinyl, eligible sum | N/A | — |
| 19 | `intakeV4ArtworkFinish.ts` | `estimated_area_m2` | **A** | Print row generation | Not shown in simplified artwork UI | — |
| 20 | `intake_v4_material_breakdown_service.py` | eligible sum, nesting footprint, floor | **A** | Plexi/Forex qty | N/A | — |
| 21 | `intake_v4_sheet_footprint_override_service.py` | candidate areas, manual m² | **A** | Override Plexi/Forex when saved | N/A | — |
| 22 | `intake_v4_nesting_material_precision.py` | `apply_sheet_material_quantity_floor` | **A** | max(eligible, nesting footprint) | N/A | — |
| 23 | CostEngine / `quote_input` | `letter_face_area_m2`, `front_face_area_m2` | **A** | Formula handlers (vinyl, diffuser, relief) | N/A — out of Intake V4 UI scope | Quote blocked without area |
| 24 | `IntakeV4ConfirmSummary` | `grossFaceAreaM2`, emblem outbox | **C** | Confirm step summary | Optional trim | — |
| 25 | Nesting rows in breakdown | `used_sheet_area_sqm`, waste | **C** | nest2 diagnostic | Already in technical accordion | — |

---

## Footprint material — special audit

### What the zone does today

Rendered inside `IntakeV4MaterialBreakdownPanel` → `IntakeV4SheetQuoteReviewPanel` → `IntakeV4SheetFootprintOverridePanel`.

Sources exposed to operator:

| Source key | Label RO | Typical role |
|------------|----------|--------------|
| `eligible_area_floor` | Aria pieselor eligibile | Default after quantity floor (max eligible vs nesting placement) |
| `face_union_bbox` | Face union bbox | Diagnostic upper bound |
| `layout_occupied_area` | Layout auto shelf | nest2 shelf occupancy |
| `operator_manual_footprint` | Manual Corel | width_cm × height_cm → m² |
| `full_sheet_allocation` | Placă fizică | Technical only (accordion) |

### What actually changes when operator selects a footprint?

| Target | Changes? | Mechanism |
|--------|----------|-----------|
| Material breakdown Plexi (`plexiglas_face`) | **Da**, when `useForQuoteEstimate: true` and saved | `apply_operator_footprint_to_sheet_material_quantities` raises face qty to `target_sqm` |
| Material breakdown Forex (`forex_backing`) | **Da**, same applies_to set | Same function, `forex_backing` in `appliesTo` |
| Oracal face vinyl | **Nu** | Vinyl area from roll nesting / face geometry — not footprint panel |
| Print + laminare | **Nu** | Artwork `estimated_area_m2` / complexity |
| Cant / return material | **Nu** | Perimeter-based (ml) |
| LED consumables | **Nu** | Perimeter + emblem area rule |
| Calcul live / Materiale folosite | **Indirect da** | Same breakdown payload |
| Commercial quote / CostEngine | **Nu today** | `is_applied_to_quote: false`; panel copy states „nu trimite în CostEngine” |
| Stock / inventory | **Nu** | Explicit non-goal |

### Default without operator action

1. Sheet nesting computes placement footprint (bbox sum on nest).
2. `apply_sheet_material_quantity_floor` raises qty to `eligible_face_area_sum_sqm` when nesting &lt; eligible.
3. Footprint override **not applied** unless `sheet_quote_override.useForQuoteEstimate` is set.

### Recommendation

| Action | Class | Phase |
|--------|-------|-------|
| Remove `IntakeV4SheetFootprintOverridePanel` from main Review scroll | **D** | Phase 1 frontend |
| Keep backend endpoint + payload for owner QA | **A** | — |
| Optional future: binary „Estimare placă: automat / manual override” **without** showing 4 competing m² values | **B/C** | Phase 2 — needs owner confirm |
| Do **not** delete `sheet_quote_override` from workspace schema | **A** | — |

---

## Print + laminare — audit (6.243 m²)

### Status: **FIXED** (frontend, other worker)

**File:** `frontend/src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.ts`  
**Function:** `sumPrintLaminateCoverage` + `resolvePrintLaminateArtworkId`

### Root cause (before fix)

| Question | Answer |
|----------|--------|
| Rows in aggregation | `artwork_*_print_vinyl` + `artwork_*_laminated_vinyl` per logo |
| Quantity field | `base_quantity` (not `priced_quantity` / waste) |
| +20% waste | **Nu** in Materiale folosite after fix |
| Doubling mechanism | Naive **sum** of print + laminate for same artwork → 2×; two logos × 2 materials × ~0.78 m² ≈ **6.24 m²** |
| Backend duplicate rows? | **Nu** — backend correctly emits separate material rows; bug was **frontend aggregation** |

### Rule after fix (Variant A — owner preference)

```text
Print + laminare: X.XXX m² acoperire
```

- Per artwork: `max(print_qty, laminate_qty)` — same physical coverage.
- Across artworks: sum of per-artwork coverage.
- Example test: two logos @ 0.849 m² each → **1.698 m² acoperire**, not 3.396 or 6.243.

### Class

| Before fix | After fix |
|------------|-----------|
| **E** (misleading 2×–4×) | **B** (final coverage qty) |

### Breakdown detaliat

Separate rows „Autocolant printabil” / „Laminare protecție” remain in full `IntakeV4MaterialBreakdownPanel` — correct for **Variant B** at detail level.

---

## Cant — perimeter-only confirmation

| Check | Status |
|-------|--------|
| `IntakeV4EdgeCantReviewCard` main card shows m² | **Nu** — only Perimetru cant, Finisaj, Adâncime, Preț/ml, Cost formula |
| Materiale folosite cant row | **ml** (`operatorCantPerimeterM` from vector sum) |
| Calcul live cant cost | `return_material` × operator perimeter display; cost from breakdown unit_price |
| `edge_cant_oracal_651` m² in breakdown | **B** — Oracal wrap area for wrapped cant; stays in **detailed** breakdown, not cant card |
| Geometry panel cant section | Perimetru m — **C**, not primary operator surface |

**Verdict:** Cant UI is **aligned** with owner direction (perimeter × €/ml). No area removal needed on cant card.

**Completed:** `BUILD_INTAKE_V4_CANT_PERIMETER_COST_SIMPLE_UI.md`, `IntakeV4EdgeCantReviewCard` tests 5/5 PASS.

---

## LED — no area in main UI confirmation

| Surface | Shows area? | Shows perimeter? |
|---------|-------------|------------------|
| `IntakeV4ReviewLightingSection` main | **Nu** | **Da** — Perimetru iluminare |
| Main card module count | Via breakdown / form sync (buc) | — |
| Collapsed „Detalii calcul LED” | **Da** — Outbox emblemă m², 60 module/m² | — |
| `IntakeV4BackingAndEmblemSection` help | m² mentioned in rule text | — |

**Verdict:** Main LED UI is **perimeter-first**. Emblem m² is **C** — keep in accordion only; optional Phase 1 trim of outbox m² from accordion if owner wants zero m² anywhere outside Materiale folosite.

---

## Plexiglas / Forex / Oracal — quantity sources

| Material | Breakdown key | Qty source (backend) | Display in Materiale folosite |
|----------|---------------|----------------------|-------------------------------|
| Plexiglas față | `plexiglas_face` | max(eligible face sum, nesting placement footprint); footprint override if saved | **B** — e.g. 1.264 m² |
| Forex spate | `forex_backing` | `resolve_backing_material_area_m2` (often mirrors floored face) | **B** — same m² when fallback |
| Oracal 651/8500/641 | `face_vinyl_*` | Roll nesting or face area fallback | **B** — e.g. 1.611 m² |
| Oracal cant wrap | `edge_cant_oracal_651` | Derived from cant scope | Detailed breakdown only |

Operator does **not** need to see *how* eligible vs placement was combined — only final m² on material rows.

---

## Bugs / risks (area-related)

| ID | Class | Issue | Status |
|----|-------|-------|--------|
| AR-1 | **E** → fixed | Print+laminare double count in Materiale folosite | Fixed `sumPrintLaminateCoverage` |
| AR-2 | **E** → fixed | Plexi qty below eligible face (nesting footprint only) | Fixed `apply_sheet_material_quantity_floor` |
| AR-3 | **D** | Five footprint sources visible in main form | Open — removal plan Phase 1 |
| AR-4 | **D** | `IntakeV4GeometryPanel` Suprafață față/emblemă in Review scroll | Open — hide or collapse |
| AR-5 | **C** | LED emblem outbox m² in accordion | Acceptable; optional trim |
| AR-6 | **E** | Symmetric logo fallback ~1.56 m² each (raster missing) | Documented in nesting audit — informational |
| AR-7 | **C** | `artwork_area_m2` in quote geometry vs print coverage | Internal; not operator decision |

---

## Perimeter migration (what stays operator-facing)

| Metric | Primary UI surface | Backend field (reference) |
|--------|-------------------|---------------------------|
| Dimensiune lucrare L×H | `IntakeV4OperatorGeometrySummaryCard` | `width_mm`, `height_mm` |
| Perimetru total vectorial | Same | `corelComparableCurveLengthM` + artwork vector |
| Perimetru cant | `IntakeV4EdgeCantReviewCard` | `sumActiveLetterGroupCantPerimeterM` |
| Perimetru iluminare | `IntakeV4ReviewLightingSection` | `led_perimeter_ml` / `letter_perimeter_m` |
| CNC față/spate | `IntakeV4FaceBackPrepCostDraftSummaryCard` | vector perimeter in cost-draft |

Area-based metrics **exit** main operator path except as **single material quantity lines** (m² on Plexi/Oracal/Print).

---

## Phased removal plan

### Phase 1 — Frontend only (recommended next, no backend)

1. **Hide** `IntakeV4GeometryPanel` from default Review scroll (or gate behind „Detalii tehnice geometrie” collapsed, default closed).
2. **Remove** `IntakeV4SheetFootprintOverridePanel` from main column; move under QA-only route or collapsed „Owner material review” with warning.
3. **Trim** `IntakeV4SheetQuoteReviewPanel` main summary — remove „Arie selectată” / „Sursă calcul” from visible block; keep copy-to-clipboard for owner.
4. **Keep** `IntakeV4OperatorGeometrySummaryCard`, cant card, LED perimeter, Materiale folosite material qty rows.
5. Add one-line operator note on material breakdown: „Cantitățile m² sunt estimate materiale, nu arii geometrice multiple.”

**Tests to run after Phase 1:**
```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx `
  src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx `
  src/components/workos/intake-v4/IntakeV4SheetFootprintOverridePanel.test.tsx `
  src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.test.ts
```

### Phase 2 — Backend contract (owner confirm)

1. Decide if footprint override remains a **persisted** operator action or becomes dev-only.
2. Optional `material-breakdown/preview` — does not require showing area candidates in UI.
3. Wire `is_applied_to_quote` only when commercial handoff is defined — **out of scope** until ProductSystem build.

### Phase 3 — CostEngine / quote (explicit build)

- `letter_face_area_m2` remains mandatory for `TPL-VOLUMETRIC-LETTERS` quote readiness.
- No removal of area from `quote_input` without template contract change.

---

## Structured report (21 sections)

### 1. Branch + HEAD

- Branch: `local/integration-pr4-plus-svg-path`
- HEAD: `e719846f15b7f0b7103e143313311b5a4742cfd2`

### 2. Git status

Many untracked Intake V4 frontend/backend files and docs from parallel builds; audit doc is new untracked. No commit performed (per instruction).

### 3. Unde apare aria în UI

| Zone | Area shown? |
|------|-------------|
| Operator geometry summary | **Nu** (perimetru only) |
| Letter finishes section | **Nu** |
| Cant card | **Nu** |
| Artwork finish section | **Nu** (simplified) |
| LED main | **Nu** (perimetru) |
| LED accordion | **Da** (emblem outbox m²) |
| Material breakdown | **Da** (material qty m² + footprint panel) |
| Geometry panel (advanced) | **Da** (Suprafață față/emblemă) |
| Calcul live / Materiale folosite | **Da** (final material m²) |
| Confirm / pricing panels | **Da** (technical) |

### 4. Unde apare aria în frontend logic

`intakeV4QuoteGeometry.ts`, `intakeV4LetterGroups.ts`, `intakeV4ArtworkFinish.ts`, `intakeV4SheetFootprintSource.ts`, `intakeV4SheetFootprintOverride.ts`, `intakeV4MaterialQuoteReviewSnapshot.ts`, `intakeV4LiveMaterialsUsedDisplay.ts`, `intakeV4ConfirmSummary.ts`, `sharedLedLightingDensity.ts` (emblem modules/m²).

### 5. Unde apare aria în backend

`intake_v4_quote_geometry_service.py`, `intake_v4_material_breakdown_service.py`, `intake_v4_nesting_material_precision.py`, `intake_v4_sheet_footprint_override_service.py`, artwork print row appenders, roll vinyl nesting helpers.

### 6. Unde apare aria în material breakdown

Plexi/Forex sheet qty (m²), face vinyl rows (m²), artwork print/laminate rows (m²), `edge_cant_oracal_651` (m²), nesting diagnostic rows, `sheet_quote_material_candidates` object with all candidate areas.

### 7. Unde apare aria în CostEngine / quote

`quote_input.letter_face_area_m2` / `front_face_area_m2` required for volumetric quote readiness; formula handlers `_handle_face_vinyl_used_sqm`, `_handle_plexi_diffuser_area`, `_handle_relief_material_area`. Intake V4 material breakdown is **estimate** — not direct CostEngine execution in Review.

### 8. Footprint material — ce schimbă real

See **Footprint material — special audit** above. Summary: **Plexi + Forex qty only**, when override saved with `useForQuoteEstimate`; not CostEngine; not Oracal/print/cant/LED.

### 9. Print + laminare — sursa 6.243 m²

Naive sum of 4 breakdown rows (2 logos × print + laminate). Fixed by `sumPrintLaminateCoverage`. Ana Maria symmetric logos: **~1.698 m² acoperire** (test fixture), not 6.243.

### 10. Plexiglas / Forex / Oracal

See table in **Plexiglas / Forex / Oracal** section. Floor rule ensures Plexi ≥ eligible face sum.

### 11. Cant — confirmare fără arie

**Confirmat** — perimeter-only on main cant UI; m² only for Oracal wrap in detailed breakdown.

### 12. LED — confirmare fără arie în UI principal

**Confirmat** — main shows Perimetru iluminare; m² only in collapsed LED details for emblem density.

### 13. Ce arii putem scoate complet din UI

- Footprint source radio list with 4+ m² values
- Geometry panel Suprafață față / emblemă (main scroll)
- Sheet quote „Arie selectată” / candidați lista în main view
- LED outbox m² (optional, accordion)

### 14. Ce arii trebuie păstrate intern

- All backend candidate fields
- `face_area_m2` / `artwork_area_m2` in workspace geometry
- `letter_group_finishes[].face_area_m2`
- `sheet_quote_override` payload
- `quote_input` face area for quote wizard handoff

### 15. Ce arii sunt bug / risc

AR-1, AR-2 fixed; AR-3, AR-4 open UX; AR-6 raster fallback informational.

### 16. Ce calcule pot trece pe perimetru

Cant (done), LED letters (done), CNC face/back (perimeter ml in cost-draft). **Cannot** move Plexi/Forex/Oracal/print to perimeter — pricing is m²-based.

### 17. Ce cere backend

Backend **must** retain area for m²-priced materials. No schema removal without migration build. Footprint override endpoint can remain dormant if UI removed.

### 18. Ce poate fi doar frontend

Phase 1 entire footprint panel visibility, geometry panel areas, sheet quote summary trim, accordion-only LED m². Print+laminare dedupe **already frontend-only**.

### 19. Teste / diagnostic rulate

```text
vitest run (2026-06-24):
  intakeV4LiveMaterialsUsedDisplay.test.ts     8/8 PASS
  IntakeV4EdgeCantReviewCard.test.tsx          5/5 PASS
  IntakeV4OperatorGeometrySummaryCard.test.tsx 3/3 PASS
Total: 16/16 PASS
```

### 20. Git status final

Unchanged — audit doc added as untracked `docs/qa/AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md`. No commit, no push.

### 21. Recomandare fază următoare

**Proceed with Phase 1 frontend visibility removal** (hide footprint panel + geometry areas from main Review) **without** backend changes. Confirm with owner whether footprint override remains a persisted owner-only action or is deprecated entirely. Defer CostEngine/quote_input area changes — **not recommended**.

---

## Boundary

- No backend, CostEngine, ProductSystem, or pricing formula changes in this audit.
- No commit or push.
- Implementation of Phase 1 requires separate build doc + owner confirm.

## References

- `docs/qa/AUDIT_INTAKE_V4_REVIEW_FORM_FUNCTIONAL_IMPACT.md`
- `docs/qa/AUDIT_AND_FIX_INTAKE_V4_SHEET_NESTING_QUANTITY_FLOOR_AND_BACKING_AREA_TRUTH.md`
- `docs/qa/BUILD_INTAKE_V4_CANT_PERIMETER_COST_SIMPLE_UI.md`
- `frontend/src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.ts`
- `backend/services/intake_v4_sheet_footprint_override_service.py`
