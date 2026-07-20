# Snapshot / downstream classification — this build

| Suite / area | Classification | Action |
|--------------|----------------|--------|
| `test_product_truth_job_confirm_v1` | BUILD_OK | Keep; closure added content_hash + pin-drift + order provenance (10+) |
| `test_active_scope_snapshot_freeze` | BUILD_OK | Closure added V6 PT gate cases: unconfirmed/stale/accepted/confirmed |
| `test_product_e2e_readiness_v1` | DIRTY_TREE_INTERACTION | WT edits mid-closure broke collector import; do not touch (Agent A/F) |
| Publication publish gate | BUILD_NEW | VL publish 409 when readiness BLOCKED |
| Quote Snapshot V2 freeze gate (`70b2fdf`) | BUILD_OK | Gate enforced; pytest covers stale/unconfirmed/accepted |
| `test_quote_snapshot_component_scope` create_v6 | STALE_TEST | Expects CREATED without ConfirmJobProductTruth; blocked by `V6_SNAPSHOT_PRODUCT_TRUTH_NOT_CONFIRMED` — not on allowlist; do not weaken |
| Order provenance (`70b2fdf`) | BUILD_OK | Pass-through revision/hash + `no_live_workspace_reread` |
| EP preview from frozen (`Build4C`) | BUILD_OK | `no_live_recompile` / `no_materialization`; OrderSnapshotV2 only |
| EIC vs Quantity Builder | PREEXISTING_RELEVANT | EIC parallel `_extract_quantity`; not converged |
| Full `test_quote_snapshot_v2` / intake snap suites | PREEXISTING_NOISE | Do not greenwash; classify only |

## Policy

- Fix **build-caused** failures only.
- Never weaken freeze / confirm assertions.
- EIC qty parallel path remains known PARTIAL (foundation worklog).
- Aggregate/Qty do not surface `product_truth_revision` in provenance (CP-B PARTIAL); Agg pin preference exists (`136f38b`).
