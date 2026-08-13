# PRICED_QUOTE_STAGE_TIMING_BEFORE

Baseline HEAD: `c8f27b17`  
Mode: legacy path = `include_internal_cost_diagnostics=True` (pre-optimization behavior)  
Workspace (read-only): `03a1da1e-003a-4139-9668-59ac6bcec812`  
Profiler: `backend/scripts/_tmp_profile_priced_quote_stages.py` (evidence-only)

## In-process warm runs (median-ish)

| Stage | Run1 ms | Run2 ms | Run3 ms |
|---|---:|---:|---:|
| workspace_load | 1.1 | 0.9 | 0.9 |
| pricing_input_preview | 3.1 | 3.0 | 3.1 |
| vat_lookup | 0.7 | 0.6 | 0.6 |
| material_breakdown | 6.5 | 5.8 | 5.4 |
| cpp_build_preview | 40.4 | 39.5 | 38.5 |
| estimated_internal_cost | 33.1 | 33.2 | 33.3 |
| diagnostic_fx_resolution | 0.7 | 0.6 | 0.6 |
| **TOTAL** | **85.4** | **83.6** | **82.3** |
| SQL queries | 114 | 114 | 114 |

## HTTP evidence before (from Save/Recalc GO, same local stack)

| Context | PRICED_QUOTE_MS |
|---|---:|
| Alone (prior session) | 816–990 |
| Concurrent Step 2 fan-out | 1389–1716 |
| Click → pricedQuote done (fan-out) | 1535–1877 |

## Dominance (service stages, warm)

1. CPP (~39–40 ms)  
2. EIC (~33 ms)  
3. Material breakdown (~6 ms)  
4. Everything else &lt; 5 ms  

HTTP wall time is dominated by process/SQLite contention under Step 2 fan-out, not by pure CPU in isolation. EIC + MB + diagnostic FX still add ~40% of in-process work and ~53 SQL queries.
