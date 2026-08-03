# DEC-009 = B — Controlled Operational Task Materialization

**Status:** RECORDED  
**Date:** 2026-08-03  
**Owner decision:** explicit Finalization Wave 3 GO  
**Runtime module:** `backend/services/dec009_materialize_gate.py`

## Decision

```text
DEC-009 = B
```

**Approved scope:**
controlled operational task materialization on demonstrated non-production fixtures.

**This decision does not authorize:**
assignment,
machine assignment,
sessions,
attendance,
scheduling,
capacity allocation,
Employee Mobile,
production rollout,
commercial pricing changes,
or legacy cleanup.

## Wave 3 GO

```text
FINALIZATION_WAVE_3_GO = GRANTED_WITH_STRICT_SCOPE
```

Authorized for this build only:

- durable QA fixture `order_id=880750` / `execution_plan_id=23`
- fail-closed OD3 True_CONDITIONAL next-dry registry
- strict idempotency
- durable audit via existing `tasks_json` envelope fields
- zero assignment / sessions / scheduling / Employee Mobile

## Runtime enforcement

| Mechanism | Behavior |
|-----------|----------|
| `LIVE_DEC009_STATUS` | `"B"` |
| `BATCH_EXECUTE_MATERIALIZE_MODE` | `True_CONDITIONAL` |
| next-dry target | `880750` / plan `23` / `WAVE2-DURABLE-QA-880750` |
| protected orders | include `880811`, `973019`, `88002`, Golden Pilot baselines |
| production `APP_ENV`/`ENVIRONMENT` | always denied |
| closed next-dry | no order may materialize |

Product code must **not** hardcode `if order_id == 880750`. Scope is expressed only through the next-dry registry helpers.

## Exact next step (not authorized here)

Finalization Wave 4 readiness review only after Owner reviews Wave 3:

- workcenter-to-machine capability read model
- eligibility read model
- zero assignment mutation
