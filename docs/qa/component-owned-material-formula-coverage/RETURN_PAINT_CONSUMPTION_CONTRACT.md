# RETURN_PAINT_CONSUMPTION_CONTRACT

**Verdict:** SOURCE_MISSING — **not implemented as Model A**  
**FormulaId:** `return_paint_consumption` (remains unregistered)

## Why not Model A

| Required truth | Status |
|----------------|--------|
| Owner component | Intended volum aluminum / finish — OK for emission gate |
| Surface geometry | Could reuse wrap-band area — not sufficient alone |
| Paint yield (m²/tub or ml/tub) | **Absent** as component-owned technical constant |
| Coat count | **Absent** |
| Authorized waste for paint | **Absent** |
| Unit | `buc` (tub) — conversion from area missing |

Existing `ceil_quote_input_quantity` uses operator/estimate `paint_tube_count` / `estimated_paint_tubes` — different formula, not auto-derived technical consumption.

## Freeze behavior (this build)

When gate `return_finish_type=ral_paint` matches:

```text
quantity = null
quantity_status = source_missing
quantity_model = A   # declared intent, unresolved
```

No invent from Inventory, Pricing Registry, or industrial defaults.

## Mutual exclusion

- Stock / white aluminum → no paint emission  
- Oracal wrap → no paint emission  
- RAL paint → emit requirement with null until yield owned  

## Next Owner decision needed

Authorize paint yield + coats (and optional waste) on the return/finish component path before Model A.
