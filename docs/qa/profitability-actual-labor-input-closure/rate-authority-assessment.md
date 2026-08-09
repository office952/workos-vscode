# Employee cost / rate authority — READ ONLY

## Candidates

| Authority | Classification | Notes |
|-----------|----------------|-------|
| `RoleSkillLaborCostPolicy.standard_internal_rate` + `effective_from`/`effective_to` | CANDIDATE / PARTIAL | Dated role+skill internal rate |
| Freeze → `ActualLaborCostLine` at job closure | PARTIAL historical freeze | Requires `actual_cost_policy_runtime_v1` on session |
| Live employee salary / HR cost | UNSAFE | Not job labor cost authority |
| Workcenter / commercial rates | LEGACY / wrong layer | Must not price historical labor |
| Per-employee historical salary snapshot | MISSING | Not present |
| Order-time commercial labor snapshot | UNKNOWN/LEGACY for internal cost | Commercial ≠ internal actual |

## Critical question

> If an employee rate changes tomorrow, what rate should profitability use for work done yesterday?

**Current answer (factual, not assumed):**

- Time provenance is stable (this closure).
- Monetary freeze path can match a **role/skill policy** by session timestamps and freeze `rate_used` onto `ActualLaborCostLine`.
- Freeze still reads **live `employee.role`** at freeze time (not a proven role-at-work-time snapshot).
- Sessions without `actual_cost_policy_runtime_v1` fail closed for money.
- No proven per-employee historical rate snapshot authority.

```text
LABOR_COST_RATE_AUTHORITY = PARTIAL
HISTORICAL_RATE_STABILITY = UNPROVEN
HISTORICAL_LABOR_RATE_SNAPSHOT_GAP = YES (employee-level / role-at-work-time)
```

## Recommendation

Do **not** authorize monetary Profitability next.
Next domain:

```text
LABOR_COST_RATE_SNAPSHOT_AUTHORITY
```
