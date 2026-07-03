# Intake V4 — Nesting Visual Layout & PBL Layer Regression Audit

**Date:** 2026-06-23  
**Branch audited:** `local/integration-pr4-plus-svg-path`  
**Commits in scope:** `4ed5033` (remote) → `6c48e25` (floor fix) → wording follow-up

## Executive summary

| Issue | Verdict |
|-------|---------|
| PBL shows only 2 layers | **Not a parser regression.** Canonical PBL has **3 Corel layers**; perception of “2 layers” comes from **2 face production groups** + **1 artwork layer**. |
| Nesting qty ≈ eligible face area after `6c48e25` | **Expected behavior** — sheet quantity floor prevents undercount when nesting footprint is below eligible part area. |
| UI “Nesting — precizie ridicată” when floor applied | **Misleading** — fixed in follow-up by showing **“Estimare arie piese — floor arie eligibilă”** when `sheet_nesting_quantity_floor_applied` is present. |

---

## 1. PBL layer counts

| Layer | Count / detail |
|-------|----------------|
| PBL raw SVG layer count | **3** (`Layer_x0020_1`, `Layer_x0020_2`, `Layer_x0020_3`) |
| PBL analyzer layer count | **3** |
| PBL UI layer table row count | **3** (E2E `layerRows: 3`) |
| PBL face production geometry layers | **2** (`autoRole === "face"` on L2 + L3) |
| PBL artwork layer | **1** (`Layer_x0020_1` → `printed_artwork`) |
| PBL letter groups (finish) | **2** (volumetric face groups L2 + L3) |

**Fixture:** `frontend/src/lib/svgAnalyzer/fixtures/pbl-layere.svg`

**Regression gates (PASS at audit time):**

- Vitest `svgAnalyzerRegressionGate.test.ts` — expects 3 Corel layer names, 10 production parts, ~0.691 m² face area
- Playwright `intake-v4-analyzer-regression-gate-smoke.spec.ts` — `layerRows: 3`

---

## 2. “2 layers” confusion

Operators may count:

- **2 face letter groups** in finish setup (green L2 + cyan L3), or
- **2 production geometry face layers** (`countProductionGeometryLayers()`),

while the **Layer roles table** correctly shows **3 Corel layers** including artwork L1.

**No SVG parser / pseudo-layer classifier / Corel extraction change** is required for PBL.

`6c48e25` did **not** touch frontend analyzer code — only backend material breakdown floor logic.

---

## 3. Nesting truth (Ana Maria & PBL)

### Ana Maria (`fara_layere_powerclip.svg`, workspace `IV4-8D89E354`)

| Metric | Value |
|--------|-------|
| Eligible face area | 1.2638 m² |
| Nesting footprint before floor | 1.1469 m² |
| Quantity after floor | 1.2638 m² |
| Floor applied | yes |
| Physical sheet allocation (quote) | 1 × 3000×2000 mm (6.0 m² stock metadata) |
| Layout efficiency (bbox / sheet) | ~72% |

### PBL (`pbl-layere.svg`, workspace `IV4-46499080`)

| Metric | Value |
|--------|-------|
| Eligible face area | 0.6907 m² |
| Nesting footprint before floor | 0.5834 m² |
| Quantity after floor | 0.6907 m² |
| Floor applied | yes |
| Physical sheet allocation (quote) | 1 × 3000×2000 mm |
| Layout efficiency | ~13% (long narrow job on large sheet) |

Material quantity after floor equals **eligible face area**, not nesting placement footprint. Warning `sheet_nesting_quantity_floor_applied` is emitted at breakdown level.

---

## 4. Visual nesting UI

**Partial preview exists** — not true geometric nesting.

- Component: `IntakeV4NestingPreviewPanel`
- Mode: `bounding_box_mvp` — placement bounding rectangles on sheet canvas
- Location: Material Breakdown → **Detalii tehnice** → **Nesting preview / Material trace**
- Disclaimer: preview-only, does not mutate inventory or consume stock

There is **no** full polygon nest / nest2 visual layout in operator UI today — only numeric estimates, efficiency, and bbox MVP.

---

## 5. Wording risk & recommendation

When `sheet_nesting_quantity_floor_applied` is active, rows previously showed:

> Nesting — precizie ridicată

even though quantity came from **eligible part area floor**, not placement footprint.

**Recommendation implemented:** when breakdown warning `sheet_nesting_quantity_floor_applied` is present and the material row is a sheet-nesting quote row with nesting confidence, display:

> Estimare arie piese — floor arie eligibilă

with operator hint:

> Footprint-ul nesting era sub aria pieselor; cantitatea a fost ridicată la aria eligibilă pentru a evita subestimarea.

Quantity, floor logic, nesting trace, and global warning are unchanged.

---

## 6. What was not changed (audit boundary)

- SVG analyzer parser / pseudo-layer classifier
- Geometry formulas (LED, CNC, cant)
- Nesting quantity floor algorithm (values unchanged)
- API/payload schema
- Pricing Registry, Color Registry, CostEngine
- Quote/order/task creation, ExecutionPlan, tasks_json, stock consumption

---

## 7. Optional future UX (not implemented)

If operator confusion persists, consider a lightweight analyzer summary line:

> 3 layere Corel · 2 grupe față · 1 artwork

Only if it fits existing summary UI without refactor.
