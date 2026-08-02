# Worklog — Golden Pilot Controlled Employee Assignment V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Worktree | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Base | `75e31d46` Establish employee eligibility read model (pushed) |
| Verdict | PASS WITH WARNINGS |

## What shipped

- Controlled assignment path: eligibility revalidation → `assign_plan_task` on `operational_tasks[]` only.
- API default `controlled=true`; legacy tests use `controlled=false`.
- Ops-Graph: Neasignat / Eligibili / Alege angajat / Asignat — candidates from GET eligibility only.
- QA assign: 973019 LED install → Andrei (7); PREPRESS remains blocked.

## Proof

- Targeted pytest: 14 passed.
- Live rejects: PREPRESS, ineligible, conflict; idempotent same-employee.
- Protected orders through 973018 hash-stable; 973019 snapshot stable; one assignment field set.
- Screenshots under `docs/qa/golden-pilot-controlled-employee-assignment-v1/screenshots/`.

## Non-goals held

No sessions, actuals, auto-assign, PREPRESS auth invention, migrations, shell redesign.

## Next

Functional: Sessions / ExecutionActuals controlled vertical slice.  
UI: App Shell + Day Mode Foundation (baseline recorded separately).
