# MATERIAL_MARKET_PRICE_REGISTRY_V1 — CP0 Contract Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `a243dd69` |
| Prior build | PRODUCT_PRICE_BREAKDOWN_V1 PASS_WITH_WARNINGS |

## Owner rule

```text
Material prices require real purchase or market truth.
AI may normalize, classify and temporarily bridge gaps, but must not impersonate supplier truth.
Inventory owns material identity.
Pricing owns price sources and normalization.
Product System consumes resolved material truth without copying it.
```

## Architecture decision (no migration)

Reuse `inventory_materials` + `inventory_material_price_history` + `suppliers`.

Additive read model only:

- `GET /api/v1/pricing/material-market-prices`
- `GET /api/v1/pricing/material-market-prices/{code}`

Map:

| Concept | Existing field |
|---------|----------------|
| raw purchase | `unit_cost` |
| currency / VAT | `currency`, `vat_percent` |
| effective_from | `valid_from` |
| supplier | `supplier_id` + `supplier` |
| source meta | `source_name/url/checked_at/notes`, `source_review_status` |
| history | `inventory_material_price_history` |

**STOP gate:** no Alembic in V1. Multi-source concurrent market rows deferred.

## Source precedence (deterministic)

```text
MEASURED_LANDED_COST
> PURCHASE_INVOICE
> SUPPLIER_OFFER
> OWNER_CONFIRMED
> SUPPLIER_CATALOG
> LEGACY
> MISSING
```

`TEMPORARY_AI_FALLBACK` reserved; V1 does **not** auto-create material price fallbacks.

## Freshness policy (AI_DECISION, configurable constants — not price truth)

| source_type | review_after_days |
|-------------|-------------------|
| SUPPLIER_OFFER | 30 |
| PURCHASE_INVOICE | 60 |
| SUPPLIER_CATALOG | 90 |
| OWNER_CONFIRMED | 90 |
| MEASURED_LANDED_COST | 90 |
| LEGACY | 90 |

Statuses: `CURRENT` | `REVIEW_SOON` | `STALE` | `EXPIRED` | `UNKNOWN_DATE`

## Normalization

Display raw vs normalized distinctly. Sheet→mp formula when dimensions exist. Do not invent dimensions. Waste stays Product System / breakdown owned.

## UI

`/inventory/pricing` → **Preturi materiale** enriched registry workspace.

## Integration

Price Breakdown material lines expose purchase provenance (source_type, supplier, freshness, normalization formula). CPP/EIC unchanged as calculators.
