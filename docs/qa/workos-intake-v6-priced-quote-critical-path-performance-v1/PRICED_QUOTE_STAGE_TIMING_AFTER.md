# PRICED_QUOTE_STAGE_TIMING_AFTER

HEAD with OPTION B: default `include_internal_cost_diagnostics=False`  
Workspace (read-only): `03a1da1e-003a-4139-9668-59ac6bcec812`

## In-process warm runs

| Stage | Run1 ms | Run2 ms | Run3 ms |
|---|---:|---:|---:|
| workspace_load | 0.8 | 0.9 | 1.0 |
| pricing_input_preview | 3.0 | 3.1 | 3.2 |
| vat_lookup | 0.6 | 0.5 | 0.6 |
| material_breakdown | — skipped — | — | — |
| cpp_build_preview | 38.0 | 36.5 | 39.5 |
| estimated_internal_cost | — skipped — | — | — |
| diagnostic_fx_resolution | — skipped — | — | — |
| **TOTAL** | **42.4** | **40.9** | **44.1** |
| SQL queries | 61 | 61 | 61 |

## Delta vs BEFORE (in-process)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| TOTAL ms | ~83–85 | ~41–44 | **~−50%** |
| SQL queries | 114 | 61 | **−53** |
| MB+EIC+FX | ~40 ms | 0 | removed from critical path |

## HTTP after (QA clone `09cea6e2-…`, live uvicorn --reload)

| Context | PRICED_QUOTE_MS |
|---|---:|
| Alone | **238 / 262 / 366** |
| Concurrent fan-out (pricedQuote) | **500 / 646** |
| Concurrent wall (all siblings) | **563 / 703** |
| Click → pricedQuote done | **699 / 767** |

Response proves deferred path live: `warnings` contains `internal_cost_diagnostics_deferred:…`; `internal_cost_trace.available=false`; `diagnostic_cost_plus_trace=null`.
