# MachineRun V1 closure + next-domain audit

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_V1_CLOSURE_AND_NEXT_DOMAIN_AUDIT`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `2bad3961`  
**Mode:** audit / read-only / docs truth-sync only  
**Verdict:** **PASS** · `MACHINE_RUN_V1_E2E = CONFIRMED_CLOSED` · `NEXT_DOMAIN = HARDEN_AND_OBSERVE`

---

## Baseline confirmed

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
HEAD = 2bad3961
CODE_ALEMBIC = s67_machine_run_execution_status
QA_ALEMBIC = s67_machine_run_execution_status
QA_machine_runs = 0
```

Accepted history (runtime + UI + evidence packs) matches expected PASS chain through CREATE/ADD/context-link closure.

---

## E2E closure proof (factual)

| Stage | Evidence |
| ----- | -------- |
| Frozen machine demand → eligibility | shared `machine_run_eligibility.py` used by CREATE/ADD writers + candidate APIs |
| Candidate discovery → CREATE UI | GET `/candidates` + CREATE dialog; isolated capture POST create → detail |
| Reservation + participants | run-owned reservation; HELD ADD/REMOVE |
| CONFIRM → START → COMPLETE → RELEASE | command service + shop-floor UI matrix; prior network proofs |
| List/detail | `/execution/machine-runs` |
| Context links | by-task chips on ExecutionDetail WorkPanel + Ops-Graph (isolated proof; QA empty ⇒ no chip noise) |

`MACHINE_RUN_V1_E2E = CONFIRMED_CLOSED` for the approved current flow. Not a claim that PAUSE/Phase B/session coupling exist.

---

## Duplicate truth

```text
DUPLICATE_TRUTH = NONE (authority-breaking)
```

Acceptable display mapping only (`MACHINE_RUN_STATUS_LABEL`, action labels).  
Frontend does not reimplement eligibility; chips use by-task API; R6 reads reservation status, not MachineRun as provenance.

Note (non-blocking STALE comment): `machineRunUi.ts` still has a comment saying candidate discovery API missing for CREATE/ADD matrix omission — functionally CREATE/ADD are separate dialogs; comment is outdated wording only (left untouched to keep feature code = 0).

---

## Dead pieces

| Item | Class | Path / note |
| ---- | ----- | ----------- |
| CREATE deferred notice UI | gone | removed in closure build |
| ADD deferred notice UI | gone | removed in closure build |
| Candidate doc “UI still deferred” | STALE → fixed this audit | `MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API.md` |
| Operator read API header “no shop-floor UI” | STALE → fixed this audit | `MACHINE_RUN_OPERATOR_READ_API.md` |
| Comment “candidate discovery API missing” | STALE | `frontend/src/lib/machineRunUi.ts` (~line 73) |
| Utilaje MachineRun home | DEFERRED by design | absent — correct |
| PAUSE/RESUME routes | DEFERRED | none in MachineRun |

`DEAD_PATHS = NONE` that still block operators. Remaining items = stale comment + historical readiness docs that correctly mark themselves as readiness-era.

---

## Boundaries

### Task / MachineRun / Session

- MachineRun owns shared machine grouping + execution status + `started_at`/`completed_at`.
- Reservation owns machine commitment + window.
- ExecutionPlan/task owns demand + task ops state.
- Employee Session (ExecutionReality `start_task`/`end_task`) owns labor actuals — separate APIs.
- `start_machine_run` / `complete_machine_run` mutate only MachineRun (+ reservation version lockstep); no task/session writes.
- UI copy on list page explicitly: Start/Finalizează refer to machine work, not employee task/session.

### R6

Derived from **reservation.status** (`HELD`/`RESERVED` → ACTIVE; `RELEASED`/`CANCELLED` → CLEAR).  
RUNNING/COMPLETED keep reservation RESERVED ⇒ ACTIVE until RELEASE. Matches expected matrix.

### Permissions

| Perm | API + UI |
| ---- | -------- |
| read | list/detail/candidates/by-task/chips |
| manage | CREATE/ADD/REMOVE/CONFIRM/RESCHEDULE/RELEASE/CANCEL |
| execute | START/COMPLETE |

No accidental write widening. Operator = read+execute only.

### Modules / Governance

Browser-verified: MachineRun row **CONFIRMAT**; CREATE/ADD + chips listed; no “UI pending / CREATE pending” copy. Reservation row present.

---

## Scenarios

| ID | Result |
| -- | ------ |
| A Normal CNC CREATE→…→RELEASE | **SUPPORTED** |
| B Temporary machine stop | Representable only as still RUNNING (or operator COMPLETE early). No pause clock. Workaround: leave RUNNING or COMPLETE+new run. **Not a V1 closer.** |
| C Employee swap while RUNNING | MachineRun need not know; sessions/assignment own labor. Pre-start reassignment exists; post-start transfer = Phase E `NOT_AUTHORIZED`. Workshop not blocked for machine grouping. |
| D Post-start responsibility transfer | Blocked by STRICT_PRE_START_ONLY + session history + resource guards. MachineRun RUNNING is documented future *signal*, not transfer owner. |
| E COMPLETE then manual work | COMPLETE/RELEASE do not complete tasks/sessions — model correct. |

---

## Priority scores (1–5)

| Domain | Value | Blocking | Deps | Complexity | Regression | Overeng. risk | Verdict priority |
| ------ | ----- | -------- | ---- | ---------- | ---------- | ------------- | ---------------- |
| PAUSE_RESUME | 2 | 1 | 3 | 4 | 4 | 4 | **LOW / NOT_NEEDED_NOW** |
| PHASE_B (MR signal / post-start) | 3 | 2 | 5 | 5 | 5 | 5 | **LOW–MEDIUM** |
| EMPLOYEE_SESSION_COUPLING | 2 | 1 | 4 | 5 | 5 | 5 | **LOW** |
| HARDEN_AND_OBSERVE | 5 | — | 1 | 1 | 1 | 1 | **SELECTED** |

```text
PAUSE_RESUME_PRIORITY = NOT_NEEDED_NOW
PHASE_B_PRIORITY = LOW
EMPLOYEE_SESSION_COUPLING_PRIORITY = LOW
```

Reasons: no measured frequency of temporary stops or handoffs; inventing pause/productive-runtime split or auto session start would mix clocks without workshop evidence; assignment post-start transfer is a larger unauthorized Phase E architecture.

---

## Exact next domain

```text
NEXT_DOMAIN = HARDEN_AND_OBSERVE
```

### NEXT_DOMAIN_REASON

1. V1 CNC lifecycle is operationally complete for the approved scope.
2. Remaining domains invent new semantics without observed friction data.
3. Sessions and pre-start reassignment already exist separately — no workshop blocker from missing coupling.
4. Need real use of CREATE/multi-plan/RELEASE discipline before designing PAUSE or handoff.
5. Lowest regression / overengineering risk; reversible observation only.

### WHY_NOT_THE_OTHER_THREE

- **PAUSE_RESUME:** temporary-stop is not proven frequent; would need pause history, productive vs wall-clock, R6/overlap review — speculative.
- **PHASE_B:** post-start transfer is Phase E / assignment-owned; MachineRun should later be a signal, not the transfer system; dependency stack too large.
- **EMPLOYEE_SESSION_COUPLING:** machine time ≠ labor time by design; auto-start session on MachineRun START would violate V1 isolation.

### Observe manually (no telemetry framework)

- CREATE / multi-plan usage frequency
- RELEASE forgotten after COMPLETE
- Temporary stops handled how?
- Operator handoffs during RUNNING
- Lifecycle/CAS errors from operators
- Candidate empty-state friction

---

## Zero-change proof

```text
CODE_FEATURE_CHANGES = 0 (comment left stale; no feature edits)
DB_SCHEMA_CHANGES = 0
RUNTIME_MUTATIONS = 0
FRONTEND_FEATURE_CHANGES = 0
QA_MUTATIONS = 0 (machine_runs count remained 0)
NO_PUSH = YES
```

Docs truth-sync only: candidate API UI deferred block; operator read API header; route stamp for recommended next domain.
