# Canonical Finish Enum Map — Readonly Contract v1

**Date:** 2026-07-09  
**HEAD before:** `506673b`  
**Owner decision source:** `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md`

## Scope

Readonly architecture doc + frontend TS contract + unit tests. No runtime bridge, no FINISH/FACE workshop, no UI changes.

## Files created

| File | Purpose |
|------|---------|
| `docs/architecture/product-system/CANONICAL_FINISH_ENUM_MAP_v1.md` | Architecture contract |
| `frontend/src/features/product-system/canonicalFinishEnumMap.ts` | Readonly enum map + helpers + retired paths |
| `frontend/src/features/product-system/canonicalFinishEnumMap.test.ts` | Contract unit tests |

## Canonical IDs included (14 entries)

**Cant (owner_confirmed):** cant_stock_color, cant_oracal_wrap, cant_ral_paint, cant_ral_minimum_policy

**Face (blocked):** face_none_or_material_default (FACE), face_oracal_641, face_oracal_651, face_oracal_8500, face_print_laminate

**Artwork (blocked):** artwork_print_laminate, artwork_print_only, artwork_cut_vinyl, artwork_translucent_vinyl, artwork_none_raw_plexi

## Retired conceptual paths

- `product.components.finish.oracal_code`
- `product.components.finish.ral_code`
- `product.components.finish.stock_color`
- `product.components.finish.type`

Exported as `CANONICAL_FINISH_RETIRED_PATHS` with `deprecated_conceptual` status.

## Forbidden scope respected

- No runtime bridge
- No ProductDefinition bridge
- No Product Truth live write
- No Pricing activation
- No FINISH / FACE workshop
- No backend / DB / seed / migration
- No catalog duplication
- No UI changes

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/canonicalFinishEnumMap.test.ts src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts src/pages/ProductSystem.badges.test.tsx
```

## UI

**Not touched** — contract/doc/test only; no screenshots required.

## Next step recommendation

**FACE_COMPONENT_TRUTH_WORKSHOP_V1** — substrate/geometry workshop before FINISH; enum map provides path prefixes for face entries already blocked pending FACE boundary.

## Final verdict

**PASS** — readonly contract ready; FINISH workshop remains blocked per owner doc.
