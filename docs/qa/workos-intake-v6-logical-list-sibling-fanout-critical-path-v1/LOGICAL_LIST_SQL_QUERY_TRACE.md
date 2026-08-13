# LOGICAL_LIST_SQL_QUERY_TRACE

Baseline: `979d22d2` · Workspace: `09cea6e2-…`

## Logical-list request (in-process)

| Phase | SQL count |
|---|---:|
| workspace | 1 |
| material_breakdown | 5 |
| **priced_quote (nested dry-run)** | **61** |
| other | 0 |
| **TOTAL** | **67** |

## Sibling pricedQuote alone (in-process)

| Metric | Value |
|---|---:|
| SQL_QUERY_COUNT | 61 |

## Interpretation

- Nested dry-run accounts for **61/67 ≈ 91%** of LL SQL.
- Under concurrent fan-out, LL’s nested dry-run + sibling PQ ≈ **122 SQL** competing on SQLite for the same revision.
- D2 does not reduce LL SQL (nested dry-run remains after CURRENT).
- A would drop LL SQL toward ~6 (workspace+MB) if nested dry-run removed.
