# Shared Edge / Cant Rules

## Purpose

Cant / volum (edge return) semantics are shared across **TPL-VOLUMETRIC-LETTERS**, future **TPL-LIGHTBOX**, vinyl-only services, and operator Intake V4 Material Breakdown. This module centralizes:

- calculated vs quote cant length (+20% waste on material quote rows)
- edge adhesive consumption (2 ml / ml cant on letter-only perimeter)
- Oracal **651** on cant when finish is `oracal_wrapped`
- preview operation rows (bonding, Oracal wrap) — **no real tasks**, no stock

Implementation: `backend/services/shared_edge_cant_rules.py`

## Perimeter families (do not mix)

| Metric | Typical PBL | Unit in API | Used for |
|--------|-------------|-------------|----------|
| LED exterior perimeter | ~11.63 m | m | LED modules, wiring density |
| CNC face perimeter | ~13.62 m | ml (CNC machine linear-meter convention) | Face cut / face bevel `operation_rows` |
| Cant / volum calculated (material) | ~15.47 m | **m** | Aluminum `return_material` base quantity |
| Cant / volum pentru preț | ~18.56 m | **m** | Priced aluminum return (+20% waste on material row) |
| Letter-only cant (adhesive) | ~13.62 m | **m** basis -> **ml** adhesive output | Adeziv lipire cant |
| Total graphic cant (bond labor) | ~15.47 m | **m** | Lipire cant / volum operation preview |

PBL geometry: `letter_return_perimeter_ml` is about 13.62 m (letters only); `return_material_perimeter_ml` is about 15.47 m (letters + artwork + interioare). Adhesive intentionally uses **letter-only** length. Bond labor (`edge_cant_bond_to_face` / `return_face_bonding`) uses **total graphic/cant perimeter** at the owner-confirmed 5 EUR/ml rate.

## Units

| Quantity | Correct unit |
|----------|----------------|
| Cant / volum length | `m` or `linear_meter` |
| Edge/cant operation preview | `m` |
| Oracal 651 cant material area | `m2` |
| Adeziv cant | `ml` (milliliters) |
| CNC operation passes | `ml` (machine linear-meter convention — not cant length) |

## Calculated vs quote edge length

- **Calculated** (`calculated_edge_length_m`): geometry / group perimeters before quote waste.
- **Quote** (`quote_edge_length_m`): calculated × 1.20 (20% owner waste on material costing).
- **Adhesive** uses **letter-only calculated** perimeter × 2 ml/ml — not quote length.

## Oracal 651 on cant

When return finish is `oracal_wrapped` (or legacy `colantat` / `oracal`):

- Series is always **651** via `shared_vinyl_material_catalog` (`RETURN_CANT_VOLUM_WRAPPING`).
- Never 641 or 8500 on cant wrap.
- Material row: `edge_cant_oracal_651` — area m² = **quote wrapped length (m)** × band width (return_depth_mm + 10 mm) / 1000.
- Example (all groups wrapped, depth 60 mm): wrapped calc 13.62 m → quote 16.35 m → band 0.07 m → area ≈ 1.1442 m² → 9 EUR/m² ≈ 10.30 EUR.
- Price from owner interim catalog (9 EUR/m²) until Pricing Registry migration.
- Owner Oracal fallback sources are protected from registry overrides even when `price_source` is composed (`shared_edge_cant_rules|intake_v4_owner_oracal_651`).

## Row types

| Type | Example keys | Notes |
|------|----------------|-------|
| Material | `return_material`, `edge_cant_oracal_651` | Quote estimate, not stock |
| Consumable | `adhesive_return_to_face` | Centralized adhesive rule |
| CNC operations | `operation_rows` | Separate list — cutting/bevel only |
| Edge operations | `edge_cant_operation_rows` | Bond + Oracal wrap preview |

## Template links

- **TPL-VOLUMETRIC-LETTERS**: Intake V4 Material Breakdown + dry-run preview consume shared rules.
- **TPL-LIGHTBOX** (future): same cant/adhesive/wrap applications; not activated in this build.
- **Colantare-only services** (future): resolve vinyl by `VinylApplication`, not template literals.

## Operator labels

Operator-facing label is **cant / volum**. Legacy internal/API field names (`return_finish_type`, `return_material`) may remain temporarily.

## Intake V4 UI (BUILD_INTAKE_V4_EDGE_CANT_UI_QUOTE_IMPACT_AND_PREVIEW_HARDENING)

- **Review**: `IntakeV4EdgeCantReviewCard` — finisaj, cant calculat / pentru preț, pierdere +20%, adeziv, Oracal 651 impact panel when wrapped.
- **Confirm Summary**: dedicated **Cant / volum** section with operations preview.
- **Material Breakdown**: grouped Materiale / Consumabile adeziv / Operații CNC / Operații cant; Oracal quote impact mini-panel; `consumes_stock_now=false` / `creates_task_now=false` on edge rows when exposed.
- **Production Preview / Task dry-run**: `edge_cant_task_source=shared_edge_cant_rules`, `edge_cant_operation_candidates` in **m** (not ml).
- **Selector hydration**: form re-syncs from saved `finish_setup` on workspace load; pending-save banner when backing / emblem / cant finish diverge from API (breakdown reads persisted workspace only).
- **Handoff warning**: `face_and_backing_cnc_cut` documented as legacy catalog alignment — CNC quantities from `operation_rows`, not catalog bundles.

## Non-goals

- Real ExecutionTask / `tasks_json` / ExecutionPlan
- Stock consumption or reservations
- Pricing Registry / CostEngine / Color Registry rewrites
- Employee assignment or procurement
