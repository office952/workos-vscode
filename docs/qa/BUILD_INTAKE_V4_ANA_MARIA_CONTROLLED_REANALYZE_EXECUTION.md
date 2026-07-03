# BUILD — Intake V4 Ana Maria Controlled Re-analysis Execution

**Date:** 2026-06-24  
**Workspace:** `2aeda68b-09e0-46af-ba1e-31b0a47482d7`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base checkpoint:** `68e6117`

## Motiv

Snapshot-ul SVG persistat conținea orphan defs / `split_layer_1_*` din analiză veche, inflând `layout_occupied_area_sqm` la ~5.36 m² și declanșând review manual stale. Re-analiza controlată cu analyzer client fresh elimină geometria orphan fără a schimba politica de selected quantity sau oferta comercială.

## Endpoint / comandă

```
save_analysis_bundle_for_intake_v4_workspace
≡ PUT /api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle
```

**Script control:** `tmp/_controlled_ana_maria_reanalyze.py` (nu comis)  
**Fresh analyze:** `vite-node tmp/_export_pbl_happy.mts` pe `svg_source_text` persistat  
**Execuții:** o singură dată, `2026-06-24T09:58:48Z` stamp `20260624-095848`

## Before table

| Metric | Value |
|--------|-------|
| orphan_defs_split_placement_sqm | 2.3211 |
| split_layer_1_* count | 6 |
| placements count | 27 |
| eligible_face_area_sqm | 1.2638 |
| placement_footprint_face_sqm | 1.1469 |
| child_part_bbox_sum_sqm | 1.1469 |
| face_union_bbox_sqm | 1.4069 |
| layout_occupied_area_sqm | 5.36 |
| full_sheet_allocation_sqm | 6.0 |
| selected_quote_sheet_area_sqm | 1.2638 |
| selected_quote_sheet_area_source | eligible_area_floor |
| requires_manual_review | true |
| isAppliedToQuote | false |

**manual_review_reasons (before):** `face_layer_filled_area_missing`, `pseudo_layer_or_unlayered_complexity`, `stale_orphan_defs_split_placement`, `orphan_defs_parts_in_analysis`, `layoutOccupied/childPartBBox>1.75`

## After table

| Metric | Value |
|--------|-------|
| orphan_defs_split_placement_sqm | null |
| split_layer_1_* count | 0 |
| placements count | 21 |
| eligible_face_area_sqm | 1.2638 |
| placement_footprint_face_sqm | 1.1469 |
| child_part_bbox_sum_sqm | 1.1469 |
| face_union_bbox_sqm | 2.5238 |
| layout_occupied_area_sqm | 2.5238 |
| full_sheet_allocation_sqm | 6.0 |
| selected_quote_sheet_area_sqm | 1.2638 |
| selected_quote_sheet_area_source | eligible_area_floor |
| requires_manual_review | true |
| isAppliedToQuote | false |

**manual_review_reasons (after):** `candidateSpread=2.20>1.35`, `face_layer_filled_area_missing`, `pseudo_layer_or_unlayered_complexity`, `layoutOccupied/childPartBBox>1.75`

## Delta table

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| orphan_defs_split_placement_sqm | 2.3211 | null | eliminated |
| split_layer count | 6 | 0 | -6 |
| placements | 27 | 21 | -6 orphan placements |
| layout_occupied_area_sqm | 5.36 | 2.5238 | -2.84 (shelf truth aligned) |
| face_union_bbox_sqm | 1.4069 | 2.5238 | +1.12 (fresh shelf bbox) |
| selected_quote_sheet_area_sqm | 1.2638 | 1.2638 | **unchanged** |
| isAppliedToQuote | false | false | **unchanged** |

## Ce s-a curățat

- Orphan defs / `split_layer_1_*` parts și placements
- Tokeni `stale_orphan_defs_split_placement` și `orphan_defs_parts_in_analysis` din motive API
- Inflația layout shelf de la 5.36 → ~2.52 m²

## Ce a rămas warning

- `requires_manual_review=true` — spread metrici / pseudo-layer / layout vs child bbox
- Verificare operator recomandată pentru footprint manual Corel dacă e cazul

## Ce NU s-a schimbat

- CostEngine / Pricing Registry / Color Registry
- Quote / order / task creation
- ExecutionPlan / tasks_json writes
- Stock consumption
- `selected_quote_sheet_area_sqm` policy (`eligible_area_floor`)
- `is_applied_to_quote=false`

## Rollback evidence

- **Before snapshot:** `tmp/intake-v4-ana-maria-before-reanalyze-20260624-095848.json`
- **After snapshot:** `tmp/intake-v4-ana-maria-after-reanalyze-20260624-095848.json`
- **Backup checkpoint:** `C:\Users\offic\Desktop\salvari\workos-intake-v4-material-review-finalization-68e6117.zip`

## Tests

- Controlled script exit 0, blockers `[]`
- Regression: `backend/tests/test_intake_v4_ana_maria_reanalysis_regression.py`
- UI alignment: Phase 2 Vitest + Phase 4 regression

## Boundary

Re-analiza reală afectează doar `svg_analysis_json` + derived geometry în workspace payload. Nu este quote final integration.
