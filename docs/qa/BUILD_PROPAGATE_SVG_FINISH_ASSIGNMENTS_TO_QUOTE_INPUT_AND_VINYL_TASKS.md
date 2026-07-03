# BUILD — Propagate SVG Finish Assignments to Quote Input + Vinyl Tasks

**Date:** 2026-06-17  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** Operational handoff + execution plan only — no CostEngine/pricing/inventory/migrations.

## Purpose

Repair propagation of operator-confirmed SVG finish assignments (`letterGroupFinishAssignments`) into `quote_input`, handoff metadata, and volumetric execution plans so face/return vinyl tasks are generated with correct order and operator instructions.

## Initial problem

For intake `IR-MQHZ41CM`, assignments were persisted correctly but:

- `quote_input.face_finish_type` stayed `none`
- `face_vinyl_enabled` stayed `false`
- return vinyl fields were absent; `return_depth_mm` fell back to wrong defaults
- execution plan had 10 tasks — missing `vinyl_application` and `return_vinyl_application`

Root cause: frontend prefill ignored group assignments; backend had no normalization from `letterGroupFinishAssignments` before handoff/plan filtering.

## Files changed

| File | Change |
|------|--------|
| `backend/services/volumetric_finish_assignment_service.py` | **New** — normalization, group handoff, return vinyl detection, operator instructions |
| `backend/services/volumetric_face_vinyl_service.py` | Resolve operational quote_input; delegate return/face instructions |
| `backend/services/volumetric_conditional_plan_tasks_service.py` | Return vinyl task inject/filter/taxonomy; vinyl dependencies |
| `backend/services/volumetric_execution_dispatch.py` | Labels/minutes for `return_vinyl_application` |
| `backend/routers/quotes.py` | Normalize quote_input from intake assignments at price/handoff |
| `backend/tests/test_volumetric_finish_assignment_normalization.py` | **New** — normalization, instructions, plan order tests |
| `backend/tests/test_volumetric_face_vinyl_task.py` | Updated return vinyl instruction tests |

## Behaviour

### Finish taxonomy — Oracal 8500 vs `face_finish_type=oracal_651`

**This is intentional and matches the existing volumetric quote contract.**

| Layer | Field | Oracal 8500 / `translucent_film` value | Role |
|-------|--------|----------------------------------------|------|
| Costing gate | `face_finish_type` | `oracal_651` | Opens template gates (`MAT-ORACAL-651`, `vinyl_application` when not `none`). CostEngine has **no** separate Oracal 8500 price path. |
| Production metadata | `face_finish_subtype` | `oracal_8500` | Preserves series for warnings/audit (`WARNING_ORACAL_8500_PRICED_AS_651`). |
| Operator truth | `face_vinyl_material`, `face_vinyl_color_*` | `Oracal 8500`, `527 Pastel blue`, … | Instructions, handoff, operator UI. |

Precedent in repo (unchanged by this build):

- Frontend `intakeFaceFinishToQuoteCostingType("oracal_8500") → "oracal_651"` with comment *no invented 8500 price*
- `QuoteInputPayload.face_finish_subtype` — *Intake subtype when Oracal 8500 priced via oracal_651 path*
- Backend `volumetric_quote_input_policy.WARNING_ORACAL_8500_PRICED_AS_651`

**Not a semantic mislabel:** `oracal_651` here is the **legacy costing umbrella** for all Oracal face-vinyl lines, not a claim that the job uses Oracal 651 series material. Real series stays on subtype + material + color.

This build does **not** introduce a new `face_finish_type=oracal_8500` or CostEngine changes.

### Normalization (groups + uniform)

Reads confirmed `letterGroupFinishAssignments` and merges into operational `quote_input`:

**Face (example IR-MQHZ41CM):**

- `face_vinyl_enabled = true`
- `face_finish_type = oracal_651` (costing-compatible)
- `face_finish_subtype = oracal_8500`
- `face_vinyl_material = Oracal 8500`
- `face_vinyl_color_code/name` preserved
- `letter_group_face_vinyl_handoff.groups[]` retains per-group detail

**Return/cant:**

- `return_vinyl_enabled = true`
- `return_finish_type = oracal_wrapped`
- `return_depth_mm = 60` (from `depthMm`, overrides stale 80)
- `return_vinyl_material/color_*` preserved
- `letter_group_return_vinyl_handoff` for multi-group instructions

**Uniform all letters:** single group or identical signatures → instructions say „toate literele”.

**Multi-group:** instructions list each group label + material/color.

### Execution plan

When vinyl applies, plan orchestration now:

1. Injects `return_vinyl_application` / **Colantare cant** before `side_forming`
2. Injects `vinyl_application` / **Colantare fețe litere** after `face_cnc_cut`
3. Sets dependencies:
   - `return_vinyl_application` → `side_forming`
   - `face_cnc_cut` → `vinyl_application` → `return_face_bonding`
   - `side_forming` → `return_face_bonding`

### Handoff

New quotes priced via `/quotes/price` store normalized `quote_input` on snapshot. `face_vinyl_handoff.quantity_basis` is no longer `face_vinyl_not_selected` when assignments enable face vinyl.

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_face_vinyl_task.py tests/test_volumetric_conditional_plan_tasks.py -q
```

**Result:** `60 passed`

Covers:

- face/return normalization (group + uniform)
- negative cases (face `none`)
- forbidden instruction tokens
- task order + dependencies
- regression on existing conditional plan + face vinyl tests

## Runtime verification

**Existing locked order `ORD-1781684509-1` is NOT regenerated** (no DB write).

In-memory diagnostic:

```powershell
cd backend
.\.venv\Scripts\python.exe ..\tmp\runtime_verify_finish_assignments_IR-MQHZ41CM.py
```

Uses intake `product_spec_json` + order snapshot to simulate normalized quote_input and plan tasks without mutating `dev.db`.

**Safety after script:** `execution_reality=0`, `stock_movements=0`.

To apply on a **new** quote/order: re-price from intake (QuoteWizard handoff) so snapshot carries normalized `quote_input`, then generate execution plan.

## Intentionally NOT in scope

- SVG letter bounding boxes / 18 vs 27 letter geometry
- Real per-letter nesting (plexiglass/forex/face vinyl roll)
- `sheet_source_selection`, offcut inventory write, post-cut measurement tasks
- CostEngine formula changes, pricing, StockMovement, migrations
- Employee Mobile routing, PWA, payroll
- Frontend QuoteWizard prefill (backend normalization covers price/handoff/plan paths)

## Next steps (owner)

1. Re-price or create new order from `IR-MQHZ41CM` to persist normalized snapshot
2. Regenerate execution plan on that order
3. Optional follow-up: frontend `mapProductSpecToVolumetricQuotePrefill` for earlier wizard visibility
