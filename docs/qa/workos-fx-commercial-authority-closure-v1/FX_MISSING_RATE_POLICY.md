# FX_MISSING_RATE_POLICY

```
CONFIGURED RATE  → usable for money consumers
MISSING / NULL / ≤0 → FAIL CLOSED
NEVER silently assume 5.0
```

Stable error codes:

- `eur_to_ron_rate_missing`
- `eur_to_ron_rate_invalid`
- `eur_to_ron_column_unavailable` (ancient SQLite; controlled HTTP 503 on Settings)
- `company_commercial_settings_row_missing`

Logo maps missing → `eur_to_ron_rate_unset` (existing Logo contract).

`DEFAULT_EUR_TO_RON_RATE = 5.0` allowed only as:

- DEMO_SEED
- TEST fixture seed
- NON_AUTHORITATIVE_UI_PLACEHOLDER (placeholder/example text)

Forbidden as LIVE_COMMERCIAL_FALLBACK.
