# Controlled QA Foreign-Key Debt Remediation Worklog

**Task:** `CONTROLLED_QA_FK_DEBT_REMEDIATION`  
**Owner GO:** `AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION`  
**Approved strategy:** `HYBRID_C_PLUS_B`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `546d8951`  
**Final HEAD:** `132edbf3`  
**Canonical plan:** `docs/architecture/QA_FOREIGN_KEY_DEBT_REMEDIATION_PLAN.md`

---

## Verdict

```text
CONTROLLED_QA_FK_DEBT_REMEDIATION = PASS
STRATEGY = HYBRID_C_PLUS_B

FOREIGN_KEY_VIOLATIONS_BEFORE = 11
FOREIGN_KEY_VIOLATIONS_AFTER = 0
FAMILY_A_NULLIFIED = 7
FAMILY_B_DELETED = 4
GLOBAL_TRANSITIONS_BEFORE = 7
GLOBAL_TRANSITIONS_AFTER = 7
PROTECTED_BASELINE_DIFF = NONE
SQLITE_FOREIGN_KEYS = VERIFIED_ON_AFTER_RESTART

QA_ALEMBIC_REVISION = s63
QA_RESOURCE_STATE_TABLES = 0
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0

R5 = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Owner GO readback

```text
OWNER GO:
AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION
APPROVED_STRATEGY:
HYBRID_C_PLUS_B
```

Family A = nullify exact orphan quote_snapshot FKs (preserve transitions).  
Family B = delete exact 4 employee_id=9 authorization rows.  
Forbidden: s64 QA rollout, synthetic parents, FK disable, Expanded D deletes, push/PR.

---

## Strategy

```text
QA_FK_REMEDIATION_STRATEGY = HYBRID_C_PLUS_B
FAMILY_A = NULLIFY_EXACT_ORPHAN_FKS
FAMILY_B = DELETE_EXACT_EMPLOYEE_9_AUTHORIZATIONS
```

---

## Repo / QA identity

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `546d8951` |
| QA path | `C:\w\psiso\backend\dev.db` |
| QA SHA before | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| QA SHA after | `af182ed4c9aa8f67b6227843e771f301cb7b3eccca88ad5cf6d233d20d6fb60b` |
| schema_fingerprint | `77011cf97c5ce19a0c5695d056ec9bf968f4b0294a3726065f9aaee3fbf795c2` (unchanged) |
| Alembic | `s63` before and after |
| Foreign tracked | none |

---

## Backup

| Item | Value |
| ---- | ----- |
| Path | `backend/_qa_backups/controlled_fk_hybrid_c_plus_b/20260805_092545/dev.db.pre_hybrid_c_plus_b.bak` |
| SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| Opens RO | YES |
| Schema fp match | YES |

Maintenance: `.\scripts\stop-dev.ps1` before mutate; `.\scripts\dev-detached.ps1` after.

---

## Precondition inventory

Exact match to clone rehearsal:

- 11 FK violations · fingerprint `07d7fde7…`
- Family A: plans 4/5 + orders 21099/22099/23099/23150/29991
- Family B: auth PKs 22/41/26/36 for employee 9
- employee 9 absent
- transitions = 7
- protected fixtures present and clean

---

## Exact affected PKs

### Family A nullify (7)

| Table | PK | Column | Was |
| ----- | -- | ------ | --: |
| `execution_plan` | 4 | `source_quote_snapshot_v2_id` | 23099 |
| `execution_plan` | 5 | `source_quote_snapshot_v2_id` | 23150 |
| `orders` | 21099 | `quote_snapshot_v2_id` | 21099 |
| `orders` | 22099 | `quote_snapshot_v2_id` | 22099 |
| `orders` | 23099 | `quote_snapshot_v2_id` | 23099 |
| `orders` | 23150 | `quote_snapshot_v2_id` | 23150 |
| `orders` | 29991 | `quote_snapshot_v2_id` | 29991 |

### Family B delete (4)

| Table | PK | employee_id |
| ----- | -- | ----------: |
| `employee_resource_authorizations` | 22 | 9 |
| `operation_employee_authorizations` | 41 | 9 |
| `employee_workcenter_authorizations` | 26 | 9 |
| `employee_skill_authorizations` | 36 | 9 |

Transaction: `BEGIN IMMEDIATE` · exact rowcount asserts · FK check 0 · protected baseline match · `COMMIT`.

---

## Verification

| Check | Result |
| ----- | ------ |
| FK before / after | 11 → 0 |
| Transitions | 7 → 7 · fp `b66b75ac…` unchanged |
| Protected baselines | NONE diff |
| Plan 23 tasks SHA | `00ee947c…` unchanged |
| LED → employee 7 | unchanged |
| F7I 15 / 1.5 / 35 / 20 EUR | unchanged |
| Canonical `PRAGMA foreign_keys` after restart | 1 |
| Health :8000 / UI :3000 | 200 |
| Rollback | not triggered |

---

## Runtime after restart

| Item | Value |
| ---- | ----- |
| Backend | :8000 (new detached PID) |
| Frontend | :3000 |
| Served commit (at restart) | `546d8951` + local uncommitted docs until commit |

---

## Files

- `backend/scripts/qa_fk_debt_remediation_hybrid_c_plus_b_apply.py` (new)
- `docs/architecture/QA_FOREIGN_KEY_DEBT_REMEDIATION_PLAN.md` (status)
- `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` (pointer)
- this worklog

Not committed: `_qa_backups/**`, `docs/qa/**`.

---

## Roadmap awareness checkpoint

```text
Nota roadmap awareness: 9/10
Poziția curentă: QA data-integrity remediation before R5 — COMPLETE for Hybrid C+B
Cât sunt în direcția stabilită: 98/100%
Dead Pieces Check:
  W5/W6 gate rows retained with NULL snapshot FKs = DATA_DEBT_RETIRED_AS_FK_RISK / TEST_ONLY_RETAINED
  employee 9 auth remnants = REMOVED
  Expanded D path = SUPERSEDED_BY_OWNER_HYBRID_CHOICE
Forbidden scope respected: YES
No s64 QA rollout
No Resource State activation
No Phase B wiring
No Phase C
No operational task mutation
No UI/Mobile changes
No push / PR / merge / deploy
Next recommended step:
reassess R5 readiness only after Owner PASS review
```

---

## Scores

```text
Direction alignment score: 98/100
Operational completion score: 78/100
```

---

## Next step

Do **not** start R5. Await Owner review / separate R5 GO.
