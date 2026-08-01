# MATERIAL_REQUIREMENT_CONTRACT

**Version:** `technical_material_requirement/v1`  
**Freeze authority:** Quote Snapshot V2 → Order Snapshot V2 (`product_aggregate_snapshot.materials[]`)  
**Downstream:** Ops-graph projection `ops_graph_frozen_technical_materials/v2` (read-only)

## Canonical fields (ProductAggregateMaterial)

| Field | Role |
|-------|------|
| `requirement_id` | Stable identity: `template\|component_ref\|material_code\|provenance\|variant` |
| `material_code` | Technical identity |
| `label` / `unit` | Display + canonical unit from template/catalog |
| `component_ref` / `provenance` / `source_template_code` / `mini_module_code` | Provenance |
| `formula_id` / `formula_params` | Component-owned formula + gate metadata |
| `quantity` | Nullable float — never invent; never null→0 |
| `quantity_status` | `derived` · `reference_only` · `source_missing` · `legacy_unspecified` |
| `quantity_model` | `A` · `B` · `D` (E rejected) |
| `variant_discriminator` | Active gate summary (e.g. `return_depth_mm=60`) |
| `quantity_formula_id` | Formula used at freeze |
| `quantity_input_keys` | Input keys / missing keys |
| `owner_scope` | `component_parent` / `component_linked_module` / `component` |

## Quantity status semantics

| Status | Meaning |
|--------|---------|
| `derived` | Model A evaluated successfully from owned inputs |
| `reference_only` | Model D — formula-less; qty null expected |
| `source_missing` | Formula declared but unresolved / unregistered / missing input |
| `legacy_unspecified` | Frozen before contract; qty null without metadata |

## Alternatives considered

| Option | Verdict |
|--------|---------|
| Parallel DTO outside ProductAggregate | Rejected — second contract risk |
| Reuse EIC `_estimate_material_quantity` | Rejected — heuristic / inventory-adjacent |
| Inventory-derived qty (Model E) | Rejected |
| Operator confirmation (Model C) | Out of scope this build |
| Composition-only qty (Model B) | Analyzed, not implemented — no exclusive composition-only case proven |

## Chosen path

Extend `ProductAggregateMaterial` + apply at freeze in `build_frozen_component_scope` via `apply_technical_material_requirements`. Downstream projects allowlisted fields only.
