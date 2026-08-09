# Labor Cost Rate Snapshot Authority — REPORT

## A. Verdict

```text
LABOR_COST_RATE_SNAPSHOT_AUTHORITY = PASS
```

## B. Repo / HEAD

```text
worktree = C:\w\psiso
branch   = feat/f7i-owner-rate-activation
baseline = 7dfc2013
```

## C. Owner GO

```text
AUTHORIZE_LABOR_COST_RATE_SNAPSHOT_AUTHORITY
```

## D. Rate source inventory

See `rate-inventory.md`.

## E. Canonical rate authority

```text
LABOR_RATE_RESOLUTION_AUTHORITY =
  RoleSkillLaborCostPolicy → session role/skill at START → finalize_labor_lines → ActualLaborCostLine
```

## F. RoleSkillLaborCostPolicy

Effective-dated role + optional skill; RON/hour; overlap blocked on create; match at timestamp.

## G. ActualLaborCostLine

Sole frozen monetary labor actual; stores `rate_used`, `duration_seconds`, `labor_cost_amount`, `role_code`, `skill_code`, `policy_id`, `policy_version`.

## H. Freeze / version point

```text
RATE_FREEZE_POINT = finalize_labor_lines
RATE_STORAGE_MODEL = FROZEN_VALUE + POLICY_REFERENCE + EFFECTIVE_DATED_MATCH
```

## I–Q. Scenarios

See `controlled-scenarios.md`. Pytest: **13 passed** in `test_labor_cost_rate_snapshot_authority.py`.

## R. Currency

```text
CURRENCY_AUTHORITY = policy.currency (default RON; no FX)
```

## S. Rounding

```text
MONETARY_ROUNDING = round(seconds * rate / 3600, 4)
DURATION_FOR_COST = duration_seconds (not display minutes)
```

## T. Correction policy

No silent reprice. No correction editor invented. Future corrections must be explicit/auditable.

## U–Y. Boundaries

Session / plan / MachineRun / payroll / commercial = untouched by freeze path.

## Z. Duplicate authority

Salary fields and workcenter rates are LIVE_UNSAFE / LEGACY for this contract — not used.

## AA–AJ

Runtime: role/skill snapshot + finalize preference.  
Regression: **51 passed** (rate + labor input + actual cost coverage + session safety + bridge + profitability RM).  
QA: 0 mutations.  
Docs: architecture + worklog + this folder.  
Commits: local only. No push.

## AK. Next

```text
NEXT_ROADMAP_DOMAIN = MASTER_FINALIZATION_ROADMAP_RECONCILIATION
NEXT_TASK = NOT_AUTHORIZED
```

---

### Pass block

```text
LABOR_COST_RATE_SNAPSHOT_AUTHORITY = PASS
LABOR_RATE_RESOLUTION_AUTHORITY = RoleSkillLaborCostPolicy + session work-time role/skill + finalize_labor_lines
RATE_FREEZE_POINT = finalize_labor_lines
RATE_STORAGE_MODEL = FROZEN_VALUE + POLICY_ID/VERSION + EFFECTIVE_DATED
ACTUAL_LABOR_COST_LINE_AUTHORITY = sole frozen monetary labor actual writer
HISTORICAL_RATE_STABILITY = PROVEN
HISTORICAL_COST_DETERMINISM = PROVEN
ROLE_CHANGE_REPRICES_HISTORY = NO
SKILL_CHANGE_REPRICES_HISTORY = NO
CURRENT_RATE_CHANGE_REPRICES_HISTORY = NO
MULTI_SESSION_RATE_HANDLING = VERIFIED
MULTI_EMPLOYEE_RATE_HANDLING = VERIFIED
CURRENCY_AUTHORITY = RON (policy.currency; no FX)
MONETARY_ROUNDING = round(seconds*rate/3600, 4)
SESSION_MUTATIONS = 0
EXECUTION_PLAN_MUTATIONS = 0
MACHINE_RUN_MUTATIONS = 0
PAYROLL_MUTATIONS = 0
COMMERCIAL_PRICE_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
PROFITABILITY_ACTUAL_LABOR_COST_READINESS = READY
PROFITABILITY_MONETARY_CALCULATION = NOT_STARTED
QA_MUTATIONS = 0
NEXT_ROADMAP_DOMAIN = MASTER_FINALIZATION_ROADMAP_RECONCILIATION
NEXT_TASK = NOT_AUTHORIZED
```
