# Capacity Stage 1 — Canonical Migration and QA Rollout Readiness

**Task:** `CAPACITY_STAGE_1_CANONICAL_MIGRATION_AND_QA_ROLLOUT_READINESS`  
**Owner GO:** `AUTHORIZE_CAPACITY_STAGE_1_CANONICAL_MIGRATION_AND_QA_ROLLOUT_READINESS`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `d70904c2`  
**Prerequisite:** `CAPACITY_STAGE_1 = PASS` (tip `d70904c2`)

---

## Verdict

```text
CAPACITY_STAGE_1_MIGRATION_READINESS = PASS
CANONICAL_MIGRATION_CLOSURE = VERIFIED
CODE_ALEMBIC_HEAD = s65_workcenter_capacity_source
QA_ALEMBIC_REVISION = s64_resource_state_persistence
ORM_MIGRATION_PARITY = VERIFIED
SCHEMA_DRIFT = NONE
CONSTRAINTS = VERIFIED
INDEXES = VERIFIED
SQLITE_FOREIGN_KEYS = VERIFIED_ON
FRESH_FULL_CHAIN = VERIFIED
S64_TO_S65 = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED
SCHEMA_FINGERPRINT = MATCH
INITIAL_CAPACITY_SOURCE_ROWS = 0
INITIAL_CAPACITY_ALLOCATIONS = 0
INITIAL_CAPACITY_CONFIGURATION = 0
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_ROLLOUT = NOT_AUTHORIZED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Preflight (confirmed)

| Check | Result |
| ----- | ------ |
| worktree | `C:\w\psiso` |
| branch | `feat/f7i-owner-rate-activation` |
| starting HEAD | `d70904c2` |
| foreign tracked changes | none (only this GO's test/doc edits) |
| code Alembic head | `s65_workcenter_capacity_source` |
| QA Alembic | `s64_resource_state_persistence` |
| QA Scheduling / Reservation | ACTIVE / ACTIVE |
| QA Capacity config | 0 |
| QA capacity source table | absent |
| QA capacity source / allocation rows | 0 / 0 |
| QA `foreign_key_check` | 0 |
| QA assignment transitions | 7 |
| QA DB SHA256 | `3b80f9a8b8071dd6a4addbf553ba372f018e131dde52e937c2d249fb02d5bea2` (unchanged vs R11) |

---

## 1. s65 package (exact)

**Ancestry:** `s64_resource_state_persistence` → `s65_workcenter_capacity_source` · single head · no branch · no orphan · no stamp.

### New tables

| Table | Role |
| ----- | ---- |
| `workcenter_capacity_sources` | Current Owner-configured available minutes per workcenter/day |
| `workcenter_capacity_source_transitions` | Append-only transition history (CAS / audit) |

### Expand-only columns (existing s64 tables)

| Table | Columns |
| ----- | ------- |
| `execution_task_capacity_allocations` | `workload_source`, `workload_source_reference`, `workload_explanation` (nullable) |
| `execution_task_capacity_allocation_transitions` | same three (nullable) |

Nullable so upgrade does not backfill or invent workload labels for pre-Stage-1 rows.

### New indexes / uniques / FKs / checks (sources)

**Indexes:** `ix_wc_capacity_source_status`, `ix_wc_capacity_source_wc_day`, partial unique `uq_wc_capacity_source_active_wc_day` (`WHERE status='ACTIVE'`).

**Uniques:** `uq_wc_capacity_source_idempotency`; transition `uq_wc_capacity_source_tr_transition_id`, `uq_wc_capacity_source_tr_idempotency`.

**FKs:** `superseded_by_id` → sources (RESTRICT); transitions `source_id` → sources (RESTRICT).

**Checks (source):** status ∈ ACTIVE|DISABLED|SUPERSEDED; policy ∈ WARN_ONLY|HARD_BLOCK|ALLOW_WITH_REASON; source_label ∈ OWNER_CONFIGURED|SYSTEM_DERIVED|AI_DECISION; `available_minutes >= 0`; `version >= 1`; nonblank workcenter; `bucket_end > bucket_start`; no self-supersede.

**Zero backfill:** upgrade creates empty tables / nullable columns only. No Capacity domain configuration row. No synthetic source.

---

## 2. ORM ↔ migration parity

Compared columns, nullability, defaults/server defaults, PK/FK, uniques, checks, indexes, status vocab, version, idempotency, timestamps for both new tables + workload columns.

```text
PARITY_CLEAN
```

SQLite may surface UniqueConstraint as `sqlite_autoindex_*`; named uniques remain in CREATE TABLE DDL (asserted in closure tests).

---

## 3. Constraint closure

### DB-enforced (s65 sources)

| Rule | Mechanism |
| ---- | --------- |
| available_minutes ≥ 0 | CHECK |
| version ≥ 1 | CHECK |
| one ACTIVE source per workcenter/day | partial UNIQUE INDEX |
| valid over-allocation policy | CHECK |
| valid source label | CHECK |
| valid day window (`end > start`) | CHECK |
| unique idempotency | UNIQUE |
| transition UUID unique | UNIQUE |
| orphan transition rejected | FK RESTRICT on `source_id` |

Timezone / exact DAY bucket alignment: **application-guarded** (`capacity_day_bucket` + command service).

### Allocation Stage 1

| Rule | Layer |
| ---- | ----- |
| `resource_scope_type` WORKCENTER\|MACHINE, unit minutes, quantity > 0, window, task_key, plan FK | DB (s64) |
| Stage 1 **WORKCENTER only** (reject MACHINE) | application |
| exact DAY bucket bounds | application |
| labeled workload; null minutes rejected (never 0) | application |
| open-allocation totals via SQL aggregate on workcenter + exact day bounds | repository (indexed paths) |

---

## 4. Index closure (query paths)

| Path | Index / support |
| ---- | --------------- |
| capacity source by workcenter + day | `ix_wc_capacity_source_wc_day` + partial active unique |
| capacity source by status | `ix_wc_capacity_source_status` |
| capacity transitions by source | `ix_wc_capacity_source_tr_source_id` |
| capacity transitions by wc/day/created | `ix_wc_capacity_source_tr_wc_day_created` |
| allocations by workcenter + day / plan+task / status | s64 indexes (unchanged); Stage 1 sums use SQL aggregate |

---

## 5–9. Isolated proofs

Suite: `backend/tests/test_capacity_stage_1_canonical_migration_closure.py`

| Proof | Result |
| ----- | ------ |
| Ancestry / single head | PASS |
| Fresh `alembic upgrade head` → s65, FK=ON, empty Capacity tables, no config | PASS |
| s64 → s65 preserves ExecutionPlan / RS configs / assignment transitions; Capacity rows stay 0 | PASS |
| downgrade s64 → re-upgrade s65; schema fingerprint A = B; RS rows intact; new tables empty | PASS |
| runtime `create_all` creates normal tables; **s65 + RS Alembic-owned absent**; Alembic head creates them | PASS |
| Constraint smoke (neg minutes / duplicate ACTIVE day) | PASS |

Also updated head expectations in R3 / R4 / Wave 10 closure suites so `upgrade head` asserts `s65`.

**Operational warning:** downgrade after Capacity source data exists is destructive and requires a separate Owner GO.

---

## 10. Stage 1 behavior regression

```text
tests/test_capacity_stage_1_workcenter_source_and_writer.py  → passed
tests/test_resource_state_r9_scheduling_writer.py            → passed
tests/test_resource_state_r9_reservation_writer.py           → passed
tests/test_resource_state_r10_activation_readiness.py        → passed
tests/test_capacity_stage_1_canonical_migration_closure.py   → passed
tests/test_resource_state_r3_migration_closure.py            → passed
tests/test_resource_state_r4_canonical_migration_closure.py  → passed
tests/test_finalization_wave10_canonical_migration_closure.py → passed
```

No semantic changes to accepted Stage 1 / R9 / R10 behavior.

---

## 11. QA read-only proof (post-audit)

```text
QA revision                 = s64_resource_state_persistence
Scheduling config           = ACTIVE
Reservation config          = ACTIVE
Capacity config             = 0 (no CAPACITY domain row)
schedule rows               = 0
reservation rows            = 0
capacity allocation rows    = 0
capacity source table       = absent
foreign_key_check           = 0
assignment transitions      = 7
QA SHA                      = 3b80f9a8… (unchanged)
QA_SCHEMA_MUTATIONS         = 0
QA_DATA_MUTATIONS           = 0
```

---

## 12. Schema rollout ≠ Capacity activation

After a **future** QA upgrade to s65 (separate GO), expected:

```text
Capacity source schema exists
Capacity source rows = 0
Capacity configuration = 0
Capacity allocations = 0
Capacity evaluator = NOT_CONFIGURED
Aggregate = BLOCKED_NOT_CONFIGURED
```

Do not activate Capacity merely because schema exists.

---

## Future controlled QA schema rollout plan (NOT AUTHORIZED)

```text
1. Maintenance window
2. Backup QA SQLite (timestamped under backend/_qa_backups/…)
3. Record pre-SHA, revision s64, config rows, assignment transitions = 7
4. alembic upgrade s65_workcenter_capacity_source
5. Verify: 8 RS tables preserved; 2 Capacity source tables empty; workload columns present nullable
6. Verify: Capacity domain still absent / NOT_CONFIGURED; Scheduling+Reservation still ACTIVE
7. Backend restart (detached stack)
8. Read-only smoke (evaluator NOT_CONFIGURED; no writer calls against QA)
9. Rollback: restore backup file OR isolated downgrade only with Owner GO if empty
```

Rollback note: if any Capacity source rows exist, downgrade is destructive — restore from backup preferred.

---

## `/modules` and `/governance` impact

| Surface | Verdict |
| ------- | ------- |
| Harta sistemelor (`/modules`) | **NO_IMPACT** now — Stage 1 code already documented; QA schema still s64; Capacity inactive. No UI route change required for this audit-only GO. |
| Guvernanța sistemului (`/governance`) | **NO_IMPACT** now — ownership already: Owner-configured workcenter/day; Alembic owns schema; AI preview-only; activation Owner-gated. Revisit when QA schema rolls out or Capacity activates. |

---

## Files (this GO)

| Path | Change |
| ---- | ------ |
| `backend/tests/test_capacity_stage_1_canonical_migration_closure.py` | new isolated s64→s65 closure suite |
| `backend/tests/test_resource_state_r3_migration_closure.py` | head = s65 |
| `backend/tests/test_resource_state_r4_canonical_migration_closure.py` | head / create_all ownership for s65 |
| `backend/tests/test_finalization_wave10_canonical_migration_closure.py` | head = s65 |
| `docs/worklog/realignment/2026-08-05_capacity_stage_1_canonical_migration_and_qa_rollout_readiness.md` | this worklog |
| `docs/architecture/CAPACITY_SOURCE_AND_WRITER_DECISION.md` | status pointer |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | next-step pointer |

**No push. No QA Alembic upgrade. No Capacity activation. Phase B / Phase C remain blocked.**

---

## Next (future candidate only)

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CONTROLLED_QA_SCHEMA_ROLLOUT
```

Installs schema `s65` in QA only. Does **not** activate Capacity, create minutes, or create allocations.
