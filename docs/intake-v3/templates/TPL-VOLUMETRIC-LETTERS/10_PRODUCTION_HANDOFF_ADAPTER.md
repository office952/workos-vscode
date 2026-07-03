# TPL-VOLUMETRIC-LETTERS — Production Handoff Adapter

**Service:** `backend/services/intake_v3_production_handoff_adapter.py`  
**Contract:** `ProductionHandoffPreview` — `preview_only=true`, `non_executable=true`  
**E2E:** consumat de `intake_v3_workspace_preview_service` + UI shell `/intake-v3` + workspace preview `GET /workspaces/{id}/preview`

---

## Rol

```text
IntakeV3Workspace → build_production_handoff_preview() → ProductionHandoffAdapterResult
```

**Regulă critică:**

```text
ProductionHandoff preview is not ExecutionPlan.
TaskSeedCandidate is not ExecutionTask.
```

---

## Implementat

| Funcție | Rol |
|---------|-----|
| `build_production_handoff_preview()` | preview complet |
| `build_task_seed_candidates()` | 13 operații catalog cu dependențe |
| `validate_production_handoff_preview()` | non-executable, fără employee names |

**Finish variation notes (local):** `finish_variation_handoff_notes`, `group_labels`, `requires_letter_group_visibility` — operator visibility only; no ExecutionTask creation.

**Quote readiness gate:** handoff summary in pre-quote review repeats non-executable boundary; no plan/tasks created.

**Dry-run contract:** handoff notes included in would-be quote payload preview; still no ExecutionTask creation.

**Guarded draft quote:** snapshot includes handoff preview reference; no ExecutionPlan/ExecutionTask created.

**Priced draft after manual pricing review:** production handoff preview unchanged in notes snapshot; execution still not started until Order exists and production handoff build runs.

**Geometry path perimeter classification:** task seed inputs may reference classified face/return/bevel perimeters from `geometry_metrics_snapshot` when available — preview-only; still no ExecutionTask creation.

**Operator layer role confirmation:** when `layer_role_confirmation_snapshot` is complete/partial, classified perimeters prefer operator-confirmed roles (`high` quality) over auto synonym mapping — still preview-only.

**Accept/convert readiness:** after guarded convert, Order exists (`locked`); use production readiness GET audit — still no ExecutionPlan/ExecutionTask/Inventory mutation.  
**Draft quote review:** read-only handoff checklist from snapshot — no production start.

---

## Task seed rules (no shared support)

- return vinyl **înainte** de return forming
- return painting **după** assembly
- face vinyl **după** assembly (după painting dacă cant vopsit)
- LED înainte de assembly
- PSU în colet la packaging — **fără** `electrical_source_mounting`
- skills/stations only — **fără** persoane hardcodate

---

## Boundary

| Nu face | Detaliu |
|---------|---------|
| ExecutionPlan | neatins |
| ExecutionTask | neatins |
| Employee Mobile runtime | `employee_mobile_action_allowed=false` |
| Task generator runtime | neatins |
| Shared support final logic | warning pending |
| Real quote creation | disabled-by-default guard policy — handoff preview does not create quotes |
| Commercial quote bridge | mapping preview only — snapshot plan, no execution or quote side effects |
| Quote creation enablement | final blocker check + owner approval contract — real creation remains blocked |
| Real quote enablement readiness | owner decision + snapshot + anti-duplicate + recovery policy contracts |
| Layer role propagation | workspace effective vs quote snapshot stale warnings; guarded technical refresh on draft/priced draft only |
| Material availability preview | read-only stock match vs breakdown quantities; no reservation or procurement |
| Procurement preview | read-only recommendations from availability; no PO / supplier order / inventory mutation |
| Production Preview UI | grouped read-only container for geometry/material/procurement/task previews; layer role confirmation stays separate input |

---

## Legături

- Operation Catalog: [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md)
- Execution boundary: [06_TASK_SEED_AND_EXECUTION_BOUNDARY.md](./06_TASK_SEED_AND_EXECUTION_BOUNDARY.md)
