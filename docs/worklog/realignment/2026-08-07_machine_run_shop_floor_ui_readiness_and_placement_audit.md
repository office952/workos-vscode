# Worklog — MACHINE_RUN shop-floor UI readiness & placement audit

**Owner GO:** `AUTHORIZE_MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT`  
**Date:** 2026-08-07  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `94b4223b`  
**Canonical doc:** `docs/architecture/MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT.md`

---

## Verdict

```text
MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT = PASS
PRIMARY_UI_LOCATION = /execution/machine-runs (Planificare)
SECONDARY_CONTEXT_LINKS =
  ExecutionDetail participant chip + Ops-Graph chip
  · Utilaje = LATER
NEW_PAGE_REQUIRED = YES
MACHINE_RUN_READ_API = INSUFFICIENT
UI_BLOCKER = MACHINE_RUN_READ_MODEL/API_MISSING
NEXT_IMPLEMENTATION_SCOPE = MACHINE_RUN_OPERATOR_READ_API
FRONTEND_IMPLEMENTATION = NOT_STARTED
QA_MUTATIONS = 0
NO_PUSH = YES
```

---

## Browser audit evidence

Live navigation (admin session, staging UI `:3000`):

| Route | Observation |
| ----- | ----------- |
| `/execution` | Order list + capacity strip; no MachineRun |
| `/execution/880750` | Dense Rezultat execuție stack; Pregătire resurse ≠ reservation; Lucru în execuție = task sessions; post-job machine usage not logged |
| `/execution/ops-graph` | Assignment only; footer: no start/stop/complete/sessions |
| `/shop-floor` | Atelier monitor; Start/Complete framed as task actions elsewhere |
| `/utilaje` | Capacity/registry honesty; util% GAP — not shop-floor run home |
| `/modules` | Spine has ExecutionPlan + Reality; no MachineRun row → STALE |
| `/governance` | Ownership matrix lacks MachineRun/Reservation → STALE |

Frontend code: **zero** `MachineRun` / `machine_run` / `machine-runs` client usage.

---

## API gap

```text
Commands = POST-only under /api/v1/execution/resource-state/machine-runs/**
GET list/detail MachineRun = MISSING
R6 task resource state = CLEAR/ACTIVE only (no run payload)
```

---

## Placement rationale (short)

MachineRun is a **shared machine execution context** (multi-plan/multi-order).  
Order-scoped ExecutionDetail cannot be primary home.  
Utilaje is capacity-registry contaminated.  
Atelier is monitoring with task-verb language collision.  
→ Dedicated `/execution/machine-runs` + contextual chips.

---

## QA zero-mutation proof

```text
QA SHA before/after =
  bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
Alembic = s67_machine_run_execution_status
machine_runs = 0
reservations = 0
QA_START_COMMANDS = 0
QA_COMPLETE_COMMANDS = 0
FRONTEND_CHANGED = NO
```

---

## Commits

Docs-only commits for this GO (no frontend, no push).
