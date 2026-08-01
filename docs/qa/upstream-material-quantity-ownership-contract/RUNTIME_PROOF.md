# RUNTIME_PROOF

**Date:** 2026-08-01  
**Branch tip at proof:** local product commit (after audit `a1e35c9c` pushed)

## Historical fixture 92401 (immutable)

| Check | Result |
|-------|--------|
| order / plan | 92401 / 13 |
| ops | 18 |
| materials | 22 |
| qty null | 22 |
| false zero | 0 |
| quantity_status | all `legacy_unspecified` (compat) |
| material_inputs nonempty | 0 |
| readiness persisted | no |
| sessions / actuals | 0 / 0 |
| authorize | false |
| projection version | `ops_graph_frozen_technical_materials/v2` |

URL: `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

## New live Order fixture

**NOT VERIFIED** — no new Order Snapshot created in this GO (avoids mutating shared DB fixtures / materialize).  
New-contract behavior proven by unit tests:

- Model A derived qty
- Model D reference_only
- inactive depth/finish filtered
- same code different provenance preserved
- ops-graph status labels

## No-side-effect

- No POST materialize
- No 92401 snapshot rewrite
- `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED=False`
