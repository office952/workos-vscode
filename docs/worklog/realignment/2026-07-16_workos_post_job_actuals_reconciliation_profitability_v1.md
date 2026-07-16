# Worklog — WORKOS Post-Job Actuals, Reconciliation & Profitability Truth V1

**Date:** 2026-07-16  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `5bc8cd5`  
**Owner gates:** G1 YES · G2 YES minutes-only · G3 YES local deduction/cleanup · G4 YES `/execution/:orderId` only

## Objective

Deliver the first trustworthy post-job truth layer: session labor minutes, inventory material actuals, plan-vs-reality reconciliation, and honest profitability coverage — without labor money, commercial rewrite, or FLEX reopen.

## Implementation

### Backend
- New cohesive read: `GET /api/v1/execution/{order_id}/post-job-truth`
  - `PostJobTruthService` + schemas (`post_job_truth.py`)
  - Baseline from Order Snapshot V2
  - Labor minutes from reality sessions (primary+helper); open sessions labeled `still_active`
  - Material actuals from non-reversed stock consumptions × `inventory_materials.unit_cost` (labeled)
  - Machine usage: planned-only / `not_captured`
  - Quantity: task completion from sessions; produced qty `not_captured`
  - Profitability coverage: PARTIAL when materials known; never COMPLETE while labor money excluded
- Extended `ProfitabilityAnalysisService` with known cost/coverage fields; `actual_total_cost` stays null
- Reversed stock movements excluded from actual material cost

### Frontend
- `PostJobTruthPanel` on `/execution/:orderId` (after ops, before profitability/stock)
- Profitability panel shows known material cost, known margin (partial), coverage status
- Frontend renders backend presence only — no canonical totals in React

### DB/migration
**No migration.** Additive read models only.

## Tests
- Backend: `tests/test_post_job_truth.py` (9) + `tests/test_profitability_analysis.py` (6) + inventory deduction regression — **33 passed** in combined run; post-job suite **9 passed**
- Frontend: `PostJobTruthPanel.test.tsx` — **4 passed**

## Runtime proof (order 23099, `:8001`)
Evidence: `docs/qa/_post_job_runtime_proof_v2.json`, prior captures `_post_job_runtime_*.json`

| Step | Result |
|------|--------|
| Before | commercial **1500**, known_cost **null**, coverage **INCOMPLETE**, labor minutes **1605** |
| Controlled deduct (mat 64, 1 buc @ 8.5) | known_cost **8.5**, known_margin **1491.5**, coverage **PARTIAL**, `actual_total_cost` **null** |
| Commercial | **unchanged 1500** |
| Reverse + remove materials | known_cost **null**, coverage **INCOMPLETE**, commercial **1500** |
| Temp material | `MAT-POSTJOB-PROOF-TMP` id 64 left in local inventory (active, stock restored to 10) |

## Cleanup
- Stock reverse succeeded for new consumption (movement 3)
- Observational materials deleted from reality
- Temp inventory SKU remains local (documented; not a canonical seed)

## Review
- Authority separation preserved (snapshot / plan / reality / inventory)
- Missing ≠ zero via `PresenceValue`
- No false final profit
- No CostEngine / quote write-back

## Remaining
- HR labor money (out of scope)
- Machine usage logging (not in runtime)
- Produced quantity field (not in domain)
- Same-scenario Intake→completed-job owner journey (follow-on)

## Next
Owner verifies `http://127.0.0.1:3000/execution/23099` Post-job truth section.
