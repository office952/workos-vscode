# Phase C Resource-Guard Proof Strategy — Owner Decision Audit

**Task:** `PHASE_C_RESOURCE_GUARD_PROOF_STRATEGY_OWNER_DECISION_ONLY`  
**Date:** 2026-08-04  
**Status:** Audit **COMPLETE** · Owner decision **NOT RECORDED** · Phase C **NOT AUTHORIZED**  
**Wave 11 retained:** `PASS` · Phase B backend **VERIFIED**  
**Worklog:** `docs/worklog/realignment/2026-08-04_phase_c_resource_guard_proof_strategy_audit.md`  
**Related:** `CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md` · Wave 11 closure worklog · `21_WORKOS_IMPLEMENTATION_ROUTE.md`

```text
PHASE_C_RESOURCE_GUARD_STRATEGY_AUDIT = COMPLETE
RECOMMENDED_STRATEGY = OPTION_D_PHASE_C_REMAINS_BLOCKED
OWNER_DECISION_RECORDED = NO
PHASE_C = NOT_AUTHORIZED
PHASE_C_QA_READINESS = BLOCKED
PHASE_C_BLOCKER = RESOURCE_GUARDS_HAVE_NO_CANONICAL_CLEAR_SOURCE
QA_MUTATIONS = 0
IMPLEMENTATION = NONE
```

---

## 1. Purpose

Choose how Phase C could **factually** demonstrate, for a single QA task (880750 LED):

```text
scheduling_state = CLEAR
machine_reservation_state = CLEAR
capacity_allocation_state = CLEAR
```

without environment bypass, hardcoded CLEAR, treating missing systems as CLEAR, implementing full scheduling, inventing tables, mutating the task, reserving a machine, or allocating capacity.

This document records the **audit + recommendation only**. It does **not** authorize Phase C or record the Owner’s final choice.

---

## 2. Mandatory Owner principle (non-negotiable)

```text
missing row     ≠ CLEAR
missing service ≠ CLEAR
not implemented ≠ CLEAR
environment override ≠ operational truth
```

Only a factual, canonical source may produce `CLEAR`.  
If the domain does not exist → `NOT_CONFIGURED` or `UNKNOWN` → transition **blocked**.

Already enforced by Phase B: `backend/services/phase_b_resource_guard_service.py`  
(`WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR` is TEST_ONLY under `APP_ENV=test`).

---

## 3. Current resource truth (repo fact)

### 3.1 Scheduling

| Question | Answer |
| -------- | ------ |
| Source of truth | **None durable** |
| Table / model | No execution-plan schedule table |
| Service | Wave 5 audit emits constant `scheduling="HOLD"` (`assignment_readiness_audit_service.py`); Phase B guard returns `NOT_CONFIGURED` |
| Classification | `PLACEHOLDER` (HOLD inventory) + `NOT_IMPLEMENTED` (schedule domain) |
| Level | Guard args include task/plan but are ignored today |
| Possible values | Inventory: `HOLD`. Phase B: `CLEAR \| ACTIVE \| UNKNOWN \| NOT_CONFIGURED` |
| Current QA value | Inventory HOLD; Phase B path → `NOT_CONFIGURED` (no CLEAR source) |
| Absence vs CLEAR | **Distinguishable** — absence → `NOT_CONFIGURED`, not CLEAR |

### 3.2 Machine reservation

| Question | Answer |
| -------- | ------ |
| Source of truth | **None** |
| Table / model | No reservation / booking / resource_lock table |
| Service | ORR candidates hardcode `reservation_status="not_reserved"` |
| Classification | `PLACEHOLDER` + `NOT_IMPLEMENTED` |
| Level | Candidate constant; Phase B not probing task data |
| Possible values | Schema literal `"not_reserved"`; Phase B ResourceState enum |
| Current QA value | No reservation rows; machine_codes on 880750 ops tasks = **0** |
| Absence vs CLEAR | **Distinguishable** — Phase B → `NOT_CONFIGURED` |

### 3.3 Capacity allocation (task/plan)

| Question | Answer |
| -------- | ------ |
| Source of truth | **None** for task/plan allocation |
| Table / model | No capacity-allocation table |
| Service | Constants `capacity_allocation="not_started"` on Wave 4/5 / eligibility boundaries |
| Related (different domain) | HR monthly productive hours; dashboard capacity util gates; `machines.capacity_metadata` — **not** reassignment allocators |
| Classification | Task/plan allocation: `PLACEHOLDER` + `NOT_IMPLEMENTED`. HR/dashboard: separate `CANONICAL_ACTIVE` / tooling |
| Current QA value | `not_started` / Phase B `NOT_CONFIGURED` |
| Absence vs CLEAR | **Distinguishable** |

### 3.4 Employee availability (audit only — not Phase C resource guard)

Eligibility emits `availability_status="not_evaluated"`. HR attendance is employee-day, not task. Phase B session-history marks attendance `NOT_APPLICABLE`. Do **not** promote availability into Phase C CLEAR proof without a separate Owner decision.

### 3.5 Adjacent real domains (not CLEAR substitutes)

| Domain | Classification |
| ------ | -------------- |
| Employee assignment + transitions | `CANONICAL_ACTIVE` |
| Operation resource requirements (ORR) + machines registry | `CANONICAL_ACTIVE` |
| Machine assignment write (`machine_code`) | `NOT_IMPLEMENTED` |
| Session / execution reality history | `CANONICAL_ACTIVE` (blocks reassign; separate from resource CLEAR) |

---

## 4. Source-of-truth matrix

| Domain | Durable SoT | Inventory constant | Phase B default | Can produce CLEAR today? |
| ------ | ----------- | ------------------ | --------------- | ------------------------ |
| Scheduling | none | `HOLD` | `NOT_CONFIGURED` | **NO** (except TEST_ONLY env) |
| Machine reservation | none | `not_reserved` | `NOT_CONFIGURED` | **NO** |
| Capacity allocation | none | `not_started` | `NOT_CONFIGURED` | **NO** |

```text
REAL_SCHEDULING_SOURCE = NOT_IMPLEMENTED
REAL_RESERVATION_SOURCE = NOT_IMPLEMENTED
REAL_CAPACITY_ALLOCATION_SOURCE = NOT_IMPLEMENTED
NEGATIVE_EVIDENCE_EQUALS_CLEAR = FORBIDDEN
```

---

## 5. Strategy comparison

### Option A — Read-only negative-evidence proof

Claim: empty queries for schedule / reservation / capacity ⇒ CLEAR.

| Dimension | Rating |
| --------- | ------ |
| SAFETY | FAIL — violates Owner principle |
| CANONICALITY | FAIL — no tables whose empty set means “configured clear” |
| FALSE_CLEAR_RISK | **CRITICAL** — “system missing” misread as “no lock” |
| IMPLEMENTATION_REQUIRED | Low code, high policy fraud |
| PHASE_C_READINESS | **NOT_SAFE** |

**Verdict:** Rejected. `PLACEHOLDER` constants (`HOLD` / `not_reserved` / `not_started`) are honesty inventory, **not** Phase B CLEAR.

### Option B — Minimal canonical resource-state contract

A thin read model reporting `CLEAR | ACTIVE | UNKNOWN | NOT_CONFIGURED` per domain, without a full scheduling engine.

| Dimension | Rating |
| --------- | ------ |
| SAFETY | Conditional — only if backed by real probes |
| CANONICALITY | Missing sources today |
| FALSE_CLEAR_RISK | High if contract invents CLEAR |
| IMPLEMENTATION_REQUIRED | Production code **yes**; schema **likely** if persisted CLEAR declarations; invented QA rows **forbidden without Owner GO** |
| PHASE_C_READINESS | **NOT_UNLOCKED** by contract alone without factual CLEAR producers |

**Verdict:** Correct **future program shape** (`RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY`), but **cannot unlock Phase C now** without inventing operational truth or implementing domain persistence. Marked blocker until Owner authorizes that program separately.

### Option C — Dedicated QA resource-state fixture

Persistent QA-only CLEAR declaration for 880750 / LED.

| Dimension | Rating |
| --------- | ------ |
| SAFETY | Poor — masked bypass risk |
| CANONICALITY | Creates second source of truth |
| FALSE_CLEAR_RISK | **HIGH** — looks like proof, is fixture |
| IMPLEMENTATION_REQUIRED | Schema or fixture store; ownership/lifecycle rules; production exclusion |
| PHASE_C_READINESS | Tempting but **not recommended** |

**Verdict:** Rejected by default. Closely resembles the already-restricted env override. Acceptable only under a future explicit Owner GO with strict lifetime/ownership — **not** recommended here.

### Option D — Phase C remains blocked

```text
PHASE_C_REMAINS_BLOCKED_UNTIL_SCHEDULING_DOMAIN_EXISTS
```

Next program name (not started):

```text
RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY
```

| Dimension | Rating |
| --------- | ------ |
| SAFETY | PASS |
| CANONICALITY | PASS — matches repo |
| FALSE_CLEAR_RISK | None (no CLEAR claim) |
| IMPLEMENTATION_REQUIRED | None in this task |
| PHASE_C_READINESS | Remains **BLOCKED** honestly |

**Verdict:** Only strategy consistent with current facts.

---

## 6. Recommended strategy

```text
RECOMMENDED_STRATEGY = OPTION_D_PHASE_C_REMAINS_BLOCKED
CONCLUSION = PHASE_C_REMAINS_BLOCKED_UNTIL_SCHEDULING_DOMAIN_EXISTS
```

**Why (repo truth, not speed):**

1. No durable scheduling, reservation, or capacity-allocation tables for execution tasks.  
2. Owner principle forbids mapping absence / placeholders / env overrides to CLEAR.  
3. Option A is false-clear by construction.  
4. Option B without real producers invents truth or stays at `NOT_CONFIGURED` (still blocked).  
5. Option C is a QA bypass class already rejected for env CLEAR.  
6. Phase B correctly fail-closes; that is success, not a Phase B defect.

---

## 7. Mandatory Q&A (audit answers)

| # | Question | Answer |
| - | -------- | ------ |
| 1 | Real scheduling source today? | **No** |
| 2 | Real machine reservation source? | **No** |
| 3 | Real capacity allocation source? | **No** (task/plan) |
| 4 | Can absence mean factual CLEAR? | **No** — means `NOT_IMPLEMENTED` / `NOT_CONFIGURED` |
| 5 | False-clear risk? | **Yes** for A and C; B if CLEAR invented |
| 6 | Read-only guard without schema? | Can keep failing closed; **cannot** unlock CLEAR |
| 7 | New contract required before Phase C? | **Yes** — as a future Owner program, not as instant unlock |
| 8 | Missing Owner semantics? | What constitutes CLEAR/ACTIVE per domain; task vs plan scope; who writes state; lifetime; relation to HOLD/not_started |
| 9 | Phase C without starting scheduling? | **Not safely** while CLEAR has no canonical producer |
| 10 | One domain CLEAR, another NOT_CONFIGURED? | Transition **blocked** (all three must be CLEAR) |
| 11 | Global override prevention? | Already: TEST_ONLY + startup BLOCKED production-like |
| 12 | LED task exact state? | Assigned employee 7; 0 machine_codes; 0 reality sessions; resource guards NOT_CONFIGURED |
| 13 | Fail-closed after restart? | Default path returns NOT_CONFIGURED without test env |
| 14 | State inside lock? | Today re-evaluates constants/env; no durable row to re-read — another reason CLEAR is unsafe |

---

## 8. Owner decisions required (not auto-recorded)

Owner must choose exactly one next decision:

```text
OWNER DECISION: KEEP_PHASE_C_BLOCKED
```

(Recommended.)

Alternatives (not recommended now):

```text
OWNER DECISION: PHASE_C_USE_READ_ONLY_NEGATIVE_EVIDENCE   # reject — false CLEAR
OWNER DECISION: BUILD_MINIMAL_CANONICAL_RESOURCE_STATE_CONTRACT
OWNER DECISION: CREATE_CONTROLLED_QA_RESOURCE_STATE_FIXTURE
```

If Owner later chooses `BUILD_MINIMAL_CANONICAL_RESOURCE_STATE_CONTRACT`, that must be a **separate GO** named approximately:

```text
RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY
```

and must define CLEAR producers without inventing QA operational lies. That GO is **not** Phase C execution.

---

## 9. Phase C implication

```text
PHASE_C_CAN_PROCEED_WITH_READ_ONLY_PROOF = NO
MINIMAL_CANONICAL_RESOURCE_STATE_IMPLEMENTATION_REQUIRED = FUTURE_PROGRAM_ONLY
PHASE_C_REMAINS_BLOCKED_UNTIL_SCHEDULING_DOMAIN_EXISTS = YES
PHASE_C = NOT_AUTHORIZED
```

---

## 10. Dead pieces check (classify only — nothing removed)

| Piece | Classification |
| ----- | -------------- |
| `WORKOS_PHASE_B_RESOURCE_GUARDS` | `TEST_ONLY` |
| Phase B resource guard service | `ACTIVE_CANONICAL` (fail-closed) |
| Wave 5 `scheduling=HOLD` | `PLACEHOLDER` |
| ORR `reservation_status=not_reserved` | `PLACEHOLDER` |
| `capacity_allocation=not_started` | `PLACEHOLDER` |
| HR monthly capacity / attendance | `SUPPORTED_NOT_ACTIVE` for Phase C guards |
| Dashboard capacity util batches | `SUPPORTED_NOT_ACTIVE` for Phase C guards |
| Machine assignment writers | `NOT_IMPLEMENTED` / `DEAD_CANDIDATE` for CLEAR proof |
| Hardcoded order/task CLEAR shortcuts | `BYPASS_RISK` if introduced — none recommended |
| Old QA fixture CLEAR shortcuts | `BYPASS_RISK` — Option C |

```text
Dead pieces discovered: placeholder constants mistaken for CLEAR candidates
Dead pieces touched: none
Dead pieces removed: none
```

---

## 11. Documentation / commit policy for this task

- Docs/audit only  
- No production code, schema, migration, QA mutation, frontend, Mobile, push/PR  

---

## 12. Stop

Await Owner review. Do not start Phase C. Do not start `RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY` until Owner GO.
