# BUILD: Volumetric Return Task Taxonomy + Production Prepared-by Responsibility

## Purpose

Fix two operational issues observed on Employee Mobile:

1. **Wrong cant task taxonomy** — `Lipire cant pe față` mapped to `welding` / `RETURN_PROFILE_FACE_BONDING`.
2. **Clarification routing** — production clarifications should target whoever prepared/instrumented the execution plan when known.

## Problem observed (Employee Mobile)

Task displayed as:

```text
Lipire cant pe față
process_type = welding
machine_type = RETURN_PROFILE_FACE_BONDING
```

This conflates **modelare cant** (CNC forming machine) with **lipire cant** (assembly tables).

## Owner rule — cant taxonomy

| Step | Task | process_id | process_type | machine_type |
|------|------|------------|--------------|--------------|
| Modelare | Modelare canturi litere volumetrice | `side_forming` | `edge_bending` | `RETURN_PROFILE_FORMING_MACHINE` |
| Lipire | Lipire canturi pe fețele literelor | `return_face_bonding` | `volumetric_letter_assembly` | `ASSEMBLY_TABLE` |

Owner-confirmed instructions (template/fixture only — not generated from `process_type`):

- Modelare: numerotare + livrare la mesele de ansamblare.
- Lipire: canturi numerotate + verificare aliniere.

## Root cause (audit)

| Layer | Finding |
|-------|---------|
| Snapshot mapper | `return_face_bonding` → `welding` (canonical) |
| Display labels | `volumetric_execution_dispatch` label „Lipire cant pe față” |
| Dossier/pricing | `RETURN_PROFILE_FACE_BONDING` workcenter for priced op (unchanged — CostEngine boundary) |
| Execution plan | Emitted `process_type`/`machine_type` from normalized snapshot as-is |

## Implementation

### Taxonomy service

`backend/services/volumetric_return_task_taxonomy_service.py`

- Applied at **plan generation** and **Sandu dev fixture** (`--apply`).
- Idempotent; preserves existing manual instructions on non-target tasks (e.g. T-008 smoke).

### Snapshot mapper

- `return_face_bonding` / `return_profile_face_bonding` → `volumetric_letter_assembly` (not `welding`).

### Prepared-by

- `execution_plan.prepared_by_user_id` set on `POST /plan/from-order/{id}` from current user.
- Alembic: `s50_execution_plan_prepared_by_clarification_target`.

### Clarification target

- `task_clarification_requests.target_user_id` set automatically from plan `prepared_by_user_id`.
- Employee cannot set target manually.
- Operator panel shows `Către: <nume>` or `Coada operator/admin`.
- Mobile success message differs when routed to responsible.

## Sandu fixture (dev-only)

Script: `backend/scripts/dev_seed_employee_mobile_sandu_fixture.py --apply`

- Fixes return taxonomy on order `1` plan.
- Sets `prepared_by_user_id = dev-admin-user-00000000`.
- Does not touch `execution_reality` or T-001 (Calin).

## Existing production plans

No global backfill. Dev fixture updates local order `1` only.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_return_task_taxonomy.py tests/test_execution_plan_prepared_by.py tests/test_employee_mobile_tasks.py tests/test_task_clarification_requests.py tests/test_dev_employee_mobile_sandu_fixture.py tests/test_production_document_handoff.py tests/test_execution_task_instructions.py -q
```

## Deferred

- Push notifications / inbox / chat
- Global plan taxonomy backfill
- CostEngine / pricing workcenter rename for `RETURN_PROFILE_FACE_BONDING`
- PDF/SVG viewer, photo upload, Home UI redesign
