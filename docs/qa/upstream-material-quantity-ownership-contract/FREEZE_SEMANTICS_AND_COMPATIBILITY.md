# FREEZE_SEMANTICS_AND_COMPATIBILITY

## Freeze path

```text
ProductAggregateService.build[_for_workspace]
  → filter_aggregate_by_active_scope (compiled ActiveScope)
  → apply_planning_duration_resolution
  → apply_technical_material_requirements(merged_payload)  # NEW
  → QuoteSnapshotV2.product_aggregate_snapshot
  → OrderSnapshotV2 convert (verbatim copy)
  → Ops-graph project_frozen_technical_materials (RO)
```

## Rules

- Downstream reads frozen PA materials only.
- No live template / inventory / pricing lookup on ops-graph.
- No rematerialize / material_inputs / readiness persistence.
- No DB migration — JSON schema evolution on material rows.
- `92401` historical freeze **not** rewritten; projection maps missing status → `legacy_unspecified`.

## Compatibility

| Snapshot vintage | Behavior |
|------------------|----------|
| Pre-contract (qty null, no status) | `quantity_status=legacy_unspecified`, label „Nespecificată” |
| New freeze with Model A | `derived` + numeric qty |
| New freeze Model D | `reference_only` + null |
| New freeze unresolved formula | `source_missing` + null |

## What is not frozen as technical qty

- Inventory stock
- Pricing registry rates
- EIC heuristic quantities
- Operator-confirmed qty (Model C)
