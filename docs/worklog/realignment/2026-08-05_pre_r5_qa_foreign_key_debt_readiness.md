# Pre-R5 QA Foreign-Key Debt Readiness Worklog

**Task:** `PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS = READ_ONLY_CLASSIFICATION_AND_REMEDIATION_PLAN`  
**Owner GO:** `AUTHORIZE_PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS_AUDIT`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `d13f78c1`  
**Final HEAD:** `1c34f5aa`  
**Canonical:** `docs/architecture/PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS.md`

---

## Verdict

```text
PRE_R5_QA_FK_DEBT_READINESS = COMPLETE
QA_FOREIGN_KEY_INTEGRITY = DEBT_PRESENT
QA_FOREIGN_KEY_VIOLATIONS = 11
R5_READINESS = REMEDIATION_REQUIRED_FIRST
RECOMMENDED_PROGRAM = QA_FOREIGN_KEY_DEBT_REMEDIATION
QA_MUTATIONS = 0
R5 = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Owner GO readback

```text
OWNER GO:
AUTHORIZE_PRE_R5_QA_FOREIGN_KEY_DEBT_READINESS_AUDIT
```

Authorized: read-only QA/code audit, remediation options, docs.  
Forbidden: QA Alembic, inserts/updates/deletes, FK repair/disable, R5, Phase B/C, push/PR.

---

## Repo / QA identity

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Tip start | `d13f78c1` |
| Code Alembic head | `s64_resource_state_persistence` |
| QA Alembic | `s63` |
| QA path | `C:\w\psiso\backend\dev.db` |
| QA_DB_FILE_SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| schema_fingerprint | `77011cf97c5ce19a0c5695d056ec9bf968f4b0294a3726065f9aaee3fbf795c2` |
| Foreign tracked | none |

---

## Findings summary

Two families:

1. **Gate snapshot orphans (7):** orders `21099,22099,23099,23150,29991` + plans `4,5` → missing `quote_snapshots_v2` (TEST_OR_DEMO / gate codes).
2. **Employee 9 auth orphans (4):** resource/operation/workcenter/skill auth → missing `employees.id=9`.

Protected 880750/23, 880811/22, 973019/21, employee 7, transitions, F7I: **clean, no intersection**.

s64 DDL: unrelated / can execute. Post-migration writes on orphan rows: **unsafe** with FK ON.

Recommended remediation: Option D (delete disposable orphans) after Owner confirmation + clone rehearsal. Reject synthetic parents.

R5: **remediation first** — not quarantine-only.

---

## Connection FK state

```text
NEW_CANONICAL_CONNECTION_FK_STATE = 1
CURRENT_RUNNING_BACKEND_FK_STATE = UNKNOWN
```

---

## Mutation counters

```text
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_ALEMBIC_UPGRADE_CALLS = 0
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
```

Before/after SHA and schema fingerprint unchanged.

---

## Method

```text
read-only inventory script + code-path subagent
single documentation writer
no Agent DB writes
no R5 / no repair
```

---

## Scores

```text
Direction alignment score: 98/100
Operational completion score: 76/100
```

Debt audited only — operational score not increased.

---

## Next step

```text
OWNER GO:
AUTHORIZE_QA_FOREIGN_KEY_DEBT_REMEDIATION_PLANNING
```

Do not start remediation. Do not migrate QA.
