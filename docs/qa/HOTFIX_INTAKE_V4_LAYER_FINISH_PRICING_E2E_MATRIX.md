# HOTFIX_INTAKE_V4_LAYER_FINISH_PRICING_E2E_MATRIX

## Bug report (owner)

Workspace `66412ccf-d088-490b-ba1b-e0e491178756` (IV4-F317489F): selecting Oracal 8500 on a second layer did not increase Material Breakdown vinyl cost — price stayed the same as a single finished layer.

## Root cause

Roll nesting path in material breakdown called `face_oracal_vinyl_areas_by_series()` with `total_area = roll_vinyl_area_sqm` (sum of **all** face roll jobs, including layers without Oracal finish). The function summed per-letter-group geometry, then **scaled** series buckets to that global roll total. Adding another Oracal layer changed group geometry but the scaled quantity stayed at the full roll aggregate (~0.9821 m² on this file), so `face_vinyl_8500` cost did not increase.

Geometry-only path (no roll nesting) was unaffected.

## Fix

1. `compute_roll_nesting_vinyl_area_by_layer()` — best roll area per `sourceLayerName`.
2. `face_oracal_vinyl_areas_by_series(..., roll_area_by_layer=...)` — attribute roll area per finished layer; **no global scale** when layer roll attribution is used.
3. Material breakdown passes per-layer roll map into owner Oracal face vinyl rows on the roll nesting path.

## Before / after (IV4-F317489F)

| Scenario | face_vinyl_8500 qty | face_vinyl_8500 cost |
|----------|---------------------|----------------------|
| Layer 2 only = 8500 (before) | 0.9821 | 19.64 EUR |
| Layer 2 only = 8500 (after) | 0.5062 | 10.12 EUR |
| Layer 2 + 3 = 8500 (before) | 0.9821 | 19.64 EUR |
| Layer 2 + 3 = 8500 (after) | 0.9821 | 19.64 EUR |

Second layer now increases quantity/cost when the first layer already had 8500 (0.5062 → 0.9821).

## E2E matrix tests

`backend/tests/test_intake_v4_layer_finish_pricing_matrix.py` — single/multi layer 641/651/8500, mixed series, remove/change finish, owner price guard.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_layer_finish_pricing_matrix.py tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_oracal_641_651_pricing.py -q
```

## Frontend

No change required — breakdown API reflects saved finish assignments; `finishSetupIdentityKey` already refetches breakdown after save when `workspace.updated_at` changes.

## Runtime smoke

Workspace restored to initial `letter_group_finishes` after matrix script.

## Boundary

No quote/order/tasks, ExecutionPlan, tasks_json, stock consumption, Pricing Registry rewrite, Color Registry rewrite, CostEngine changes, or employee assignment.
