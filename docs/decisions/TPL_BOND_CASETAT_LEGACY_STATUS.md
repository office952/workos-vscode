# Decision — `TPL-BOND-CASETAT` legacy status

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Status | **Deprecated mapping** (strategy B) |
| Live authority | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

## Findings

| Question | Answer |
|----------|--------|
| Defined as seeded Product Template? | **No** — string-only placeholder |
| Consumers | Intake composition recommendation (historical pending path) |
| Active / offerable? | No |
| Unique data? | No |
| Duplicates ACM boxed? | Intent yes; code was pending, not live |

## Decision

1. **Not** new-selection authority.
2. **Not** owner-facing.
3. New support recommendations map to **`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`**.
4. Constant retained as `SUPPORT_TEMPLATE_LEGACY_CODE` / `STALE_BOND_CASETAT` for documentation and redirect messaging.
5. No DB migration (never persisted as a real template row).

## Strategy

**B — Deprecated mapping** (preferred). Alias strategy unnecessary (no real template to alias).
