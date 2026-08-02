# Service-level coverage review

## Denominator (accepted)

```text
F6-LED     = fixture izolată service-level (880061)
F6-ACM     = fixture izolată service-level (880062)
F6-PROFILE = fixture izolată service-level (880063)
product-linked ProductDefinition → closure = 0
```

## Family distinctness

| Dimension | F6-LED | F6-ACM | F6-PROFILE |
|-----------|--------|--------|------------|
| Units | buc | mp + buc | ml + buc |
| Materials | LED modules + PSU | ACM sheet + fasteners | profile + adhesive |
| Tasks | LED_WIRE | CUT_ACM / V_GROOVE | FORM_PROFILE / BOND |
| Machine | not_applicable | applicable_optional → unavailable | not_applicable |
| Consumption | buc issues | multi-unit issues + full return path | ml issues + partial return |
| Closure | close → reopen → scrap → reclose | open for return proof | open for return proof |

Not clones of 880041; not renamed copies of one another.

## Not claimed

- ProductDefinition compilation for real products
- ProductAggregate frozen snapshot E2E
- product-linked task_contract / task_rules
- operational task materialization from real order
- product → closure E2E
