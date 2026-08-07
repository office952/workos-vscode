# Worklog — QA SQLite byte-drift closure before s67 rollout

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_QA_SQLITE_BYTE_DRIFT_CLOSURE_BEFORE_S67_ROLLOUT`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `5a3697b1`  
**Tip HEAD:** `df46f30d`  
**Verdict:** **PARTIAL_BLOCKED** → Owner accepted current SHA as new baseline  
**Scope:** read-only audit · no alembic · no VACUUM/checkpoint · no restore · no product code

---

## Owner acceptance (baseline closure)

```text
ACCEPT_CURRENT_QA_SHA_AS_NEW_BASELINE = YES
CURRENT QA SHA ACCEPTED AS NEW BASELINE =
7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
KNOWN_BASELINE_DRIFT =
  intake_requests.id=50
  delivery_type = delivery_standard
  updated_at = 2026-08-07 22:10:46.650895
  source = live PUT /api/v1/entities/intake_requests/50
SCHEMA_DRIFT = NONE
PROTECTED_MACHINE_RUN_BASELINE_DIFF = NONE
DO_NOT_RESTORE_OLD_BACKUP = YES
```

This acceptance closed the byte-drift hold. Controlled s67 rollout is a separate GO
(`AUTHORIZE_ACCEPT_CURRENT_QA_BASELINE_AND_CONTROLLED_S67_ROLLOUT`).

---

## Verdict block (audit)

```text
QA_SQLITE_BYTE_DRIFT_CLOSURE_BEFORE_S67_ROLLOUT = PARTIAL_BLOCKED
PREVIOUS_QA_SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
CURRENT_QA_SHA  = 7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
DRIFT_CLASSIFICATION = LOGICAL_QA_STATE_DRIFT
DRIFT_CAUSE = live_backend PUT /api/v1/entities/intake_requests/50
  updated delivery_type='delivery_standard' and updated_at
  at 2026-08-07 22:10:46.650895 (matches file mtime)
LOGICAL_DIFF = intake_requests.id=50 (delivery_type + updated_at)
SCHEMA_DIFF = NONE
PROTECTED_MACHINE_RUN_BASELINE_DIFF = NONE
UNEXPECTED_WRITER = live uvicorn (app_20260807_142745.log) — NOT schema-foundation tests
ROOT_CAUSE = PROVEN
S67_ARTIFACTS_IN_QA = 0
QA_ALEMBIC_AT_AUDIT = s66_machine_run_reservation_grain
```

---

## Why not BENIGN_SQLITE_BYTE_DRIFT

Copy experiments (temp file only) showed:

```text
mode=ro SELECT           → SHA unchanged
write-capable SELECT     → SHA unchanged
SQLAlchemy SELECT        → SHA unchanged
empty BEGIN/COMMIT       → SHA unchanged
```

Byte change is explained by a **committed row UPDATE**, not WAL/header-only noise.

---

## File identity (current)

```text
path = C:\w\psiso\backend\dev.db
size = 36515840
mtime_utc = 2026-08-07T19:10:46.655101+00:00
SHA256 = 7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
journal_mode = delete
WAL/SHM/journal siblings = absent
page_count = 8915
page_size = 4096
freelist_count = 3
schema_version = 296
user_version = 0
data_version = 1
file_change_counter = 3320
```

Prior SHA `b7950463…` was the post-s66 rollout tip; no on-disk copy of that exact file remains (pre_s66 bak is `b54d223f…`).

---

## Schema / Alembic

```text
QA Alembic = s66_machine_run_reservation_grain
schema_fp  = 51e442d471529de20b69a2974be14a16525f77ce2e8838a9e6177dc2c0237644
             (= s66 rollout after-fingerprint)
machine_runs.started_at = ABSENT
machine_runs.completed_at = ABSENT
RUNNING/COMPLETED in machine_runs CHECK = ABSENT
S67_ARTIFACTS_IN_QA = 0
foreign_key_check = []
```

---

## Protected baseline (unchanged)

| Item | Observed |
| ---- | -------- |
| order 880750 / plan 23 | present |
| plan 21/22/23 tasks_json SHA | exact match to documented |
| plan 23 ops | 13 · assigned=1 · unassigned=12 · LED → employee 7 |
| assign_tr count / fp | 7 / `79aca87d…` exact |
| config_fp | `8cc6cc88…` exact · SCHEDULING+MACHINE_RESERVATION ACTIVE |
| machine_runs / participants / transitions | 0 |
| reservations / reservation transitions | 0 |
| capacity sources/allocs | 0 · CAPACITY_ALLOCATION domain absent (NOT_CONFIGURED) |
| F7I rates 15 / 1.5 / 35 / 20 EUR | code constants intact (not DB-owned) |

---

## Logical drift (explained)

```text
table = intake_requests
id = 50
code = IR-MSCTAFGU
API = PUT /api/v1/entities/intake_requests/50
SQL = UPDATE intake_requests SET delivery_type=?, updated_at=? WHERE id=50
values = ('delivery_standard', '2026-08-07 22:10:46.650895')
log = backend/logs/app_20260807_142745.log @ 22:10:46
```

No other table had a `2026-08-07 22:10:*` timestamp mutation.

---

## Hypothesis classification

| ID | Hypothesis | Verdict | Evidence |
| -- | ---------- | ------- | -------- |
| A | WAL/checkpoint/page-layout only | **rejected** | journal_mode=delete; no WAL; committed UPDATE present |
| B | Header/change-counter only | **rejected** | row content changed |
| C | backend open/close side effect | **rejected as sole cause** | copy experiments; UPDATE logged |
| D | tests touched real QA | **rejected** | pytest uses `tmp_path` / `test_placeholder.db` |
| E | actual row-level mutation | **supported** | UPDATE intake_requests/50 |
| F | schema-level mutation | **rejected** | schema_fp exact s66 |
| G | unknown | **rejected** | root cause proven |

---

## Test/script isolation

Schema-foundation migration/runtime tests set `DATABASE_URL` to isolated temp DBs.  
`conftest.py` defaults to `test_placeholder.db`.  
No alembic upgrade/stamp on QA in that GO.  
QA write came from **live stack** already serving `:8000`.

---

## Implications

```text
MACHINE_RUN / reservation / assignment / capacity protected path = intact
QA whole-file SHA baseline = superseded by intake_requests write
BENIGN_SQLITE_BYTE_DRIFT = NOT applicable
S67_QA_ROLLOUT = BLOCKED until Owner accepts new QA SHA as baseline
  or explicitly authorizes rollout despite intake drift
schema foundation code/migration proofs remain valid
ACCEPTED_FINAL for schema foundation = deferred
```

```text
PUSH = NO
PRODUCT_CODE_CHANGED = NO
QA_MUTATIONS_BY_THIS_GO = 0
```
