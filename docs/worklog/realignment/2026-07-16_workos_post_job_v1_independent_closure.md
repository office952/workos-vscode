# Independent closure — WORKOS Post-Job Actuals V1

**Date:** 2026-07-16  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Reviewed range:** `5bc8cd5..f9dd11e` (ea70fa1, 8dd7279, 31c37de, f9dd11e)  
**Compile health note:** `0b97f7d` (JSX closer fix) required for frontend build; acceptance is of working tree including `0b97f7d`  
**Method:** Independent code + runtime evidence review (not implementer self-report)

## Stage A verdict

**WORKOS_POST_JOB_V1_ACCEPT_WITH_NONBLOCKING_LIMITATIONS**

## Classifications

| Domain | Classification |
|--------|----------------|
| Planned/actual authority | **PROVEN** |
| Material actual source | **PROVEN** |
| Material valuation (`unit_cost_at_read`) | **ACCEPTABLE_V1_WITH_CLEAR_LABEL** |
| Labor minutes | **PROVEN** |
| Machine/quantity missing truth | **PROVEN** |
| Profitability wording | **PROVEN_PARTIAL_TRUTH** |
| Snapshot/pricing immutability | **PROVEN** |
| Runtime cleanup | **DOCUMENTED_LOCAL_RESIDUE** |

## Blocking findings

None affecting post-job truth / profitability semantics.

## Nonblocking limitations

1. Catalog `unit_cost` at read is not historical deduction-time cost — labeled in API (`inventory_materials.unit_cost_at_read`) and profitability warning chip; PostJobTruthPanel surfaces cost number more prominently than the valuation nuance (acceptable V1).
2. Known materials-only margin can be numerically large vs revenue while remaining correctly labeled partial / not final.
3. Machine usage and produced quantity remain `not_captured` by design.
4. Labor money excluded by G2 — coverage never COMPLETE.
5. Local residue: temp inventory SKU `MAT-POSTJOB-PROOF-TMP` (id 64) left in local DB with stock restored — documented, not canonical seed.
6. In-range HEAD `f9dd11e` had frontend compile break from stray `)}`; fixed by `0b97f7d` (ship with that fix).

## Runtime proof (order 23099)

Source: `docs/qa/_post_job_runtime_proof_v2.json`

- Real deduction → known_cost 8.5, coverage PARTIAL, `actual_total_cost` null  
- Commercial frozen 1500 unchanged  
- Reverse → known_cost null, coverage INCOMPLETE, commercial still 1500  

## Post-job V1 acceptance

Accepted for operational use with the limitations above. Does **not** authorize same-scenario implementation — only Stage B planning.
