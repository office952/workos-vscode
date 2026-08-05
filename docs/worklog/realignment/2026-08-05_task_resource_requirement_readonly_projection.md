# Worklog — Task Resource Requirement Read-Only Projection

**Date:** 2026-08-05  
**Owner GO:** `AUTHORIZE_TASK_RESOURCE_REQUIREMENT_READONLY_PROJECTION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `fbdee6b1`  
**Tip HEAD:** `5ad352dc`  
**Verdict:** **PASS**

```text
TASK_RESOURCE_REQUIREMENT_READONLY_PROJECTION = PASS
READONLY_SERVICE = IMPLEMENTED
READONLY_API = IMPLEMENTED
PLAN_SUMMARY = IMPLEMENTED
TASK_FILTER = IMPLEMENTED
RESOURCE_REQUIREMENTS_STATUS = VERIFIED
SOFT_RESOURCE_MODE_HINT = VERIFIED
HYBRID_MODE = UNKNOWN
NULL_BEHAVIOR = PRESERVED
SOURCE_PROVENANCE = VERIFIED
PLANS_21_22_23 = VERIFIED
TASKS_JSON_MUTATIONS = 0
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Objective

Expose a read-only projection of what is known / derived / unknown about operational task resource demand — without mutating `tasks_json`, without writers, without frontend.

---

## 2. Deliverables

| Artifact | Path |
| -------- | ---- |
| Schema | `backend/schemas/task_resource_requirement_projection.py` |
| Service | `backend/services/task_resource_requirement_projection_service.py` |
| API | `GET /api/v1/execution/plans/{plan_id}/resource-requirements?task_key=` |
| Tests | `backend/tests/test_task_resource_requirement_projection.py` (16 passed) |
| Contract update | `docs/architecture/TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT.md` |
| Route update | `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` |

Permission: `execution.plan_generate` (admin/manager).

---

## 3. Status vocabulary (projection)

```text
KNOWN_MINIMAL | PARTIAL | UNKNOWN | NOT_APPLICABLE
```

Distinct from R6 Resource State (`CLEAR` / `ACTIVE` / `NOT_CONFIGURED`).

Soft `resource_mode_hint`:

```text
MACHINE_BOUND | MANUAL_WORKSPACE | PERSON_DRIVEN | FIELD | UNKNOWN
```

HYBRID workcenters (`WC_METAL_FAB`, `WC_VINYL_APPLICATION`) → hint **UNKNOWN**.

---

## 4. Plans 21 / 22 / 23 (QA runtime)

| Plan | total | known_minimal | partial | unknown | duration_known | duration_unknown | safe_mode_hint | hybrid_unknown |
| ---- | ----- | ------------- | ------- | ------- | -------------- | ---------------- | -------------- | -------------- |
| 21 | 18 | 1 | 17 | 0 | 1 | 17 | 17 | 1 |
| 22 | 5 | 0 | 5 | 0 | 0 | 5 | 4 | 1 |
| 23 | 13 | 0 | 13 | 0 | 0 | 13 | 11 | 2 |

### Plan 23 LED (`…:led_install_letters`)

```text
workcenter_code = WC_LED_ASSEMBLY
resource_mode_hint = MANUAL_WORKSPACE
estimated_time_minutes = null
resource_requirements_status = PARTIAL
```

Assignment of employee 7 was **not** used to invent `required_people_min`.

`tasks_json` SHA plan 23 (unchanged):

```text
00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
```

---

## 5. QA zero-mutation (before = after)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
capacity source rows = 0
capacity allocation rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
```

R6 read on LED after projection: scheduling/reservation CLEAR; capacity NOT_CONFIGURED; aggregate BLOCKED_NOT_CONFIGURED.

---

## 6. Boundaries honored

- No `tasks_json` mutation
- No migration / ORM changes
- No Capacity / Reservation / Schedule writers
- No Phase B wiring
- No frontend
- No push

---

## 7. Recommended next (not authorized)

Surface gaps remain intentional (people / workspace / authoritative mode / batch). Any persistence or MACHINE_RUN / workspace booking requires a separate Owner GO.

```text
NEXT_TASK = NOT_AUTHORIZED
```
