# 2026-08-09 — Labor Cost Rate Snapshot Authority

## Owner GO

```text
AUTHORIZE_LABOR_COST_RATE_SNAPSHOT_AUTHORITY
```

## Starting state

```text
HEAD = 7dfc2013
PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE = PASS
LABOR_COST_RATE_AUTHORITY = PARTIAL
HISTORICAL_RATE_STABILITY = UNPROVEN
```

## Decision

```text
BOUNDED_EXISTING_PATH_CLOSURE
DB_SCHEMA_CHANGES = 0
```

Existing `RoleSkillLaborCostPolicy` + `ActualLaborCostLine` already froze `rate_used`.
Gap closed: controlled session START now snapshots `role_code` / `skill_code`;
`finalize_labor_lines` prefers those work-time inputs over live `employee.role`.

## Code

| File | Change |
|------|--------|
| `controlled_task_session_service.py` | Snapshot role/skill at START |
| `actual_cost_policy_runtime_service.py` | Resolve freeze role from session first |
| `test_labor_cost_rate_snapshot_authority.py` | Historical scenario matrix |
| `currentTruthControlCenter.ts` | Factual sync |

## Verdict

```text
LABOR_COST_RATE_SNAPSHOT_AUTHORITY = PASS
HISTORICAL_RATE_STABILITY = PROVEN
HISTORICAL_COST_DETERMINISM = PROVEN
PROFITABILITY_ACTUAL_LABOR_COST_READINESS = READY
PROFITABILITY_MONETARY_CALCULATION = NOT_STARTED
NEXT_ROADMAP_DOMAIN = MASTER_FINALIZATION_ROADMAP_RECONCILIATION
NEXT_TASK = NOT_AUTHORIZED
```

Do **not** open another labor/rates deep-dive. Next: master finalization roadmap reconciliation.
