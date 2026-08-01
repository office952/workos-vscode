# Source-to-UI Contract — Frozen Technical Materials (Ops-Graph)

## Trace

```text
orders.snapshot_v2_json
  └─ product_aggregate_snapshot.materials[]   (frozen technical truth)
       ↓ read-only projection (allowlisted fields only)
services/ops_graph_frozen_technical_materials.py
       ↓ attached on GET /api/v1/execution/plan/{order_id}
plan.frozen_technical_materials
       ↓ frontend mapping
OpsGraphFrozenTechnicalMaterials (order/plan-level section)
```

## Allowlisted entry fields

`entry_index`, `material_code`, `label`, `unit`, `quantity` (null preserved), `provenance`, `component_ref`, `source_template_code`

## Explicitly excluded

Pricing/EIC/CPP · unit_cost · inventory · reservation · consumption · live Intake · live Product System · task `material_inputs` mutation · envelope `material_readiness_inputs` persist

## Semantics

| UI | Meaning |
|----|---------|
| Title | Materiale tehnice conform comenzii |
| Note | Frozen technical definition — not stock/reservation/consumption |
| Cantitate null | **Nespecificată** (never `0`) |
| Order of rows | Snapshot list order (deterministic; no code-sort merge) |
| Duplicates | Preserved; warning listed in projection |

## Placement

Variant B — compact order-level summary between metrics and task table; list expands on demand. Not per-operation (no material→task mapping).
