# LOGICAL_LIST_STAGE_TIMING_BEFORE

Baseline HEAD: `979d22d2`  
Workspace (QA clone): `09cea6e2-41d3-44a3-a862-add13b01af84`  
Profiler (evidence-only): `backend/scripts/_tmp_profile_logical_list_stages.py`

## In-process warm runs

| Stage | Run1 ms | Run2 ms | Run3 ms |
|---|---:|---:|---:|
| workspace_load | 0.8 | 0.9 | 0.8 |
| material_breakdown | 6.9 | 6.5 | 6.6 |
| **priced_quote_dry_run (nested)** | **48.6** | **51.2** | **47.6** |
| logical_projection_and_assembly | 0.4 | 0.3 | 0.3 |
| **TOTAL** | **56.4** | **58.6** | **55.0** |

## Dominance

Nested `build_intake_v6_priced_quote_dry_run` ≈ **86–87%** of logical-list in-process wall time.  
Projection/assembly is negligible (&lt;1 ms). MB ≈ 7 ms.

Sibling pricedQuote alone (same session, in-process): **46.5–53.5 ms** — nearly identical to the nested dry-run stage inside LL (expected: same Option B path).

## HTTP alone (browser fetch)

| Endpoint | ms |
|---|---:|
| LL alone | 763 / 471 / 400 |
| PQ alone | 526 / 881 / 868 |

HTTP variance is large; both endpoints remain hundreds of ms under local SQLite load.
