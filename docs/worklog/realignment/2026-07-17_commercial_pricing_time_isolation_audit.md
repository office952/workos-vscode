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

## Implementation — Legacy commercial pricing path isolation

### Consumer research (summary)

| Consumer | Runtime active | Operator reachable | External integration | Test only | Action |
|----------|---------------:|-------------------:|---------------------:|----------:|--------|
| QuoteWizard `priceQuote` | was yes | `/quotes` modal | no evidence | no | Disabled + retired banner |
| VolumetricLettersQuoteFlow `priceQuote` | was yes | Intake quote tab / wizard | no | no | Commercial button retired |
| QuoteRevisionDialog `priceExistingQuote` | was yes | Quotes revision | no | no | Submit blocked |
| `POST /entities/quotes/price` | was yes | via FE | **none found** | yes | HTTP 410, excluded from OpenAPI |
| `POST /entities/quotes/{id}/price` | was yes | revision FE | **none found** | yes | HTTP 410, excluded from OpenAPI |
| CostEngine / simulate-cost | yes (internal) | Product System / preliminary | no | no | Preserved — not customer authority |
| QuoteOrchestrator module | present | only via retired routes | no | yes | Unreachable as commercial authority |

No external/production webhook or third-party caller found in repo configs.

### Strategy

Preferred transitional isolation: routes remain registered for explicit **410 Gone** (no calculation, no write), `include_in_schema=False` (absent from OpenAPI). Frontend clients refuse to call. No automatic 7G adapter.

### Backend

- `services/legacy_quote_price_retirement.py`
- `routers/quotes.py` — `price_quote` / `price_existing_draft_quote` raise retirement only

### Frontend

- `lib/legacyQuotePriceRetirement.ts` + `LegacyQuotePriceRetiredBanner`
- `api/quotes.ts` — `priceQuote` / `priceExistingQuote` throw 410 locally (no fetch)
- QuoteWizard / VolumetricLettersQuoteFlow / QuoteRevisionDialog disabled commercial actions
- Control Center limitation text updated

### Tests

- `test_legacy_quote_price_isolation.py` + retired rewrites of legacy `/price` suites
- Vitest `quotes.legacyPriceRetirement.test.ts`
- Time-isolation + TE2E-028A + CPP + profitability remain green

### Runtime

- OpenAPI: `/api/v1/entities/quotes/price` absent
- POST legacy price → **410** `legacy_quote_price_retired`, `financial_write=false`
- 7G unchanged

### Modules / Governance

- Modules: STATUS/LIMITATION update (7G active; legacy hourly not authoritative)
- Governance: POLICY ENFORCEMENT IMPROVEMENT (route + FE + tests)

### Status

`LEGACY COMMERCIAL PRICING PATH = ISOLATED — PROVEN_CURRENT`  
TE2E-028B = **not started**

### Commits

1. `test(pricing): prove time isolation and flag legacy route` (`45d1d57`)
2. `fix(pricing): isolate legacy hourly quote path` (this implementation)
3. docs/evidence commit if needed
