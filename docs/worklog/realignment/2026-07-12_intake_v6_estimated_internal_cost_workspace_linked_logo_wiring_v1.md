# Intake V6 — Estimated Internal Cost workspace linked logo wiring v1

**Task:** INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1  
**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT  
**Accepted HEAD before:** bcdd14d  
**Branch:** main  
**Compound folder:** `.compound-engineering/intake-v6-estimated-internal-cost-workspace-linked-logo-wiring-v1/`

## Owner decisions applied

- **DEC-EIC-03:** Artwork finish area usable only for artwork-owned logo materials (`print_media`, `laminate_media`). Not for plexiglas/cant/backing/LED/general logo geometry.
- **DEC-EIC-04:** V1 includes logo **material** internal cost from Cost BOM only. Logo **operation** internal cost explicitly deferred.

## Root gap

After bcdd14d, Cost BOM was workspace-aware but `EstimatedInternalCostService.build_preview` still built template-only ProductAggregate + local adapter BOM, producing letters-only material graph for workspace-linked logo segments.

## Selected architecture

```text
workspace_id
  → ProductDefinitionBuilderService.build_preview (existing)
  → AggregateCostBomBuilderService.build_preview (canonical BOM)
  → EstimatedInternalCostService (aggregate from bom.costable_materials + letters RULES_BY_TEMPLATE operations)
```

Template-only path: same builder with `workspace_id=None` — no parallel local PA/BOM construction in EIC.

## Orchestration

- Replaced `aggregate_svc.build` + `_bom_adapter.build` with `_bom_builder.build_preview(...)`.
- Injectable `bom_builder` for tests (`PatchedAggregateCostBomBuilder`).

## Cost BOM consumption

EIC reads: `costable_materials`, `bom_status`, `warnings`, component refs, source template, quantities from BOM row rates. Does not read bindings, recommendation, or expand linked templates.

## Logo material eligibility

Linked logo rows eligible when Cost BOM row has `TPL-VOLUMETRIC-LOGO_v1` source and namespaced `component_ref` (`comp_logo_face::logo-stanga`). Not filtered by letters-only `active_modules`.

## DEC-EIC-03 quantity boundary

- Print/laminate: segment artwork finish area from PD-enriched payload.
- Plexiglas/cant/backing/LED: no quantity invented; `INTERNAL_GEOMETRY_MISSING` when BOM row present without canonical qty path.

## Material cost semantics

One BOM material row → one EIC line. `logo-stanga` and `logo-dreapta` separate. Same material code on two segments not deduped. Missing rate → `INTERNAL_MATERIAL_COST_MISSING`, not zero.

## Partial semantics

`bom_status=partial` or finish-partial warning → EIC `status=partial`, no fabricated logo material lines, letter costs preserved. Contamination still forces `blocked`.

## Missing rate behavior

Canonical blockers preserved. No zero fallback, no commercial rate borrow.

## Provenance

Provenance entry `aggregate_cost_bom_builder_service`; namespaced component refs preserved on material lines.

## Operation debt

Logo operation internal cost **not included**. Letters operations via existing `RULES_BY_TEMPLATE` unchanged. No new operation dedupe.

## Commercial boundary

No markup, margin, VAT, CPP, Quote, Order, Execution. Read-only preview only.

## Tests

| Command | Result |
|---|---|
| `pytest tests/test_estimated_internal_cost_workspace_linked_logo.py tests/test_estimated_internal_cost_preview.py -q` | 32 passed |
| `pytest ... tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_product_aggregate_workspace_linked_logo_composition.py -q` | 59 passed |
| `pytest tests/test_product_definition_gradi_composition.py tests/test_intake_v6_layer_binding_persistence.py tests/test_selected_layer_refs_runtime_capture.py tests/test_return_cant_product_truth_bridge.py -q` | 34 passed |
| `pytest tests/test_estimated_internal_cost_preview.py tests/test_return_cant_pricing_registry_keys.py -q` | 19 passed |

## Runtime

`POST /api/v1/product-system/estimated-internal-cost-preview/TPL-VOLUMETRIC-LETTERS_v2` with `workspace_id` — 200, no DB writes, no commercial fields. Partial finish → `status=partial`, no logo material fabrication.

## Validation

Frontend/ProductDefinition/ProductAggregate/Cost BOM adapter/pricing/CPP/Quote/Order/Execution/DB: no staged changes.

## Review

APPROVED_WITH_DOCUMENTED_DEBT — bounded wiring complete; logo operations remain documented debt.

## Files changed

- `backend/services/estimated_internal_cost_service.py`
- `backend/tests/eic_patched_bom_builder.py` (new)
- `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py` (new)
- `backend/tests/test_estimated_internal_cost_preview.py`
- `.compound-engineering/intake-v6-estimated-internal-cost-workspace-linked-logo-wiring-v1/*`
- This worklog

## Forbidden scope

Not touched: aggregate_cost_bom_adapter, ProductAggregate, ProductDefinition, bindings, frontend, pricing registry, CPP, Quote, Order, Execution, DB schema, migrations, seeds, templates.

## Honest opinion

The change is the right minimal closure after bcdd14d: one orchestration swap plus logo row eligibility and DEC-EIC-03 quantity guard. Main residual risk is operators expecting logo CNC/print operation hours in EIC — those are correctly absent and must be a separate owner decision.

## Remaining debt

- Workspace-linked logo **operation** internal costs are not included in V1.
- Real-environment logo material lines may show blockers until inventory rates seeded (existing behavior).

## Next safe step

**INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1** — bounded mapping of workspace-linked logo operations from Cost BOM `costable_operations` into EIC with explicit owner GO. Do **not** jump to CommercialPriceProposal until that debt is closed or explicitly waived.

## Commit

Message: `Wire workspace Cost BOM into Estimated Internal Cost`

## Direction score

**92/100** — completes workspace-aware internal material cost chain without commercial activation or operation-scope creep.
