# ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 — CP0 Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `8aac9eda` |
| Target | `MAT-LED-PSU-12V` |

## Identity verdict (frozen before writes)

```text
MAT-LED-PSU-12V = VARIANT_SELECTOR / FAMILY_PLACEHOLDER
```

Not a purchasable SKU. Not priced. Resolves via `selected_psu_watts` → concrete variants.

| Code | Role | unit_cost live | source |
|------|------|----------------|--------|
| MAT-LED-PSU-12V | selector | null | MISSING (intentional) |
| MAT-LED-PSU-12V-60W | SKU | 12 EUR/buc | OWNER_CONFIRMED |
| MAT-LED-PSU-12V-100W | SKU | 16 EUR/buc | OWNER_CONFIRMED |
| MAT-LED-PSU-12V-160W | SKU | 20 EUR/buc | OWNER_CONFIRMED |
| MAT-LED-PSU-12V-200W | SKU | 40 EUR/buc | OWNER_CONFIRMED |

## Remediation (Outcome A)

1. Do **not** invent a generic price.
2. Classify selector as non-priced; exclude from `critical_missing`.
3. Keep variant prices as purchase authority.
4. Prove VL breakdown continues to emit concrete variant (e.g. 100W).

## Out of scope

Supplier Import · invented prices · broad material cleanup · offer · Execution · Analyzer · Alembic
