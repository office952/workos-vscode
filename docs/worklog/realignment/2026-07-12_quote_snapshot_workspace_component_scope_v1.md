# Quote Snapshot Workspace Component Scope V1

**Task:** `QUOTE_SNAPSHOT_WORKSPACE_COMPONENT_SCOPE_V1`  
**HEAD before:** `4d943b3`  
**Verdict:** `APPROVED_WITH_DOCUMENTED_DEBT`

## Problem fixed

Quote Snapshot V2 froze a base `ProductAggregate` (`build()`) while BOM/EIC/CPP used `build_for_workspace()`. Intake V6 official snapshots omitted aggregate and offer_scope entirely. Logo `::segment_key` identity and component sold scope were lost at freeze.

## Files changed

- `backend/schemas/quote_snapshot_v2.py` — optional scope fields + `FrozenComponentScope`
- `backend/services/quote_snapshot_component_scope_service.py` — shared freeze helper
- `backend/data/offer_scope_canonical_map.py` — `runtime_to_canonical()`
- `backend/services/quote_snapshot_v2_service.py` — wire helper (Path A)
- `backend/services/intake_v6_quote_snapshot_v2_service.py` — wire helper (Path B)
- `backend/tests/test_quote_snapshot_component_scope.py` — new scenario tests
- `backend/tests/test_intake_v6_quote_snapshot_v2.py` — FakeDb scope mocks
- `backend/tests/test_offer_scope_resolver.py` — inverse map unit test

## Snapshot contract

Frozen optional fields on `QuoteSnapshotV2`:

- `component_scope_version: quote_component_scope/v1`
- `offer_scope_snapshot` — mode, sold_modules, resolved_runtime_sold_modules, use_legacy, resolver_contract_version, validation_errors
- `component_instances[]` — instance_id, canonical/runtime codes, source_template, segment_key, classification
- `geometry_input_snapshot` — quote_geometry, svg_source, analysis_ready, workspace_payload_hash
- `product_aggregate_snapshot` — workspace-composed when `workspace_id` present

`calc_modules` not persisted (derived from frozen sold + resolver version).

## Tests

Targeted batch (41 component-scope + offer_scope; 34 quote_snapshot_v2 excluding 2 known drift cases; 14 intake v6 excluding 2 output-composition drift cases).

## Backward compatibility

All new fields optional. Legacy JSON deserializes. No DB migration. No backfill.

## Deferred

- OrderSnapshotV2 offer_scope passthrough
- Execution sold-scope filter
- Offer line model
- PD builder internal `build()` debt
- 2 pre-existing `test_quote_snapshot_v2` CPP readiness/owner-decision drift cases
- 2 pre-existing output composition API drift tests

## Next step

Order snapshot offer_scope passthrough slice; Intake V6 sold-scope UI wiring.
