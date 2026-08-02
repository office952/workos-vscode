# Machine applicability review

## Claim under review

```text
machine applicability citește și ExecutionPlan.tasks.machine_id
```

## Independent checks

| # | Question | Verdict |
|---|----------|---------|
| 1 | Does reading `machine_id` establish applicability only? | YES — `_machine_cost_category` |
| 2 | Does it invent usage or actual cost? | NO — returns `value: None`, `available: False` |
| 3 | Missing actual facts remain unavailable? | YES — `REASON_MACHINE_ACTUAL_NOT_CAPTURED` |
| 4 | Task assignment ≠ usage proof? | YES — no usage ledger consulted for money |
| 5 | Tests separate applicability vs actual? | YES — F6 ACM + LED assertions |
| 6 | Pricing Registry touched? | NO |
| 7 | Hourly fallback used? | NO |

## Disposition

```text
ACCEPTABLE — machine_id used only for applicability classification
```

If assignment had been converted into cost without usage: PUSH BLOCKER. Not observed.
