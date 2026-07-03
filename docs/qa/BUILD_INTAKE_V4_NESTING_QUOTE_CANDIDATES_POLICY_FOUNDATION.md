# BUILD_INTAKE_V4_NESTING_QUOTE_CANDIDATES_POLICY_FOUNDATION

## Purpose

Establish a **sheet quote candidate policy preview** for Intake V4 material review: expose technical bbox/shelf metrics, a recommended auto candidate, manual-review flags, and selection preview — without changing final quote quantity, CostEngine, or stock.

## Context — why SUM semantic × 20% failed

Ana Maria experiments showed universal `SUM(bbox) × 20%` cannot reach owner manual Corel footprint (2.7627 m²):

| Rule | Ana Maria m² |
|------|----------------|
| eligible / selected floor | 1.2638 |
| child_part_bbox_sum × 1.20 | 1.3760 |
| semantic × 1.20 | 1.5164 |
| faceUnionBBox × 1.20 | 1.6883 |
| layoutOccupied (stale) | 5.3600 |
| owner manual Corel | 2.7627 |

## Why fresh childPartBBoxSum matters

External `svg-analyzer-vs` reported **childPartBBoxSumSqm ≈ 2.7132** on a fresh path. WorkOS fresh analyze on `ana-maria-gradinita-fara-layere.svg` (after `c67df28` orphan fix) gives:

| Metric | Fresh WorkOS | Persisted Ana Maria workspace |
|--------|--------------|-------------------------------|
| eligibleAreaSqm | 1.2638 | 1.2638 |
| childPartBBoxSumSqm (face child) | 1.1469 | placement face 1.1469 |
| designSpaceUnionBBoxSqm | 2.1839 | — |
| faceUnionBBoxSqm (shelf) | 2.5238 | 1.4069 (stale nesting) |
| layoutOccupied | 2.5238 | **5.3600** (stale orphans) |
| orphan_defs | 0 | **2.3211 m²** (6× split_layer_1_*) |

**Root cause of 1.2638 vs ~2.71 gap:**

1. **Stale persisted snapshot** — workspace `2aeda68b…` still has pre-fix analysis with orphan `split_layer_1_*` parts inflating shelf to 5.36 m² while face placement stays 1.1469 m².
2. **Metric definition** — WorkOS `childPartBBoxSumSqm` is **face-role child part bbox sum** (1.1469 fresh), not all-production-child sum (layered file all-child ≈ 2.82 m²).
3. **Closer fresh proxies to owner manual** — design-space union (2.18 m²), shelf face union (2.52 m²); not SUM×20%.

Re-analyze workspace was **not forced** on owner DB in this build.

## New candidates (API)

Extended `sheet_quote_material_candidates` with:

- `child_part_bbox_sum_sqm`, `semantic_group_bbox_sum_sqm`
- `design_space_union_bbox_sqm`, `design_space_union_bbox_with_buffer_sqm`
- `nesting_shelf_occupied_sqm` (alias of layout occupied)
- `recommended_auto_candidate` (source, area_sqm, buffer_percent, confidence, reason)
- `requires_manual_review`, `manual_review_reason`
- `operator_override` preview (from existing `sheet_quote_override` when present)
- `selection` preview (`selected_source`, `final_area_sqm`, `selection_mode`, `is_applied_to_quote=false`)

Backward-compatible legacy fields retained.

## Recommended auto candidate

```
areaSqm = max(eligibleAreaSqm, childPartBBoxSumSqm × (1 + bufferPercent/100))
bufferPercent default = 5 (not 20% universal)
confidence from candidateSpread among eligible, child, faceUnion, designUnion
```

## Manual review rules

`requires_manual_review=true` when:

- candidateSpread > 1.35
- stale orphan_defs placement or orphan parts in analysis
- layoutOccupied / childPartBBox > 1.75
- pseudo-layer / unlayered complexity
- operator manual Corel measurement present

## Selected quantity

**Unchanged:** `selected_source = eligible_area_floor`, `is_applied_to_quote = false`.

## Ana Maria numbers

| | Fresh fara-layere | Persisted workspace |
|--|-------------------|---------------------|
| eligible | 1.2638 | 1.2638 |
| childPartBBoxSum | 1.1469 | 1.1469 (placement) |
| recommendedAuto (5%) | 1.2638 | 1.2638 |
| designSpaceUnion | 2.1839 | — |
| faceUnionBBox | 2.5238 | 1.4069 |
| layoutOccupied | 2.5238 | 5.3600 |
| requiresManualReview | yes (spread) | yes (orphans + shelf) |

## PBL numbers (fresh `pbl-layere.svg`)

| Metric | Value |
|--------|-------|
| eligible | 0.6907 |
| childPartBBoxSum | 0.5834 |
| designSpaceUnion | 1.6607 |
| faceUnionBBox | 1.1577 |
| orphan_defs | null |
| 3 Corel layers, 2 face + 1 artwork | confirmed |

## Tests

- `backend/tests/test_intake_v4_sheet_quote_candidate_policy.py`
- `backend/tests/test_intake_v4_nesting_material_precision.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `frontend/.../IntakeV4MaterialBreakdownPanel.test.tsx`
- `frontend/.../sheetQuoteCandidateFreshAudit.test.ts` (Phase 1 audit harness)

## Next builds

1. Re-analyze Ana Maria workspace after owner approval (clear stale orphans).
2. Persistent operator override integration with policy selection toggle.
3. Final quote / CostEngine integration only after explicit commercial policy.
4. Full sheet / fraction stock policy (separate from review preview).

## Boundary

No Pricing Registry, Color Registry, CostEngine, quote/order/tasks, ExecutionPlan, tasks_json, stock consumption.
