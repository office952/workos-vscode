# Profitability Actual Labor Input Contract

**Status:** CLOSED (factual time provenance)  
**Contract id:** `profitability_actual_labor_input/v1`  
**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE`

## Separation (non-negotiable)

```text
Session / Execution Reality
  → employee/time provenance
  → ACTUAL LABOR INPUT          ← this contract
       + approved historical rate authority
  → ACTUAL LABOR COST           ← NOT authorized here
       + other actuals + commercial revenue snapshot
  → PROFITABILITY               ← NOT authorized here
```

Do not collapse labor time, labor cost, margin, or client price.

## Write authority (upstream)

```text
EXECUTION_REALITY_WRITE_AUTHORITY = controlled_task_session_service
ACTIVE_LEGACY_UNSAFE = 0
```

Canonical writers: `start_controlled_task_session` / `end_controlled_task_session` /
`complete_controlled_task_session`. Compatibility bridges delegate to the same authority.

## Canonical source

| Item | Value |
|------|--------|
| SoT | `execution_reality.tasks_json` session rows |
| Task identity | ExecutionPlan V2 `operational_tasks[]` |
| Read helper | `build_profitability_actual_labor_input` |
| Persistence of labor totals | **None** (derived only) |
| MachineRun | **Excluded** (`machine_run_included=false`) |

## Closed-session rule

| Runtime state | Contribution |
|---------------|--------------|
| Active (`is_session_active`) | Listed under `active_sessions`; **not** in finals |
| Closed (`ended_at` present, valid) | Eligible for final aggregation |
| Invalid (bad timestamps / missing employee / orphan task) | Listed under `invalid_sessions`; **not** counted |

`END session ≠ task complete`. Closed labor remains queryable while the task is still incomplete.

## Duration authority

```text
CANONICAL_DURATION_SOURCE = ended_at - started_at
CANONICAL_DURATION_UNIT   = minutes   (stored / aggregated)
SECONDS_DERIVED           = int(total_seconds) from absolute timestamps
ROUNDING_RULE             = python_round_half_to_even_seconds_over_60_to_int_minutes
```

- No client-provided duration authority.
- Duration does not depend on browser/local timezone (absolute ISO timestamps).
- Prefer high-precision seconds for future cost boundaries; minutes remain the existing session field.

## Field ownership

| Field | SOURCE | OWNER | STORED_OR_DERIVED | CANONICALITY |
|-------|--------|-------|-------------------|--------------|
| `order_id` | request / plan | Orders | stored key | CANONICAL |
| `execution_plan_id` | ExecutionPlan | ExecutionPlan | stored | CANONICAL |
| `task_id` / task_key | operational task | ExecutionPlan V2 | stored on session + plan | CANONICAL |
| `employee_id` | session row | controlled writer | stored | CANONICAL |
| `session_id` | session row | controlled writer | stored | CANONICAL |
| `started_at` / `ended_at` | server clock | controlled writer | stored | CANONICAL |
| `actual_duration_minutes` | ended−started (or stored duration_minutes) | session SoT | stored + re-derivable | CANONICAL |
| `actual_duration_seconds` | ended−started | labor input helper | derived | CANONICAL (precision) |
| `workcenter` | operational task | plan | projected | FACTUAL if present |
| `planned_minutes` | `estimated_time_minutes` | plan | projected read-only | PLANNED (never overwritten) |
| rates / money | — | — | — | **OUT OF SCOPE** |

## Aggregation

Derived from session-level closed truth (no duplicate stored totals):

| Level | Rule |
|-------|------|
| SESSION | one closed session record |
| EMPLOYEE + TASK | sum session minutes/seconds |
| TASK | sum employee-minutes on task |
| EXECUTION_PLAN | sum all closed sessions on plan |
| ORDER | equal to plan under current 1-plan-per-order architecture |

**Multi-employee:** sum employee-minutes. Two employees working the same wall-clock 30 minutes ⇒ **60 employee-minutes**. No wall-clock dedupe.

**Multi-session same employee/task:** sum; never “latest wins”.

**Overlapping policy (writer):** concurrent primary sessions on the same task are blocked (`active_session_exists`); same employee active elsewhere blocked (`employee_active_elsewhere`). Aggregation still sums any closed rows present in SoT.

## Planned vs actual

```text
PLANNED_LABOR = operational_tasks[].estimated_time_minutes
ACTUAL_LABOR  = sum(closed session durations)
```

Actual never overwrites planned. Variance is optional/honest and may remain unavailable at aggregate level.

## MachineRun separation

```text
MACHINE_RUN_LABOR_DOUBLE_COUNT = NO
```

Labor input uses employee sessions only. Machine runtime is a separate future actual input.

## Profitability boundary

Profitability **MAY** consume: closed-session labor provenance, future approved labor-cost snapshot, other closed actuals, commercial revenue snapshot.

Profitability **MUST NOT**: rewrite sessions, rewrite execution plan, change assignments/lifecycle, reprice quote, feed commercial values back into Order/Quote, change employee rates.

One-way consumption.

## Rate / cost authority (read-only assessment)

| Candidate | Classification |
|-----------|----------------|
| `RoleSkillLaborCostPolicy` + freeze → `ActualLaborCostLine` | CANDIDATE / PARTIAL dated role-skill internal rate |
| Live `employee` salary / HR cost | UNSAFE for job labor cost |
| Workcenter commercial rates | LEGACY / wrong layer |
| Per-employee historical salary snapshot | MISSING |

```text
LABOR_COST_RATE_AUTHORITY   = PARTIAL
HISTORICAL_RATE_STABILITY   = UNPROVEN
PROFITABILITY_MONETARY_CALCULATION = NOT_AUTHORIZED
```

Freeze path requires `actual_cost_policy_runtime_v1` on sessions and matches role/skill policy by timestamp, but still reads live `employee.role` at freeze time and is not a proven per-employee historical rate snapshot. **Do not build monetary Profitability next.**

## Consumer wiring

- Helper: `backend/services/profitability_actual_labor_input_service.py`
- Embedded (no new HTTP endpoint): `ProfitabilityActualReadModelService` → `actual_operational_truth.labor_input`
- Existing ExecutionActuals RM remains task-level projection; labor input is the session-level canonical contract for Profitability time.

## Explicit non-goals

- Profitability dashboard / UI
- CPP / client pricing
- Employee rate activation
- Payroll / attendance merge
- Schema migration
- REASSIGNMENT_PHASE_E / Capacity / MachineRun changes
