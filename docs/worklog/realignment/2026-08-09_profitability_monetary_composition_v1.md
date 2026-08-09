# WorkOS — Profitability Monetary Composition V1

**Date:** 2026-08-09  
**Starting HEAD:** `032db07f`  
**Owner GO:** `AUTHORIZE_PROFITABILITY_MONETARY_COMPOSITION_V1`  
**Owner decisions:** MACHINE + OTHER = `DECLARE_NA_FOR_V1`

## Verdict

```text
PROFITABILITY_MONETARY_COMPOSITION_V1 = PARTIAL_BLOCKED
BLOCKER = PROFITABILITY_CURRENCY_COMPOSITION_GAP
MACHINE_COST = N_A_FOR_V1
OTHER_DIRECT_COST = N_A_FOR_V1
N_A_REPRESENTED_AS_ZERO = NO
FX_REQUIRED = YES (Letters EUR revenue vs RON actual costs)
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
NEXT_TASK = NOT_AUTHORIZED
NEXT_RECOMMENDED_BUILD = WORKOS_V1_PROFITABILITY_CURRENCY_COMPOSITION_AUTHORITY
```

## What closed

- Explicit Owner N/A for machine + other (not silent zero)
- Same-currency composition: revenue − labor − material
- Fail-closed currency mismatch (no invent FX)
- `monetary_v1` projection on Profitability Actual RM
- Bounded UI honesty on `/execution/:orderId`
- Historical stability tests (live rate/catalog changes do not reprice)

## What blocks PASS

Letters V1 commercial is native **EUR**; actual labor/material freeze is typically **RON**. Composition cannot subtract without historical-safe FX authority (out of scope / forbidden to invent).

## Commits

- `fd3b4580` — fix(profitability): V1 monetary composition with N/A and currency fail-closed  
- (this docs commit) — evidence + roadmap
