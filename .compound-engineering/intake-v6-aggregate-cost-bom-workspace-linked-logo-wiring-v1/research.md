# INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** bee9757  
**Verdict:** READY_FOR_BOUNDED_IMPLEMENTATION

## Repository preflight

| Check | Result |
|---|---|
| Branch | `main` |
| HEAD | `bee9757` — Compose workspace-linked logo ProductAggregate |
| A. Accepted committed state | Prior tasks committed: binding persistence (`9d18806`), PA workspace composition (`bee9757`) |
| B. Unrelated dirty files | `.gitignore`, ProductSystem QA screenshots/worklogs, `IntakeV6LayersOperatorPanel.tsx`, capture scripts, QA folders, `config.local.example.yaml` |
| C. ProductAggregate files | `backend/services/product_aggregate_service.py`, `backend/services/product_aggregate_workspace_composition_service.py`, `backend/routers/product_system_aggregate.py`, `backend/tests/test_product_aggregate_workspace_linked_logo_composition.py` |
| D. Cost BOM files | `backend/services/aggregate_cost_bom_adapter.py`, `backend/routers/product_system_cost_bom_preview.py`, `backend/tests/test_aggregate_cost_bom_adapter.py`, `backend/schemas/aggregate_cost_bom.py` |
| E. Internal cost consumers | `backend/services/estimated_internal_cost_service.py`, `backend/routers/estimated_internal_cost.py`, `backend/tests/test_estimated_internal_cost_preview.py` |
| F. Commercial pricing consumers | `backend/services/aggregate_cost_bom_price_bridge.py`, `backend/services/commercial_price_proposal_service.py`, `backend/services/quote_orchestrator.py`, `backend/routers/quotes.py`, `backend/services/quote_snapshot_v2_service.py` |
| G. Unexpected changes | None on accepted HEAD; dirty tree is unrelated UI/QA only |

## Architecture readback

```text
Intake V6 workspace
  → ProductDefinitionBuilderService.build_preview(ROOT, workspace_id)
       ├─ letters technical truth (canonical values, modules, linked_template_runtime_segments)
       └─ linked segment readiness (from PD compiler — not binding re-read)
  → ProductAggregateService.build_for_workspace(ROOT, workspace_id)
       └─ workspace-composed ProductAggregate (letters + namespaced logo segments)
  → AggregateCostBomBuilderService.build_preview(ROOT, workspace_id)   ← GAP TODAY
       └─ AggregateCostBomAdapter.build(pd, aggregate, …)
  → AggregateExpandedCostBom (technical BOM preview)
  → [optional, separate slice] EstimatedInternalCostService
  → [forbidden] CommercialPriceProposal / Quote / Order / Execution
```

Confirmed:

| Assertion | Status |
|---|---|
| ProductDefinition compiles technical truth | YES |
| ProductAggregate expands technical graph | YES (bee9757) |
| Cost BOM should consume ProductAggregate | YES — adapter already accepts PA object |
| Cost BOM does not compile product composition | YES today — must stay YES |
| Cost BOM does not own layer bindings | YES — must stay YES |
| Cost BOM does not read recommendations | YES today — must stay YES |
| Cost BOM is not commercial pricing | YES — read-only BOM schema |
| CommercialPriceProposal remains separate | YES — different service/bridge |
| Quote/Order snapshots outside task | YES |
| Execution outside task | YES |
| Internal hours for analysis/cost only | YES — EIC uses internal rules, not commercial hourly |

## Source inventory

| File/function | Responsibility | Input | Output | Recompiles truth? | Pricing-coupled? | Risk |
|---|---|---|---|---:|---:|---|
| `ProductAggregateService.build_for_workspace` | Workspace PA orchestration | template + workspace_id | composed PA | NO (calls PD once) | NO | LOW |
| `compose_from_product_definition` | Merge letters PA + logo segments | PD + letters PA + logo PAs | composed graph | NO | NO | LOW — canonical PA source |
| `ProductAggregateService.build` | Template-only PA | template_code | letters-only PA | NO | NO | MED — builder still uses this |
| `get_product_aggregate` | Public PA API | template + optional workspace_id | PA | NO | NO | DONE |
| `AggregateCostBomBuilderService.build_preview` | PD+PA orchestration for BOM | template + workspace_id | `AggregateExpandedCostBom` | **PARTIAL** — PD workspace-aware, PA template-only | NO | **HIGH GAP** |
| `AggregateCostBomAdapter.build` | Map PA→BOM rows | PD + PA + rates | cost BOM | NO | NO (rates are inventory/WC lookup only) | MED — module filter excludes logo |
| `get_cost_bom_preview` | Public read-only endpoint | template + workspace_id | BOM JSON | NO | NO | LOW — endpoint exists |
| `EstimatedInternalCostService.build_preview` | Internal cost from BOM | template + workspace_id | EIC preview | **PARTIAL** — same PA gap | NO direct commercial | OUT OF SCOPE v1 |
| `aggregate_cost_bom_price_bridge` | Commercial price path | BOM + markup rules | offer price | NO | **YES** | FORBIDDEN |
| `CommercialPriceProposalService` | Client offer preview | internal + commercial rules | proposal | NO | **YES** | FORBIDDEN |
| `build_intake_v4_material_breakdown` | Legacy intake breakdown | payload | material rows | YES (parallel path) | partial | NOT canonical for this slice |

## Current Cost BOM contract

### Adapter input (`AggregateCostBomAdapter.build`)

| Input | Used? | Notes |
|---|---|---|
| `ProductDefinitionPreview` | YES | `active_modules`, `canonical_values`, `source_context`, warnings |
| `ProductAggregate` | YES | `components`, `materials`, `operations`, `warnings`, provenance |
| `quote_input` | optional | Merged into geometry/finish resolution |
| `material_rates` / `workcenter_rates` | YES | Inventory/admin lookup — not commercial markup |
| `template_code` alone | NO direct | Comes via PD/PA |
| Layer bindings | **NO** | Correct |
| Composition recommendation | **NO** | Correct |
| DB writes | **NO** | Correct |

### Contract Q&A

| # | Question | Answer |
|---|---|---|
| 1 | Accepts existing ProductAggregate object? | **YES** — `aggregate: ProductAggregate` parameter |
| 2 | Rebuilds ProductAggregate internally? | **NO** in adapter; **YES in builder** (template-only `build()`) |
| 3 | Reads only `template_code`? | Builder uses workspace for PD only; aggregate ignores workspace today |
| 4 | Supports `workspace_id`? | Endpoint + builder accept it; aggregate path does not |
| 5 | Preserves namespaced component ids? | Pass-through on rows; module filter may drop them |
| 6 | Preserves `logo-stanga` / `logo-dreapta`? | Only if aggregate contains them (builder gap) |
| 7 | Supports partial components? | PA emits `status=partial`; adapter does not check status — may omit component via module filter |
| 8 | Fabricates zero-cost rows for missing values? | NO — `pricing_availability=missing`, notes forbid silent zero |
| 9 | Distinguishes definition vs consumption? | Maps aggregate material rows; quantities resolved via geometry keys, not second geometry engine |
| 10 | Calculates commercial total? | NO |
| 11 | Reads recommendation/binding directly? | NO |
| 12 | Mutates state? | NO |

### Contract gap table

| Contract area | Current behavior | Required behavior | Gap |
|---|---|---|---|
| Aggregate source | `aggregate_svc.build(template_code)` always | `build_for_workspace` when `workspace_id` set | **BUILDER** |
| Logo material activation | `mini_module_code in active_modules` (letters modules only) | Logo linked rows active when present in composed PA | **ADAPTER** |
| Logo component visibility | Skipped if module not in letters `active_modules` | Namespaced partial/complete logo components visible | **ADAPTER** |
| Partial finish | PA omits logo materials/ops + warning | BOM partial; no fabricated print/laminate | Mostly OK once aggregate wired |
| Warning propagation | `aggregate.warnings` copied to BOM warnings | Include `LINKED_SEGMENT_FINISH_PARTIAL`, composition applied | OK |
| BOM status | `_resolve_bom_status` partial/blocked/ready | Partial when logo partial or geometry missing | OK with existing vocabulary |
| Provenance | `component_ref`, `source_template_code`, `provenance` on rows | Segment traceability | OK if rows not filtered out |
| Endpoint | `GET /cost-bom-preview/{template}?workspace_id=` | Same | **NO API CHANGE** |

## Workspace-composed aggregate input (evidence)

Fixture chain: `test_product_aggregate_workspace_linked_logo_composition.py` + gradi workspace payloads.

| Aggregate row | Owner | Segment | Qty | Complete/partial | Cost BOM expected behavior |
|---|---|---|---:|---|---|
| Letter dossier components | LETTERS_v2 | — | 1 assembly | complete (when finish ok) | Unchanged letters BOM rows |
| `comp_logo_face::logo-stanga` | LOGO_v1 | logo-stanga | 1 | complete w/ finish | Costable component + segment materials/ops |
| `comp_logo_face::logo-dreapta` | LOGO_v1 | logo-dreapta | 1 | complete w/ finish | Distinct rows from stanga |
| Logo materials (print/laminate) | LOGO_v1 | per segment | formula | complete | Separate `component_ref`; no merge |
| Partial logo structure | LOGO_v1 | segment | 1 | partial (finish missing) | Component visible; **no** logo material/ops rows |
| Missing binding | — | — | — | letters-only | Identical to template aggregate |
| Same template twice | LOGO_v1 | both segments | 1 each | complete | Two instances, not qty=2 on one row |
| Task rules `linked_segment:*` | composed | segment | — | informational | Not auto-cost rows |

Mandatory states covered by PA tests (bee9757):

- letters only ✓
- one/two bound logos ✓
- same template twice ✓
- binding missing ✓
- finish missing ✓
- distinct segment geometry refs ✓

## Duplicate truth audit (initial)

| Concept | Source A | Source B | Canonical source | Double-count risk | Plan |
|---|---|---|---|---:|---|
| Print vinyl qty | PA aggregate row per segment | Cost BOM geometry resolution | PA row identity; BOM maps once | MED if adapter merges segments | Preserve separate `component_ref` |
| Laminate qty | PA per segment | Cost BOM | PA | MED | Same |
| Face material (letters) | PA letters dossier | Cost BOM | PA | LOW | Unchanged |
| Return/cant | PA letters + logo modules | Cost BOM | PA per `component_ref` | MED | No cross-segment dedupe |
| LED/PSU | PA module rows | EIC rules (separate) | PA for BOM listing | MED | Out of EIC scope v1 |
| CNC/print/laminate ops | PA operations | Cost BOM costable_operations | PA | MED if shared op duplicated in PA | PA `_dedupe_operations` already runs |
| Material definitions | Template dossier | PA expansion | Template → PA | LOW | Adapter does not re-expand |
| Commercial price | price bridge | Quote orchestrator | Neither | N/A | Forbidden |
| Binding truth | layer_bindings[] | — | bindings (already persisted) | N/A | Adapter must not read |

**Quantity owner:** ProductAggregate (via template formulas at composition time).  
**Rate owner:** Cost BOM adapter (inventory material rates + workcenter rates lookup).

## Pricing boundary proof

| Layer | Input | Output | In scope? |
|---|---|---|---:|
| Technical BOM | composed PA + PD | costable rows, skipped items, warnings | **YES** |
| Internal cost preview | BOM + internal rules | internal estimate lines | **NO (deferred)** |
| Commercial pricing | BOM bridge + markup | client price | **NO** |
| Quote/Order | frozen commercial | documents | **NO** |

`AggregateCostBomAdapter` and `AggregateCostBomBuilderService` do not import `aggregate_cost_bom_price_bridge` or `CommercialPriceProposalService`.

## Central question answer

**Can the existing Cost BOM adapter consume the workspace-composed ProductAggregate as the single technical BOM source, while keeping commercial pricing fully outside this slice?**

**YES — with bounded wiring:**

1. Builder must pass workspace-composed aggregate (one orchestration change).
2. Adapter must extend module-activation rules for linked-logo rows already present in aggregate (no binding read, no PA rebuild).
3. Partial semantics already encoded in PA output; adapter must not treat missing logo rows as complete.

**Verdict:** `READY_FOR_BOUNDED_IMPLEMENTATION`

Not blocked by pricing coupling, duplicate BOM truth (if dedupe rules followed), or missing evidence.
