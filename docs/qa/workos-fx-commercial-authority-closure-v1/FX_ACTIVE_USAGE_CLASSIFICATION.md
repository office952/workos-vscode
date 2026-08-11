# FX_ACTIVE_USAGE_CLASSIFICATION

Post-implementation search of `DEFAULT_EUR_TO_RON_RATE` / `get_eur_to_ron_rate` / `ensure_eur_to_ron_column*`:

| Location | Classification |
|----------|----------------|
| `company_commercial_settings_service.DEFAULT_EUR_TO_RON_RATE` | DEMO/TEST/UI constant — not live fallback |
| `require_configured_*` / `resolve_configured_*` | CONFIGURED_AUTHORITY |
| `get_eur_to_ron_rate` | CONFIGURED_AUTHORITY (fail-closed alias) |
| `ensure_eur_to_ron_column_explicit` | DEMO / TEST bootstrap only |
| `seed_atoms_demo_v1` / `tests/conftest` | DEMO / TEST |
| `profitability_fx_v1` on OrderSnapshotV2 | FROZEN_SNAPSHOT |
| Settings UI `DEFAULT_EUR_TO_RON_RATE` in copy/placeholder | NON_AUTHORITATIVE_UI_PLACEHOLDER |
| FE `normalizeEurToRonRate` (deprecated) | LEGACY helper — invents 5; not used by Settings hook / money authority |
| FE `parseConfiguredEurToRonRate` | CONFIGURED_AUTHORITY |
| Active unexplained LIVE_COMMERCIAL_FALLBACK | **NONE** |
