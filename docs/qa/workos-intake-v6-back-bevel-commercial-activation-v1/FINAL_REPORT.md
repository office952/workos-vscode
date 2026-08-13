# FINAL_REPORT — Intake V6 back bevel commercial activation V1

```text
OWNER GO = 1 + 3
COMMERCIAL_EFFECT = CORRECT
PRODUCTION_TASK_FRAGMENTATION = NONE
EXECUTION_TASK_COUNT_DELTA = 0
BEVEL_AND_BACK_CUT_SAME_TASK = YES
DOUBLE_CHARGE = NO
OWNER_DEV_DB_MUTATIONS = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```

## What changed

1. Layer/group `backing_mode` reaches quote_input (persist-stripped globals no longer hide șanfren).
2. CPP line `sanfren_spate` = contour ml × 2 passes × CNC_ROUTER 1.5 EUR/ml/pass.
3. `cnc_backing_cutting_forex_10mm` + `cnc_backing_bevel_forex_10mm` fold into **one** backing CNC candidate task.
4. Commercial lines stay separate. Technical op identity stays. Execution task does not split.

## Owner formula proof

`7.41749 ml × 2 × 1.5 = 22.2525 EUR` net. Totals 568.64 / 688.05 → 590.89 / 714.98.

## Lesson for the future unification audit

```text
COMMERCIAL_SERVICE ≠ SEPARATE_PRODUCTION_TASK
```

A priced Servicii line is not automatically a shop-floor task. Exposing 1:1 internal ops to the operator makes the app too technical.
