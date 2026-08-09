# Controlled scenarios (pytest)

| # | Scenario | Result |
|---|----------|--------|
| 1 | Single material issue + catalog cost change | Historical total stays C1 |
| 2 | Multi material (plexi + Oracal + return) | Separate lines; correct sum |
| 3 | Same Oracal on two tasks | Separate task lines; no merge loss |
| 4 | Issue then partial return | Net quantity/cost |
| 5 | Legacy stock reversal | Consumption excluded; incomplete if none left |
| 6 | planned_bom source | 422 rejected |
| 7 | Missing unit cost | incomplete / fail-closed |
| 8 | RM embed | `material_input` present on Actual RM |
| 9 | New session after commit | Same totals (DB durability) |

Suite: `tests/test_v1_material_actuals_sufficiency.py`
