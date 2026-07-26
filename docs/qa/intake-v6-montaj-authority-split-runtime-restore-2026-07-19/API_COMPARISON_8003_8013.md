# API COMPARISON — :8003 vs :8013

Workspace: `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982`

## Before restore

| Surface | PD status | PD blockers | ACM included | Agg conflicts |
|---------|-----------|-------------|--------------|---------------|
| :8003 stale | blocked | `MOUNTING_SCOPE_INACTIVE` | no | `COMPOSITION_GRAPH_BLOCKED`, `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` |
| :8013 proof | confirmed | `[]` | yes | `[]` |

Finish payload **identical** (`updated_at` match) → discrepancy = **code version**, not DB divergence.

Evidence: `runtime/probe_8003_before.json`, `runtime/probe_8013_before.json`.

## After restore (before stopping :8013)

| Check | Result |
|-------|--------|
| finish_identical | **true** |
| pd_status_match | **true** (`confirmed`) |
| pd_blockers_match | **true** (`[]`) |
| agg_match | **true** (`[]`) |
| fe_matches_8003 | **true** |
| no_MOUNTING_SCOPE_INACTIVE | **true** |
| acm_included | **true** |

Evidence: `runtime/comparison_summary.json`, `runtime/probe_8003_after.json`, `runtime/probe_8013_after.json`.

## Verdict

`:8003 after restore == :8013 proof truth` for the audited ACM authority scenario.
