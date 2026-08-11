# COMMERCIAL_ADJUSTMENT_ORDER

Verified against existing backend + historical evidence before implementation.

## Canonical order (unchanged)

```
CPP commercial_base_subtotal
→ + markup% (Adaos on base)
→ + manual adjustment in commercial currency
→ − discount% (of base + markup + manual)
→ + VAT%
→ gross
```

## Evidence

- Code: `backend/services/intake_v6_priced_quote_dry_run_service.py` `_apply_commercial_adjustments_to_base`
- Test: `test_dry_run_applies_discount_and_manual_adjustment_on_7g_base`
  - base 1000 + manual 100 → 1100; discount 10% → net 990
- Worklog: `docs/worklog/realignment/2026-07-24_intake_v6_offer_total_visibility_and_adaos_wiring.md`

## Conflict check

Proposed plan order matched existing backend. **No STOP.** Policy A only changes how Manual RON becomes commercial-currency units before the same add step (EUR via FX when presentation is EUR; RON unchanged on RON diagnostic path).

## Rounding

All money steps use existing `_round_money` = `round(float(value), 2)`. Manual RON→EUR uses the same helper (`manual_ron / eur_to_ron_rate`).
