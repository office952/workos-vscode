# Resource State Contract and Scheduling Boundary — Readiness Audit

**Task:** `RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY_READINESS_AUDIT`  
**Date:** 2026-08-05  
**Status:** Audit **COMPLETE** · Implementation **NOT AUTHORIZED** · Phase C **BLOCKED**  
**Prior Owner decision:** `DEC-PHASE-C-RESOURCE-01 = KEEP_PHASE_C_BLOCKED`  
**Worklog:** `docs/worklog/realignment/2026-08-05_resource_state_contract_and_scheduling_boundary_readiness_audit.md`  
**Related:** `PHASE_C_RESOURCE_GUARD_OWNER_DECISION.md` · `PHASE_C_RESOURCE_GUARD_PROOF_STRATEGY.md` · Wave 11 closure

```text
RESOURCE_STATE_BOUNDARY_READINESS_AUDIT = COMPLETE
RECOMMENDED_PATH = MINIMAL_CANONICAL_RESOURCE_STATE_CONTRACT
RECOMMENDED_CONCLUSION = PERSISTED_RESOURCE_STATE_MODEL_REQUIRED
SCHEMA_CHANGE_REQUIRED = YES
IMPLEMENTATION_AUTHORIZED = NO
PHASE_C = BLOCKED
PHASE_C_BLOCKER = RESOURCE_GUARDS_HAVE_NO_CANONICAL_CLEAR_SOURCE
QA_MUTATIONS = 0
FULL_SCHEDULING_ENGINE = NOT_REQUIRED_FIRST
READ_ONLY_WRAPPER_OVER_PLACEHOLDERS = REJECTED
```

---

## 1. Purpose

Establish factual readiness for the future program `RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY` without implementing scheduling, reservations, capacity allocation, or unlocking Phase C.

Separates:

```text
Phase B backend safety     = VERIFIED (fail-closed)
Phase C operational readiness = BLOCKED
Resource-state program     = readiness audited, not started
```

---

## 2. Non-negotiable principles (retained)

```text
missing row     ≠ CLEAR
missing service ≠ CLEAR
not implemented ≠ CLEAR
HOLD            ≠ CLEAR
not_reserved    ≠ CLEAR
NOT_STARTED     ≠ CLEAR
NOT_CONFIGURED  ≠ CLEAR
UNKNOWN         ≠ CLEAR
environment override ≠ operational truth
employee assignment ≠ scheduling / reservation / availability
machine requirement ≠ machine assignment ≠ machine reservation
```

Configured-domain rule (mandatory for future CLEAR):

```text
no record in a CONFIGURED domain  → may mean CLEAR
no domain / table / service       → NOT_CONFIGURED
```

---

## 3. Domain inventory

### 3.1 Scheduling

| Aspect | Fact |
| ------ | ---- |
| Models / tables | **None** for execution-plan shop scheduling |
| Unrelated field | `FieldInstallationTeam.scheduled_at` (field install teams) — not shop schedule |
| Services | `assignment_readiness_audit_service` emits `scheduling="HOLD"`; eligibility notes “scheduling remains HOLD” |
| Phase B | `phase_b_resource_guard_service` → `scheduling_state=NOT_CONFIGURED` (ignores order/plan/task) |
| Routes | `GET …/assignment-readiness` returns `scheduling` |
| Frontend | `AssignmentReadinessPanel` shows `Programare: HOLD`; `ResourceReadinessPanel` “Scheduling rămâne HOLD” |
| Background jobs | None found for shop scheduling |
| Classification | `PLACEHOLDER` + `NOT_IMPLEMENTED` |
| QA value (880750) | HOLD inventory / Phase B NOT_CONFIGURED |

### 3.2 Machine reservation

| Aspect | Fact |
| ------ | ---- |
| Models / tables | **None** (no booking / resource_lock) |
| Services | ORR always `reservation_status="not_reserved"` |
| Phase B | `machine_reservation_state=NOT_CONFIGURED` |
| Routes | `GET …/resource-readiness` |
| Frontend | Types lock `'not_reserved'`; honesty copy “compatibil ≠ atribuit ≠ rezervat” |
| Classification | `PLACEHOLDER` + `NOT_IMPLEMENTED` |
| QA | 0 machine codes on plan 23 ops tasks |

### 3.3 Capacity allocation (task/plan)

| Aspect | Fact |
| ------ | ---- |
| Models / tables | **None** for task/plan allocation |
| Placeholders | `capacity_allocation="not_started"` (Wave 4/5, eligibility, ORR boundary) |
| Phase B | `capacity_allocation_state=NOT_CONFIGURED` |
| Adjacent real (different domain) | HR `GET …/lifecycle/capacity` productive hours; dashboard `capacity_batch_04` util gates; `machines.capacity_metadata` |
| Classification | Task/plan: `PLACEHOLDER` + `NOT_IMPLEMENTED`. HR/dashboard: `SUPPORTED_NOT_ACTIVE` for Phase C CLEAR |
| QA | NOT_STARTED inventory |

### 3.4 Employee availability (separate)

| Aspect | Fact |
| ------ | ---- |
| Eligibility | Always `availability_status="not_evaluated"` — `PLACEHOLDER` |
| HR attendance | `CANONICAL_ACTIVE` employee-day — not task resource CLEAR |
| Do not merge into Phase B triad without separate Owner GO | |

### 3.5 Machine assignment (≠ reservation)

| Aspect | Fact |
| ------ | ---- |
| Intended field | `operational_tasks[].machine_code` in `tasks_json` |
| Write path | **NOT_IMPLEMENTED** |
| Registry | `machines` — `CANONICAL_ACTIVE` for capability |
| ORR | Capability match only — never assigns |

### 3.6 Employee assignment / sessions (adjacent)

| Domain | Classification |
| ------ | -------------- |
| Employee assign + transitions | `CANONICAL_ACTIVE` |
| ExecutionReality / session history | `CANONICAL_ACTIVE` (Phase B session guard) |
| ORR + skill/WC allow-lists | `CANONICAL_ACTIVE` |

---

## 4. Source-of-truth matrix

| Domain | Current source | Authority | Persisted/derived | Granularity | Status |
| ------ | -------------- | --------- | ----------------- | ----------- | ------ |
| Scheduling | constant `HOLD` | inventory honesty | neither (hardcoded emit) | response-level | `PLACEHOLDER` |
| Reservation | constant `not_reserved` | inventory honesty | neither | candidate-level constant | `PLACEHOLDER` |
| Capacity allocation | constant `not_started` | inventory honesty | neither | envelope-level | `PLACEHOLDER` |
| Availability (eligibility) | `not_evaluated` | intentional unevaluated | neither | per candidate | `PLACEHOLDER` |
| HR productive hours | attendance/calendar | HR | derived | employee-month | `CANONICAL_ACTIVE` (other domain) |
| Dashboard capacity util | gates/read models | tooling | derived | dashboard | `SUPPORTED_NOT_ACTIVE` |
| Phase B guard | `NOT_CONFIGURED` / TEST_ONLY CLEAR | fail-closed gate | env only for CLEAR | process-global | `ACTIVE_CANONICAL` as guard |
| Employee assignment | `tasks_json` + transitions | execution | persisted | task | `CANONICAL_ACTIVE` |
| Machine assignment | intended `machine_code` | none writing | n/a | task | `NOT_IMPLEMENTED` |

---

## 5. Semantic audit

| Token | Meaning today | Persisted? | Writer | Reader | Granularity | Stale? | Inside-lock revalidatable as truth? | Absence vs CLEAR |
| ----- | ------------- | ---------- | ------ | ------ | ----------- | ------ | ----------------------------------- | ---------------- |
| `HOLD` | Inventory: scheduling domain not active / not programmed | No | hardcoded | assignment-readiness UI/API | plan response | N/A (constant) | No — not a schedule row | ≠ CLEAR |
| `NOT_STARTED` | Inventory: capacity allocator not started | No | hardcoded | eligibility/ORR/Wave5 | envelope | N/A | No | ≠ CLEAR |
| `not_reserved` | Inventory: no reservation subsystem claim | No | hardcoded | ORR | candidate | N/A | No | ≠ CLEAR |
| `NOT_CONFIGURED` | Phase B: no authoritative CLEAR source | No | guard default | reassignment | process | N/A | Re-eval only re-reads env/constants | Correct fail-closed |
| `UNKNOWN` | Enum reserved; used on query failure policy (future) | — | — | — | — | — | Fail-closed block | ≠ CLEAR |
| `CLEAR` | Allowed to reassign/unassign | Only via TEST_ONLY env today | test env | Phase B | process | N/A | Env not operational | Forbidden from absence |
| `ACTIVE` | Enum reserved for active lock/reservation/allocation | No producer | — | — | — | — | — | Blocks |
| `BLOCKED` | Generic readiness language (eligibility/materialize) | Mixed | various | UI | mixed | yes possible | domain-specific | ≠ resource CLEAR |
| `ready` / `Pregătit` | ORR/eligibility capability — **not** scheduled | derived | ORR/eligibility | UI | task | yes | capability only | Misleading risk |

---

## 6. Ownership comparison

### Option A — Execution Plan owns resource state (`tasks_json`)

| Dimension | Assessment |
| --------- | ---------- |
| SAFETY | Medium — shares plan lock; payload growth / lost updates risk |
| CANONICALITY | Weak for time-window/machine entities |
| SCHEMA_IMPACT | Low (JSON) but opaque |
| CONCURRENCY | Fits current SQLite plan lock |
| AUDITABILITY | Poor vs append-only events |
| REPORTING | Hard |
| PHASE_B_COMPATIBILITY | Easy under existing lock |
| FUTURE_SCHEDULING | Poor — schedule entities outgrow JSON |
| COMPLEXITY | Low short-term, high long-term |
| RECOMMENDATION | **Reject as sole SoT** for reservation/capacity; may mirror denormalized cache later |

### Option B — Dedicated resource-state service/model

| Dimension | Assessment |
| --------- | ---------- |
| SAFETY | High if fail-closed + provenance |
| CANONICALITY | High if Owner-defined |
| SCHEMA_IMPACT | **YES** (new tables/events) |
| CONCURRENCY | Needs CAS/version; readable in same SQLite txn as plan |
| AUDITABILITY | Strong with events |
| REPORTING | Strong |
| PHASE_B_COMPATIBILITY | Clean probe inside lock |
| FUTURE_SCHEDULING | Good bridge until full domain |
| COMPLEXITY | Medium |
| RECOMMENDATION | **Preferred path** for Phase C unblock without full optimizer |

### Option C — Scheduling domain owns state

| Dimension | Assessment |
| --------- | ---------- |
| SAFETY | Highest long-term |
| CANONICALITY | Highest when domain exists |
| SCHEMA_IMPACT | Large |
| CONCURRENCY | Cross-entity |
| AUDITABILITY | Strong |
| REPORTING | Strong |
| PHASE_B_COMPATIBILITY | Requires domain first |
| FUTURE_SCHEDULING | Native |
| COMPLEXITY | High |
| RECOMMENDATION | **Not required first**; later SoT for scheduling CLEAR from schedule records |

### Option D — Derived read-only over existing sources

| Dimension | Assessment |
| --------- | ---------- |
| SAFETY | **FAIL** for CLEAR today |
| CANONICALITY | FAIL — only placeholders |
| SCHEMA_IMPACT | NO |
| CONCURRENCY | N/A |
| AUDITABILITY | Misleading |
| PHASE_B_COMPATIBILITY | Would wrap NOT_CONFIGURED forever or invent CLEAR |
| RECOMMENDATION | **Rejected** for producing CLEAR |

**Ownership recommendation:** Option B (dedicated minimal persisted resource-state / source-event model) with Option C as future scheduling SoT that can feed the contract. Option A not sole authority. Option D rejected for CLEAR.

---

## 7. Granularity

| Domain | Natural grain | Must not collapse to |
| ------ | ------------- | -------------------- |
| Scheduling | task + time window (+ workcenter) | single plan boolean |
| Machine reservation | machine + task + time window | “has machine_code” |
| Capacity allocation | workcenter/resource + time bucket | employee assignment |
| Availability | employee + day/window | eligibility “ready” |

Aggregation for Phase B (conceptual):

```text
ALL CLEAR     → allow (when domains configured)
ANY ACTIVE    → block
ANY UNKNOWN   → block
ANY NOT_CONFIGURED → block
```

Do not force one task-level boolean for all three.

---

## 8. Persistence versus derivation

| Domain | Recommendation | Why |
| ------ | -------------- | --- |
| Scheduling | **Hybrid later**: persisted schedule records → derived CLEAR/ACTIVE; until then **persisted resource-state declaration or source events** | No schedule rows exist; derivation cannot invent configured domain |
| Reservation | **Persisted reservations** (future) or **persisted resource-state** interim | `not_reserved` constant is not a queryable empty set |
| Capacity | **Persisted allocations** or derived from schedules once they exist; interim **persisted resource-state** | `NOT_STARTED` is program status, not empty allocation table |

Pure derivation over current inventory constants → **cannot produce factual CLEAR**.

---

## 9. Minimal contract feasibility

Conceptual interface (not implemented):

```text
get_task_resource_state(execution_plan_id, task_key) -> {
  scheduling_state, reservation_state, capacity_state,
  provenance, evaluated_at
}
```

| Question | Answer |
| -------- | ------ |
| Factual today? | **No** for CLEAR — only NOT_CONFIGURED / placeholders |
| Merely wrap placeholders? | If built now without new sources — **yes, useless/dangerous** |
| Schema required for factual CLEAR? | **YES** (or full schedule/reservation/allocation domains) |
| Revalidatable under plan lock? | Yes **after** durable rows exist in same DB |
| Second SoT risk? | High if parallel to future schedule without ownership rules |
| Useful after scheduling exists? | Yes as stable Phase B probe / facade |

```text
MINIMAL_READ_ONLY_RESOURCE_STATE_CONTRACT_POSSIBLE = NO  # for factual CLEAR
PERSISTED_RESOURCE_STATE_MODEL_REQUIRED = YES
FULL_SCHEDULING_DOMAIN_REQUIRED_FIRST = NO
```

---

## 10. Scheduling boundary (future, not designed as optimizer)

Minimum concepts (manual scheduling first):

```text
scheduled task identity
employee assignment relation (optional link)
machine relation (optional)
start/end window
status
ownership
version/CAS
cancellation / reschedule
audit
timezone
dependencies
workcenter
```

Separate:

```text
manual scheduling ≠ automatic scheduling ≠ capacity planning ≠ dispatch ≠ execution
```

This audit covers **contract boundary**, not optimization.

---

## 11. Machine reservation boundary

Minimum concepts:

```text
machine identity
task identity
time window
reservation state
owner
created_at / cancelled_at
conflict semantics
capacity interaction
```

Current `machine_code` on ops task = assignment truth (unimplemented write), **not** reservation.  
ORR allow-list = requirement/capability, **not** reservation.

---

## 12. Capacity allocation boundary

Minimum concepts:

```text
resource/workcenter
time bucket
required / allocated / available capacity
state, source, version
```

May later be: persisted allocation, derived from schedules, or manual planning record.  
HR productive hours and dashboard util are **not** this boundary.

---

## 13. Lock and revalidation

Conceptual Phase B graph:

```text
lock execution plan
→ re-read task
→ query canonical scheduling state
→ query reservation state
→ query capacity state
→ verify all CLEAR
→ continue reassignment dual-write
```

| Question | Current answer |
| -------- | -------------- |
| Same transaction? | Possible if resource rows live in **same SQLite DB** as plan |
| Same DB required? | **Yes** for practical SQLite consistency |
| Snapshot consistency | SQLite single-writer; still need version/CAS on resource rows |
| Multi-process | Not multi-node safe today |
| PostgreSQL later | Same logical txn + row locks preferred |
| Race check→write | Mitigate with resource row version checked inside plan lock |

Do **not** claim multi-node atomicity. Current Phase B only re-reads env/constants — insufficient for operational CLEAR.

---

## 14. Failure / unknown policy (canonical target)

```text
source unavailable → UNKNOWN → block
query fails       → UNKNOWN → block
domain absent     → NOT_CONFIGURED → block
active record     → ACTIVE → block
explicit factual absence under CONFIGURED domain → CLEAR → allow
```

“Configured domain” proof (Owner must decide): schema present + activation flag / registry / Owner GO stamp — **not** mere code deploy.

---

## 15. Audit / provenance (target)

Every evaluation should identify:

```text
source, entity IDs, evaluated_at, configuration state, result, reason code
```

Must not expose: pricing, rates, salary, PII, full `tasks_json`, JWT, secrets.  
History: prefer append-only source events; current-state view may be derived.

---

## 16. API / read-model options (conceptual only)

| Option | Consumer | Security | Staleness | Notes |
| ------ | -------- | -------- | --------- | ----- |
| Internal service only | Phase B | Best | Fresh in txn | **Preferred first** |
| Read-only admin diagnostics | managers/admins | AuthZ required | May lag | Useful after R3 |
| Extend existing readiness GET | operators | Overload risk | Confuses HOLD vs CLEAR | **Defer** — high misleading risk |

No endpoint added in this audit.

---

## 17. UI findings (page-wide, no redesign)

| Surface | Risk |
| ------- | ---- |
| `Programare: HOLD` | Looks like live planning state; is inventory constant |
| ORR **“Pregătit”** | Capability match ≠ scheduled/reserved/assigned |
| Honesty footers (“neprogramat”, “≠ rezervat”) | Helpful but green “Pregătit” still misleading |
| Employee eligibility “ready” | Technical candidate — clearer than ORR “Pregătit” |

Future UI must not imply scheduled / available / reserved / capacity clear / ready to start without canonical proof. Gap recorded; **no UI change authorized**.

---

## 18. Schema decision gate

```text
SCHEMA_CHANGE_REQUIRED = YES
```

Conceptual models (not created):

```text
task_schedule              # later Option C
machine_reservation        # later Option C
capacity_allocation        # later Option C
resource_state_event       # Option B interim / audit spine
# and/or resource_state_current projection
```

A read service with **no** new sources cannot unlock CLEAR:

```text
SCHEMA_CHANGE_REQUIRED = NO  # only if wrapping placeholders — REJECTED as path
```

---

## 19. Recommended program (unauthorized)

```text
RECOMMENDED_PATH = MINIMAL_CANONICAL_RESOURCE_STATE_CONTRACT
RECOMMENDED_CONCLUSION = PERSISTED_RESOURCE_STATE_MODEL_REQUIRED
FULL_SCHEDULING_DOMAIN_REQUIRED_FIRST = NO
IMPLEMENTATION_AUTHORIZED = NO
```

### Phase R1 — Owner decisions and domain contract

Semantics CLEAR/ACTIVE/UNKNOWN/NOT_CONFIGURED; configured-domain proof; grain; ownership Option B vs C; SQLite freeze compatibility.

### Phase R2 — Minimal canonical data/source model

Schema/events for resource state (and/or minimal schedule/reservation/allocation records) — **Owner GO + schema GO required**.

### Phase R3 — Read service and fail-closed guards

Wire Phase B to real probes; remove reliance on operational CLEAR from env.

### Phase R4 — Isolated runtime and concurrency proof

No QA mutation.

### Phase R5 — Controlled QA resource-state proof

Only after Owner GO (still ≠ Phase C reassignment).

### Phase R6 — Reconsider Phase C

Only if all three domains return factual CLEAR under lock.

---

## 20. Owner decisions required (before implementation)

1. Confirm `PERSISTED_RESOURCE_STATE_MODEL_REQUIRED` (or reject for full domain first).  
2. Define **configured domain** activation criterion.  
3. Define CLEAR/ACTIVE/UNKNOWN/NOT_CONFIGURED per domain.  
4. Choose grain per domain (task/window/machine/bucket).  
5. Choose ownership Option B interim vs jump to Option C.  
6. Authorize schema/migration GO separately (`DEC-DATABASE-01` still SQLite freeze).  
7. Decide whether availability enters the triad.  
8. Decide admin diagnostic API vs internal-only.  
9. Decide UI honesty remediation GO (separate from resource implementation).  
10. Explicitly keep Phase C blocked until R5/R6 Owner GO.

---

## 21. Dead pieces check

| Piece | Classification |
| ----- | -------------- |
| scheduling HOLD | `PLACEHOLDER` |
| not_reserved | `PLACEHOLDER` |
| capacity NOT_STARTED | `PLACEHOLDER` |
| Phase B resource guard | `ACTIVE_CANONICAL` (fail-closed) |
| `WORKOS_PHASE_B_RESOURCE_GUARDS` | `TEST_ONLY` |
| HR/dashboard capacity | `SUPPORTED_NOT_ACTIVE` for Phase C |
| unused schedule helpers | `DEAD_CANDIDATE` / `UNKNOWN` |
| old readiness UI “Pregătit” | `ACTIVE_LEGACY` honesty risk |
| QA CLEAR fixture | `REJECTED_STRATEGY` |

```text
Dead pieces removed: NONE
```

---

## 22. Stop

```text
IMPLEMENTATION_AUTHORIZED = NO
PHASE_C = BLOCKED
RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY = NOT_STARTED
```

Await Owner review. Do not implement.
