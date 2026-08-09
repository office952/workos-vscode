# MachineRun V1 — Controlled Operational Scenario Validation

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_V1_CONTROLLED_OPERATIONAL_SCENARIO_VALIDATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `8bb8856e`  
**Evidence pack:** `docs/qa/machine-run-v1-controlled-operational-validation/`

---

## A. Verdict

```text
MACHINE_RUN_V1_CONTROLLED_OPERATIONAL_SCENARIO_VALIDATION = PARTIAL_BLOCKED
LIVE_WORKSHOP_VALIDATION = NOT_AVAILABLE
EVIDENCE_TYPE = CONTROLLED_SCENARIO_EVIDENCE
CONTROLLED_VALIDATION_RESULT = HARDENING_GAP_FOUND
NEXT_RECOMMENDATION = MACHINE_RUN_V1_HARDENING_FIX_CANDIDATE
HARDENING_FIX_CANDIDATE = YES
FAILED_SCENARIO = 8 TERMINAL_MEMBERSHIP_REELIGIBILITY
RESULT = UNSUPPORTED
TECHNICAL_SEVERITY = S3
OPERATIONAL_FREQUENCY = UNKNOWN
FEATURE_CODE_CHANGES = 0
DB_SCHEMA_CHANGES = 0
NEW_ENDPOINTS = 0
NEW_UI_FEATURES = 0
PROTECTED_QA_MUTATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
NEXT_TASK = NOT_AUTHORIZED
```

Most lifecycle scenarios are **SUPPORTED**. One controlled correctness gap blocks terminal re-eligibility (CREATE/candidates after RELEASE/CANCEL). No feature implementation in this GO.

---

## B. Repo / HEAD

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 8bb8856e
baseline = STABLE_BASELINE / HARDEN_AND_OBSERVE / UNSELECTED
```

---

## C. Owner GO

Authorized: isolated controlled scenarios, browser/network proof, regression, docs, gap classification.  
Not authorized: PAUSE/Phase E/session/Capacity/schema/endpoints/QA writes/feature implementation/push.

---

## D. Validation environment

```text
ISOLATED_DB_PATH = docs/qa/machine-run-v1-controlled-operational-validation/_isolated_s67_validation.db
BACKEND_PORT (scenario services) = in-process / TestClient (no QA DB)
BACKEND_PORT (optional isolated HTTP) = 8012 / pre-existing 8010 closure DB
FRONTEND_PORT (QA browser themes) = 3000
FRONTEND_PORT (attempted isolated) = 3013/3014 (CORS/local-compat absolute :8010 blocked)
SERVED_HEAD = 8bb8856e
PROTECTED_QA_RUNTIME_WRITES = 0
```

---

## E. Evidence classification

| Class | Used for |
| ----- | -------- |
| CONTROLLED_SCENARIO_EVIDENCE | Scenario matrix services/TestClient |
| REGRESSION_TEST_EVIDENCE | 46 pytest MachineRun tests PASS |
| BROWSER_RUNTIME_EVIDENCE | QA `:3000` light/dark + reload |
| QA_READ_ONLY_EVIDENCE | QA empty MachineRun tables fingerprint |
| ASSUMPTION | none promoted as fact |

**Not used:** `REAL_OPERATIONAL_EVIDENCE`.

---

## F. Protected QA proof

**Before/after (unchanged):**

| Item | Value |
| ---- | ----- |
| Alembic | `s67_machine_run_execution_status` |
| SHA | `8bb8856e` (start) |
| machine_runs | 0 |
| participants | 0 |
| transitions | 0 |
| reservations | 0 |
| assignment_transitions | 7 |

```text
PROTECTED_BASELINE_DIFF = NONE
```

---

## G. Scenario matrix

| # | Scenario | Evidence type | Result | Limitation | Candidate domain |
|---|----------|---------------|--------|------------|------------------|
| 1 | NORMAL_MACHINE_RUN | CONTROLLED | SUPPORTED | NONE | NONE |
| 2 | MULTI_PLAN_MULTI_ORDER | CONTROLLED | SUPPORTED | NONE | NONE |
| 3 | PARTICIPANT_CORRECTION | CONTROLLED | SUPPORTED | NONE | NONE |
| 4 | CAS_CONCURRENCY | CONTROLLED | SUPPORTED | NONE | NONE |
| 5 | RESERVATION_OVERLAP | CONTROLLED | SUPPORTED | NONE | NONE |
| 6 | COMPLETE_WITHOUT_RELEASE | CONTROLLED | SUPPORTED | intentional COMPLETED+RESERVED | NONE |
| 7 | CANCEL_PATHS | CONTROLLED | SUPPORTED_WITH_LIMITATION | re-CREATE blocked after CANCEL | MACHINE_RUN_V1_HARDENING_FIX |
| 8 | TERMINAL_MEMBERSHIP | CONTROLLED | UNSUPPORTED | candidates not re-eligible | MACHINE_RUN_V1_HARDENING_FIX |
| 9 | TEMPORARY_STOP | CONTROLLED | SUPPORTED_WITH_LIMITATION | RUNNING coarse if long stop | PAUSE_RESUME |
| 10 | EMPLOYEE_CHANGE | CONTROLLED | SUPPORTED | labor separate by design | NONE |
| 11 | PHASE_E | CONTROLLED | BLOCKED_BY_DESIGN | expected policy guard | REASSIGNMENT_PHASE_E |
| 12 | MANUAL_AFTER_MACHINE | CONTROLLED | SUPPORTED | NONE | NONE |
| 13 | PERMISSIONS | CONTROLLED | SUPPORTED_WITH_LIMITATION | role mapping env-specific | NONE |
| 14 | INVALID_TRANSITIONS | CONTROLLED | SUPPORTED | NONE | NONE |
| 15 | IDEMPOTENCY | CONTROLLED | SUPPORTED | NONE | NONE |
| 16 | LOOKUP_VOLUME | CONTROLLED | SUPPORTED | N lookups @ ≤24 OK | NONE |
| 17 | LIGHT/DARK | BROWSER | SUPPORTED | detail states via prior isolated packs | NONE |
| 18 | REFRESH | BROWSER | SUPPORTED | NONE | NONE |
| 19 | BACKEND_RESTART | CONTROLLED | SUPPORTED | NONE | NONE |
| 20 | READ_WRITE_PARITY | CONTROLLED | SUPPORTED | NONE | NONE |

Full JSON: `docs/qa/machine-run-v1-controlled-operational-validation/scenario_matrix.json`.

---

## H–AA. Scenario notes (condensed)

- **Normal / multi-plan / correction / CAS / overlap / COMPLETE-without-RELEASE / invalid / idempotency / restart / R/W parity:** SUPPORTED.
- **Cancel:** transitions PASS; re-CREATE after CANCEL fails (hardening).
- **Terminal membership:** by-task clears; candidates do not → UNSUPPORTED S3.
- **Temporary stop:** TECHNICALLY_TOLERABLE; YES_CONCEPTUALLY misleading → limitation only.
- **Employee / Phase E / manual continuation:** boundaries as designed.
- **Lookup:** `ACCEPTABLE_CURRENT_SCALE` (≤24).
- **Browser:** QA empty list light/dark + reload SUPPORTED; no PAUSE/deferred stale copy.

---

## AB. Limitations / severity

| Issue | Tech severity | Op frequency |
| ----- | ------------- | ------------ |
| Terminal membership re-eligibility gap | S3 | UNKNOWN |
| RUNNING coarse for long temporary stops | S1 | UNKNOWN |
| Permission role mapping env-specific | S1 | UNKNOWN |

`TECHNICAL_SEVERITY_MAX = S3`

---

## AC–AE. Domain assessments

```text
PAUSE_RESUME_TECHNICAL_NEED = POSSIBLE
PAUSE_RESUME_OPERATIONAL_PRIORITY = UNPROVEN
TECHNICAL_CANDIDATE = YES (semantic coarseness only)
OPERATIONALLY_PROVEN_PRIORITY = NO

REASSIGNMENT_PHASE_E_TECHNICAL_NEED = EXPECTED_FUTURE_DOMAIN
REASSIGNMENT_PHASE_E_OPERATIONAL_PRIORITY = UNPROVEN

EMPLOYEE_SESSION_RELATION_TECHNICAL_NEED = NONE
EMPLOYEE_SESSION_RELATION_OPERATIONAL_PRIORITY = UNPROVEN
```

---

## AF. Hardening candidate

```text
MACHINE_RUN_V1_HARDENING_FIX_CANDIDATE = YES
ID = TERMINAL_MEMBERSHIP_REELIGIBILITY
STATUS = RESOLVED
RESOLVED_BY_GO = AUTHORIZE_MACHINE_RUN_TERMINAL_MEMBERSHIP_REELIGIBILITY_HARDENING_FIX
RESOLVED_WORKLOG = docs/worklog/realignment/2026-08-09_machine_run_terminal_membership_reeligibility_hardening_fix.md
```

**Was:** CREATE → CANCEL/RELEASE → CREATE again → `task_already_in_active_machine_run`; candidates omitted while by-task clear.  
**Fix:** blocking membership = ACTIVE participant on non-terminal run; RELEASE/CANCEL set participants REMOVED (provenance kept; no schema change).

---

## AG. Controlled vs live

```text
LIVE_WORKSHOP_VALIDATION = NOT_AVAILABLE
CONTROLLED_OPERATIONAL_VALIDATION = COMPLETED
```

Controlled scenarios prove technical behavior; they do not prove workshop frequency or commercial priority.

---

## AH. Next roadmap domain outside MachineRun

From `21_WORKOS_IMPLEMENTATION_ROUTE.md` status summary (read-only):

```text
NEXT_ROADMAP_DOMAIN_OUTSIDE_MACHINE_RUN =
CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY
```

Rationale: Assignment surface implemented / readiness PARTIAL_BLOCKED; command safety `NOT_VERIFIED`; assignment still CLOSED — nearest unfinished execution-domain work outside MachineRun deferred features. Parallel track remains `CAPACITY_STAGE_1` (`IMPLEMENTED_INACTIVE`, activation `NOT_AUTHORIZED`).

This is a **read-only recommendation**. Not authorized.

---

## AI–AL. Proof / docs / commit

```text
QA_MUTATIONS = 0
FEATURE_CODE_CHANGES = 0
REGRESSION = 46 passed (bounded MachineRun pytest)
DOCS = this worklog + evidence pack
COMMIT = docs/evidence only
PUSH = NO
```

---

## Decision stamps (product mode unchanged)

```text
MACHINE_RUN_V1 = STABLE_BASELINE
CURRENT_MODE = HARDEN_AND_OBSERVE
NEXT_FEATURE_DOMAIN = UNSELECTED
CONTROLLED_VALIDATION = audit mode only (not a new product lifecycle status)
```
