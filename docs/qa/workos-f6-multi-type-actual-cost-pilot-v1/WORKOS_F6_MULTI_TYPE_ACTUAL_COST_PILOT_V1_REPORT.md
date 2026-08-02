# WorkOS F6 — Multi-Type Actual-Cost Pilot V1

**Stamp:** `PASS WITH WARNINGS` / documented coverage
**Base:** `4ec3d384`
**Controller:** `C:\w\psiso`

## Verdict language

```text
Representative multi-type actual-cost pilot PASS for the tested families.
Platform-wide Profitability Complete remains NOT READY.
Product-linked end-to-end families = PILOT_COVERAGE_BLOCKED until Owner materialization GO.
```

## Pilot families (operationally distinct, isolated)

| Family | Order | Units | Tasks | Machine | Distinctness |
|--------|------:|-------|-------|---------|--------------|
| F6-LED | 880061 | buc | LED_WIRE | not_applicable | electrical modules |
| F6-ACM | 880062 | mp + buc | CUT_ACM / V_GROOVE | applicable_optional → unavailable | sheet ACM CNC path |
| F6-PROFILE | 880063 | ml + buc | FORM_PROFILE / BOND | not_applicable | linear profile forming |

These are service-level families proving StockMovement + labor policy + closure. They are **not** claimed as frozen ProductDefinition/ProductAggregate product proofs.

## Coverage denominator

```text
eligible operational families proven in isolated tests = 3
product-linked frozen→closure families proven = 0
applicable categories considered per family = labor, material, machine, other_direct, closure
```

## Gap closed in this round

Profitability machine applicability now also reads ExecutionPlan task declarations (`machine_id`), without inventing usage or rates.

## Limitations

- No real product materialization for ACM/letters/profile finished jobs
- Machine remains unavailable (no usage + dated policy)
- Other-direct remains not_applicable (no classified ledger)
- 92401 / 973019 not used as closure pilots (historical / not materialized)
