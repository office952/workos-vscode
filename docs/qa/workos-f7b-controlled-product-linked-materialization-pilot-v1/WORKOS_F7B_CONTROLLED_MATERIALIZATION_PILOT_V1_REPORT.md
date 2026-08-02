# WORKOS F7B — Controlled product-linked materialization pilot

## Verdict

```text
F7B = PASS
EXACT FIXTURE = 880811 / 22
FIRST POST = MATERIALIZED
SECOND POST = IDEMPOTENT
OPERATIONAL TASKS = 5
CANDIDATE PARITY = PASS
COMMERCIAL DRIFT = ZERO
PROTECTED BASELINE DRIFT = ZERO
SESSIONS = ZERO
ASSIGNMENTS = ZERO
GATE FINAL STATE = CLOSED
PUSH = NOT EXECUTED
Production Ready = NU
```

## Identity (resume start)

| Field | Value |
|-------|-------|
| Repo | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD before edits | `b5d976be` |
| Remote | `0c8a76cd` |
| Ahead / behind | 0 / 7 |
| Stash | `wip-employee-unrelated` intact |

## Agents

| Agent | Role | Result |
|-------|------|--------|
| Lead | Gate retarget, POST×2, close, commits | PASS |
| A | Fixture / DB guard | PASS — 880811/22, commercial 1847.5, ops empty before |
| B | Contract parity audit | PASS — 5 candidates, fingerprint `cd03f9ac…` |
| C | Fresh runtime restart | PASS — open then closed verified |

## Gate ownership

**File:** `backend/services/dec009_materialize_gate.py`

**Why 973019 was eligible before:** it was the sole `next_dry_target` with `allow_materialize=True` and was **not** in `PROTECTED_ORDER_IDS`. Gate checks both `order_id` and `plan_id` via `scoped_b_matches` / `enforce_dec009_materialize_gate` (called from `execution_plan_v2_materialize_service` with resolved plan id).

**Retarget:** temporary open `880811` / `22` only; `973019` added to `PROTECTED_ORDER_IDS`. Second POST remained gate-eligible (gate does not auto-close); HTTP returned **409** `operational_tasks_already_materialized` with zero duplicate rows.

**Final committed state:** `close_materialize_pilot_gate` posture — `next_dry` order/plan `0`, `allow_materialize=False`, fixture `FIX-F7B-CONTROLLED-MATERIALIZE-CLOSED`. No order authorized. `973019` remains protected. Helpers: `open_f7b_controlled_materialize_pilot`, `close_materialize_pilot_gate`, `register_golden_pilot_materialize_target` (tests / future Owner GO only).

## Fixture

| Field | Value |
|-------|-------|
| order_id | 880811 |
| execution_plan_id | 22 |
| commercial | 1847.5 |
| snapshot sha256 | `a59b6c447d9e6afb484bae9415e85041e12fc73bf5bb20a7cf2a089bd393738b` |
| planned_tasks | 5 |
| ops before | 0 |
| F7A.1 / blocked preflight | linked at commit `b5d976be` + `preflight-recreated-fixture.json` |

## Tests

Targeted suite after closed gate: **64 passed**  
(`test_dec009_materialize_gate`, F7A, F7A.1, DAG, materialize, step9 audit).

Gate cases covered: 880811/22 open allow; 973019 forbid; other order forbid; wrong plan forbid; second call still gate-eligible; closed allows none.

## POST evidence

| Call | HTTP | Semantics |
|------|------|-----------|
| 1 | **201** | `status=materialized`, plan 22, ops 5, `no_sessions_created=true` |
| 2 | **409** | `operational_tasks_already_materialized`, ops still 5, no drift |

Artifacts: `preflight-open-gate.json`, `post1-materialize.json`, `post2-idempotency.json`, `post-materialization-parity.json`, `post-pilot-summary.json`.

## Post-materialization parity

- Ops = 5; CNC = `WC_CNC_ROUTING`; bond ← face + side; aliases/premount/SVG-DWG ops absent
- Commercial / snapshot / protected `973019` prefix `2d412e6e1234ae44` unchanged
- Sessions / assignments / actuals / ExecutionReality = 0
- `v2_operational_ready` = envelope only — **not** scheduled / assigned / atelier / Production Ready

## Boundaries respected

No 973019 POST, no third POST, no sessions/assignment/scheduling, no push, no UI/Pricing/SVG changes.

## Next Owner gate

Scheduling / assignment / sessions / atelier readiness remain **out of scope** until a new explicit Owner GO.
