# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** bcdd14d  
**Verdict:** READY_FOR_BOUNDED_IMPLEMENTATION

## Repository preflight

| Check | Result |
|---|---|
| Branch | `main` |
| HEAD | `bcdd14d` — Wire workspace ProductAggregate into Cost BOM |
| A. Accepted committed state | Cost BOM workspace wiring committed; PA composition at bee9757 |
| B. Unrelated dirty files | `.gitignore`, ProductSystem QA screenshots/worklogs, `IntakeV6LayersOperatorPanel.tsx`, capture scripts |
| C. EstimatedInternalCost files | `backend/services/estimated_internal_cost_service.py`, `backend/routers/estimated_internal_cost.py`, `backend/schemas/estimated_internal_cost.py`, `backend/tests/test_estimated_internal_cost_preview.py`, `backend/data/internal_cost_rules_volumetric_v2.py` |
| D. Cost BOM files | `backend/services/aggregate_cost_bom_adapter.py` (`AggregateCostBomBuilderService`, `AggregateCostBomAdapter`), `backend/routers/product_system_cost_bom_preview.py`, `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` |
| E. ProductAggregate files | `backend/services/product_aggregate_service.py`, `backend/services/product_aggregate_workspace_composition_service.py` (upstream, unchanged) |
| F. CommercialPriceProposal consumers | `commercial_price_proposal_service.py`, `aggregate_cost_bom_price_bridge.py`, `quote_snapshot_v2_service.py`, `quotes.py` — not imported by EIC |
| G. Unexpected modifications | None on accepted HEAD |

## Architecture readback

```text
Intake workspace
  → ProductDefinition (compiler)
  → workspace ProductAggregate (bee9757)
  → workspace-aware Cost BOM (bcdd14d)
  → EstimatedInternalCost (GAP)
  → [future] CommercialPriceProposal
```

Confirmed:

| Assertion | Status |
|---|---|
| ProductDefinition compiles technical truth | YES |
| ProductAggregate owns technical graph | YES |
| Cost BOM owns mapped costable rows | YES (bcdd14d) |
| EIC consumes internal-cost inputs | YES — from Cost BOM materials + internal rules |
| EIC must not compile PD / read bindings / read recommendation | Required |
| CPP separate | YES — EIC notes forbid price bridge |
| Quote/Order outside task | YES |
| Commercial hourly forbidden | YES — `scan_hourly_contamination`, capacity_hints excluded from totals |

## Source inventory

| File/function | Responsibility | Input | Output | Rebuilds truth? | Commercially coupled? | Risk |
|---|---|---|---|---:|---:|---|
| `EstimatedInternalCostService.build_preview` | EIC orchestration | template + workspace_id + quote_input | `EstimatedInternalCostPreview` | **YES today** (template PA) | NO | **HIGH** |
| `AggregateCostBomBuilderService.build_preview` | Workspace Cost BOM | template + workspace_id | `AggregateExpandedCostBom` | NO (delegates) | NO | LOW — reuse target |
| `AggregateCostBomAdapter.build` | BOM mapping | PD + PA | costable rows | NO | NO | bcdd14d wired |
| `_estimate_material_quantity` | Material qty for EIC lines | BOM mat row + payload | quantity | NO | NO | **MED** — letters geometry only |
| `_operation_rule_applies` + `RULES_BY_TEMPLATE` | Operation internal lines | payload + active_modules | operation lines | NO | NO | **MED** — letters modules only |
| `ProductAggregateService.build_for_workspace` | Workspace PA | template + workspace_id | composed PA | NO | NO | upstream |
| `CommercialPriceProposalService` | Client offer | separate path | proposal | — | YES | FORBIDDEN |

## Current EIC contract Q&A

| # | Question | Answer |
|---|---|---|
| 1 | Accepts existing Cost BOM? | **Indirectly** — calls `AggregateCostBomAdapter.build`, not builder |
| 2 | Rebuilds ProductAggregate? | **YES** — always `aggregate_svc.build(template_code)` |
| 3 | Template-only aggregate? | **YES** at line ~462 |
| 4 | Accepts workspace_id? | **YES** on PD path; aggregate/BOM ignore it |
| 5 | Preserves namespaced component ids? | **Only if BOM contains them** — currently no |
| 6 | Preserves source_template_code? | Via BOM mat lines when present |
| 7 | Segment provenance? | `component_code=mat.component_ref` on material lines |
| 8 | Material vs operation distinction? | YES — separate line lists |
| 9 | Supports partial Cost BOM? | **NO explicit** — status from blockers/completeness only |
| 10 | Treats missing rates as zero? | **NO** — `INTERNAL_MATERIAL_COST_MISSING` blocker |
| 11 | Blocks/warns on missing rates? | YES — blockers |
| 12 | Commercial amount? | **NO** |
| 13 | Imports CPP / price bridge? | **NO** (note in code only) |
| 14 | Mutates state? | **NO** |

## Orchestration gap (proven)

| Step | Current call | Workspace-aware? | Result | Gap |
|---|---|---|---|---|
| 1 PD | `pd_builder.build_preview(code, workspace_id=…)` | YES | workspace PD | OK |
| 2 PA | `aggregate_svc.build(template_code)` | **NO** | letters-only PA | **GAP-1** |
| 3 BOM | `_bom_adapter.build(pd, aggregate, …)` | **NO** | letters-only BOM | **GAP-2** (duplicate of pre-bcdd14d Cost BOM) |
| 4 Materials | loop `bom.costable_materials` | — | letters materials | logo rows absent |
| 4b Filter | `mini_module_code not in active_modules` | — | skips logo modules | **GAP-3** (even if BOM fixed) |
| 5 Operations | `rules["operations"]` + `active_modules` | letters only | no logo op lines | **GAP-4** (documented debt) |
| 6 Qty | `_estimate_material_quantity` | letter geometry | wrong/missing for logo m² | **GAP-5** (bounded extension) |

Evidence:

```459:480:backend/services/estimated_internal_cost_service.py
        pd = await self._pd_builder.build_preview(template_code, workspace_id=workspace_id)
        ...
        aggregate = await self._aggregate_svc.build(template_code)
        ...
        bom = self._bom_adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            ...
        )
```

Cost BOM builder (bcdd14d) already correct:

```1285:1288:backend/services/aggregate_cost_bom_adapter.py
        if workspace_id:
            aggregate = await aggregate_svc.build_for_workspace(template_code, workspace_id)
        else:
            aggregate = await aggregate_svc.build(template_code)
```

## Central question answer

**Can EstimatedInternalCost consume the workspace-aware ProductAggregate / Cost BOM chain without a second costing graph or commercial coupling?**

**YES — with bounded wiring:**

1. Delegate BOM to `AggregateCostBomBuilderService.build_preview` (canonical upstream from bcdd14d).
2. Extend EIC material eligibility for linked-logo BOM rows (same PA-derived rule as Cost BOM — via BOM row shape, not binding reads).
3. Propagate partial BOM / finish-partial warnings into EIC status.
4. Bounded segment quantity resolution for logo material lines (payload `artwork_finishes` / geometry keyed by segment suffix in `component_ref`).

**Not blocked** by commercial coupling or missing evidence. Operation internal lines for logo remain **documented v1 debt** (EIC uses letters `RULES_BY_TEMPLATE` for operations, not `bom.costable_operations`).

**Verdict:** `READY_FOR_BOUNDED_IMPLEMENTATION`

## Duplicate truth audit (initial)

| Concept | Owner A | Owner B | Canonical | Double-count risk | Plan |
|---|---|---|---|---:|---|
| Material rows | Cost BOM | EIC material loop | Cost BOM | LOW if EIC reads BOM once | Delegate to builder |
| Material quantity | EIC `_estimate_material_quantity` | — | EIC (from payload) | MED for logo segments | Segment-aware qty helper |
| Material rate | inventory / BOM `unit_cost` | — | inventory | LOW | unchanged |
| Operation lines (letters) | internal rules | — | rules | LOW | unchanged |
| Operation lines (logo) | bom.costable_operations (unused) | rules (missing) | **undefined v1** | MED | document debt; optional v2 |
| Commercial price | CPP / bridge | — | CPP | N/A | forbidden |

## Pricing boundary

EIC service explicitly excludes CostEngine, QuoteOrchestrator, price bridge. No CPP import in `estimated_internal_cost_service.py`.
