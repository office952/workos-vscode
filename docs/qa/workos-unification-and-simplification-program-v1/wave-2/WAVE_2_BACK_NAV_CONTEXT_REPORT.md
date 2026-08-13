# Wave 2 browser-back / context (H)

Read-only. Admin × light + dark. Perfect preservation is **not** required to PASS.

| FROM_ROUTE | TO_ROUTE | BACK_ROUTE | FILTER | SELECTION | SCROLL | CONTEXT_PRESERVED | Theme |
|------------|----------|------------|--------|-----------|--------|-------------------|-------|
| `/intake` | `/intake-v6/IR-MSRB28PU/operator` | `/intake` | UNKNOWN | UNKNOWN | NO | **YES** | light, dark |
| `/orders` | `/orders/ORD-IV6-V2-1786318810-31` | `blank` | UNKNOWN | NO | NO | **NO** | light, dark |
| `/clients` | `/clients/SC%20CLIENT%20NOU%20SRL` | `/clients` | UNKNOWN | UNKNOWN | NO | **YES** | light, dark |

**BACK_NAV_CASES_TESTED = 6**  
**BACK_NAV_GAPS = 2** (orders list → detail → Back leaves a blank document; SPA history, both themes)

Scroll was set to 80 before drill; after back, scroll was not preserved on any case.

This is audit evidence, not an implementation defect ticket.
