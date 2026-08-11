# FX_PROVENANCE_AND_FREEZE

## Live authority

`company_commercial_settings.eur_to_ron_rate` via `require_configured_eur_to_ron_rate`.

## Freeze point

At Quote→Order / Order Snapshot V2 convert:

`OrderSnapshotV2.profitability_fx_v1`

- `policy = "A"`
- `eur_to_ron_rate` = configured rate at convert
- `freeze_point = "order_convert"`
- `rate_source = "company_commercial_settings.eur_to_ron_rate"`

Later Settings FX changes must not rewrite historical `profitability_fx_v1`.

No historical backfill. No schema migration.
