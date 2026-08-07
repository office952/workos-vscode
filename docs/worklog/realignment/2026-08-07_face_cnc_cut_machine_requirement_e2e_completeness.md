# Worklog — Face CNC Cut Machine Requirement E2E Completeness

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_FACE_CNC_CUT_MACHINE_REQUIREMENT_E2E_COMPLETENESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `c26341d5`  
**Verdict:** **PASS**

```text
FACE_CNC_CUT_MACHINE_REQUIREMENT_E2E_COMPLETENESS = PASS
OPERATION = face_cnc_cut
WORKCENTER = WC_CNC_ROUTING
MACHINE_CAPABILITY = CNC_ROUTER_CUTTING
CAPABILITY_SOURCE = OPERATION_CONTRACT
RESOURCE_MODE = MACHINE_BOUND
BATCH_ELIGIBLE = true
AGGREGATE_PROJECTION = VERIFIED
EXECUTION_PLAN_SNAPSHOT = VERIFIED
READONLY_PROJECTION = VERIFIED
MACHINE_ID = NOT_PERSISTED
MACHINE_RESERVATION_WRITES = 0
MACHINE_RUN = NOT_IMPLEMENTED
BATCH_GROUPING_WRITES = 0
PROTECTED_PLAN_MUTATIONS = 0
QA_MUTATIONS = 0
VECTOR_PREP_E2E = STILL_PASS
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Owner decisions applied

From `FACE_CNC_CUT_MACHINE_REQUIREMENT_OWNER_DECISIONS.md`:

```text
machine_capability_code = CNC_ROUTER_CUTTING
resource_mode = MACHINE_BOUND
batch_eligible = true
machine_exclusive = true → implied by MACHINE_BOUND (not a separate stamp)
machine_id = Reservation only
```

**Why no `machine_exclusive` field:** no near-term consumer; exclusivity is the meaning of `MACHINE_BOUND` for this pilot (Owner D3). Avoids a decorative column.

---

## 2. Path

```text
operation_machine_requirement_contract (FACE_CNC_CUT / CUT_FACE capability)
  → apply_machine_requirement_resolution (ProductAggregate)
  → EP preview PlannedTaskPreview fields
  → materialize operational_tasks snapshot
  → GET .../resource-requirements (reads snapshot; no recalculation)
```

Files:

- `backend/services/operation_machine_requirement_contract.py`
- `backend/services/product_aggregate_machine_requirement_service.py`
- Aggregate / EP schemas + preview / materialize / projection
- `backend/tests/test_face_cnc_cut_machine_requirement_e2e.py`

---

## 3. Proof

Controlled fixture (isolated pytest DB):

```text
operation_code = face_cnc_cut
workcenter = WC_CNC_ROUTING
machine_capability_code = CNC_ROUTER_CUTTING
resource_mode = MACHINE_BOUND
batch_eligible = true
status = PARTIAL (duration still unknown — deferred)
```

Legacy / HYBRID: no WC→capability invent; HYBRID soft hint remains UNKNOWN without authoritative stamp.

Side effects: reservation count 0; no MACHINE_RUN; plans 21/22/23 SHA unchanged.

---

## 4. Machine Reservation boundary

```text
machine requirement = demand (capability on task)
machine reservation = commitment (selects machine_id later)
```

Reservation writer not called. Capability available for future match — not wired in this GO.

---

## 5. QA

```text
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
plan 21/22/23 SHAs unchanged
Capacity 0/0 · assign 7 · s65
```

---

## 6. Tests

```text
pytest test_face_cnc_cut_machine_requirement_e2e.py
     + projection + vector_prep + te2e_028b
→ 44 passed
```
