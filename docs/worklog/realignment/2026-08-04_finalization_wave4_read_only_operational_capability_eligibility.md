# Finalization Wave 4 — Read-only Operational Capability & Eligibility

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Mini decision | `FINALIZATION_WAVE_4_GO = GRANTED_WITH_STRICT_READ_ONLY_SCOPE` |
| Scope | Workcenter→machine capability RO + employee role/skill eligibility RO + factual UI on `/execution/:order_id` |
| Exclusions | assignment, machine assignment, sessions, attendance, scheduling, capacity, Employee Mobile, pricing/ORR mutations |
| Repo | `C:\Users\offic\workos_app_vs` (common git) |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `1e8d3344` |
| Ancestry | `788171b4`, `f6dfe4e3`, `cdb6e7ac`, `1e8d3344` ⊂ HEAD |
| Verdict | `FINALIZATION_WAVE_4 = PASS` |

## Solution chosen

**Compose existing canonical services (option C)** + minimal honesty hardening:

| Surface | Canonical source |
| ------- | ---------------- |
| Machine capability | `GET …/resource-readiness` (F7C) |
| Employee eligibility | `GET …/employee-eligibility` (DEC-015) |
| Task source | `execution_plan.tasks_json.operational_tasks[]` only |
| UI | `ResourceReadinessPanel` + new `EmployeeEligibilityPanel` on `ExecutionDetail` |

Rejected: new parallel registries, new endpoint family, schema/migration, docs-only (eligibility was missing on ExecutionDetail).

## Architecture notes

- Frozen workcenter on operational task is never rewritten by live ORR.
- Live ORR ∩ machines registry used only for capable-machine candidates.
- Live employee authorizations used only for eligible-candidate lists.
- `wave4_boundary`: assignable/machine_assignable/schedulable/sessions = false.
- Machine candidates carry `assignment_status=unassigned`, `reservation_status=not_reserved`, `match_provenance`.
- Availability/calendar not evaluated (`availability_status=not_evaluated`).
- Planning minutes remain null with warning; scheduling HOLD.

## Runtime proof (fixture 880750 / plan 23)

| Check | Result |
| ----- | ------ |
| Backend | `:8001` worktree uvicorn, `APP_ENV=development`, DB `backend/dev.db` |
| Frontend | `:3000` Vite with `BACKEND_PORT=8001` |
| Resource readiness | status=ok · ops=13 · warn=13 · blocked=0 · assignable=false |
| Employee eligibility | status=ok · ops=13 · ready/warn=11 · blocked=2 · side_effects=none |
| Plan | ops=13 · `execution_tasks_created=true` · readiness `v2_operational_ready` (API/UI) |
| tasks_json sha (after GETs) | `e120b0cb…` unchanged by reads |
| plan `updated_at` | `2026-08-04 02:21:47.122899` unchanged by reads |
| Protected 880811 | total **1847.5** · ops=5 · plan 22 unchanged |
| Protected 973019 | total **847.5** · ops=18 · plan 21 unchanged |
| F7I | 15 / 1.5 / 35 / 20 EUR · 4/4 identities unchanged in `commercial_rules_volumetric_v2.py` |
| Assignments / sessions | 0 / 0 |
| Forbidden UI buttons | absent (Assign/Materialize/Schedule/Start) |

Local screenshots (not committed):

- `docs/qa/workos-wave4-read-only-capability-eligibility-v1/screenshots/wave4-880750-1920-light.png`
- `…/wave4-880750-1920-eligibility.png`
- `…/wave4-880750-1366-light.png`

Dark: NOT_OFFICIALLY_SUPPORTED for this GO (light/day primary).

## Tests

- Backend: `test_finalization_wave4_read_only_capability_eligibility.py` + F7C + DEC-015 suites — PASS
- Frontend: eligibility/resource display + TruthPanel readiness — PASS (targeted)

## Dead pieces (read-only)

| Piece | Class |
| ----- | ----- |
| Ops-Graph assignment picker UI | ACTIVE_LEGACY / out of Wave 4 ExecutionDetail path |
| Frontend `operationEligibility.ts` | COMPATIBILITY_BRIDGE (admin registry tooling) |
| `machine_type` as WC fallback in eligibility helper | DEVIATED (pre-existing; not removed) |
| Docs still saying DEC-009 pending | SUPERSEDED by Wave 3/4 records |

Dead pieces removed: **NONE**.

## Scores

- Direction alignment: **90/100**
- Operational completion: **48/100** (eligible/capable ≠ assigned/schedulable)

## Exact next step

**DO NOT START ASSIGNMENT.** Owner reviews Wave 4. Recommended unauthorized Wave 5: controlled assignment audit-only / command contract research with zero mutation.

## Honest opinion

F7C + DEC-015 already solved the hard matching math; Wave 4’s value was composing them honestly on the operator Execution page with fail-closed Wave 4 boundary fields and zero-mutation proof on the durable fixture.
