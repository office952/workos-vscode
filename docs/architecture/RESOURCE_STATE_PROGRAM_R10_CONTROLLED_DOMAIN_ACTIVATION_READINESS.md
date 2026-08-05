# Resource State Program R10 — Controlled Domain Activation Readiness

**Task:** `RESOURCE_STATE_PROGRAM_R10 = CONTROLLED_DOMAIN_ACTIVATION_READINESS`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R10_CONTROLLED_DOMAIN_ACTIVATION_READINESS`  
**Date:** 2026-08-05  
**Status:** **PASS** · readiness complete; QA activation executed under **R11** (separate Owner GO)  
**Starting HEAD:** `393337ba`  
**Worklog:** `docs/worklog/realignment/2026-08-05_resource_state_program_r10_controlled_domain_activation_readiness.md`  
**R11 follow-through:** `docs/worklog/realignment/2026-08-05_resource_state_program_r11_controlled_qa_scheduling_and_reservation_activation.md`

```text
RESOURCE_STATE_PROGRAM_R10 = PASS
CONTROLLED_DOMAIN_ACTIVATION_READINESS = COMPLETE
SCHEDULING_ACTIVATION_READINESS = READY
MACHINE_RESERVATION_ACTIVATION_READINESS = READY
CAPACITY_ACTIVATION_READINESS = BLOCKED_MISSING_WRITER_AND_SOURCE
DOMAIN_SPECIFIC_ACTIVATION_GUARD = VERIFIED
DISABLE_SAFETY = VERIFIED
ACTIVATION_WRITE_CONCURRENCY = VERIFIED
RECOMMENDED_ACTIVATION_STRATEGY = OPTION_A
RESOURCE_STATE_PROGRAM_R11 = PASS
QA_DOMAIN_CONFIGURATIONS = 2
QA_SCHEDULING_CONFIGURATION = ACTIVE
QA_MACHINE_RESERVATION_CONFIGURATION = ACTIVE
QA_CAPACITY_CONFIGURATION = NOT_CONFIGURED
QA_RESOURCE_STATE_OPERATIONAL_ROWS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## 1. Primary question (answered)

| Question | Answer |
| -------- | ------ |
| Can Scheduling become ACTIVE while Reservation/Capacity are NOT_CONFIGURED? | **YES** (isolated; writers independent) |
| Can Machine Reservation become ACTIVE while Capacity is NOT_CONFIGURED? | **YES** |
| Does aggregate become CLEAR when only schedule+reservation are CLEAR? | **NO** — remains `BLOCKED_NOT_CONFIGURED` |

Fail-closed aggregate (R6) preserved:

```text
Scheduling = CLEAR
Reservation = CLEAR
Capacity = NOT_CONFIGURED
Aggregate = BLOCKED_NOT_CONFIGURED
```

Phase B consumer wiring is **not** connected; even after future QA activation, Capacity NOT_CONFIGURED continues to block aggregate CLEAR.

---

## 2. Domain readiness matrix

| Prerequisite | SCHEDULING | MACHINE_RESERVATION | CAPACITY_ALLOCATION |
| ------------ | ---------- | ------------------- | ------------------- |
| Schema s64 | yes | yes | yes |
| Read evaluator | yes | yes | yes |
| Writer | yes (R9) | yes (R9) | **no** |
| History tables | yes | yes | yes (unused) |
| Manage permissions | yes | yes | not registered |
| CAS/idempotency | yes | yes | N/A writer |
| Machine/overlap | N/A | yes | N/A |
| Capacity source / over-alloc | N/A | N/A | **missing** |
| **Activation readiness** | **READY** | **READY** | **BLOCKED_MISSING_WRITER_AND_SOURCE** |

`DOMAIN_WRITER_READY` is a **per-domain dict** (not a global boolean). Capacity cannot be unlocked by the legacy env flag.

---

## 3. Independent activation (isolated proofs)

Proven on temporary SQLite:

1. **Scheduling ACTIVE only** → schedule writer works; evaluator CLEAR/ACTIVE as appropriate; aggregate `BLOCKED_NOT_CONFIGURED`.  
2. **Reservation ACTIVE only** → reservation writer works; aggregate `BLOCKED_NOT_CONFIGURED`.  
3. **Both ACTIVE, Capacity absent** → both writers/evaluators work; aggregate still `BLOCKED_NOT_CONFIGURED`.  
4. **Capacity ACTIVE** → rejected with `ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE`.

---

## 4. Disable safety

```text
ACTIVE → DISABLED
```

| Condition | Result |
| --------- | ------ |
| Blocking source rows present (PLANNED/CONFIRMED schedules; HELD/RESERVED reservations) | **409** `disable_blocked_active_source_rows` |
| No rows / terminal-only rows | **allowed** |
| After DISABLED | writers reject (`domain_disabled` / `domain_not_active`); reader → `NOT_CONFIGURED` |
| Rows on disable | **never deleted**; history preserved |

---

## 5. Recommended activation strategy

```text
RECOMMENDED_ACTIVATION_STRATEGY = OPTION_A
```

**Activate Scheduling and Reservation together later (R11 Owner GO); Capacity remains NOT_CONFIGURED; aggregate remains blocked.**

Rationale (repo-confirmed):

- Both domains have real writers and can collect factual truth.  
- Capacity has neither writer nor available-capacity source.  
- Aggregate fail-closed keeps Phase B blocked until Capacity is ready (or Owner revisits aggregate policy — out of R10).  
- Option C (wait for Capacity) delays useful factual capture without necessity.  
- Option B (Scheduling first) is valid but adds an extra activation GO with little benefit once both writers exist.

---

## 6. Phase B / Phase C

```text
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

R10 does not wire `evaluate_task_resource_state` into reassignment. Phase B remains the legacy fail-closed / TEST_ONLY path.

---

## 7. Bounded code changes in R10

| Change | Why |
| ------ | --- |
| Domain-specific activation codes; remove global env unlock for capacity | Acceptance #7 |
| `assess_disable_readiness` + reject DISABLE with blocking rows | Disable safety |
| `domain_activation_readiness_report` | Readiness matrix for tests/docs |
| Isolated tests `test_resource_state_r10_activation_readiness.py` | GO §7 |

No QA writes. No capacity writer. No Phase B wiring. No migration.

---

## 8. Next Owner gate

```text
R11 = PASS (controlled QA Scheduling + Machine Reservation activation; zero operational rows)
FUTURE CANDIDATE:
CAPACITY_SOURCE_AND_WRITER_DECISION
```

R10 authorized readiness only. R11 performed OPTION_A activation under its own Owner GO. Capacity writer/source and Phase B wiring remain **NOT_AUTHORIZED**.
