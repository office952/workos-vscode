# VAT_SOURCE_MAP — WORKOS_VAT_SNAPSHOT_BOUNDARY_INTEGRITY_V1

| VAT_VALUE | SOURCE | FREEZE POINT | STORAGE | READ CONSUMER |
|-----------|--------|--------------|---------|---------------|
| CURRENT_DEFAULT_VAT | `company_commercial_settings.default_vat_pct` | none (live) | DB row | Settings UI; pre-freeze dry-run; new freeze CPP supplementary stamp |
| CPP_VAT | `commercial_product_breakdown.vat_rate_percent` | new freeze only (supplementary) | QSV2 JSON | Frozen resolver (secondary) |
| QUOTE_VAT (amount) | dry-run / offer stamp `vat_amount` | priced write / offer stamp | `quotes.vat` | Order envelope amount; **not** rate authority |
| SNAPSHOT_VAT (rate) | priced write Settings default | priced write | `notes.commercial_adjustment_trace.vat_percent` | **PRIMARY** post-freeze offer/review; Order `accepted_vat_percent` |
| OFFER_REVIEW_VAT | frozen resolver | post-freeze read | derived from notes (+ optional CPP) | authoritative offer + pricing-review |
| ORDER_VAT | notes trace + quote amounts | order convert | OrderSnapshot `accepted_vat_percent` / amount | Profitability / order commercial envelope |
| DOCUMENT_VAT | quote snapshot `pricing.vat_pct` → `quote.vat` → constant DEFAULT | document build | document payload | `quote_document_service` (no live Settings GET) |

## Owner locks applied

```
FROZEN_VAT_SOURCE_CANDIDATE = notes.commercial_adjustment_trace.vat_percent
LIVE_SETTINGS_VAT_AFTER_FREEZE = FORBIDDEN
MISSING_FROZEN_VAT = FAIL_CLOSED
SCHEMA_CHANGE = NO
HISTORICAL_BACKFILL = NO
```
