# QA Foreign-Key Debt Remediation Plan

**Planning task:** `QA_FOREIGN_KEY_DEBT_REMEDIATION = PLANNING_AND_ISOLATED_CLONE_REHEARSAL`  
**Execution task:** `CONTROLLED_QA_FK_DEBT_REMEDIATION`  
**Owner GO (planning):** `AUTHORIZE_QA_FOREIGN_KEY_DEBT_REMEDIATION_PLANNING`  
**Owner GO (execution):** `AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION`  
**Approved strategy:** `HYBRID_C_PLUS_B`  
**Date:** 2026-08-05  
**Status:** Planning **PASS** · Clone rehearsal **VERIFIED** · Controlled QA remediation **PASS** · R5 schema-only **PASS** (follow-on) · R6 **NOT AUTHORIZED**  
**Planning worklog:** `docs/worklog/realignment/2026-08-05_qa_foreign_key_debt_remediation_planning_and_clone_rehearsal.md`  
**Execution worklog:** `docs/worklog/realignment/2026-08-05_controlled_qa_foreign_key_debt_remediation.md`  
**Rehearsal script:** `backend/scripts/qa_fk_debt_remediation_clone_rehearsal.py`  
**Apply script:** `backend/scripts/qa_fk_debt_remediation_hybrid_c_plus_b_apply.py`

```text
QA_FK_DEBT_REMEDIATION_PLANNING = PASS
ISOLATED_CLONE_REHEARSAL = VERIFIED
QA_FK_REMEDIATION_STRATEGY = HYBRID_C_PLUS_B
CONTROLLED_QA_FK_DEBT_REMEDIATION = PASS

FOREIGN_KEY_VIOLATIONS_BEFORE = 11
FOREIGN_KEY_VIOLATIONS_AFTER = 0
FAMILY_A_NULLIFIED = 7
FAMILY_B_DELETED = 4
GLOBAL_TRANSITIONS_BEFORE = 7
GLOBAL_TRANSITIONS_AFTER = 7
PROTECTED_BASELINE_DIFF = NONE
SQLITE_FOREIGN_KEYS = VERIFIED_ON_AFTER_RESTART

QA_ALEMBIC_REVISION = s64  (post-R5 schema-only)
QA_RESOURCE_STATE_TABLES = 8
RESOURCE_STATE_ROWS = 0
R6 = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## 1. Scope

This program plans and rehearses elimination of the 11 preexisting QA foreign-key violations discovered in Pre-R5.

Authorized in this task:

- read-only QA audit
- isolated clone copy / writes / deletes
- clone rollback rehearsal
- clone runtime smoke (non-Owner port)
- clone `s63 → s64`
- remediation SQL design + Owner decision package
- documentation

Not authorized:

- any QA mutation or Alembic on QA
- R5 / Phase B wiring / Phase C
- synthetic parents / FK disable
- push / PR / merge / deploy

---

## 2. Canonical 11-row inventory (reconfirmed)

Source: `PRAGMA foreign_key_check` on QA via sqlite backup copy (`mode` content identity).

| # | Child table | PK | Missing parent | Family | Classification |
| - | ----------- | -- | -------------- | ------ | -------------- |
| 1 | `execution_plan` | 4 | `quote_snapshots_v2` 23099 | A | TEST_OR_DEMO / W5 gate |
| 2 | `execution_plan` | 5 | `quote_snapshots_v2` 23150 | A | TEST_OR_DEMO / W6 gate |
| 3 | `employee_resource_authorizations` | 22 | `employees` 9 | B | LEGACY_ORPHAN |
| 4 | `orders` | 21099 | `quote_snapshots_v2` 21099 | A | TEST_OR_DEMO / W5 gate |
| 5 | `orders` | 22099 | `quote_snapshots_v2` 22099 | A | TEST_OR_DEMO / W5 gate |
| 6 | `orders` | 23099 | `quote_snapshots_v2` 23099 | A | TEST_OR_DEMO / W5 gate |
| 7 | `orders` | 23150 | `quote_snapshots_v2` 23150 | A | TEST_OR_DEMO / W6 gate |
| 8 | `orders` | 29991 | `quote_snapshots_v2` 29991 | A | TEST_OR_DEMO / W5 gate |
| 9 | `operation_employee_authorizations` | 41 | `employees` 9 | B | LEGACY_ORPHAN |
| 10 | `employee_workcenter_authorizations` | 26 | `employees` 9 | B | LEGACY_ORPHAN |
| 11 | `employee_skill_authorizations` | 36 | `employees` 9 | B | LEGACY_ORPHAN |

```text
FAMILY_A_GATE_SNAPSHOT_ORPHANS = 7
FAMILY_B_EMPLOYEE_9_AUTHORIZATION_ORPHANS = 4
PROTECTED_FIXTURE_INTERSECTION = NONE
```

---

## 3. Delete eligibility matrix (11/11)

| # | Row | Verdict | Notes |
| - | --- | ------- | ----- |
| 1 | `execution_plan` id=4 | `DELETE_CANDIDATE_CONFIRMED` | Requires exact gate dependents first (RESTRICT transitions + soft help/participants) |
| 2 | `execution_plan` id=5 | `DELETE_CANDIDATE_CONFIRMED` | Requires exact gate transitions first |
| 3 | `employee_resource_authorizations` id=22 | `DELETE_CANDIDATE_CONFIRMED` | employee 9 absent; no protected mapping |
| 4 | `orders` id=21099 | `DELETE_CANDIDATE_CONFIRMED` | no dependents |
| 5 | `orders` id=22099 | `DELETE_CANDIDATE_CONFIRMED` | no dependents |
| 6 | `orders` id=23099 | `DELETE_CANDIDATE_CONFIRMED` | requires plan 4 + reality/stock/help/participants/transitions |
| 7 | `orders` id=23150 | `DELETE_CANDIDATE_CONFIRMED` | requires plan 5 + transitions |
| 8 | `orders` id=29991 | `DELETE_CANDIDATE_CONFIRMED` | requires soft plan 1 + reality (plan 1 not in FK check) |
| 9 | `operation_employee_authorizations` id=41 | `DELETE_CANDIDATE_CONFIRMED` | print / emp 9 |
| 10 | `employee_workcenter_authorizations` id=26 | `DELETE_CANDIDATE_CONFIRMED` | WC_PRINT / emp 9 |
| 11 | `employee_skill_authorizations` id=36 | `DELETE_CANDIDATE_CONFIRMED` | SK_PRINT_OPERATOR / emp 9 |

```text
DELETE_NOT_SAFE = 0
UNKNOWN = 0
```

Parent truth cannot be reconstructed without synthetic snapshots or employee 9 — rejected by Owner GO.

---

## 4. Critical clone finding — pure 7-row delete is blocked

Deleting only the 7 FK-check rows fails with:

```text
FOREIGN KEY constraint failed
```

Cause: `execution_task_assignment_transitions` references plans 4/5 with `ON DELETE RESTRICT`. Additional soft children (help requests, participants, stock movements, execution_reality, plan 1) also block clean gate-order removal.

```text
PURE_SEVEN_ROW_DELETE = BLOCKED
EXPANDED_EXACT_PK_DELETE = REQUIRED_FOR_OPTION_D
```

---

## 5. Recommended execution strategy

### Primary — Expanded Option D (rehearsed)

Single transaction, exact PKs only (no wildcard deletes):

1. Delete gate help requests `id 1..23` where `execution_plan_id=4`
2. Delete participants `id 1,2,3` where `execution_plan_id=4`
3. Delete gate transitions `id 1..5` where `execution_plan_id IN (4,5)`
4. Delete stock movements `id 1..4` where `order_id=23099`
5. Delete execution_reality `id 1,2` where `order_id IN (23099,29991)`
6. Delete soft plan `id=1` (order 29991, null snapshot FK)
7. Delete Family A plans `id 4,5`
8. Delete Family A orders `id 21099,22099,23099,23150,29991`
9. Delete Family B auth rows (4 exact PKs, `employee_id=9`)
10. `PRAGMA foreign_key_check` → 0
11. Protected baseline asserts
12. COMMIT / rollback on mismatch

### Side effect Owner must accept

| Metric | Before | After Expanded D |
| ------ | -----: | ---------------: |
| Global assignment transitions | 7 | 2 |
| Protected transitions (plans 21/23) | 2 | 2 (unchanged) |
| Plan 23 tasks_json SHA | `00ee947c…` | unchanged |
| LED → employee 7 | yes | yes |

Historical invariant text “transitions 7 · fp 27c68a53…” included **gate debt**. After Expanded D, protected-scope fingerprint is the authority:

```text
protected_transition_fp = 95c2b6769632674319b54c33996e71afd61a1fed7de9b172184edd4bb6a20b7e
```

### Alternative — Hybrid Option C + B (also rehearsed)

- Nullify Family A nullable snapshot FKs (7 column updates)
- Delete Family B auth (4 rows)
- Preserves global transition count 7 and gate audit/help/stock rows
- FK check → 0

Use if Owner prefers retaining gate fixture audit rows.

---

## 6. Clone rehearsal evidence

| Check | Result |
| ----- | ------ |
| Clone initial SHA = source backup SHA | YES |
| Pre FK count | 11 |
| Pure 7-delete blocked | YES |
| Expanded D FK after | 0 |
| Protected orders/plans/tasks/LED/emp7 | unchanged |
| Hybrid C+B FK after | 0 · transitions preserved |
| Rollback via pre-remediation file restore | VERIFIED |
| Deterministic result fingerprint | `75a257f1…` (match across two clones) |
| Runtime smoke port 8017 · FK ON · health | OK |
| `alembic upgrade s64` on remediated clone | OK · 8 RS tables · 0 rows |
| QA mutations | 0 |

Script classification:

```text
NOT_EXECUTED_ON_QA
ISOLATED_CLONE_VERIFIED
OWNER_GO_REQUIRED
```

Local evidence directory (not committed):  
`backend/_qa_backups/fk_debt_remediation_rehearsal/<timestamp>/`

---

## 7. Future QA maintenance-window plan

```text
1. stop writes / maintenance window
2. identify DB file and process owners (Owner backend :8000)
3. create byte-for-byte backup (sqlite backup API + file copy)
4. verify backup SHA
5. verify backup opens read-only
6. capture QA baseline (FK inventory, protected fingerprints)
7. execute exact remediation transaction (Expanded D or Hybrid — Owner choice)
8. run foreign_key_check → expect 0
9. run protected baseline checks
10. restart backend with FK ON (canonical helper)
11. run bounded smoke
12. retain backup until Owner closure
```

Rollback trigger: unexpected row count / PK mismatch / remaining FK violations / protected fingerprint change / backend startup or smoke failure.

Rollback action: stop backend → restore verified backup → verify SHA/schema/fingerprints → restart.

---

## 8. Current backend restart implication

```text
CURRENT_RUNNING_BACKEND_FK_STATE = UNKNOWN until restart
```

Do not declare QA fully protected by FK until a controlled restart onto R3+ code is demonstrated after real remediation.

---

## 9. R5 implication

```text
R5 = NOT_AUTHORIZED
```

Next gate after this planning PASS:

```text
OWNER GO:
AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION
```

Only after real QA remediation + post-repair verification may R5 be reconsidered. No jump from clone rehearsal to R5.

---

## 10. Dead Pieces Check

| Piece | Class |
| ----- | ----- |
| W5/W6 gate orphan fixtures | DATA_DEBT / TEST_ONLY |
| Employee 9 authorization remnants | DATA_DEBT |
| Legacy FK-OFF insert paths | BYPASS_RISK (historical) |
| Soft-end without auth cleanup | ACTIVE_LEGACY |
| Manual DB maintenance / clone rehearsal script | TEST_ONLY / OWNER_GO_REQUIRED |
| Remediation SQL package (in rehearsal script) | NOT_EXECUTED_ON_QA |
| Canonical FK helper | ACTIVE_CANONICAL |

```text
Dead pieces removed from source code: NONE
```

---

## 11. Controlled QA execution (completed)

Owner selected and authorized:

```text
STRATEGY = HYBRID_C_PLUS_B
FAMILY_A = NULLIFY_EXACT_ORPHAN_FKS
FAMILY_B = DELETE_EXACT_EMPLOYEE_9_AUTHORIZATIONS
```

Executed on live QA under maintenance window (2026-08-05):

| Item | Value |
| ---- | ----- |
| Backup | `backend/_qa_backups/controlled_fk_hybrid_c_plus_b/20260805_092545/dev.db.pre_hybrid_c_plus_b.bak` |
| Backup SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| QA SHA after | `af182ed4c9aa8f67b6227843e771f301cb7b3eccca88ad5cf6d233d20d6fb60b` |
| FK check | 11 → 0 |
| Transitions | 7 → 7 |
| Alembic | remains `s63` |
| RS tables | 0 |
| Rollback | not required |

## 12. R5 follow-on (completed)

After this remediation PASS, Owner authorized and completed:

```text
RESOURCE_STATE_PROGRAM_R5 = PASS
QA_ALEMBIC_REVISION = s64_resource_state_persistence
RESOURCE_STATE_TABLES = 8
RESOURCE_STATE_ROWS = 0
```

Worklog: `docs/worklog/realignment/2026-08-05_resource_state_program_r5_controlled_qa_schema_only_rollout.md`  
R6 / Phase B wiring / Phase C remain **NOT_AUTHORIZED**.
