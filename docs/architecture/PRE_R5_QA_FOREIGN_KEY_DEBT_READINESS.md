# Pre-R5 QA Foreign-Key Debt Readiness

**Task:** `PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS = READ_ONLY_CLASSIFICATION_AND_REMEDIATION_PLAN`  
**Owner GO:** `AUTHORIZE_PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS_AUDIT`  
**Date:** 2026-08-05  
**Status:** **COMPLETE** · Remediation **NOT EXECUTED** · R5 **NOT AUTHORIZED**  
**Worklog:** `docs/worklog/realignment/2026-08-05_pre_r5_qa_foreign_key_debt_readiness.md`

```text
PRE_R5_QA_FK_DEBT_READINESS = COMPLETE
QA_FOREIGN_KEY_INTEGRITY = DEBT_PRESENT
QA_FOREIGN_KEY_VIOLATIONS = 11
R5_READINESS = REMEDIATION_REQUIRED_FIRST
R5_CAN_PROCEED_WITH_DEBT_QUARANTINED = NO
R5_REQUIRES_FK_DEBT_REMEDIATION_FIRST = YES
RECOMMENDED_PROGRAM = QA_FOREIGN_KEY_DEBT_REMEDIATION
QA_MUTATIONS = 0
R5 = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

This audit is **read-only**. It does not repair rows, disable FK, migrate QA, or start R5.

---

## 1. Context

Resource State R3 enabled canonical `PRAGMA foreign_keys=ON` on product/Alembic/test engines.  
R4 reported 11 preexisting QA violations. Code Alembic head is `s64`; QA remains `s63` with zero Resource State tables.

Debt is **not** caused by Resource State schema. It becomes operationally relevant because FK enforcement is now ON for new connections.

---

## 2. Canonical violation inventory

Source: `PRAGMA foreign_key_check` on `backend/dev.db` (URI `mode=ro`, non-mutating).

| # | Child table | Child PK / identity | FK column | FK value | Parent table | Parent exists | Classification |
| - | ----------- | ------------------- | --------- | -------- | ------------ | ------------- | -------------- |
| 1 | `execution_plan` | id=4 · order 23099 · `ORD-W5INT02-GATE` | `source_quote_snapshot_v2_id` | 23099 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 2 | `execution_plan` | id=5 · order 23150 · `ORD-W6T03-BLOCK-GATE` | `source_quote_snapshot_v2_id` | 23150 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 3 | `employee_resource_authorizations` | id=22 | `employee_id` | 9 | `employees` | no | LEGACY_ORPHAN / DELETED_PARENT_REMAINDER |
| 4 | `orders` | id=21099 · status locked | `quote_snapshot_v2_id` | 21099 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 5 | `orders` | id=22099 · locked | `quote_snapshot_v2_id` | 22099 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 6 | `orders` | id=23099 · locked | `quote_snapshot_v2_id` | 23099 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 7 | `orders` | id=23150 · locked | `quote_snapshot_v2_id` | 23150 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 8 | `orders` | id=29991 · locked | `quote_snapshot_v2_id` | 29991 | `quote_snapshots_v2` | no | TEST_OR_DEMO |
| 9 | `operation_employee_authorizations` | id=41 · op `print` | `employee_id` | 9 | `employees` | no | LEGACY_ORPHAN |
| 10 | `employee_workcenter_authorizations` | id=26 · `WC_PRINT` | `employee_id` | 9 | `employees` | no | LEGACY_ORPHAN |
| 11 | `employee_skill_authorizations` | id=36 · `SK_PRINT_OPERATOR` | `employee_id` | 9 | `employees` | no | LEGACY_ORPHAN |

### Families

| Family | Count | Description |
| ------ | ----- | ----------- |
| A — Gate snapshot orphans | 7 | 5 locked gate orders + 2 plans pointing at missing `quote_snapshots_v2` (IDs reused as order/snapshot ids) |
| B — Missing employee 9 auth | 4 | Auth rows for `employee_id=9` with no employees row |

---

## 3. Protected fixture intersection

| Asset | FK health |
| ----- | --------- |
| order 880750 / plan 23 / snapshot 23 | parent exists · **not in violation list** |
| order 880811 / plan 22 / snapshot 21 | parent exists · clean |
| order 973019 / plan 21 / snapshot 20 | parent exists · clean |
| employee 7 | exists; auth rows present and valid |
| assignment transitions (7) | not involved |
| F7I identities | not involved |

```text
PROTECTED_FIXTURE_INTERSECTION = NONE
REMEDIATION_RISK_FOR_PROTECTED = LOW
```

Gate/demo orders (`21099`…`29991`, W5/W6 gate codes) are outside the protected pilot set.

---

## 4. Root-cause findings

| Family | Root cause | Confidence |
| ------ | ---------- | ---------- |
| A | Children inserted / retained while `foreign_keys` was OFF; snapshot parents missing or never persisted for integration-gate fixtures (`ORD-W5INT02-GATE`, `ORD-W6T03-BLOCK-GATE`, etc.) | **PROBABLE** |
| B | Auth rows for employee 9 left after employee row removed (or never committed); soft-end does not CASCADE; FK OFF allowed orphan inserts | **PROBABLE** |

```text
ROOT_CAUSE_CONFIRMED_FOR_R3_S64 = NO
RESOURCE_STATE_CAUSED_DEBT = NO
```

Insufficient evidence to claim exact delete timestamps without fabricating history → not `CONFIRMED` for every row.

---

## 5. Runtime impact (FK ON)

### Connection state

| Connection | FK state |
| ---------- | -------- |
| Raw sqlite3 / historical process | may be 0 |
| New canonical helper connection to QA | **1** (proven read-only) |
| Running Owner backend process | **UNKNOWN** until process restart onto R3+ code |

```text
CURRENT_RUNNING_BACKEND_FK_STATE = UNKNOWN
NEW_CANONICAL_CONNECTION_FK_STATE = 1
READ_ONLY_RUNTIME_COMPATIBILITY = YES
WRITE_RUNTIME_COMPATIBILITY = NOT_PROVEN_UNSAFE_FOR_ORPHAN_ROWS
```

### Reads

Unaffected: SELECT/list of orders, plans, auth. Orphans remain readable.

### Writes (risk matrix)

| Path | Op | Risk with FK ON |
| ---- | -- | --------------- |
| Order update setting/keeping bad `quote_snapshot_v2_id` | UPDATE | IntegrityError on orphan gate orders |
| New order convert with live snapshot | INSERT | Safe when parent exists |
| ExecutionPlan V2 persist on existing orphan plan | early return / mismatch | Does not heal orphan FK; new insert with missing snapshot fails |
| Employee authorization PUT for missing emp | 404 then no write | Orphans for emp 9 persist |
| Operation mapping rewrite for same op code | DELETE+INSERT by operation | May clear orphan op-auth for that code as side effect |
| Employee soft-end | UPDATE | Does not clean auth orphans |
| Hard employee DELETE | forbidden in product | Would CASCADE if ever used |

```text
new valid inserts = protected by FK
updates to orphan rows = potentially blocked
deletes of missing parents = N/A (already missing)
```

---

## 6. Migration impact (`s63 → s64`)

| Question | Answer |
| -------- | ------ |
| s64 reads/rewrites orders/plans/auth? | **No** — expand-only Resource State tables |
| s64 creates FKs to debt tables? | **No** — FKs to `execution_plan` / `machines` only |
| Requires global FK check success? | **No** for SQLite Alembic DDL |
| `MIGRATION_DDL_CAN_EXECUTE` | **YES** (isolated proofs already show this) |
| `POST_MIGRATION_APPLICATION_WRITES_ARE_SAFE` | **NO** for debt rows after FK ON |

Successful DDL does **not** erase FK debt.

---

## 7. Remediation options

### Option A — Recreate missing parents

**Rejected for default path.** No factual snapshot payload / employee 9 truth available to reconstruct without synthetic commercial/authorization history.

### Option B — Repoint child FK

**Rejected.** No evidence of alternate canonical snapshot/employee.

### Option C — Nullify optional FK

`orders.quote_snapshot_v2_id` and `execution_plan.source_quote_snapshot_v2_id` are **nullable**.  
Technically possible for Family A if Owner accepts “no V2 snapshot link” for gate orders/plans.  
**Not preferred** if rows are disposable gate fixtures (prefer D).  
Auth `employee_id` is **NOT NULL** → C invalid for Family B.

### Option D — Delete orphan child rows

**Preferred for both families** after Owner confirmation they are disposable gate/demo/orphan auth:

- Family A: delete 5 gate orders + 2 plans (and any non-protected dependents) **or** delete only FK-bearing children after dependency check on clone.
- Family B: delete 4 auth rows for employee_id=9.

Preserves protected fixtures. Avoids synthetic parents.

### Option E — Quarantine/archive

No first-class archive tables for these rows. Soft quarantine would still leave FK_check red.

### Option F — Formal legacy exception

Document debt and block affected writes. **Insufficient for R5** while product FK ON remains active after backend restart — debt remains live risk.

### Option G — Rebuild sanitized QA DB

Heavy; only if Family A/B cleanup proves tangled. Not first choice.

---

## 8. Recommended strategy

```text
RECOMMENDED =
FAMILY_SCOPED_OPTION_D_AFTER_OWNER_CONFIRMATION
+ ISOLATED_CLONE_REHEARSAL
+ THEN_R5_RECONSIDERATION
```

Do **not**:

- synthesize quote snapshots or employee 9;
- disable FK;
- auto-repair without Owner GO;
- casually delete without clone rehearsal and dependency check.

---

## 9. R5 readiness verdict

```text
R5_REQUIRES_FK_DEBT_REMEDIATION_FIRST
```

Reasons:

1. Product connections now enforce FK; restart exposes debt to write paths.
2. Orphan locked orders are still updateable surfaces.
3. Owner already correctly blocked R5 readiness on this debt.
4. Remediation is bounded (2 families, 11 rows) and does not touch protected fixtures.
5. Quarantine-only R5 would require explicit Owner risk acceptance that this audit does **not** recommend.

`R5_CAN_PROCEED_WITH_DEBT_QUARANTINED = NO` (not recommended).

---

## 10. Cleanup program design (not started)

```text
QA_FOREIGN_KEY_DEBT_REMEDIATION
```

| Phase | Content |
| ----- | ------- |
| D1 | Factual row classification (**this audit**) |
| D2 | Owner decisions per family (confirm disposable gate fixtures; confirm delete emp-9 auth) |
| D3 | Isolated clone repair rehearsal |
| D4 | Verification + rollback rehearsal on clone |
| D5 | Controlled QA repair (separate Owner GO) |
| D6 | Post-repair `foreign_key_check` + FK ON smoke |
| D7 | R5 reconsideration |

---

## 11. Isolated clone rehearsal plan (future)

```text
copy QA → temp
verify source SHA
apply Family A/B deletes (or nullify if Owner chose C) on clone only
PRAGMA foreign_key_check → expect 0
protected baseline checks (880750/23, transitions, F7I)
targeted runtime smoke with FK ON
optional s63→s64 on clone
produce repair diff
discard clone
```

Do **not** execute in this task.

---

## 12. Next Owner gate

```text
OWNER GO:
AUTHORIZE_QA_FOREIGN_KEY_DEBT_REMEDIATION_PLANNING
```

Not R5. Not automatic repair. Not FK disable.

---

## 13. Dead pieces

| Piece | Class |
| ----- | ----- |
| Gate orders/plans with missing snapshots | DATA_DEBT / TEST_OR_DEMO |
| Auth rows for missing employee 9 | DATA_DEBT |
| Historical FK-OFF inserts | BYPASS_RISK (historical) |
| Canonical FK helper | ACTIVE_CANONICAL |
| Soft-end without auth cleanup | ACTIVE_LEGACY |

```text
Dead pieces removed: NONE
```
