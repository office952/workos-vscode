# QA Foreign-Key Debt Remediation — Planning & Clone Rehearsal Worklog

**Task:** `QA_FOREIGN_KEY_DEBT_REMEDIATION = PLANNING_AND_ISOLATED_CLONE_REHEARSAL`  
**Owner GO:** `AUTHORIZE_QA_FOREIGN_KEY_DEBT_REMEDIATION_PLANNING`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `a03dd4e7`  
**Script commit:** `b19dd451`  
**Final HEAD:** `a741f357`  
**Canonical:** `docs/architecture/QA_FOREIGN_KEY_DEBT_REMEDIATION_PLAN.md`

---

## Verdict

```text
QA_FK_DEBT_REMEDIATION_PLANNING = PASS
ISOLATED_CLONE_REHEARSAL = VERIFIED
QA_FK_REMEDIATION_PLAN = READY_FOR_OWNER_EXECUTION_GO

VIOLATIONS_BEFORE = 11
VIOLATIONS_AFTER = 0

FAMILY_A_DELETE_CANDIDATES = 7_CONFIRMED
FAMILY_B_DELETE_CANDIDATES = 4_CONFIRMED

PROTECTED_BASELINE_DIFF = NONE_FOR_PROTECTED_SCOPE
ROLLBACK_REHEARSAL = VERIFIED
REMEDIATION_RESULT = DETERMINISTIC

CLONE_RUNTIME_FK_ON = VERIFIED
CLONE_RUNTIME_READ_SMOKE = VERIFIED
CLONE_S63_TO_S64 = VERIFIED
RESOURCE_STATE_TABLES = 8
RESOURCE_STATE_ROWS = 0
RESOURCE_CONFIGURATIONS = 0
SYNTHETIC_CLEAR = 0

QA_MUTATIONS = 0
REAL_QA_REMEDIATION = NOT_AUTHORIZED
R5 = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Owner GO readback

```text
OWNER GO:
AUTHORIZE_QA_FOREIGN_KEY_DEBT_REMEDIATION_PLANNING
```

Authorized: isolated clone copy/writes/deletes, clone migration, clone runtime smoke, docs.  
Forbidden: QA mutations, QA Alembic, R5, Phase B/C, synthetic parents, FK disable, push/PR.

---

## Repo / QA identity

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `a03dd4e7` |
| Ancestry | `964d10d0` · `02d3e51b` · `d13f78c1` · `1c34f5aa` · `a03dd4e7` |
| Code Alembic head | `s64_resource_state_persistence` |
| QA Alembic | `s63_execution_task_assignment_transitions` |
| QA path | `C:\w\psiso\backend\dev.db` |
| QA SHA (sqlite backup API) | `c2c5c88a9c00d17a50f4ab94074a8235c3ec9f6582cfe56fc45d0a3eb7db606c` |
| schema_fingerprint | `77011cf97c5ce19a0c5695d056ec9bf968f4b0294a3726065f9aaee3fbf795c2` |
| Foreign tracked | none |
| FE | :3000 PID 27752 |
| BE Owner | :8000 PID 25992 (untouched) |
| Clone smoke BE | :8017 (terminated after proof) |

Note: Pre-R5 documented file SHA `0023d2fb…` differs from current backup SHA while schema fingerprint and the exact 11-row FK inventory remain identical. This rehearsal uses backup SHA as content identity; QA was not mutated by this task (`qa_sha_after` match).

---

## Clone identity

| Item | Value |
| ---- | ----- |
| Work dir | `backend/_qa_backups/fk_debt_remediation_rehearsal/20260805_092010/` (not committed) |
| Clone initial SHA | equals source backup SHA |
| Pre FK | 11 |
| Post Expanded D FK | 0 |
| Remediation result fp | `75a257f140844c5528b309aa59196c23b955edf4eec7dadc30638bf8bd61da07` |

---

## Key findings

1. **Pure 7-row delete blocked** by `ON DELETE RESTRICT` on assignment transitions for plans 4/5.
2. **Expanded Option D** with exact dependent PKs reaches FK=0; removes 5 gate transitions → global count 7→2; protected plans 21/23 transitions unchanged.
3. **Hybrid Option C+B** also reaches FK=0 and preserves all 7 transitions (Owner alternative).
4. Protected 880750/23 (13 ops, LED→7, tasks SHA `00ee947c…`), 880811/22, 973019/21, emp7 auth, F7I code constants 15/1.5/35/20 EUR — unchanged.
5. Clone `s63→s64` succeeds; 8 RS tables empty.
6. Rollback by restoring pre-remediation clone file — VERIFIED.
7. Determinism across two fresh clones — VERIFIED.

---

## Mutation counters

```text
ISOLATED_CLONE_MUTATIONS = ALLOWED (executed)
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_ALEMBIC_UPGRADE_CALLS = 0
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_ASSIGNMENT_REQUESTS = 0
```

---

## Method

```text
read-only QA inventory
single clone writer (one script)
exact-PK deletes (no wildcards)
backup-restore rollback (not orphan re-insert)
planning separated from QA execution
Owner ports 3000/8000 never killed/restarted for this task
```

---

## Scores

```text
Direction alignment score: 98/100
Operational completion score: 77/100
```

No increase for real QA remediation (not executed).

---

## Next step

```text
OWNER GO:
AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION
```

Owner must choose Expanded D vs Hybrid C+B. Do not start R5.
