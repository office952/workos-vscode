# Labor Cost Rate Snapshot Authority

**Status:** CLOSED / PROVEN  
**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_LABOR_COST_RATE_SNAPSHOT_AUTHORITY`  
**Decision:** `BOUNDED_EXISTING_PATH_CLOSURE` (no schema migration)

## Separation

```text
ACTUAL LABOR TIME          = closed sessions (PROVEN)
+ HISTORICAL-SAFE RATE     = this contract (PROVEN)
→ ACTUAL LABOR COST INPUT  = READY for next Profitability monetary slice
≠ client price / payroll / CPP / margin UI
```

## Canonical chain

```text
LABOR_RATE_RESOLUTION_AUTHORITY =
  RoleSkillLaborCostPolicy (effective-dated role + optional skill)
  resolved at session started_at / ended_at
  using role_code + skill_code snapshotted on the session at controlled START
  frozen by finalize_labor_lines → ActualLaborCostLine
```

| Layer | Role |
|-------|------|
| `RoleSkillLaborCostPolicy` | Dated standard internal rate (RON/hour) |
| Session `role_code` / `skill_code` | Work-time resolution inputs (JSON on `execution_reality.tasks_json`) |
| `finalize_labor_lines` | Sole monetary writer for labor actuals |
| `ActualLaborCostLine` | Frozen `rate_used`, `duration_seconds`, `labor_cost_amount`, `policy_id` |

```text
RATE_FREEZE_POINT = finalize_labor_lines (explicit API)
RATE_STORAGE_MODEL = FROZEN_VALUE + POLICY_ID/VERSION_REFERENCE + EFFECTIVE_DATED_MATCH
```

Freeze is **not** session END and **not** automatic inside `close_job`. Closure readiness requires lines already frozen.

## Formula (internal cost only)

```text
labor_cost_amount = round(duration_seconds * rate_used / 3600, 4)
currency          = policy.currency (canonical default RON)
rate_unit         = hour
```

Uses **seconds** from timestamps — not rounded display minutes.  
No FX conversion. Mixed-currency history is out of scope.

## Historical stability rules

1. After a line exists for `(order_id, session_ref)`, re-finalize never rewrites it.
2. Role/skill used for match come from **session snapshot at START**, not live `employee.role` after the fact.
3. Legacy sessions without `role_code` fall back to live `employee.role` (pre-snapshot only).
4. Policy row edits after freeze do not mutate existing lines.
5. Rate change between sessions: each session matches policy at its own timestamps.
6. Inactive/ended employee rows remain attributable; never hard-delete.
7. Employee salary fields (`cost_lunar_firma`, `monthly_internal_pay_amount`) are **never** read.

## Boundaries

| Boundary | Rule |
|----------|------|
| Session truth | Read-only input; no rewrite of times/employee/task |
| ExecutionPlan | Mutations = 0 from this path |
| MachineRun | Not in labor cost |
| Payroll / pontaj | Separate truth |
| Commercial / CPP | Untouched |
| Profitability UI | NOT_STARTED |

## Readiness

```text
HISTORICAL_RATE_STABILITY = PROVEN
HISTORICAL_COST_DETERMINISM = PROVEN
PROFITABILITY_ACTUAL_LABOR_COST_READINESS = READY
PROFITABILITY_MONETARY_CALCULATION = NOT_STARTED
```

READY means duration + stable rate + frozen line + provenance — **not** a finished Profitability product.

## Correction policy

No silent reprice from live config.  
No dedicated labor-cost correction editor in this GO.  
Explicit future correction must be auditable and create new facts — not mutate frozen lines in place without Owner GO.

## Next (do not deepen labor here)

```text
NEXT_ROADMAP_DOMAIN = MASTER_FINALIZATION_ROADMAP_RECONCILIATION
```
