# FX_CONSUMER_MAP

Canonical field: `company_commercial_settings.eur_to_ron_rate`

| Consumer | File | Class | Post-fix |
|----------|------|-------|-----------|
| Settings GET/PUT | `backend/routers/company_commercial_settings.py` | SETTINGS_EDITOR | Nullable GET; Save explicit |
| Settings service | `backend/services/company_commercial_settings_service.py` | SETTINGS_EDITOR + money resolver | `require_configured_eur_to_ron_rate` fail-closed; no write-on-read; no ALTER on GET |
| Quote→Order V6 | `intake_v6_quote_to_order_service.py` | QUOTE_TO_ORDER | `require_*` |
| Quote→Order V4/V3 | `intake_v4_*` / `intake_v3_guarded_*` | QUOTE_TO_ORDER | `require_*` |
| Orders router convert | `backend/routers/orders.py` | QUOTE_TO_ORDER | `require_*` |
| Order Snapshot V2 | `order_snapshot_v2_convert_service.py` | ORDER_SNAPSHOT / PROFITABILITY | Stamps `profitability_fx_v1` from `require_*` |
| Conversion math | `order_currency_conversion_service.py` | QUOTE_TO_ORDER | Unchanged; still rejects None/≤0 |
| Logo / CPP FX | `linked_logo_commercial_price_service.py` | LOGO_CPP | Shared `resolve_configured_*` (maps missing → `eur_to_ron_rate_unset`) |
| Intake V6 dry-run | `intake_v6_priced_quote_dry_run_service.py` | DRY_RUN | Official EUR path skips FX; diagnostic cost-plus only if FX configured |
| Settings UI | `frontend/src/pages/Settings.tsx` | SETTINGS_EDITOR | Missing copy; no fabricated 5.0 as configured |
| FE hook / offer calc | `useCompanyCommercialSettings` / `intakeV6OfferCalculator` | PRE_COMMERCIAL_CALC | Nullable rate; no silent 5.0 for money |
| Demo seed | `scripts/seed_atoms_demo_v1.py` | DEMO | Explicit FX seed |
| Pytest conftest | `tests/conftest.py` | TEST | Explicit FX seed |
