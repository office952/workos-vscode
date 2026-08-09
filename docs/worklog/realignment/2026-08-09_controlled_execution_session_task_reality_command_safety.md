# Controlled Execution Session / Task Reality Command Safety

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_CONTROLLED_EXECUTION_SESSION_TASK_REALITY_COMMAND_SAFETY`  
**Decision:** `A/B — PASS` (controlled path proven; tests + factual truth sync; no schema/policy expansion)

---

## A. Verdict

```text
CONTROLLED_EXECUTION_SESSION_TASK_REALITY_COMMAND_SAFETY = PASS
HARDENING_APPLIED = YES
HARDENING_SCOPE = isolated_safety_tests + modules Phase B/session factual sync
EVIDENCE_TYPE = CONTROLLED_SESSION_VALIDATION_EVIDENCE
LIVE_WORKSHOP_VALIDATION = NOT_AVAILABLE
```

## B. Repo / HEAD

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = b7aebd04
MACHINE_RUN_V1_E2E = STABLE_BASELINE_AFTER_HARDENING
CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY = PASS
```

## C. Owner GO

Authorized audit + isolated validation + assignment→session boundary + auth/IDOR/CAS/idempotency/txn + ExecutionActuals + bounded hardening without schema/policy expansion + modules factual sync + docs. Not authorized: Phase E, MachineRun↔session coupling, Capacity, PAUSE/RESUME, Profitability write-back, push/PR.

## D. Current execution-reality architecture

Labor work truth lives in `execution_reality.tasks_json` as session observations. Controlled start/end are assignment-gated. Assignment remains on `execution_plan.tasks_json`. MachineRun / reservation / Capacity / commercial are separate. Shop-floor UI is read-only for actions.

## E. Canonical task source

```text
CANONICAL_TASK_SOURCE = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
```

Planned-only rejected (`v2_not_materialized`). No ProductDefinition/Intake fallback on controlled path.

## F. START call graph

See `docs/qa/controlled-execution-session-task-reality-command-safety/call-graph.md`.

```text
POST …/sessions/start → permission execution.task_start
→ resolve employee (self|supervisor)
→ operational task + assigned match + active employee
→ FOR UPDATE reality → append in_progress observation (server UTC)
```

## G. END call graph

```text
POST …/sessions/end → same permission
→ assigned match + active session for employee
→ FOR UPDATE → close session, duration from timestamps
→ task_auto_completed = false
```

## H. Assignment / session boundary

Assignment does not create sessions. START requires current `assigned_employee_id`. Unassigned / wrong employee rejected. Proven in isolated tests.

## I. START scenarios

Valid / duplicate idempotent / concurrent one-winner / unassigned / wrong employee / inactive / forged / cross-order / employee-elsewhere — all classified in scenario matrix.

## J. END scenarios

Normal end, end-without-start reject, duplicate end idempotent, duration ownership, no auto-complete.

## K. Task-state guards

Active primary blocks second start; employee active elsewhere blocked; completed/history blocks Phase B reassignment (via session-history guard).

## L. Resource-state guards

Controlled START does **not** require Resource State CLEAR (factual contract). Not invented. Capacity remains IMPLEMENTED_INACTIVE.

## M. MachineRun boundary

```text
MACHINE_RUN_MUTATIONS = 0
```

No auto-create/start/end of MachineRun from session commands. QA machine_runs=0.

## N. Auth

`execution.task_start` for controlled start/end: admin/manager/operator. Viewer 403 proven. Actuals read: `execution.production_blueprint`.

## O. IDOR / security

Forged task, cross-order task, wrong employee → reject, zero mutation. Supervisor may name employee_id but domain revalidates assignment match.

## P. Timestamp truth

Controlled path: server `datetime.now(timezone.utc)` (injectable clock in tests). Raw legacy path accepts client timestamp — `ACTIVE_LEGACY` review note, not controlled path.

## Q. Duration truth

```text
ACTUAL_DURATION_SOURCE = ended_at - started_at
```

No PAUSE exclusion. Planning minutes not overwritten.

## R. Multiple-employee behavior

Controlled V1: one active primary session per task; employee cannot hold two active task sessions. Helper path remains ACTIVE_LEGACY collab (separate).

## S. Active-session / reassignment boundary

Active/any execution history → Phase B REASSIGN/UNASSIGN → `task_has_execution_history`.

## T. Phase E boundary

```text
EXPECTED_REASSIGNMENT_PHASE_E_BOUNDARY
REASSIGNMENT_PHASE_E = FAIL_CLOSED_DEFERRED
```

## U. CAS

`execution_reality` row `FOR UPDATE` + active-session predicates. No second invented version field.

## V. Idempotency

Natural-key: `already_active` / `already_ended` without rewriting timestamps. No client idempotency-key header on controlled sessions.

```text
IDEMPOTENCY = PROVEN
```

## W. Concurrency

Two concurrent STARTs → one active observation (isolated two-session gather).

## X. Transaction rollback

Session observation write is the actual write (single JSON document commit). No orphan dual-store.

```text
TRANSACTIONALITY = PROVEN
```

## Y. Restart durability

Commit → re-query reality → active session intact; after END timestamps stable.

## Z. Read-after-write parity

START/END response fields match persisted observation; ExecutionActuals projection matches closed totals.

## AA. ExecutionActuals

Read model: per-task session_count, active flag, total_actual_duration_minutes, first/last timestamps, planned/variance (planned preserved separately). No price fields.

## AB. HR / privacy

No salary/hourly/HR private fields in controlled responses. Employee id + name for operational identity only.

## AC. Commercial boundary

```text
COMMERCIAL_MUTATIONS = 0
EMPLOYEE_COST_USED_FOR_PRICING = NO
```

## AD–AF. Scheduling / Capacity / machine assignment

```text
SCHEDULING_MUTATIONS = 0
CAPACITY_MUTATIONS = 0
MACHINE_ASSIGNMENT_MUTATIONS = 0
```

## AG. Scenario matrix

25 scenarios — see evidence `scenario-matrix.md`.

## AH. Hardening applied

1. New isolated suite `tests/test_controlled_session_command_safety.py` (10 proofs).  
2. Modules/governance factual sync in `currentTruthControlCenter.ts` (Phase B SAFETY_PROVEN vs Phase E deferred; Execution Reality limitation honesty).

No product schema/policy expansion. No Phase E. No MachineRun changes.

## AI. Regression

```text
85 passed
```

## AJ. Browser / UI truth

Shop-floor RO; no assigned=working conflation observed. Modules Phase B stale label corrected and verified in browser.

## AK. Modules / Governance

```text
MODULES_IMPACT = factual sync Phase B proven / Phase E deferred / session≠MachineRun
GOVERNANCE_IMPACT = same PresentTruth source (currentTruthControlCenter)
```

## AL. Dead Pieces

| Piece | Class |
|-------|-------|
| Controlled sessions start/end + actuals GET | `ACTIVE_CANONICAL` |
| Mobile assigned start/complete | `ACTIVE_CANONICAL` |
| Raw `/reality/start|end` | `ACTIVE_LEGACY` / `BYPASS_RISK` (no assignment; client ts) |
| Operator task-action | `ACTIVE_LEGACY` / `BYPASS_RISK` |
| claim / start-from-available | `FROZEN` |
| Helper sessions | `ACTIVE_LEGACY` |
| Shop-floor actions | `DEAD_CANDIDATE` (monitor only) |
| Controlled FE client | missing (`UNKNOWN`/absent) |

## AM. Profitability labor-input readiness

```text
PROFITABILITY_LABOR_INPUT_READINESS = PARTIAL
```

Ready facts on controlled closed sessions: employee, task, order/plan, started/ended, duration. Blockers for READY: legacy writers can still append labor without assignment gate; rates intentionally deferred.

## AN. QA proof

```text
QA_START_COMMANDS = 0
QA_END_COMMANDS = 0
QA_MUTATIONS = 0
plan 23 · assigned 1 · transitions 7 · machine_runs 0 · sessions table absent / reality untouched for QA
```

## AO. Schema

```text
DB_SCHEMA_CHANGES = 0
ALEMBIC_REVISION_CREATED = NO
```

## AP. Docs / evidence

```text
docs/worklog/realignment/2026-08-09_controlled_execution_session_task_reality_command_safety.md
docs/qa/controlled-execution-session-task-reality-command-safety/
```

## AQ. Commits

1. tests + modules factual sync  
2. docs/evidence  

## AR. No-push

```text
PUSH = NO
```

## AS. Next roadmap recommendation

```text
NEXT_ROADMAP_DOMAIN = LEGACY_SESSION_WRITE_PATH_ASSIGNMENT_GATE_CLOSURE
NEXT_TASK = NOT_AUTHORIZED
```

Close or freeze-bypass operator/raw start writers that share `execution_reality.tasks_json` without assignment gate — prerequisite before treating labor actuals as exclusive profitability input. Do not auto-start Phase E / Capacity / MachineRun coupling.

---

## PASS block

```text
CONTROLLED_EXECUTION_SESSION_TASK_REALITY_COMMAND_SAFETY = PASS
CANONICAL_TASK_SOURCE = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
CANONICAL_START_COMMAND = VERIFIED
CANONICAL_END_COMMAND = VERIFIED
ASSIGNMENT_SESSION_BOUNDARY = VERIFIED
VALID_START = VERIFIED
DUPLICATE_START = SAFE
CONCURRENT_START = SAFE
VALID_END = VERIFIED
END_WITHOUT_START = SAFE
DUPLICATE_END = SAFE
CONCURRENT_END = SAFE
AUTHORIZATION = VERIFIED
IDOR_PROTECTION = VERIFIED
TASK_STATE_GUARDS = VERIFIED
RESOURCE_STATE_GUARDS = VERIFIED_NOT_REQUIRED_ON_CONTROLLED_START
CAS_CONCURRENCY = PROVEN
IDEMPOTENCY = PROVEN
TRANSACTIONALITY = PROVEN
RESTART_DURABILITY = PROVEN
READ_AFTER_WRITE_PARITY = VERIFIED
EXECUTION_ACTUALS = VERIFIED
ACTUAL_DURATION_SOURCE = ended_at - started_at
ASSIGNMENT_MUTATIONS_FROM_SESSION = 0
MACHINE_RUN_MUTATIONS = 0
SCHEDULING_MUTATIONS = 0
CAPACITY_MUTATIONS = 0
MACHINE_ASSIGNMENT_MUTATIONS = 0
COMMERCIAL_MUTATIONS = 0
EMPLOYEE_COST_USED_FOR_PRICING = NO
REASSIGNMENT_PHASE_E = FAIL_CLOSED_DEFERRED
DB_SCHEMA_CHANGES = 0
NEW_FEATURES = 0
HARDENING_APPLIED = YES
HARDENING_SCOPE = isolated_safety_tests + modules_factual_sync
QA_START_COMMANDS = 0
QA_END_COMMANDS = 0
QA_MUTATIONS = 0
MODULES_IMPACT = Phase B SAFETY_PROVEN vs Phase E DEFERRED sync
GOVERNANCE_IMPACT = same PresentTruth source
PROFITABILITY_LABOR_INPUT_READINESS = PARTIAL
LIVE_WORKSHOP_VALIDATION = NOT_AVAILABLE
EVIDENCE_TYPE = CONTROLLED_SESSION_VALIDATION_EVIDENCE
NEXT_ROADMAP_DOMAIN = LEGACY_SESSION_WRITE_PATH_ASSIGNMENT_GATE_CLOSURE
NEXT_TASK = NOT_AUTHORIZED
```

```text
Roadmap awareness: 8/10
Cât sunt în direcția stabilită: 95/100%
Metoda de lucru și logica abordării:
  Inventory actual routes → prove controlled assignment-gated path on isolated DB
  → cross-domain reassignment fail-closed → factual modules sync → docs
Ce este demonstrat tehnic:
  Controlled START/END safety, actuals parity, restart durability, Phase E fail-closed
Ce NU este validat fără atelier live:
  Operator frequency/preferences, shop-floor ergonomics, real workshop cadence
Ce rămâne intenționat separat:
  Legacy write-path closure, Phase E, Capacity, MachineRun↔session, profitability rates
Dead Pieces Check:
  Catalogued; BYPASS_RISK left for next authorized domain
Forbidden Scope Respected:
  YES
```
