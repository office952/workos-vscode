# Letters face finish — meaning + Inventory/Pricing presence

**Date:** 2026-07-23  
**Scope:** Operator identity for Oracal 8500 / 641 / 651 / Printat·Laminat without inventing `BADGE-FACE-*` codes.

## Decisions

1. **No `BADGE-FACE-ORACAL-*`** — avoids confusion with `BADGE-CNC-PROCESSABLE` (sole capability badge on plexi + CNC 4020).
2. **Identity** = display label + stable `MAT-*` code.
3. Materials must appear in **Inventory** and **Pricing** with owner-confirmed unit costs.

## Materials

| Label | Code | EUR/mp (excl. TVA) |
|---|---|---|
| Oracal 8500 | `MAT-ORACAL-8500` | 20.0 |
| Oracal 641 | `MAT-ORACAL-641` | 6.5 |
| Oracal 651 | `MAT-ORACAL-651` | 9.0 |
| Printat / Laminat | `MAT-VINYL-PRINT-LAMINATED` | 10.0 |

Shared labor (any option): Aplicare față · Decupare contur.

## Code

- FE contract: `frontend/src/lib/materials/lettersFaceFinishMaterialDisplay.ts`
- PS chips/tooltips: `LettersFaceFinishOptionBadges.tsx`
- Pricing display lock: `pricingDisplayNaming.ts`
- BE naming/seeds: `material_canonical_naming.py`, `seed_volumetric_owner_confirmed_prices.py`

## Local verify (2026-07-23)

After `seed_build4_materials` + `seed_volumetric_owner_confirmed_prices`, all four rows are `active` with the names/prices above.
