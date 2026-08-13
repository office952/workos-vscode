# SQL_QUERY_TRACE

Measured via SQLAlchemy `before_cursor_execute` on the same AsyncSession as `build_intake_v6_priced_quote_dry_run`.

| Mode | SQL count | Notes |
|---|---:|---|
| BEFORE (diagnostics on) | **114** | Workspace + VAT + MB + CPP + EIC + diagnostic FX |
| AFTER (diagnostics off) | **61** | Workspace + VAT + CPP (+ manual FX only if needed) |

## Observations

- Duplicate registry/settings reads still occur **inside CPP** (request-scoped; not addressed — CPP not dominant HTTP bottleneck after OPTION B).
- Removing MB+EIC removes ~53 queries per pricedQuote GET.
- No Redis / global cache added.
- No AsyncSession concurrency (`asyncio.gather`) — unsafe without session proof; eliminated work instead.
