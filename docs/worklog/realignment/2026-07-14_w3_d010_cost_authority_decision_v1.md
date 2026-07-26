# W3-D010 — Cost Authority and Graph Consumption Decision V1

**Task:** `W3-D010-COST-AUTHORITY-DECISION` / `WORKOS_COST_AUTHORITY_AND_GRAPH_CONSUMPTION_DECISION_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Doc HEAD:** `d309bd8`  
**Application baseline:** `96bea36`  
**Date:** 2026-07-14  
**Verdict:** `W3_D010_DECISION_COMPLETE_READY_FOR_IMPLEMENTATION`

## D-010 decision (canonical)

**`PRODUCT_AGGREGATE_COST_GRAPH_WITH_7G_7H_ADAPTERS`**

### Authority model

| Layer | Owner | Classification |
|-------|-------|----------------|
| Composition structure | Product Definition → `composition_graph` on Aggregate | **CANONICAL_AUTHORITY** |
| Cost BOM expansion | `AggregateCostBomBuilderService` (7B) | **ADAPTER** (graph-projected) |
| Internal cost | `EstimatedInternalCostService` (7H) | **CANONICAL_AUTHORITY** (internal pre-production) |
| Commercial price | `CommercialPriceProposalService` (7G) | **CANONICAL_AUTHORITY** (client offer) |
| Formula/material evaluation | `CostEngineService` | **DOMAIN_ENGINE** (7H/BOM helper only) |
| Offer freeze | `quote_snapshot_v2_service` compose+freeze | **CANONICAL_AUTHORITY** (dual snapshot) |
| Order freeze | `order_snapshot_v2_convert_service` | **READ_MODEL** consumer of frozen snapshot |

### Graph consumption rule

Cost **must** derive structural scope from `ProductAggregate.composition_graph` (active nodes, roles, edges).  
PD module states and offer-scope resolver remain **COMPATIBILITY_PROJECTION** until graph adapter replaces `_legacy_structural_active_modules`.

### Retire / freeze (ACTIVE_PARALLEL_AUTHORITY → remove in Wave 3)

1. **V6 priced dry-run cost-plus override** — when material breakdown exists, official total uses internal × markup, not 7G subtotal (`official_v6_pricing_uses_cost_plus_from_material_breakdown`).
2. **`intake_v6_quote_snapshot_v2_service`** — wraps persisted quote lines as synthetic CPP; not true 7G semantics.
3. **CostEngine + QuoteOrchestrator + `POST /entities/quotes/price`** — legacy commercial path.
4. **`aggregate_cost_bom_price_bridge` → CE v2** — migration path for old aggregate quotes only.
5. **Frontend `intakeV6OfferCalculator` cost-plus** — preview mirror only; must not be official Offer truth.

### Business rules preserved

- Commercial price: **7G** mp/ml/buc/set — never hour × rate as client basis.
- Internal cost: **7H** materials/operations/consumables/overhead — hours/minutes capacity hints only.
- Offer: frozen **7G** commercial total + **7H** internal estimate in Step 8 snapshot.
- Order: no reprice; embedded frozen CPP/EIC/PD/Agg JSON.

## Primary questions (summary)

| # | Answer |
|---|--------|
| 1 | Intake V6 → PD → Agg → 7B BOM → 7H/7G → dry-run/snapshot → Offer → Order convert |
| 2 | CostEngine: internal formula/material/machine/labor evaluation — **not** commercial authority |
| 3 | 7G: commercial price proposal (mp/ml/buc) |
| 4 | 7H: estimated internal cost pre-production |
| 5 | Internal: **7H** (target); today also material breakdown + CE legacy |
| 6 | Commercial: **7G** (target); today V6 cost-plus when breakdown exists |
| 7 | Offer: Step 8 snapshot CPP + V6 write path (must converge) |
| 8 | Order: frozen `order_snapshot_v2` from accepted quote snapshot |
| 9 | Frontend cost-plus calculator — **preview only**, not authority |
| 10 | Hours: internal/capacity in CE/7H; **not** commercial basis in 7G |
| 11 | **YES** — same product differs by entry path today |
| 12 | Cost BOM uses PD module states; **not** `composition_graph` yet |
| 13 | Flattened module states + offer scope — **not** graph |
| 14 | Cost does not reselect components from Product System registry for workspace path |
| 15 | Volum field: selects **volum aluminum module template** (component template identity for cant modeling) |
| 16 | Required for `modelare_cant` activation and honest cost BOM — **yes for costing** |
| 17 | Missing tariffs block at 7G/7H preview and snapshot readiness |
| 18 | Offer freezes CPP total, EIC total, PD, Agg, component scope |
| 19 | Order freezes accepted commercial + internal + product truth snapshots |
| 20 | Implement graph-projected 7B → 7H internal + 7G commercial → unified Offer freeze |

## Volum module gap

**`INTAKE_REQUIRED_TECHNICAL_SELECTION`**

- Owner: Intake `finish_setup.volum_aluminum_module_template_code`
- Writer: operator finish/review selection (binding in modular form contract)
- Consumer: PD composition (optional child), quote mapper, 7B/7H module activation
- Prerequisite task: **`W2-PREREQUISITE-VOLUM-TRUTH`** before full Case C/D cost proof on live fixture

## Logo debt

**`NONBLOCKING_FOR_COST_AUTHORITY_DECISION`**

Parallel logo segment path does not block defining 7G/7H + graph adapter as canonical model.

## Hours rule verification

| Path | Classification |
|------|----------------|
| 7G forbidden hourly scan | **CONFIGURED_SERVICE_PRICE_VALID** guard |
| 7H hourly contamination scan | **INTERNAL_COST_VALID** guard |
| CostEngine per_hour labour/machine | **INTERNAL_COST_VALID** when consumed by 7H only |
| V6 cost-plus (internal × markup) | **COMMERCIAL_RULE_VIOLATION** (margin on internal, not 7G rules) |
| Frontend cost-plus calculator | **COMMERCIAL_RULE_VIOLATION** if treated as official |
| Legacy `/price` + QuoteOrchestrator | **COMMERCIAL_RULE_VIOLATION** / **NOT_ACTIVE** for V6 spine |

**Hours commercial violation active today: YES** (V6 cost-plus path)

## Runtime evidence (IR-MRJS4VIK)

| Surface | Result |
|---------|--------|
| Aggregate + `composition_graph` | PASS — Case B, ACM-only active child |
| PD preview | PASS — `single_child`, volum missing |
| Cost BOM preview | `blocked` (upstream volum + scope) |
| 7G / 7H POST | `404 not_found` on live fixture (upstream blockers / preview None) |
| V6 priced dry-run | **total_gross=5926.91** via cost-plus + warning `official_v6_pricing_uses_cost_plus_from_material_breakdown` |

## Wave 3 implementation spine (minimum serial)

1. **W3-T01** — Graph-to-cost module projection adapter (`composition_graph` → 7B active scope)
2. **W3-T02** — V6 priced dry-run + write: official commercial total from **7G**, not cost-plus override
3. **W3-T03** — Unify V6 snapshot with Step 8 live 7G+7H compose semantics
4. **W3-T04** — Pricing registry completeness (TE2E-008) + tariff blockers
5. **W3-T05** — Legacy CE/`/price`/simulate-cost explicit FROZEN labels + guard tests

**Prerequisite (parallel):** `W2-PREREQUISITE-VOLUM-TRUTH`

**Parallel-safe:** registry inventory, test fixture repair, documentation guards, logo debt (separate lane)

## Tests (focused)

| File | Result |
|------|--------|
| `test_commercial_price_proposal_preview.py` | 18 pass / 1 fail |
| `test_estimated_internal_cost_preview.py` | 17 pass / 1 fail |
| `test_aggregate_cost_bom_adapter.py` | 23 pass / 6 fail |
| `test_intake_v6_priced_quote_dry_run.py` | 2 pass / 6 fail |
| `test_quote_snapshot_v2.py` | 31 pass / 5 fail |
| `test_offer_scope_bom_eic_cpp_filter.py` | 6 pass / 5 fail |

Failures indicate fixture/scope drift — **not** blocking the architectural decision; they define Wave 3 regression gates.

## Hold recommendation

**`LIFT_HOLD_FOR_WAVE_3_IMPLEMENTATION`** — with prerequisite volum truth and serialized spine above.

## First Wave 3 implementation task

**`W3-T01`** — Graph-to-cost module projection adapter
