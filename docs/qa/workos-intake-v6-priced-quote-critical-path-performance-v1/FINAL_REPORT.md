# WORKOS_INTAKE_V6_PRICED_QUOTE_CRITICAL_PATH_PERFORMANCE_V1 — FINAL REPORT

## Verdict

```text
OPTION = B — REMOVE DIAGNOSTIC WORK FROM CRITICAL PATH
STATUS = PASS (local commit; PUSH = NO)
BASELINE_HEAD = c8f27b17
```

Default GET `priced-quote-dry-run` no longer runs material-breakdown, EIC, or diagnostic cost-plus. Official CPP totals / blockers / readiness unchanged. Write + Snapshot V2 opt back in.

## Required answers

```text
What dominates pricedQuote latency?
EXACT: Before — CPP + EIC (~equal in-process) amplified by SQLite/fan-out HTTP;
       After — CPP remains the main service stage; HTTP still amplified by
       sibling GETs + nested dry-run in logical-list-read-model.

Does pricedQuote recompute material breakdown?
YES (legacy) / NO (default GET after this GO; YES when include_internal_cost_diagnostics=True)

Is material breakdown required for official CPP total?
NO

Does pricedQuote compute EstimatedInternalCost synchronously?
YES (legacy / write / snapshot) / NO (default Step 2 GET)

Is EIC required for official commercial total?
NO

Is diagnostic cost-plus blocking official offer?
YES (was on critical path) / NO (deferred; never authority)

Are duplicate DB/registry reads present?
YES (inside CPP; reduced overall by −53 queries via skip MB/EIC)

Was redundant work removed?
YES

Did commercial totals change?
NO

Did readiness semantics change?
NO

Did Confirm regress?
NO

Did GET diet regress?
NO (production/task GETs = 0 on discrete depth change)

Did save/recalc responsiveness regress?
NO (policy still 100 ms short; PQ itself faster)

PRICED_QUOTE_BEFORE_MS = 1535–1877 (fan-out) / 816–990 (alone)
PRICED_QUOTE_AFTER_MS = 699–767 (fan-out) / 238–366 (alone)
CLICK_TO_CURRENT_PRICE_BEFORE_MS = 1923–2089
CLICK_TO_CURRENT_PRICE_AFTER_MS = 1842–1989
SQL_QUERY_COUNT_BEFORE = 114
SQL_QUERY_COUNT_AFTER = 61
PRICING_RULE_CHANGES = 0
PRICING_REGISTRY_VALUE_CHANGES = 0
PRODUCT_TRUTH_SCHEMA_CHANGES = 0
DB_SCHEMA_CHANGES = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```

## Code changes

| File | Change |
|---|---|
| `backend/services/intake_v6_priced_quote_dry_run_service.py` | `include_internal_cost_diagnostics` default False; skip MB/EIC/cost-plus |
| `backend/services/intake_v6_priced_quote_write_service.py` | opt-in True |
| `backend/services/intake_v6_quote_snapshot_v2_service.py` | opt-in True |
| `backend/tests/test_intake_v6_priced_quote_dry_run.py` | deferred default + parity + opt-in |

## Metoda de lucru si logica abordarii

1. Baseline parity at `c8f27b17`.  
2. Stage-instrument before optimizing.  
3. Prove MB/EIC/cost-plus are diagnostic for official Ofertă.  
4. Apply single OPTION B — delete work from critical path, keep API shape.  
5. Parity tests + HTTP proof on QA clone only.

## Impact Harta sistemelor

| System | Impact |
|---|---|
| CPP / official money | Unchanged authority |
| Material-breakdown GET | Still owns Step 2 letters cost UI |
| EIC | Off default GET; on write/snapshot |
| Confirm | Same blockers/totals/readiness |
| Logical-list | Still nests dry-run (residual) |

## Impact Guvernanța sistemului

No ownership change. Performance trim of existing canonical path.

## Dead Pieces Check

Diagnostic fields still returned (unavailable / null) for API compatibility — not deleted from contract.

## Overengineering Check

No cache framework, no gather, no new endpoints, no background jobs.

## Rollback

Revert the three service files + test updates; or force `include_internal_cost_diagnostics=True` on the router GET.

## Roadmap awareness

Next performance lever (not authorized): nested dry-run in logical-list / fan-out diet. Commercial `NO_EFFECT` / back bevel deferred per Owner.

## Forbidden Scope respected

No pricing rates, registry, RETURN-CANT, face finish, VAT/FX policy, mounting/PSU/ACM pricing, FE money invention.
