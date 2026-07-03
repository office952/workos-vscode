# BUILD_INTAKE_V4_NESTING_PREVIEW_AND_MATERIAL_PRECISION_CLOSURE

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `ec9b79f` — gate backing CNC cost |
| Build date | 2026-06-22 |
| Push | **No** |

## Root causes closed

| Bug | Root cause | Fix |
|-----|------------|-----|
| Plexiglas face **4.482 m²** | `usedSheetAreaSqm` (full sheet 3000×2000 = 6 m²) prorated/summed into quote estimate | Sheet material qty = **Σ placement footprints** by role/part kind on **one active layout** |
| Vinil față **2.784 m²** | Alternative roll widths + artwork roll jobs **summed** | Best roll area per layer/color; exclude `printed_artwork`; never sum alternatives |
| Material breakdown WIP test **2.34 expected** | Test assumed full sheet stock area | Updated to **0.56 m²** footprint (800×500 + 400×400 mm placements) |
| Forex when backing absent | `backing_area_m2` in geometry triggered forex row | Gate on **confirmed backing layer** (`backing_layer_confirmed`) |

## Final policies

### Sheet quantity (quote estimate)

```txt
quote_material_quantity_sqm = sum relevant placed part footprints (face/backing) on active sheet layout
usedSheetAreaSqm = diagnostic efficiency only — not quote quantity when placements exist
prorated_fallback = only when placements/roles missing (legacy payloads)
```

### Roll quantity (quote estimate)

```txt
one active roll layout per (layer, color) — lowest usedRollAreaSqm among alternatives
printed_artwork / needs_decision artwork excluded from face Oracal row
```

### Active vs alternative layouts

```txt
active: highest-efficiency sheet with placements OR best roll width per layer
alternative: all other sheet configs / roll widths — layout_kind=alternative_variant, not summed
```

### Quote estimate vs procurement preview

| Mode | Purpose | Quantity basis |
|------|---------|----------------|
| **Material breakdown** | Quote material cost estimate | Footprint + waste policy; `consumption_mode=quote_estimate_not_stock` |
| **Nesting preview** | Read-only diagnostic | Same active layout as breakdown; links material rows → partIds |
| **Procurement preview** (existing V3 handoff) | Sheet/roll purchase candidates | Full sheets possible — **not** auto-merged into quote breakdown |

### Child parts / holes / artwork

```txt
nesting on child parts only (placements.partId)
inner holes excluded from sheet footprint (letter part classification)
printed_artwork excluded from plexiglas_face / face_vinyl rows
backing Forex requires confirmed backing layer
```

## IV4-46499080 expected (after ec9b79f + this build)

| Item | Expected |
|------|----------|
| Plexiglas face | present — face layers only, footprint not 4.482 full sheet |
| Vinil face | **absent** (`face_finish_type=none` per group) |
| Print/Laminare L1 | **absent** (`needs_decision`) |
| Cant/return | ~14.5711 ml |
| LED / PSU | active |
| Forex/backing | **absent** (`backing_not_confirmed`) |
| `back_cut` | skipped (`gate:backing_absent`) |
| Nesting preview | read-only; no inventory mutation |

## API

```txt
GET /api/v1/intake-v4/workspaces/{id}/material-breakdown  → includes nesting_preview
GET /api/v1/intake-v4/workspaces/{id}/nesting-preview       → read-only diagnostic
```

Boundary flags: `preview_only`, `mutates_inventory=false`, `creates_execution_plan=false`, `consumes_stock=false`.

## UI

Review → Material breakdown panel embeds **Nesting preview / Material trace** (collapsible):

- Summary cards (layouts, alternatives, nestable parts, holes excluded)
- Sheet / roll tables with active vs alternative
- Parts table + material line trace
- MVP bounding-box canvas on active sheet only

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_nesting_preview.py -q          # 5 passed
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q        # 24 passed
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_nesting_material_precision.py -q  # 10 passed
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py -q  # 19 passed
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pricing_input.py -q             # 7 passed
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py -q   # 12 passed
```

**Total scoped: 75 passed.**

## Remaining gaps

- Procurement preview sheet purchase qty not split from quote footprint (by design — separate build)
- Full toolpath nesting canvas (MVP uses bounding boxes)
- Operator backing/șanfren selector UI (separate build)

## Boundary

No ExecutionPlan, `tasks_json`, task creation, stock consumption, CostEngine registry, or Pricing Registry changes.
