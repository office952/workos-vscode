# MachineRun — Terminal membership re-eligibility hardening fix

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_TERMINAL_MEMBERSHIP_REELIGIBILITY_HARDENING_FIX`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `097d03db`  
**Verdict:** **PASS**

---

## A. Verdict

```text
MACHINE_RUN_TERMINAL_MEMBERSHIP_REELIGIBILITY_HARDENING_FIX = PASS
BUG = TERMINAL_MEMBERSHIP_REELIGIBILITY
TECHNICAL_SEVERITY = S3
OPERATIONAL_FREQUENCY = UNKNOWN
ACTIVE_MEMBERSHIP_RULE = PARTICIPANT_ACTIVE_AND_RUN_NON_TERMINAL
RELEASED_REELIGIBILITY = VERIFIED
CANCELLED_REELIGIBILITY = VERIFIED
COMPLETED_RESERVED_STILL_BLOCKS = VERIFIED
RUNNING_STILL_BLOCKS = VERIFIED
RESERVED_STILL_BLOCKS = VERIFIED
HELD_STILL_BLOCKS = VERIFIED
REMOVED_NON_BLOCKING = VERIFIED
HISTORICAL_PROVENANCE = PRESERVED
BY_TASK_PARITY = VERIFIED
CANDIDATE_PARITY = VERIFIED
CREATE_WRITER_PARITY = VERIFIED
ADD_WRITER_PARITY = VERIFIED
R6_BEHAVIOR_CHANGED = NO
DB_SCHEMA_CHANGES = 0
NEW_ENDPOINTS = 0
NEW_UI_FEATURES = 0
CONTROLLED_BROWSER_PROOF = API_AND_PYTEST_VERIFIED
QA_MUTATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
MACHINE_RUN_V1_E2E = STABLE_BASELINE_AFTER_HARDENING
PAUSE_RESUME = DEFERRED
REASSIGNMENT_PHASE_E = DEFERRED
EMPLOYEE_SESSION_COUPLING = DEFERRED
NEXT_FEATURE_DOMAIN = UNSELECTED
NEXT_TASK = NOT_AUTHORIZED
```

---

## B–C. Repo / GO

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 097d03db
OWNER GO = AUTHORIZE_MACHINE_RUN_TERMINAL_MEMBERSHIP_REELIGIBILITY_HARDENING_FIX
```

---

## D–E. Reproduction / root cause

**Before:** After RELEASE/CANCEL, `participant.status` stayed `ACTIVE` while run was terminal.  
`by-task` filtered terminal runs (correct). Candidate discovery + CREATE used `status=ACTIVE` alone → blocked re-use. Partial unique index `uq_machine_run_participant_active_plan_task` also prevented a second ACTIVE row.

**Root cause (simple):** “ACTIVE participant” was treated as permanent exclusivity, without requiring a non-terminal MachineRun. DB unique index on ACTIVE made eligibility-only filtering insufficient.

---

## F. Active membership semantics

```text
ACTIVE (participant) = membership row on a run (history may later become REMOVED)
blocking membership =
  participant.status = ACTIVE
  AND machine_run.status IN (HELD, RESERVED, RUNNING, COMPLETED)
```

Terminal runs: `RELEASED`, `CANCELLED`, `SUPERSEDED` — not blockers.  
`COMPLETED` still blocks until RELEASE.

---

## G. Fix

1. **Canonical helpers** in `machine_run_eligibility.py`:
   - `BLOCKING_MACHINE_RUN_STATUSES` / `TERMINAL_MACHINE_RUN_STATUSES`
   - `find_active_membership` / `find_all_active_memberships` join non-terminal runs
   - `blocking_membership_keys` for candidate discovery
2. **Candidate service** uses `blocking_membership_keys` (same rule).
3. **RELEASE/CANCEL/SUPERSEDED** in `_mutate_machine_run_lifecycle` set ACTIVE participants → `REMOVED` (provenance kept: same row, `machine_run_id`, `removed_at`/`removed_by`) so partial unique index allows re-CREATE. **No schema change.**

---

## H. Files changed

| File | Change |
| ---- | ------ |
| `backend/services/machine_run_eligibility.py` | blocking membership rule |
| `backend/services/machine_run_candidate_service.py` | use shared keys + shared status sets |
| `backend/services/machine_run_command_service.py` | REMOVED on terminalize |
| `backend/tests/test_machine_run_candidate_discovery_and_task_lookup.py` | re-eligibility + COMPLETED block + REMOVED |
| `backend/tests/test_machine_run_confirm_release_cancel_runtime.py` | expect REMOVED after terminal |
| `backend/tests/test_machine_run_operator_read_api.py` | active_count=0 after RELEASE |

---

## I–Q. Proof matrix

Covered by new + updated pytest (67 passed in bounded MachineRun set):

| Case | Result |
| ---- | ------ |
| RELEASE → re-candidate + re-CREATE | PASS |
| CANCEL HELD / CANCEL RESERVED → re-CREATE | PASS |
| COMPLETED+RESERVED still blocks | PASS |
| HELD/RESERVED/RUNNING still block | PASS (existing) |
| REMOVED non-blocking | PASS |
| by-task / candidate / CREATE parity | PASS |
| R6 CLEAR on RELEASE/CANCEL | PASS (unchanged expectations) |

---

## R–T. R6 / browser / regression

```text
R6_BEHAVIOR_CHANGED = NO
CONTROLLED_BROWSER_PROOF = API_AND_PYTEST_VERIFIED
  (UI inherits corrected candidate APIs; no FE code change)
REGRESSION = 67 passed
  candidate + create + add/remove + confirm/release/cancel + operator read
```

---

## U–Y. QA / expansion / docs / commit

```text
QA machine_runs/participants/transitions/reservations = 0
QA_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
NEW_ENDPOINTS = 0
NEW_UI_FEATURES = 0
FRONTEND_CHANGED = NO
PUSH = NO
```

Docs: this worklog; controlled-validation worklog gap → RESOLVED; route stamp `STABLE_BASELINE_AFTER_HARDENING`.
