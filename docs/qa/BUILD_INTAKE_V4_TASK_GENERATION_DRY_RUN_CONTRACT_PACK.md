# BUILD_INTAKE_V4_TASK_GENERATION_DRY_RUN_CONTRACT_PACK

**Date:** 2026-06-22  
**Status:** PASS (scoped task generation dry-run contract)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `1449fcadb1482a66716d1b2931d882b847808c6e`  
**Commit:** none (awaiting user confirmation)

---

## Working tree before (off-scope dirty — do NOT include in commit)

V2/V3 operator workspace, AuthContext, `tmp/`, untracked E2E off-scope, atoms docs — unchanged.

---

## Files audited

- `backend/models/execution_plan.py` — ExecutionPlan (tasks in `tasks_json`, no separate ExecutionTask ORM)
- `backend/services/execution_task_assignment_service.py` — task assignment via plan JSON
- `backend/services/intake_v4_production_handoff_preview_service.py`
- `backend/services/intake_v4_template_option_contract_service.py`
- `backend/services/intake_v4_production_task_dry_run_service.py` — legacy V3 wrapper (unchanged behavior)
- `backend/services/intake_v3_production_task_dry_run_service.py` — V3 catalog dry-run reference

---

## Files modified (in-scope)

| File | Change |
|------|--------|
| `backend/schemas/intake_v4.py` | Task generation dry-run response models |
| `backend/services/intake_v4_task_generation_dry_run_service.py` | **New** — dry-run contract builder |
| `backend/services/intake_v4_workspace_service.py` | `get_task_generation_dry_run_for_workspace` |
| `backend/routers/intake_v4_workspaces.py` | GET `/task-generation-dry-run` |
| `backend/tests/test_intake_v4_task_generation_dry_run.py` | **New** — 11 tests |
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | Types + API client |
| `frontend/src/components/workos/intake-v4/IntakeV4TaskGenerationDryRunPanel.tsx` | **New** — Review panel |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Load + render dry-run panel |
| `docs/qa/BUILD_INTAKE_V4_TASK_GENERATION_DRY_RUN_CONTRACT_PACK.md` | This document |

**Not touched:** CostEngine, Pricing, ExecutionPlan creation, Order/Production mutations, stock, Employee Mobile, V2/V3 dirty.

---

## ExecutionTask model audit

| Question | Answer |
|----------|--------|
| Where is ExecutionTask? | **No dedicated ORM.** Tasks live as JSON dicts in `execution_plan.tasks_json` (+ `execution_reality.tasks_json` for shop-floor state). |
| Required fields | Plan-level: `order_id`, `order_code`, `snapshot_version`, `tasks_json`. Task dicts: `id`, `type`, display fields — assigned via `execution_task_assignment_service`. |
| Status | Runtime status on task dict in reality JSON; plan is write-once from order snapshot. |
| Order / Production links | `ExecutionPlan.order_id` FK-like; Employee Mobile reads plan + reality via `employee_mobile_tasks_service`. |
| Real creation flow | Order snapshot → ExecutionPlan generation (separate service); **not** from Intake V4 workspace in this build. |
| Existing dry-run | V3 `production_task_dry_run_service`; V4 wrapper at `/production-task-dry-run` (catalog seeds). |
| Idempotency | No DB constraint yet; this build previews keys only. |
| Audit log | No real audit write in dry-run; `audit_preview` object only. |
| Employee Mobile fields | `display_name`, `station`, assignment metadata on task dict — future build. |
| Not touched | ExecutionPlan rows, reality JSON, inventory, order status. |

---

## Production handoff preview audit

| Item | Current state |
|------|----------------|
| Material jobs | From V4 material breakdown rows (`face_plexiglas_cutting`, etc.) |
| Operation groups | Local catalog doc codes (`cnc_cutting`, `return_forming`, …) |
| Task seed preview | V3 catalog via `build_v4_task_preview_response`; `creates_execution_task=false` |
| Blockers | Analysis boundary, finish not confirmed, unsupported template |
| Warnings | PSU, return depth, template contract, pricing missing |
| Template-backed | Material registry codes yes; operation groups **provisional** |
| Gap for dry-run | No dependency graph, idempotency plan, or `can_generate_tasks` contract |

---

## Template option contract audit (summary)

- **Aligned:** face/backing materials, return depth, Oracal/print, PSU watts (when mapped)
- **Partial:** oracal_641/8500, multi-group finish, LED pitch, preview operation codes
- **Missing:** mounting_system, back_bevel in V4 form
- Dry-run merges contract blockers/warnings into response

---

## New endpoint

`GET /api/v1/intake-v4/workspaces/{id}/task-generation-dry-run`

Read-only. Blockers in body. No DB writes. No audit log persistence.

Legacy endpoint `/production-task-dry-run` (V3 wrapper) **unchanged**.

---

## Dry-run response contract

```json
{
  "dry_run_mode": "task_generation_preview_only",
  "creates_execution_tasks": false,
  "writes_to_production": false,
  "stock_consumption": false,
  "dry_run_only": true,
  "can_generate_tasks": false,
  "task_candidates": [],
  "dependency_graph": [],
  "idempotency_plan": [],
  "blockers": [],
  "warnings": [],
  "audit_preview": {}
}
```

---

## Task candidates (when data complete)

Generated from production handoff material jobs + catalog seeds:

- Preflight: `preflight_vector_and_layers`, `cnc_file_preparation`
- CNC: `cnc_face_cutting`, `cnc_backing_cutting`
- Vinyl/print: `oracal_vinyl_cutting`, `print_artwork`, `laminate_print`, `face_vinyl_application`
- Return: `return_side_forming`, `return_face_bonding`
- LED: `led_module_install`, `psu_electrical_wiring`, `light_test_qc`
- Assembly/packaging: `letter_assembly` (provisional), `packaging_delivery_prep`

Each candidate: `creates_execution_task=false`, stable `idempotency_key`, optional `provisional` flag.

---

## Dependency graph

Template rules (examples):

- preflight → CNC prep → face/backing cut
- vinyl cut/print/laminate → face application
- return forming → return bonding
- face cut → return bonding
- backing → LED → electrical → assembly → QC → packaging

Edges marked `provisional` when candidate is provisional.

---

## Idempotency plan

```txt
idempotency_key = intake-v4:{workspace_id}:{template_code}:{task_key}
source_fingerprint = sha256(analysis_hash | finish_fingerprint | template_contract_version)
```

**Decision:** `analysis_hash` is **not** in idempotency key (prevents duplicate click duplicates only). Fingerprint signals when regeneration needed after reupload/finish change.

---

## Blockers (real generation)

- Analysis boundary / finish not confirmed (from handoff)
- Template unsupported / contract blockers
- `dry_run_only_no_order` — always present at workspace stage
- `material_jobs_missing` when no candidates
- `can_generate_tasks=false` always in this build

---

## Warnings

- Template contract warnings (provisional preview, multi-group, etc.)
- `provisional_task_candidates_present`
- `template_operation_mapping_missing`
- `production_preview_not_template_backed`

---

## Audit preview (not persisted)

`event_type=intake_v4_task_generation_dry_run`, counts, analysis_hash, finish_fingerprint, template_code.

---

## What this build does NOT do

- Create ExecutionTask / ExecutionPlan / WorkSession
- Write audit log to DB
- Mutate orders, production, inventory
- Stock consumption or reservations
- Employee Mobile changes
- CostEngine / Pricing changes
- Replace legacy `/production-task-dry-run` endpoint

---

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py tests/test_intake_v4_production_handoff_preview.py tests/test_intake_v4_template_option_contract.py -q
```

**Result:** `35 passed`

Frontend Vitest: omitted — panel is presentational summary only.

E2E: not run (follow-up).

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| Dry-run endpoint read-only | ✅ |
| Task candidates useful | ✅ |
| Dependencies | ✅ |
| Idempotency plan | ✅ |
| Blockers clear | ✅ |
| No ExecutionTask created | ✅ |
| No Order/Production mutation | ✅ |
| No stock | ✅ |
| Template contract respected | ✅ |
| UI states dry-run | ✅ |
| Tests pass | ✅ |
| V2/V3 untouched | ✅ |

---

## Recommendation

**Recommend commit** (scoped files only):

```
feat(intake-v4): add task generation dry-run contract for review step
```

---

## Follow-ups

1. Controlled real ExecutionTask creation (order-bound, owner approval)
2. Owner approval UI + explicit regeneration on fingerprint change
3. DB idempotency constraint on `(workspace_id, task_key)` or order scope
4. Production order binding before generation
5. Employee assignment + Mobile visibility
6. Align operation catalog doc codes → dossier `operation_keys` 1:1
