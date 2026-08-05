# Worklog — Vector Prep Duration E2E Completeness

**Date:** 2026-08-05  
**Owner GO:** `AUTHORIZE_VECTOR_PREP_DURATION_E2E_COMPLETENESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `10129e8c`  
**Tip HEAD:** `84319ddc`  
**Verdict:** **PASS**

```text
VECTOR_PREP_DURATION_E2E_COMPLETENESS = PASS
SELECTED_PILOT = vector_prep
PILOT_WORKCENTER = WC_PREPRESS
FORMULA = 2_MINUTES_X_LETTER_COUNT
FORMULA_AUTHORITY = planning_duration_contract / LETTERS_VECTOR_PREP_DURATION
GEOMETRY_INPUT = factual_letter_count
AGGREGATE_DURATION_RESOLUTION = VERIFIED
EXECUTION_PLAN_SNAPSHOT = VERIFIED
READONLY_PROJECTION = VERIFIED
KNOWN_LETTER_COUNT_CASE = VERIFIED
MISSING_LETTER_COUNT_CASE = NULL_PRESERVED
PLANNING_MINUTES_SOURCE = LETTERS_VECTOR_PREP_DURATION
NEW_CONTROLLED_FIXTURE = VERIFIED
PLAN_21 = UNCHANGED
PLAN_22 = UNCHANGED
PLAN_23 = UNCHANGED_NULL_REFERENCE_CASE
PLAN_23_NULL_DURATION = VALID_MISSING_GEOMETRY_INPUT
TASKS_JSON_MUTATIONS_ON_PROTECTED_PLANS = 0
QA_MUTATIONS = 0
PEOPLE_REQUIREMENTS = DEFERRED
WORKSPACE_REQUIREMENTS = DEFERRED
BATCH_ELIGIBILITY = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Owner decisions applied

```text
OWNER_DECISION_1: vector_prep selected as first E2E duration pilot = ACCEPT
OWNER_DECISION_2: duration = 2 minutes × letter_count = ACCEPT
OWNER_DECISION_3: missing letter_count preserves null = ACCEPT
OWNER_DECISION_4: positive proof uses new controlled fixture = ACCEPT
OWNER_DECISION_5: plan 23 remains unchanged null reference = ACCEPT
```

---

## 2. What changed (bounded)

| Change | Why |
| ------ | --- |
| `PlanningDurationContract.planning_minutes_source` optional field | Single contract stamps Aggregate provenance |
| `LETTERS_VECTOR_PREP_DURATION.planning_minutes_source = LETTERS_VECTOR_PREP_DURATION` | Owner-expected source label; not a second formula |
| Resolver uses contract stamp when present | Aggregate remains sole calculator |
| Tests: TE2E-028B + new `test_vector_prep_duration_e2e_completeness.py` | Positive/negative + EP + projection |

**Not changed:** formula engine, `minutes_per_letter=2.0` location (still only on contract), plan 21/22/23, Capacity, people/workspace/batch.

---

## 3. Path

```text
factual letter_count (PD geometry / quote_geometry)
  → collect_planning_duration_facts
  → LETTERS_VECTOR_PREP_DURATION + COUNT_BASED_TIME
  → ProductAggregate estimated_minutes + planning_minutes_source
  → EP preview/persist/materialize snapshot (no recalculation)
  → GET .../resource-requirements
```

Positive (letter_count=5):

```text
estimated_time_minutes = 10
planning_minutes_source = LETTERS_VECTOR_PREP_DURATION
workcenter = WC_PREPRESS
resource_requirements_status = KNOWN_MINIMAL
```

Missing letter_count → minutes null, source null (plan 23 remains valid example).

Zero / invalid letter_count → null (`INVALID_INPUT` per existing `_coerce_positive_int`).

---

## 4. Protected plans / QA

```text
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
plan21 SHA = 75933211…ff59 (unchanged)
plan22 SHA = 0ec2dce6…ecb97 (unchanged)
plan23 SHA = 00ee947c…c1f2 (unchanged)
plan23 vector_prep duration = null
Capacity source/alloc = 0 / 0
assignment transitions = 7
```

---

## 5. Tests run

```text
pytest tests/test_vector_prep_duration_e2e_completeness.py
     tests/test_te2e_028b_formula_planning_duration.py
     tests/test_planning_minutes_source_contract.py
→ 25 passed
```

---

## 6. Next (not authorized)

CNC / people / workspace / batch / Capacity / Phase B — separate Owner GO only.
