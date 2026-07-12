# Order Snapshot Component Scope Passthrough V1

**Task:** `ORDER_SNAPSHOT_COMPONENT_SCOPE_PASSTHROUGH_V1`  
**HEAD before:** `967fd0a`  
**Verdict:** `APPROVED`

## Problem fixed

Quote Snapshot V2 froze component scope at `967fd0a`, but Order Snapshot convert only copied aggregate/PD/commercial — not `offer_scope_snapshot`, `component_instances`, or `geometry_input_snapshot`.

## Files changed

- `backend/schemas/order_snapshot_v2.py` — optional scope fields (reuse quote snapshot types)
- `backend/services/order_snapshot_v2_convert_service.py` — `_component_scope_fields_from_quote()` verbatim copy
- `backend/tests/test_order_snapshot_component_scope_passthrough.py` — passthrough scenarios

## Behavior

Order convert copies from Quote Snapshot V2 without resolver rerun, aggregate rebuild, or repricing:

- `component_scope_version`
- `offer_scope_snapshot` (mode, sold_modules, resolved runtime modules)
- `component_instances`
- `geometry_input_snapshot`
- `product_aggregate_snapshot` (unchanged passthrough path, now grouped)

Legacy quote snapshots without scope fields still convert (optional defaults).

## Tests

11 passthrough tests + 31 existing convert tests PASS.

## Deferred

Execution sold-scope filter; Offer line model; Intake V6 UI.

## Next step

Execution plan preview may read frozen `offer_scope_snapshot` from order snapshot when sold-scope task filtering is implemented.
