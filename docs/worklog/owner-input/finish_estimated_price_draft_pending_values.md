# FINISH estimated price draft — pending owner values / audit

Status: **pending** — readonly draft slice only (`FINISH_ESTIMATED_PRICE_DRAFT_V1`)

## Owner price not required yet (evidence_only from seeds)

| Key | Evidence EUR/mp | Classification |
|-----|-----------------|----------------|
| MAT-ORACAL-641 | 6.50 | evidence_only |
| MAT-ORACAL-651 | 9.00 | evidence_only |
| MAT-ORACAL-8500 | 20.00 | evidence_only |
| MAT-VINYL-PRINT-LAMINATED | 10.00 | evidence_only |
| MAT-VINYL-PRINT | 1.50 | evidence_only |
| FACE_VINYL_APPLICATION_LABOR | 5.00 | evidence_only |
| LARGE_FORMAT_PRINT | 8.50 | evidence_only |
| LAMINATION | 5.00 | evidence_only |

These are **not** owner-confirmed FINISH pricing authority. Do not activate.

## Source inventory audit required

| Draft row | Issue |
|-----------|-------|
| `artwork_print_laminate_draft` | Artwork-specific print/lam keys need inventory cross-ref before owner price draft |
| `artwork_print_only_draft` | Artwork print keys — confirm MAT-VINYL-PRINT + LARGE_FORMAT_PRINT mapping for artwork surface |

Recommended next slice: **FINISH_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1**

## Explicitly not FINISH (no owner price needed here)

- `RETURN_CANT_VINYL_APPLICATION_LABOR` — RETURN-CANT only
- `MAT-ACP-FATA-LITERE` — FACE base material
- RAL 100 lei minimum — RETURN-CANT commercial policy

## Activation blockers (unchanged)

- `pricingActive: false`
- `readyForPricing: false`
- No Product Truth live write
- No Pricing Registry write
- No ProductDefinition bridge
