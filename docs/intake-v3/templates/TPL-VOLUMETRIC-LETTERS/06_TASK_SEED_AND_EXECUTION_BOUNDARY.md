# TPL-VOLUMETRIC-LETTERS — Task Seed and Execution Boundary

---

## Principiu

```text
Operation Catalog → operation candidates / task seed
Intake V3 → ProductionHandoff (preview_only=true)
Order → ExecutionPlanService → taskuri REALE
ExecutionPlanService → Employee Mobile
```

---

## Diagramă

```text
ProductSystem Template (TPL-VOLUMETRIC-LETTERS)
        │
        ▼
Operation Catalog (condiționat: active_if, depends_on)
        │
        ▼
Intake V3 ConfirmedProductionModel + FinishAssignment
        │
        ▼
ProductionHandoff.task_seed  ← preview via intake_v3_production_handoff_adapter ✅
        │
        ▼
Quote → Order (snapshot înghețat)
        │
        ▼
ExecutionPlanService  ← taskuri reale, dependențe runtime
        │
        ▼
Employee Mobile  ← Start Task, work sessions
```

---

## Ce poate task seed-ul

- listă operații candidate filtrate după `active_if`;
- dependențe declarative între `operation_code`;
- instrucțiuni operator (preview);
- material summary estimativ;
- **fără** `task_id` real, **fără** status operational.

---

## Ce NU poate task seed-ul

- crea `execution_plan` row;
- crea `execution_reality`;
- porni work sessions;
- consuma inventory;
- înlocui CostEngine sau pricing.

---

## Gap față de runtime actual

Execution plan WorkOS actual (`volumetric_conditional_plan_tasks_service`) **nu** implementează încă toate regulile din Operation Catalog (ex. ordine face vinyl, PSU în colet). Build: `AUDIT/FIX — Volumetric execution task order and electrical source handling`.

---

## Legături

- Catalog: [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md)
- Handoff adapter: [10_PRODUCTION_HANDOFF_ADAPTER.md](./10_PRODUCTION_HANDOFF_ADAPTER.md)
- Global boundary: [../../../03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md](../../../03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md)
