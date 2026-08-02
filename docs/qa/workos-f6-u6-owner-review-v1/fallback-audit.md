# Fallback audit — C3 independent

Searched profitability + F6 path for:

- `workcenter.rate_per_hour`
- `machine_rate_ron_per_hour`
- planned/estimated minutes as actual money
- BOM quantities as consumption
- live catalog prices rewriting history
- default zero for missing categories
- generic other_direct invention

## Result

```text
NO FABRICATED COST
NO HIDDEN FALLBACK
NO CAPACITY-AS-ACTUAL
```

Notes:
- `or 0` in profitability session/minute counters is UI/count aggregation, not cost fabrication.
- ACM `machine_id` sets applicability only; `value` stays `null` / `unavailable`.
- Catalog `unit_cost` mutation after freeze does not rewrite LED material actual (F6 test).
