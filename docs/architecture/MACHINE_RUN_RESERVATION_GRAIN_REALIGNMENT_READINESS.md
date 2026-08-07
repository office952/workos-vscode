# MACHINE_RUN — Reservation Grain Realignment Readiness

**Task:** `MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · docs-only · **no ORM · no migration · no runtime**  
**Starting HEAD:** `7aef85e1`  
**Prerequisites:** `MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS = PASS` · Owner D4 · Reservation R9 ACTIVE  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_reservation_grain_realignment_readiness.md`

```text
MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS = PASS
CURRENT_RESERVATION_GRAIN = TASK_OWNED
TARGET_RESERVATION_GRAIN = TASK_OR_MACHINE_RUN_OWNED
OWNERSHIP_MODEL = OPTION_B_EXPLICIT_DUAL_OWNERSHIP_FIELDS
OWNER_CONSTRAINT = TASK_OWNER_XOR_RUN_OWNER
TASK_RESERVATION_COMPATIBILITY = PRESERVED
RUN_RESERVATION_MODEL = FINALIZED
OVERLAP_ENGINE = SINGLE_SHARED
CAS_IDEMPOTENCY = FINALIZED
TRANSITION_HISTORY = FINALIZED
R6_TASK_TO_RUN_RESERVATION_PATH = FINALIZED
MACHINE_RUN_CREATE_RESERVATION_FLOW = FINALIZED
SCHEMA_GAP = RESERVATION_OWNER_COLUMNS_PLUS_MACHINE_RUN_TABLES
MIGRATION_ORDER = SINGLE_ATOMIC_SCHEMA_SLICE
BACKFILL_POLICY = NO_SYNTHETIC_RUN_BACKFILL
RUNTIME_IMPLEMENTATION = NOT_STARTED
RESERVATION_SCHEMA_CHANGE = IMPLEMENTED_IN_CODE_ALEMBIC_S66
MACHINE_RUN_SCHEMA_FOUNDATION = PASS
QA_S66_SCHEMA_ROLLOUT = PASS
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
QA_ALEMBIC = s66_machine_run_reservation_grain
QA_ROLLOUT_RUNTIME = NOT_AUTHORIZED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Why this must precede MACHINE_RUN runtime

```text
MACHINE_RUN contract says:
  1 run → 1 Reservation → N participants

Current Reservation says:
  1 open claim → 1 (plan, task_key, machine)
```

Implementing `machine_runs` first while Reservation stays task-keyed would force a structural lie (pick one participant as “owner” or invent a sentinel `task_key`). Grain realignment readiness closes that contradiction **before** ORM.

---

## 2. Current reservation grain (demonstrated)

### Current-state row — `execution_task_machine_reservations`

| Column / constraint | Today |
| ------------------- | ----- |
| PK | `id` |
| Plan | `execution_plan_id` NOT NULL FK |
| Order | `order_id` NOT NULL (denormalized) |
| Task | `task_key` NOT NULL + `ck_…_task_key_nonblank` |
| Machine | `machine_id` NOT NULL FK |
| Window | `reservation_start` / `reservation_end` / `timezone` |
| Status | HELD · RESERVED · CANCELLED · RELEASED · SUPERSEDED |
| CAS | `version` ≥ 1 |
| Idempotency | `idempotency_key` UNIQUE |
| Open unique | `(execution_plan_id, task_key, machine_id)` WHERE open |
| Indexes | plan+task · status · machine+window |

### Transition row — `execution_task_machine_reservation_transitions`

Stores `reservation_id`, `execution_plan_id`, **`task_key` NOT NULL**, `machine_id`, operation, previous/new status/window/version, actor/reason, `idempotency_key`, `created_at`.

### `task_key` required matrix

| Layer | Required |
| ----- | -------- |
| `TASK_KEY_REQUIRED_AT_DB` | **YES** |
| `TASK_KEY_REQUIRED_AT_SCHEMA` | **YES** (CREATE body) |
| `TASK_KEY_REQUIRED_AT_SERVICE` | **YES** (`require_task_in_plan`, open-per-task-machine) |
| `TASK_KEY_REQUIRED_AT_API` | **YES** (CREATE); mutate by `reservation_id` |
| `TASK_KEY_REQUIRED_AT_READER` | **YES** (`list_reservations_for_task`) |

Evidence roots: `backend/models/execution_task_machine_reservation.py`, `schemas/resource_state_reservation.py`, `execution_task_machine_reservation_command_service.py`, `resource_state_read_repository.py`, Alembic s64.

---

## 3. Consumer inventory (`task_key` dependencies)

| Consumer | Dependency | Hard/soft | Impact if run-owned |
| -------- | ---------- | --------- | ------------------- |
| CREATE_RESERVATION | body `task_key`, membership, open unique, row write | **Hard** | New create path; must not require single task owner |
| CONFIRM / RELEASE / CANCEL | input by `reservation_id`; persist copies `row.task_key` | Soft input / **Hard** persist | OK if row has owner snapshot columns |
| SUPERSEDE | copies `task_key` to replacement | **Hard** | Run-owned supersede copies `machine_run_id`, not a fake task |
| Overlap `find_overlapping_open` | `machine_id` + window only | **Soft** (machine-centric) | **Reuse unchanged** |
| `get_open_for_task_machine` | plan+task+machine | **Hard** | Keep for task-owned; add open-by-run lookup |
| `require_task_in_plan` | every write | **Hard** | Task-owned only; run-owned skips |
| R6 evaluator | `list_reservations_for_task` | **Hard** | Must union participant→run→reservation |
| Resource-state GET task | `?task_key=` | **Hard** | Same join for run-owned claims |
| Permissions | role gate only | None | Unchanged |
| Phase B guard | does not read reservations today | None | Future: must use join path |
| Capacity | sibling domain; inactive | None | Must stay decoupled |
| Tests (R9/R10/R6) | CREATE fixtures with `task_key` | **Hard** | Keep task-owned suites; add run-owned suites later |

**Overlap engine stays single and machine-centric** — owner type must not fork exclusivity logic.

---

## 4. Options compared

| Option | Shape | Pros | Cons | Verdict |
| ------ | ----- | ---- | ---- | ------- |
| **A — polymorphic** | `owner_type` + `owner_id` | One abstract owner | Weak RI on SQLite; opaque FK; harder CHECKs | **Reject** |
| **B — explicit dual fields** | `machine_run_id` nullable + task fields nullable + XOR CHECK | Explicit FK to future `machine_runs`; task path preserved; clear constraint | Nullable columns; CHECK complexity | **Select** |
| **C — separate tables** | `task_*` + `machine_run_*` reservations | Clearest ownership | Duplicate lifecycle, overlap, CAS, history — forbidden | **Reject** |

```text
OWNERSHIP_MODEL = OPTION_B_EXPLICIT_DUAL_OWNERSHIP_FIELDS
```

Why B fits this repo:

1. Reservation table already carries exclusive clock + CAS + transitions — keep one engine.
2. SQLite can enforce XOR via CHECK; FK `machine_run_id → machine_runs.id` is real (unlike polymorphic).
3. Task-level CREATE API and open unique can remain for `TASK` owner form.
4. Option C would violate “one overlap truth” and double R9 surface area.

---

## 5. Selected ownership model and constraint

### Canonical rule

```text
OWNER_CONSTRAINT = TASK_OWNER_XOR_RUN_OWNER
```

**Task-owned (existing / individual runs):**

```text
execution_plan_id  NOT NULL
task_key           NOT NULL (nonblank)
machine_run_id     NULL
order_id           NOT NULL (from plan)
```

**Run-owned (shared MACHINE_RUN):**

```text
machine_run_id     NOT NULL  FK → machine_runs.id
execution_plan_id  NULL
task_key           NULL
order_id           NULL   (participants carry plan/order provenance)
```

**Forbidden:**

```text
both owners set
neither owner set
task fields partially set under RUN owner
machine_run_id set under TASK owner
```

### Authority direction (unchanged from MACHINE_RUN readiness)

```text
machine_runs.reservation_id → reservation.id     (ownership authority)
reservation.machine_run_id  → machine_runs.id     (explicit back-FK for OPTION_B / RI)
```

Both sides of the 1:1 link are set in the **same transaction**. Authority for “who owns the claim” when reasoning about D4 remains: **run owns reservation** (`machine_runs.reservation_id`). The reservation’s `machine_run_id` is the dual-ownership discriminator and FK integrity aid — not a second competing owner story.

### Open uniqueness (future)

| Owner form | Open uniqueness |
| ---------- | --------------- |
| TASK | Keep partial unique `(execution_plan_id, task_key, machine_id)` WHERE open AND task-owned |
| RUN | Partial unique `(machine_run_id)` WHERE open AND run-owned **or** rely on `machine_runs.reservation_id` UNIQUE + machine overlap |

Machine overlap (`find_overlapping_open`) remains the cross-owner exclusivity truth.

---

## 6. Task reservation compatibility (preserved)

```text
existing task reservation     → stays task-owned
future individual CNC task    → may still use task-owned reservation
future shared CNC batch       → uses run-owned reservation only
```

- No reinterpretation of historical rows as MACHINE_RUN.
- No requirement that every `face_cnc_cut` become a run.
- Single-participant CNC may use either form later; default for shared batch is run-owned.

---

## 7. Run reservation lifecycle

```text
Reservation still owns:
  machine_id + exclusive interval + status/version/CAS

MACHINE_RUN owns:
  participant set + run status + reservation_id link

Reservation does NOT validate participants.
MACHINE_RUN service validates participants
  (batch_eligible, MACHINE_BOUND, capability compatibility, membership).
```

Statuses stay HELD / RESERVED / CANCELLED / RELEASED / SUPERSEDED for the claim. Run status names align; writers keep run↔reservation consistent in one txn (see MACHINE_RUN readiness).

---

## 8. MACHINE_RUN creation flow (finalized)

Circular dependency closed by **Flow C**:

```text
MACHINE_RUN_CREATE_RESERVATION_FLOW = SINGLE_ORCHESTRATION_COMMAND
```

```text
one service command (same DB transaction):
  1. validate participants (MACHINE_RUN domain)
  2. insert machine_runs row (version=1, status=HELD, reservation_id pending or assigned after step 3)
  3. insert run-owned reservation (machine_run_id set; task fields null)
  4. set machine_runs.reservation_id = reservation.id
  5. insert run participants
  6. append run + reservation transitions
  7. commit
```

SQLite/ORM may insert run first with a deferred assignment of `reservation_id` inside the same txn, or insert reservation after run id is known — **both are valid as long as commit is atomic and no open run exists without reservation**.

Rejected as primary operator flows:

- Flow A split across two client calls without orchestration
- Flow B “orphan reservation then attach” as the happy path (allowed only as controlled attach of an already-open claim in a later GO if needed)

```text
API: MACHINE_RUN service owns run-level reservation creation (Variant B)
Task-level POST /resource-state/reservations remains for TASK owner form
```

---

## 9. Participant validation boundary

| Layer | Validates |
| ----- | --------- |
| Reservation writer (run-owned) | machine reservability, window, overlap, owner XOR, CAS/idempotency |
| MACHINE_RUN service | participants exist in plans, `batch_eligible`, `resource_mode=MACHINE_BOUND`, capability match, membership uniqueness |
| Reservation writer (task-owned) | unchanged: `require_task_in_plan` + open-per-task-machine |

Do **not** duplicate participant eligibility checks inside Reservation.

---

## 10. Overlap engine (finalized)

```text
OVERLAP_ENGINE = SINGLE_SHARED
```

```text
same machine + overlapping interval + open status
→ conflict
regardless of TASK vs MACHINE_RUN owner
```

Reuse `find_overlapping_open` / `list_open_for_machine`. No second exclusivity clock on `machine_runs`.

---

## 11. CAS / idempotency (finalized)

- CAS remains **reservation-level** `version` / `expected_version`.
- Transition `idempotency_key` UNIQUE + fingerprint replay remains.

### Fingerprint ownership

| Owner form | CREATE fingerprint must include |
| ---------- | ------------------------------- |
| TASK | `owner=TASK`, `execution_plan_id`, `task_key`, `machine_id`, window |
| RUN | `owner=RUN`, `machine_run_id`, `machine_id`, window — **no canonical `task_key`** |

Mutate ops (confirm/release/cancel) stay keyed by `reservation_id` + version (task_key not required in match fingerprint today — keep that).

---

## 12. Transition history (finalized)

Favor auditability: **snapshot owner identity on each transition**.

Future transition columns (design):

| Field | Role |
| ----- | ---- |
| `owner_form` | `TASK` \| `MACHINE_RUN` |
| `execution_plan_id` | nullable — set for TASK owner |
| `task_key` | nullable — set for TASK owner |
| `machine_run_id` | nullable — set for RUN owner |

Current rows always have `task_key` NOT NULL; migration must relax that and backfill `owner_form=TASK` for existing history (no synthetic runs).

Deriving owner only from current row is insufficient after supersede/replace chains — snapshot on transition.

---

## 13. R6 evaluator impact (finalized)

Today:

```text
task → list_reservations_for_task(plan, task_key) → HELD|RESERVED ⇒ ACTIVE
```

Future (design):

```text
task →
  (A) task-owned reservations WHERE plan+task_key
  UNION
  (B) participants → machine_run → reservation
→ evaluate blocking = HELD|RESERVED
```

| Reservation status | Effect on each ACTIVE participant |
| ------------------ | --------------------------------- |
| HELD | ACTIVE (blocking) |
| RESERVED | ACTIVE (blocking) |
| RELEASED | not blocking → CLEAR (if no other blockers) |
| CANCELLED | not blocking |
| SUPERSEDED | not blocking; follow current run’s reservation |

Without this join, participants would false-CLEAR while the run holds the machine.

Phase B (future, not wired): pre-start reassignment must consume the same union path.

---

## 14. API compatibility (finalized)

| Surface | Disposition |
| ------- | ----------- |
| `POST …/resource-state/reservations` | **Keep** — TASK owner only |
| confirm / release / cancel / supersede by id | **Keep** — works for both owner forms once row exists |
| GET task resource-state | **Keep** query shape; **extend** evaluation join |
| Future CREATE_RUN | **New** MACHINE_RUN command surface — creates reservation internally |

Operator must not be required to manually create run + reservation + link.

---

## 15. Schema gap (exact)

### Future columns on `execution_task_machine_reservations`

| Change | Why now (for impl GO) |
| ------ | --------------------- |
| `machine_run_id` nullable FK → `machine_runs.id` | RUN owner form |
| `execution_plan_id` nullable | RUN owner has no single plan |
| `task_key` nullable; drop/adjust nonblank CHECK to apply only when TASK | RUN owner |
| `order_id` nullable | RUN owner; provenance on participants |
| CHECK `TASK_OWNER XOR RUN_OWNER` | integrity |
| Adjust open partial unique for task-owned only | grain |
| Optional: open unique on `machine_run_id` where run-owned open | one open claim per run |

### Future columns on transitions

| Change | Why |
| ------ | --- |
| `owner_form` | audit |
| `machine_run_id` nullable | audit |
| `task_key` / `execution_plan_id` nullable | match owner form |

### Future tables (still required; not created here)

```text
machine_runs
machine_run_participants
machine_run_transitions
```

---

## 16. Migration order (finalized)

```text
MIGRATION_ORDER = SINGLE_ATOMIC_SCHEMA_SLICE
```

**Safe order inside one Alembic revision (future GO):**

1. Create `machine_runs` (+ participants + transitions) with nullable `reservation_id` temporarily **or** create tables then add FKs after reservation columns exist — prefer:
2. Add reservation owner columns + relax nullability + XOR CHECK + indexes.
3. Add `machine_runs.reservation_id` UNIQUE FK → reservations (and/or finalize both directions).
4. Backfill: existing reservation rows → `owner_form` implicit TASK (`machine_run_id` NULL; task fields remain).
5. **No** synthetic MACHINE_RUN rows.

**Rejected:** Reservation grain migration without `machine_runs` (cannot FK `machine_run_id`).  
**Rejected:** MACHINE_RUN runtime before grain columns (returns to structural contradiction).

```text
same GO / same migration slice for:
  MACHINE_RUN tables + Reservation owner grain
runtime writers may still be a follow-on GO if Owner splits —
but schema must land together
```

---

## 17. Backfill policy

```text
BACKFILL_POLICY = NO_SYNTHETIC_RUN_BACKFILL
```

```text
QA reservation rows = 0 today → no data rewrite needed
future/real DBs with task reservations → preserve as TASK owner
no invented MACHINE_RUN for historical CNC claims
```

---

## 18. face_cnc_cut example (conceptual)

```text
Task A: face_cnc_cut · CNC_ROUTER_CUTTING · MACHINE_BOUND · batch_eligible=true
Task B: face_cnc_cut · CNC_ROUTER_CUTTING · MACHINE_BOUND · batch_eligible=true
compatible under future grouping rules
→ MACHINE_RUN X
→ participants A + B
→ one run-owned Reservation (machine_run_id = X)
≠ Reservation(A) + Reservation(B) for the same shared interval
```

Individual non-batched face cut may still use a **task-owned** reservation.

---

## 19. Capacity / Phase B boundaries

```text
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
```

Run-owned reservation must **not** auto-seed or consume Workcenter Capacity.

```text
PHASE_B = NOT_AUTHORIZED
```

Future effect only: participant + open run reservation ⇒ task sees ACTIVE machine commitment via R6 union path.

---

## 20. What must be implemented before MACHINE_RUN runtime writers

Ordered prerequisites:

1. **Atomic schema slice** — DONE in code (`s66`); QA rollout not authorized.
2. R6 union reader path — DONE (`list_reservations_visible_to_task`).
3. Task-owned reservation writer compatibility — DONE (R9 unchanged).
4. Reservation writer support for RUN owner form + CREATE fingerprint without `task_key` — future runtime GO.
5. MACHINE_RUN orchestration command (`CREATE_MACHINE_RUN`) — contract READY; implementation GO separate  
   (`docs/architecture/MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS.md`).
6. Grouping eligibility beyond the three demand stamps — separate GO.

```text
RESERVATION_SCHEMA_CHANGE = IMPLEMENTED_IN_CODE_ALEMBIC_S66
MACHINE_RUN_SCHEMA_FOUNDATION = PASS
QA_S66_SCHEMA_ROLLOUT = PASS
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
QA_ALEMBIC = s66_machine_run_reservation_grain
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
QA_ROLLOUT_RUNTIME = NOT_AUTHORIZED
```

Schema foundation worklog: `docs/worklog/realignment/2026-08-07_machine_run_reservation_grain_schema_foundation.md`.  
QA rollout worklog: `docs/worklog/realignment/2026-08-07_machine_run_reservation_grain_controlled_qa_s66_schema_rollout.md`.  
Command readiness: `docs/architecture/MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS.md`.

**Implemented link shape (s66):** one-direction `reservation.machine_run_id → machine_runs.id` UNIQUE (no `machine_runs.reservation_id`) to avoid circular FK; D4 semantic ownership unchanged.

---

## 21. Overengineering check

| Candidate | Needed for 1 run → 1 res → N tasks? | Verdict |
| --------- | ----------------------------------- | ------- |
| Option C dual tables | no | defer/reject |
| Auto-batching / nesting optimizer | no | defer |
| UI / telemetry / cost split | no | defer |
| Polymorphic owner_type | no | reject |
| OPTION_B XOR + single overlap | **yes** | accept (design) |

---

## 22. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_RUNTIME_STATUS_CHANGE** — design only: Reservation currently task-owned; future TASK\|RUN owner |
| `/governance` | **NO_RUNTIME_STATUS_CHANGE** — document mentally: demand (task) · commitment (reservation) · grouping (MACHINE_RUN) |

---

## 23. QA proof (read-only)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Machine Reservation = ACTIVE
Capacity = NOT_CONFIGURED
reservation rows = 0
MACHINE_RUN tables = absent
capacity source/alloc = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
plan 21 SHA = 75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59
plan 22 SHA = 0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97
plan 23 SHA = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
QA_MUTATIONS = 0
```

---

## 24. Answers to the ten GO questions

| # | Answer |
| - | ------ |
| 1 | Grain = task-owned `(plan, task_key, machine)` open unique + required `task_key` |
| 2 | `task_key` obligatory at DB, schema CREATE, service, API CREATE, R6 reader |
| 3 | See §3 consumer inventory |
| 4 | Run-owned via OPTION_B `machine_run_id` + null task fields; run.`reservation_id` authority |
| 5 | Yes — task-level remains valid for individual claims |
| 6 | Two owner **forms** on one table (XOR), not two reservation engines |
| 7 | Nullable owner columns + XOR CHECK + indexes + MACHINE_RUN tables |
| 8 | No synthetic run backfill; existing rows stay TASK |
| 9 | Overlap unchanged; CAS reservation-level; R6 gains participant union |
| 10 | Atomic schema slice + writer/reader/orchestration before grouping UI |

```text
NEXT_TASK = NOT_AUTHORIZED
```
