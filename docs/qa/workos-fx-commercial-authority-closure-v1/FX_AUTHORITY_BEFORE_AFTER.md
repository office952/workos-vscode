# FX_AUTHORITY_BEFORE_AFTER

## Before

- `get_eur_to_ron_rate` / `get_settings` could invent `DEFAULT_EUR_TO_RON_RATE = 5.0`
- `get_or_create` could persist 5.0 on read when NULL
- `_ensure_eur_to_ron_column` could `ALTER TABLE` during Settings/money read
- Logo/CPP already fail-closed; Quote→Order conversion validated rates but never saw missing because helper invented 5.0

## After

| Behavior | Result |
|----------|--------|
| Money resolve | `require_configured_eur_to_ron_rate` — missing/invalid → explicit error |
| Settings GET | Returns `eur_to_ron_rate: null` when unset; does not persist FX |
| Schema | Normal GET: no ALTER; `ensure_eur_to_ron_column_explicit` only for demo/test bootstrap |
| Quote→Order | Uses configured rate or blocks |
| Profitability | Freezes exact configured rate at convert |
| Dry-run official | EUR without requiring FX; diagnostic RON omitted when FX missing |
| UI | “Cursul EUR/RON nu este configurat.” when unset |
