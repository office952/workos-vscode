# Intake V6 — Aggregate Cost BOM workspace linked logo wiring v1

**Task:** INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1  
**Verdict:** PASS  
**Accepted HEAD before:** bee9757  
**Branch:** main  
**Compound folder:** `.compound-engineering/intake-v6-aggregate-cost-bom-workspace-linked-logo-wiring-v1/`

## Owner decisions applied

- **DEC-CBOM-ARCH-01:** Builder orchestration + bounded adapter activation (Option B/C hybrid).
- **DEC-CBOM-01:** Reuse existing `GET /api/v1/product-system/cost-bom-preview/{template_code}?workspace_id=`.
- **DEC-CBOM-02:** BOM mapping only; EstimatedInternalCost deferred.
- **DEC-CBOM-06 (GO):** Logo module eligibility derived exclusively from workspace-composed ProductAggregate rows. No binding/recommendation/payload reads in Cost BOM.

## Root gap

`AggregateCostBomBuilderService.build_preview` built workspace-aware ProductDefinition but always used template-only `ProductAggregateService.build()`. Logo segments from bee9757 never reached Cost BOM. Adapter additionally filtered logo rows as `module_inactive` because letters-only `active_modules` did not include logo template modules.

## Architecture

```text
workspace_id
  → ProductDefinitionBuilderService.build_preview
  → ProductAggregateService.build_for_workspace
  → AggregateCostBomAdapter.build
  → AggregateExpandedCostBom (read-only)
```

## Builder orchestration

When `workspace_id` present: `build_for_workspace(template, workspace_id)`. When absent: `build(template)` unchanged.

## Adapter changes

- Helpers: `_is_aggregate_linked_logo_{component,material,operation}`, `_aggregate_has_partial_linked_logo`.
- Linked logo rows active when present in aggregate with namespaced `component_ref`/`component_id` and `TPL-VOLUMETRIC-LOGO_v1` source template.
- Partial linked logo forces `bom_status=partial` (overrides blocked when finish partial).
- Warning propagation unchanged (`aggregate.warnings` merged).

## Logo activation

No second registry. Eligibility = row exists in composed ProductAggregate with namespaced segment ref + logo template code.

## Materials / operations

One PA row → one BOM row. Segment refs preserved. No geometry recalculation. No fabricated print/laminate when PA omitted them.

## Partial semantics

Binding confirmed + finish missing → logo components visible, no logo material/ops, `LINKED_SEGMENT_FINISH_PARTIAL` warning, `bom_status=partial`. Missing binding → letters-only unchanged.

## Provenance

`component_id`, `component_ref`, `source_template_code`, `provenance`, `mini_module_code` pass through on BOM rows.

## Pricing boundary

Technical BOM only. No commercial price, markup, VAT, CPP, Quote, Order, Execution changes.

## Tests

| Command | Result |
|---|---|
| `pytest tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_aggregate_cost_bom_adapter.py -q` | 46 passed |
| `pytest tests/test_product_aggregate_workspace_linked_logo_composition.py tests/test_intake_v6_layer_binding_persistence.py tests/test_product_definition_gradi_composition.py tests/test_selected_layer_refs_derivation.py tests/test_return_cant_product_truth_bridge.py -q` | 99 passed |

## Runtime evidence

| Scenario | Method | URL | HTTP | BOM status | Logo rows | Commercial price |
|---|---|---|---|---|---|---|
| Template-only | GET | `/api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS_v2` | 200 | partial/ready | none | NO |
| Letters-only workspace | GET | `...?workspace_id=` | 200 | — | none | NO |
| Two logo segments | GET | `...?workspace_id=` | 200 | — | stanga + dreapta | NO |
| Partial logo finish | GET | `...?workspace_id=` | 200 | partial | components only | NO |

Writes: NONE for all scenarios.

## Validation

- Frontend diff: none staged
- ProductDefinition diff: none
- ProductAggregate composition diff: none
- Pricing / Quote / Order / Execution: none
- DB / migration / seed: none

## Review

**APPROVED** — minimal wiring; PA canonical; no forbidden reads; partial semantics explicit.

## Files changed

- `backend/services/aggregate_cost_bom_adapter.py`
- `backend/tests/test_aggregate_cost_bom_adapter.py`
- `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` (new)
- `.compound-engineering/intake-v6-aggregate-cost-bom-workspace-linked-logo-wiring-v1/*`
- This worklog

## Forbidden scope

Not touched: frontend, ProductDefinition, PA composition, bindings, pricing registry, EIC, CPP, Quote, Order, Execution, DB schema, migrations, seeds, templates.

## Honest opinion

The fix is intentionally small: one orchestration branch plus aggregate-derived logo eligibility. The main risk was module filtering, not missing adapter architecture. EIC still uses template-only aggregate and should be a separate bounded task.

## Remaining debt

- `EstimatedInternalCostService.build_preview` still calls `aggregate_svc.build(template_code)` without workspace composition.
- Logo material rates may show `missing` until registry/inventory seeded — existing Step 7B behavior.

## Next safe step

Wire workspace-composed ProductAggregate into EstimatedInternalCost preview (read-only, same orchestration pattern). Do not proceed to CommercialPriceProposal without owner GO.

## Direction score

**90/100** — completes technical BOM chain after PA composition without pricing activation.
