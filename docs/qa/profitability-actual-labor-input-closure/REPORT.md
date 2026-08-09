# Profitability Actual Labor Input Closure — REPORT

## A. Verdict

```text
PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE = PASS
```

## B. Repo / HEAD

```text
worktree = C:\w\psiso
branch   = feat/f7i-owner-rate-activation
baseline HEAD = 5034f762
```

## C. Owner GO

```text
AUTHORIZE_PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE
```

## D. Existing profitability inventory

See `source-inventory.md`.

## E. Actual labor source

```text
ACTUAL_LABOR_SOURCE = execution_reality.tasks_json (closed sessions)
EXECUTION_REALITY_WRITE_AUTHORITY = controlled_task_session_service
READ_HELPER = build_profitability_actual_labor_input
```

## F–K. Provenance / duration / closed-session

See architecture contract + `field-ownership.md`.

## L–V. Controlled scenarios

See `controlled-scenario-matrix.md`. Pytest: **19 passed**.

## W. Rounding / timezone

```text
CANONICAL_DURATION_UNIT = minutes
SECONDS_DERIVED = absolute timestamp delta
ROUNDING_RULE = python_round_half_to_even_seconds_over_60_to_int_minutes
TIMEZONE = absolute ISO; no browser TZ dependence
```

## X. Invalid-data

Malformed rows classified in `invalid_sessions`; excluded from totals (fail-closed).

## Y. Correction / backfill

No production session duration correction writer found that bypasses controlled SoT.
Attendance correction ≠ execution sessions.
Assignment backfill ≠ labor minutes.
```text
LABOR_CORRECTION_BYPASS_RISK = NONE_REACHABLE_FOR_DURATION
```

## Z. Historical stability (time provenance)

Employee rename does not change labor minutes/ids.
Task identity from frozen operational plan keys.
ProductDefinition / pricing / machine rates not consulted by labor input helper.

## AA. Duplicate labor authority

```text
DUPLICATE_WRITABLE_LABOR_AUTHORITY = 0
```

Canonical writable duration lives on session rows via controlled writer.
Higher aggregations are derived. `ExecutionReality.total_actual_time_minutes` is recomputed from sessions by reality service (same SoT), not an independent write authority for Profitability.

## AB. Profitability boundary

One-way consumption. Documented in architecture contract.

## AC–AD. Rate authority

```text
LABOR_COST_RATE_AUTHORITY = PARTIAL
HISTORICAL_RATE_STABILITY = UNPROVEN
```

See `rate-authority-assessment.md`.

## AE. Scenario matrix

`controlled-scenario-matrix.md`

## AF. Runtime/code changes

- `backend/services/profitability_actual_labor_input_service.py` (new)
- `backend/services/profitability_actual_read_model_service.py` (embed labor_input)
- `backend/tests/test_profitability_actual_labor_input_closure.py` (new)
- `frontend/src/lib/currentTruthControlCenter.ts` (truth sync)

## AG. Regression

```text
pytest test_profitability_actual_labor_input_closure.py
     + test_legacy_session_write_path_assignment_gate_closure.py
     + test_controlled_session_command_safety.py
     + test_profitability_analysis.py
→ 41 passed
```

## AH. QA proof

```text
QA_MUTATIONS = 0
Isolated pytest DB only; order 880750 not mutated.
```

## AI. Modules / Governance

Truth Control Center `execution_reality` node updated: labor input CLOSED; rate snapshot next.
No Capacity / Phase E activation.

## AJ. Dead Pieces

See `dead-pieces.md`.

## AK. Docs / evidence

- `docs/architecture/PROFITABILITY_ACTUAL_LABOR_INPUT_CONTRACT.md`
- `docs/worklog/realignment/2026-08-09_profitability_actual_labor_input_closure.md`
- this folder

## AL–AM. Commits / push

Implementation + docs commits local only.
```text
NO_PUSH = YES
```

## AN. Next roadmap

```text
NEXT_ROADMAP_DOMAIN = LABOR_COST_RATE_SNAPSHOT_AUTHORITY
NEXT_TASK = NOT_AUTHORIZED
PROFITABILITY_MONETARY_CALCULATION = NOT_AUTHORIZED
```

---

### Pass block

```text
PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE = PASS
ACTUAL_LABOR_SOURCE = execution_reality.tasks_json closed sessions
EXECUTION_REALITY_WRITE_AUTHORITY = controlled_task_session_service
CLOSED_SESSION_LABOR_INPUT = VERIFIED
CANONICAL_DURATION_SOURCE = ENDED_AT_MINUS_STARTED_AT
CANONICAL_DURATION_UNIT = minutes
ROUNDING_RULE = python_round_half_to_even_seconds_over_60_to_int_minutes
SESSION_PROVENANCE = VERIFIED
EMPLOYEE_PROVENANCE = VERIFIED
TASK_PROVENANCE = VERIFIED
PLAN_PROVENANCE = VERIFIED
ORDER_PROVENANCE = VERIFIED
MULTI_SESSION_AGGREGATION = VERIFIED
MULTI_EMPLOYEE_AGGREGATION = VERIFIED
MACHINE_RUN_DOUBLE_COUNT = NO
PLANNED_ACTUAL_SEPARATION = VERIFIED
END_TASK_COMPLETION_SEPARATION = VERIFIED
RESTART_DURABILITY = VERIFIED
IDEMPOTENT_REPLAY_DUPLICATION = NONE
COMPATIBILITY_BRIDGE_PARITY = VERIFIED
LABOR_AGGREGATION_LEVELS = SESSION_EMPLOYEE_TASK_PLAN_ORDER
DUPLICATE_WRITABLE_LABOR_AUTHORITY = 0
COMMERCIAL_MUTATIONS = 0
EMPLOYEE_RATE_MUTATIONS = 0
LABOR_COST_RATE_AUTHORITY = PARTIAL
HISTORICAL_RATE_STABILITY = UNPROVEN
PROFITABILITY_MONETARY_CALCULATION = NOT_AUTHORIZED
DB_SCHEMA_CHANGES = 0
NEW_PROFITABILITY_UI = 0
QA_MUTATIONS = 0
MODULES_IMPACT = truth_control_center_execution_reality_sync
GOVERNANCE_IMPACT = none_beyond_factual_docs
NEXT_ROADMAP_DOMAIN = LABOR_COST_RATE_SNAPSHOT_AUTHORITY
NEXT_TASK = NOT_AUTHORIZED
```
