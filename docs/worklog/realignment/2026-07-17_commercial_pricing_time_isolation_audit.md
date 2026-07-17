# Worklog — Commercial Pricing Time Isolation Audit

**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `37a0e2f`  
**Authority doc:** `docs/audits/2026-07-17_commercial_pricing_time_isolation_audit.md`

## Purpose

Prove whether planned/actual operational minutes can influence customer commercial offers on current code + runtime. Audit and focused tests only — no pricing refactor.

## Verdict

`LEGACY_PRICING_PATH_REACHABLE`

- Active V6 / 7G / Snapshot V2 spine: **minutes do not change offers** (planned 15 vs 150, actual 0/10/180 — commercial frozen).  
- Legacy `POST /api/v1/entities/quotes/price` + CostEngine `per_hour` remains **runtime-reachable** (QuoteWizard).  
- TE2E-028A diffs: no commercial dependency.  
- Post-Job: `write_back_performed=false`; no pricing imports (AST).

## Tests run

```text
pytest tests/test_commercial_pricing_time_isolation_audit.py
     + TE2E-028A + CPP no-hourly + quote snapshot no rate_per_hour
     + profitability
→ 23 passed
```

Uncommitted test file: `backend/tests/test_commercial_pricing_time_isolation_audit.py`

## Owner conclusion (exact)

```text
MINUTELE INFLUENTEAZA OFERTA = NU
PLANNED MINUTES = OPERATIONAL ONLY
ACTUAL MINUTES = ANALYSIS ONLY
QUOTE SNAPSHOT = PROTECTED
ORDER SNAPSHOT = PROTECTED
INTERNAL COST = SEPARATE
HOURLY PRICING = INACTIVE
LEGACY PRICING = REACHABLE
IMPLEMENTATION REQUIRED = NU
```

## Owner decision (approved)

```text
ACTIVE COMMERCIAL ENGINE = Intake V6 → CommercialPriceProposalService / 7G
ACTIVE ENGINE STATUS = ACCEPTED AND PROTECTED
LEGACY /entities/quotes/price = MUST BE ISOLATED
LEGACY QuoteWizard CALLER = MUST BE REMOVED, DISABLED OR EXPLICITLY BLOCKED
CostEngine per_hour = MUST NOT REMAIN CUSTOMER-PRICING AUTHORITY
AUDIT COMMIT = DA
IMPLEMENTATION = GO
TE2E-028B = NOT STARTED
```

## Commit

Audit commit: `test(pricing): prove time isolation and flag legacy route`  
(Implementation follows in the same worklog section below.)

## Next

Legacy commercial pricing path isolation (this build). Do not start TE2E-028B.
