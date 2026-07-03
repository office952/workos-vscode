# BUILD — INTAKE_V3_QUOTE_CREATION_GUARD_POLICY_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `0ff8e65` — quote creation dry-run contract foundation  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Add **Quote Creation Guard Policy** — explicit disabled-by-default policy that blocks real commercial quote creation from Intake V3, independent of quote readiness or dry-run quality.

Answers: *Why can't Intake V3 create a real quote yet?* → Real quote creation is **disabled-by-default by policy** until owner approves a dedicated enablement build.

## Disabled-by-default policy

| Field | Value (always in this build) |
|-------|------------------------------|
| `policy_status` | `disabled_by_default` |
| `policy_code` | `INTAKE_V3_QUOTE_CREATION_DISABLED_BY_DEFAULT` |
| `can_create_quote` | `false` |
| `real_quote_creation_enabled` | `false` |
| `disabled_by_policy` | `true` |
| `owner_confirmation_required` | `true` |

`is_real_quote_creation_enabled()` always returns `false` — no env var activation in this build.

## Why `can_create_quote` remains false

Operational readiness (`ready_preview_only`) and a complete dry-run payload **do not** enable quote creation. Policy is a separate lock from readiness blockers.

Quote readiness includes info item `QUOTE_CREATION_POLICY_DISABLED` (severity `info`, not operational blocker).

## Dry-run allowed vs quote creation blocked

| Layer | Allowed |
|-------|---------|
| Quote creation dry-run GET | Yes — payload/snapshot preview only |
| Real quote creation | No — policy disabled |
| `safe_to_dry_run` | `true` when workspace not archived |

Dry-run response includes `guard_policy`; `quote_creation_disabled_reason` derives from policy message.

## Backend

- `backend/services/intake_v3_quote_creation_guard_policy_service.py`
- Schemas: `IntakeV3QuoteCreationGuardPolicy`, `IntakeV3QuoteCreationGuardReason`, `IntakeV3QuoteCreationEnableRequirement`
- Integrated in dry-run + quote readiness checklist
- `GET /api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-guard-policy` (read-only)

## Frontend

- `fetchIntakeV3QuoteCreationGuardPolicy(workspaceId)`
- `IntakeV3QuoteCreationGuardPolicyPanel` after dry-run panel
- Dry-run panel shows embedded `guard_policy`
- Command bar: policy lock, dry-run allowed, real quote disabled
- Create quote button remains disabled

## Tests

### Backend targeted

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_quote_creation_guard_policy.py tests/test_intake_v3_quote_creation_dry_run.py tests/test_intake_v3_quote_readiness_gate.py -q
```

**Result:** 31 passed

### Backend regression

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_finish_variation_summary.py ... test_volumetric_execution_task_order.py -q
```

**Result:** 112 passed

### Frontend targeted

```powershell
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
```

**Result:** 82 passed

## Boundary (not touched)

CostEngine, pricing formulas, TVA, commercial markup, Inventory, StockMovement, real quote endpoints, order creation, ExecutionPlanService, ExecutionTask, Employee Mobile, Intake V2, DB schema/migrations, production dispatch runtime.

## Pending build 2

**Commercial Quote Bridge disabled-by-default** — map dry-run payload to real quote handoff with owner approval gate.

## Recommended commit message

```
feat(intake-v3): add quote creation guard policy foundation
```
