# BUILD_INTAKE_V4_OPERATOR_SHEET_FOOTPRINT_OVERRIDE_FOR_QUOTE_MATERIAL_REVIEW

## Purpose

Add a scoped **operator manual sheet footprint** candidate to Intake V4 material review so complex SVG layouts (e.g. Ana Maria) can record real Corel/layout measurements without forcing automatic nesting shelf or bbox heuristics into quote material quantities.

## Context

After `c67df28` (orphan split role propagation + sheet quote candidates), Ana Maria still under-estimates offerable sheet area when using automatic rules:

| Candidate | Ana Maria m² |
|-----------|--------------|
| eligible / current selected | 1.2638 |
| child_part_bbox_sum × 1.20 | 1.3760 |
| semantic_part_bbox_sum × 1.20 | 1.5164 |
| faceUnionBBox × 1.20 | 1.6883 |
| layoutOccupied auto shelf | 5.3600 |
| **owner manual Corel footprint** | **2.7627** |
| fullSheet 3000×2000 | 6.0000 |

**Conclusion:** no single automatic rule is safe as default for all jobs.

## Why SUM bbox × 20% failed (Ana Maria)

Semantic/placement bbox sums with waste still land ~45–54% below the operator’s measured Corel rectangle. Letter groups, emblem overlap, and non-rectangular semantics make a universal multiplier wrong.

## Why layoutOccupied 5.36 m² is not default

Auto shelf nesting occupies the full bin width/length for placement physics — useful for stock preview, not for “how much sheet did the operator actually quote in Corel.” Using it would over-estimate Ana Maria by ~94% vs owner manual.

## Why fullSheet 6.0 m² is separate

Full sheet allocation is stock/commercial policy (physical 3000×2000 mm), not quote material review truth.

## Override model

Persisted on workspace payload as `sheet_quote_override`:

```json
{
  "enabled": true,
  "source": "operator_manual_footprint",
  "widthCm": 192.67,
  "heightCm": 143.389,
  "areaSqm": 2.7627,
  "reason": "Manual Corel layout footprint measured by operator",
  "appliesTo": ["plexiglas_face", "forex_backing"],
  "useForQuoteEstimate": false,
  "createdBy": "operator",
  "createdAt": "..."
}
```

Override is **operator / material review** — not real stock consumption.

## API / UI changes

- **PUT** `/api/v1/intake-v4/workspaces/{workspace_id}/operator/sheet-footprint-override`
- Material breakdown `sheet_quote_material_candidates` extended with `operator_manual_footprint_sqm`, width/height cm, `operator_manual_use_for_quote_estimate`
- UI section **Footprint manual operator** on Material Breakdown (Review step) with live `widthCm × heightCm / 10_000` and candidate summary list

## Ana Maria example

`192.67 cm × 143.389 cm / 10_000 = 2.7627 m²`

## Selected quantity policy (chosen: safe default + explicit opt-in)

**Default:** override persisted and shown as candidate; `selected_quote_sheet_area_source = eligible_area_floor`; selected quantity unchanged.

**Opt-in:** operator checks *Folosește footprint manual pentru estimare material ofertabil* → `use_for_quote_estimate=true` → `selected = max(eligible, manual)` and internal material row qty raised for plexiglas_face / forex_backing only in breakdown preview — **not** CostEngine or final commercial quote.

## Tests

- `backend/tests/test_intake_v4_sheet_footprint_override.py` — area calc, candidates, selection policy, PBL unchanged, no ExecutionPlan/tasks_json mutation
- `backend/tests/test_intake_v4_nesting_material_precision.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `frontend/src/lib/intakeV4/intakeV4SheetFootprintOverride.test.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx`

## Ana Maria re-analyze (Task G)

Not forced on owner DB in this build. Fresh analyze after `c67df28` should exclude `split_layer_1_*` from nesting when defs/clipPath paths are filtered at parse time; orphan_defs should be null on fresh bundle. Re-run analysis bundle on Ana Maria workspace in dev when owner approves.

## Boundary (unchanged)

No Pricing Registry, Color Registry, CostEngine, QuoteWizard final pricing, quote/order/task creation, ExecutionPlan, tasks_json, stock consumption, LED/CNC/cant formulas, SVG parser major, V2/V3, Employee Mobile.

## Remaining decision

Wire `operator_manual_footprint` into **final commercial quote / CostEngine** only after explicit product policy — separate build with regression on PBL and Ana Maria.
