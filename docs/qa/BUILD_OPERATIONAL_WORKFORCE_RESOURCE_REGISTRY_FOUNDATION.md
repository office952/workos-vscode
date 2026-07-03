# BUILD — Operational Workforce & Resource Registry Foundation

**Date:** 2026-06-09  
**Status:** Implemented  
**Audit prerequisite:** PASS (`/tablet`, `/operator`, registry audit)

## Scope

Foundation layer for global Employee + production resources registry, without touching CostEngine, Pricing, or Quote flow.

## What was reused

| Existing structure | Role in foundation |
|--------------------|-------------------|
| `employees` table + CRUD API | Canonical employee record |
| `machines` table (created if missing) | Canonical machines/tools/work_areas |
| Foundation `roles/skills/workcenters` codes | Referenced by authorization codes (read-only) |
| `ProductTemplateOperation.code` | Key for `operation_resource_requirements` |
| `execution_reality.tasks_json` | Optional `employee_id` annotation on task-action start |

## What was created

| Artifact | Purpose |
|----------|---------|
| Migration `s43_operational_resource_registry` | Schema extensions + M2M tables |
| `models/operational_registry.py` | ORM for authorizations, mappings, montaj teams |
| `services/operational_registry_service.py` | Registry business logic |
| `routers/operational_registry.py` | `/api/v1/operational-registry/*` |
| `seeds/seed_operational_workforce_registry.py` | Real employees + resources + mappings |
| `frontend/src/api/operationalRegistry.ts` | Future consumption client |
| `tests/test_operational_resource_registry.py` | Foundation contract tests |

## Many-to-many model

```
Employee
  ├── employee_skill_authorizations (employee_id, skill_code)*
  ├── employee_workcenter_authorizations (employee_id, workcenter_code)*
  └── employee_resource_authorizations (employee_id, resource_code)*

operation_resource_requirements
  operation_code → required_skill_codes[], allowed_workcenter_codes[], allowed_resource_codes[]

field_installation_teams + field_installation_team_members
  installation_ref → multiple employee_id (montaj teren, draft only)
```

`*` Unique pairs — many employees per resource, many resources per employee.

## Real data seeded

- **8 employees** with RON/monthly salary (`cost_lunar_firma` + `salary_currency` + `salary_period`)
- **14 resources** (machines, tools, work areas)
- **9 operation mappings** including `colantare` (atelier) vs `field_installation` (teren)

## Boundaries preserved

| Area | Status |
|------|--------|
| CostEngine | ❌ Not modified |
| Pricing | ❌ Not modified |
| Quote flow | ❌ Not modified |
| `/tablet` | Demo preserved; `DEMO_OPERATORS` marked non-canonical |
| `/operator` | UI unchanged; `performAction` accepts optional `employee_id` |
| Salaries in quotes | ❌ Not introduced |
| Auto-assignment | ❌ Not implemented |

## API surface

```
GET  /api/v1/operational-registry/employees
GET  /api/v1/operational-registry/employees/{id}
PUT  /api/v1/operational-registry/employees/{id}/authorizations
GET  /api/v1/operational-registry/resources
GET  /api/v1/operational-registry/resources/{code}/authorized-employees
GET  /api/v1/operational-registry/operation-mappings
PUT  /api/v1/operational-registry/operation-mappings
POST /api/v1/operational-registry/field-installation-teams
```

## Test plan

```bash
cd backend
python -m pytest tests/test_operational_resource_registry.py -v
```

## Next build (out of scope)

1. Wire `/tablet` queue to `operational-registry` + `operator/tasks`
2. Operator UI: employee picker from registry (remove hardcoded assignee)
3. Montaj module UI consuming `field_installation_teams`
4. Product Systems editor: show operation mapping from registry
5. Reports: productivity per `employee_id` from execution reality
