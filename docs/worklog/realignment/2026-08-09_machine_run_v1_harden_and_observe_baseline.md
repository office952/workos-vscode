# MachineRun V1 — Harden & Observe baseline

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_V1_HARDEN_AND_OBSERVE_BASELINE`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `1fedbf08`  
**Verdict:** **PASS** · `MACHINE_RUN_V1 = STABLE_BASELINE` · `CURRENT_MODE = HARDEN_AND_OBSERVE`

---

## Baseline confirmed

```text
worktree = C:\w\psiso
HEAD = 1fedbf08 (start) → tip after this commit
MACHINE_RUN_V1_E2E = CONFIRMED_CLOSED
QA_ALEMBIC = s67_machine_run_execution_status
QA_machine_runs = 0
```

---

## Terminology result

```text
POST_START_TRANSFER_CANONICAL_PHASE = REASSIGNMENT_PHASE_E
TERMINOLOGY_DRIFT = YES
PHASE_NOMENCLATURE_AMBIGUOUS = NO
```

| Label in docs | Actual meaning |
| ------------- | -------------- |
| Reassignment **Phase B** | Pre-start reassign/unassign backend — Wave 11 VERIFIED |
| Reassignment **Phase E** | Post-start operational transfer — NOT_AUTHORIZED |
| MachineRun doc **PHASE_B** | Future MR→R6 guard coupling — NOT_AUTHORIZED; ≠ transfer |
| Loose “Phase B transfer/handoff” | **Drift** — should mean Phase E |

Canonical source for A–E ladder: `docs/architecture/REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA_DECISIONS.md` § Implementation phases.

---

## Stale / dead cleanup

| Item | Class | Action |
| ---- | ----- | ------ |
| `machineRunUi.ts` ~L73 comment (“candidate discovery API missing”) | STALE_TEXT_ONLY | Corrected |
| Historical shop-floor worklog CREATE=DEFERRED stamps | CURRENT (as-of that GO) | Left |
| QA `state_matrix.md` CREATE deferred note | CURRENT (evidence of that build) | Left |
| Live UI deferred CREATE/ADD notices | gone | Verified absent |

```text
RUNTIME_BEHAVIOR_CHANGED = NO
NEW_MACHINE_RUN_FEATURES = 0
NEW_API_ENDPOINTS = 0
NEW_DB_SCHEMA = 0
NEW_UI_WORKFLOWS = 0
```

---

## Regression

```text
INTRODUCED_FAILURES = 0
PREEXISTING_FAILURES = 0 (in bounded MachineRun set)
ENVIRONMENTAL_FAILURES = 0
```

| Suite | Result |
| ----- | ------ |
| FE machineRunUi + list/detail + CREATE/ADD/chip | 24 passed |
| BE candidate + lookup | passed (in 53) |
| BE read API | passed (in 53) |
| BE ADD/REMOVE | passed (in 53) |
| BE START/COMPLETE | passed (in 53) |
| BE CONFIRM/RELEASE/CANCEL | run in this GO |

Runtime behavior unchanged (comment + docs only).

---

## Browser hardening

QA `:3000` verified:

```text
/execution/machine-runs — CREATE CTA · boundary copy · no deferred CREATE/ADD
/execution/880750 · /execution/ops-graph · /shop-floor · /utilaje — nav coherent · no second MR home
/modules · /governance — MachineRun CONFIRMAT
```

---

## Observation contract

Canonical: `docs/architecture/MACHINE_RUN_V1_OPERATIONAL_OBSERVATION_CONTRACT.md`

Signals: CREATE/grouping · RELEASE · temporary stops · employee change · post-start transfer · CAS · bulk-lookup watch.  
Default next feature: `NO_CHANGE` until workshop evidence.

---

## Route stamp

```text
MACHINE_RUN_V1 = CLOSED / STABLE_BASELINE
CURRENT_MODE = HARDEN_AND_OBSERVE
NEXT_FEATURE_DOMAIN = UNSELECTED
NEXT_TASK = NOT_AUTHORIZED
```
