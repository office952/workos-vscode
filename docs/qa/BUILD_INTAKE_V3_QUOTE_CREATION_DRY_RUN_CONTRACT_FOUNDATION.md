# BUILD — INTAKE_V3_QUOTE_CREATION_DRY_RUN_CONTRACT_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `0b1fc07` — quote readiness gate and pre-quote review foundation  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Add **Quote Creation Dry-Run Contract** — simulates what a future quote creation build would receive, without calling real quote endpoints, CostEngine, or creating quotes/orders/plans.

## Dry-run vs quote creation

| Layer | Behavior |
|-------|----------|
| **Quote readiness gate** | Operator checklist; `can_create_quote` always false |
| **Dry-run contract** | Payload + snapshot preview of would-be handoff; `can_create_quote_now` always false |
| **Real quote creation** | **Not implemented** — `POST /api/v1/entities/quotes`, `POST /from-intake/{id}` exist elsewhere but are **never called** |

Real quote endpoints audited (read-only): `backend/routers/quotes.py` — `create_quotes`, `create_quote_from_intake`, pricing routes. None invoked by Intake V3 dry-run.

## Endpoint

`GET /api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-dry-run`

- Read-only — no DB writes, no preview snapshot persistence
- Builds in-memory workspace preview + dry-run contract
- Archived workspace → blocked dry-run response

## Payload preview

`IntakeV3QuoteCreationDryRunPayloadPreview`: workspace/template identity, dimensions, confirmed counts, finish summary, variation count, pricing/handoff notes (preview-only, no final price).

## Snapshot preview

`IntakeV3QuoteCreationDryRunSnapshotPreview`: payload marker hash, raw SVG reference (non-truth), confirmed model snapshot, finish assignments, variation/pricing/prequote snapshots, `created_quote_id: null`.

## Safety flags

All enforced false via Pydantic validators: `quote_creation_endpoint_called`, `quote_created`, `order_created`, `execution_plan_created`, `inventory_mutated`, `cost_engine_called`, `pricing_formula_modified`.

## Workspace preview integration

`quote_creation_dry_run_available: bool` on `IntakeV3WorkspacePreview` — dry-run body fetched via separate GET (keeps preview lightweight).

## Frontend

- `fetchIntakeV3QuoteCreationDryRun(workspaceId)`
- `IntakeV3QuoteCreationDryRunPanel` after preview shell when workspace loaded
- Command bar: dry-run availability/status; quote creation remains disabled
- Flow stepper: **Quote Dry-Run** (7th step)

## Tests

### Backend targeted

```powershell
pytest tests/test_intake_v3_quote_creation_dry_run.py tests/test_intake_v3_quote_readiness_gate.py tests/test_intake_v3_finish_variation_summary.py -q
```

**Result:** 31 passed

### Backend regression

```powershell
pytest tests/test_intake_v3_finish_assignments.py ... test_volumetric_execution_task_order.py -q
```

**Result:** 103 passed

### Frontend targeted

```powershell
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
```

**Result:** 76 passed

## Boundary (respected)

No CostEngine, pricing formulas, inventory, real quote/order/plan creation, Employee Mobile, Intake V2, DB migration.

## Pending real quote creation build

- Wire dry-run payload to `create_quote_from_intake` or dedicated Intake V3 handoff
- Enable quote CTA when product policy allows
- Commercial price via CostEngine (separate build)

## Recommended commit message

```
feat(intake-v3): add quote creation dry-run contract foundation
```
