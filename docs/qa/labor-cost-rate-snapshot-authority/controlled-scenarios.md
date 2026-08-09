# Controlled scenarios

```text
pytest tests/test_labor_cost_rate_snapshot_authority.py -q
→ 13 passed
```

| # | Scenario | Result |
|---|----------|--------|
| 1 | Single closed session + stable rate | 60 RON for 1h @ 60/h |
| 2 | Multi-session same employee | costs sum |
| 3 | Multi-employee | costs sum; no wall-clock dedupe |
| 4/11/12 | Rate change + hostile policy edit after freeze | frozen line unchanged; re-finalize existing=1 |
| 5 | Role change before finalize | still operator / R1 |
| 6 | Skill change on plan after work | session skill wins |
| 7 | Rate change between sessions | S1@60 + S2@90 |
| 8 | Employee inactive + role changed | history stable |
| 9/10 | Restart / repeat finalize | deterministic same amount |
| 13 | Machine declared on task | labor cost = employee only |
| 14–16 | Payroll/commercial/labor-input boundaries | salary unused; plan/session unchanged |
| 20 | QA 880750 | untouched |
| — | START snapshots role/skill | proven |

Implementation decision: **B — BOUNDED_EXISTING_PATH_CLOSURE**.
