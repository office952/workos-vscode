# BACK_BEVEL_EXECUTION_GROUPING_PROOF

```text
OWNER GO = 1 + 3
EXECUTION_TASK_COUNT_DELTA = 0
BEVEL_AND_BACK_CUT_SAME_TASK = YES
SEPARATE_BEVEL_TASK_CREATED = NO
```

## After (implemented)

Bounded merge only for this pair:

```text
cnc_backing_cutting_forex_10mm
+ cnc_backing_bevel_forex_10mm
→ ONE candidate task
  id = cnc_op:cnc_backing_cutting_forex_10mm
  seed = cnc_backing_cutting
  title = CNC spate Forex 10 mm / pregătire spate
```

Commercial lines stay separate. Technical operation identity stays on `cnc_operation_candidates`.

Face CNC cut/bevel remain 1:1. No new grouping framework.

## Runtime (QA clones, Owner unread-only)

| | OFF `ce8f2b4e-…` | ON `a1598742-…` |
|--|--|--|
| Production candidate tasks | 16 | 16 |
| Generation task candidates | 21 | 21 |
| Bevel operation row | absent | `cnc_backing_bevel_forex_10mm` (7.4175 ml, 2 passes) |
| Separate bevel task | NO | NO |
| Backing CNC task title | Debitare CNC spate Forex 10 mm | CNC spate Forex 10 mm / pregătire spate |

```text
COMMERCIAL_SERVICE ≠ SEPARATE_PRODUCTION_TASK
```
