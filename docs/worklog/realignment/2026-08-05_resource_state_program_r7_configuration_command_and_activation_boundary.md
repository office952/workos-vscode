# Resource State Program R7 — Configuration Command & Activation Boundary

**Task:** `RESOURCE_STATE_PROGRAM_R7_CONFIGURATION_COMMAND_AND_ACTIVATION_BOUNDARY`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R7_CONFIGURATION_COMMAND_AND_ACTIVATION_BOUNDARY`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `365d7d1e`  
**Code commit:** `03c2817e`

---

## Verdict

```text
RESOURCE_STATE_PROGRAM_R7 = PASS
CONFIGURATION_COMMAND = IMPLEMENTED
CONFIGURATION_CAS = VERIFIED
CONFIGURATION_IDEMPOTENCY = VERIFIED
CONFIGURATION_TRANSITIONS = VERIFIED_APPEND_ONLY
ACTIVATION_READINESS_GUARD = VERIFIED
QA_CONFIGURATIONS = 0
QA_CONFIGURATION_TRANSITIONS = 0
QA_RESOURCE_RECORDS = 0
QA_OPERATIONAL_STATE = UNCHANGED
DOMAIN_ACTIVATION_IN_QA = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
R8 = NOT_AUTHORIZED
```

---

## Owner GO readback

Authorized: configuration service, write boundary for config rows, activate/disable commands, CAS, idempotency, transition history, admin/manager API, isolated DB tests, docs.  
Forbidden: QA configuration activation, QA Resource State writes, schedule/reservation/capacity writes, Phase B wiring, Phase C, new migration, frontend/Mobile, push/PR/merge/deploy.

---

## Configuration contract

```text
POST /api/v1/execution/resource-state/configurations/{domain}
permission: execution.resource_domain.configure  (admin, manager)
```

Body:

| Field | Rule |
| ----- | ---- |
| `target_status` | `ACTIVE` \| `DISABLED` only |
| `expected_version` | `0` on create; else CAS match |
| `idempotency_key` | 8–36 chars; unique |
| `reason_code` | required |
| `reason_note` | optional |
| `correlation_id` | optional |
| `application_scope_key` | default `application` |

Operations derived:

| Situation | Operation |
| --------- | --------- |
| First row → `DISABLED` | `CONFIGURE_DOMAIN` |
| Target `ACTIVE` | `ACTIVATE_DOMAIN` |
| Target `DISABLED` (existing) | `DISABLE_DOMAIN` |

Actor = authenticated user id; correlation from body.

---

## CAS / idempotency / transaction

1. **Create:** no row → `expected_version` must be `0` → insert config `version=1` + transition.
2. **Update:** `expected_version` must equal current → `version = version + 1` + transition.
3. **Stale CAS:** `409` `cas_stale` (or `cas_stale_or_missing`).
4. **Idempotency:** same key + same payload → return prior result, `already_applied=true`, no second transition; same key + different payload → `409` `idempotency_payload_conflict`.
5. **Atomicity:** current-state flush + transition insert in the same SQLite transaction; router `commit` after both succeed.

Transition history is append-only at application level (repository has no update/delete transition methods).

---

## Activation readiness (explicit R7 decision)

```text
ACTIVATION = BLOCKED_UNTIL_DOMAIN_WRITER_EXISTS
```

Checks before any transition to `ACTIVE`:

| Check | Fail code |
| ----- | --------- |
| Domain supported | `domain_not_supported` |
| Resource State schema tables present | `schema_missing` |
| Read evaluator importable | `read_evaluator_missing` |
| No inconsistent source status rows | `inconsistent_source_records` |
| Domain writer ready **or** test allow env | `ACTIVATION_BLOCKED_UNTIL_DOMAIN_WRITER_EXISTS` |

R7 writers for schedule/reservation/capacity are **not** implemented (`DOMAIN_WRITER_READY[*]=False`). Activating without writers would make R6 return `CLEAR` on empty records — a false operational clear if Phase B were wired.

Isolated tests may set:

```text
WORKOS_RESOURCE_STATE_ALLOW_DOMAIN_ACTIVATION=1
```

QA activation remains **NOT_AUTHORIZED** regardless — configure endpoint was **not** called against live QA.

`DISABLED` read semantics (R1/R2/R6): only `ACTIVE` configs are loaded → `DISABLED` evaluates as `NOT_CONFIGURED`.

---

## Permission matrix

| Role | Configure |
| ---- | --------- |
| admin | allowed |
| manager | allowed |
| operator | denied (403) |
| viewer | denied (403) |

---

## Files

| Layer | Path |
| ----- | ---- |
| Schema | `backend/schemas/resource_state_configuration.py` |
| Write repo | `backend/services/resource_domain_configuration_repository.py` |
| Command | `backend/services/resource_domain_configuration_command_service.py` |
| Permission | `execution.resource_domain.configure` in `backend/dependencies/permissions.py` |
| API | `POST …/resource-state/configurations/{domain}` in `execution_plan_v2.py` |
| Tests | `backend/tests/test_resource_state_r7_configuration_command.py` (14 passed) |

---

## QA zero-mutation proof

Path: `C:\w\psiso\backend\dev.db` (read-only; no configure calls).

| Metric | Value |
| ------ | ----- |
| Alembic | `s64_resource_state_persistence` |
| configurations | 0 |
| configuration transitions | 0 |
| schedules + reservations + capacity | 0 |
| assignment transitions | 7 |
| foreign_key_check | 0 |
| plan 23 `tasks_json` SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| QA DB SHA | `57fc48730108c8a9022d8151ddaa1f809a51cdfeff2174f2fb6f6ba293d463e9` (unchanged vs post-R5) |

```text
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_CONFIGURATIONS_CREATED = 0
QA_RESOURCE_RECORDS_CREATED = 0
```

---

## Phase B / Phase C / modules / governance

```text
PHASE_B_WIRING = NOT_AUTHORIZED   (evaluate_resource_guards still env/fail-closed; not R6/R7)
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
```

**/modules:** configuration command exists; no active domain in QA; no operational writer active.  
**/governance:** admin/manager ownership; activation Owner-gated + writer readiness; configuration history append-only.

---

## Roadmap awareness

```text
Nota roadmap awareness: 9/10
Poziția curentă: Resource State configuration command
Cât sunt în direcția stabilită: 70/100%
Dead Pieces Check: none introduced; ORR Pregătit remains ACTIVE_LEGACY; Phase B fail-closed remains ACTIVE_CANONICAL
Forbidden scope respected: YES
No QA activation
No resource writes
No Phase B wiring
No Phase C
No task mutation
No frontend/Mobile
```

---

## Next step (not started)

```text
FUTURE CANDIDATE:
RESOURCE_STATE_PROGRAM_R8_DOMAIN_WRITE_SERVICE_READINESS
```
