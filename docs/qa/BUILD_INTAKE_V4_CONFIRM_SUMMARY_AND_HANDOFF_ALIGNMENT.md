# BUILD_INTAKE_V4_CONFIRM_SUMMARY_AND_HANDOFF_ALIGNMENT

## Purpose

Align Intake V4 **Confirm / Summary / Quote Handoff** with canonical backend analysis, material, lighting, nesting, and readiness signals so operators see quote-relevant truth before draft quote creation.

## Audit source

- `docs/audit/INTAKE_V4_E2E_UTILITY_AND_UI_ALIGNMENT_PBL.md`
- Verdict: **PARTIAL PASS backend / FAIL Confirm utility**
- Workspace: `IV4-4B172FD4` (`0f300dcf-0b77-4fc1-affd-6e2a20329804`)

## Before / after

| Area | Before | After |
|------|--------|-------|
| Confirm summary | Generic: Layers 3, Față/cant none/standard_aluminum, single geometry line | Six operational blocks: SVG structure, finish/material, geometry (gross vs plexiglas), lighting, nesting, warnings |
| Geometry area | `A 0.691 m²` unlabeled (layer gross) | Gross `0.6907 m²` + quoteable plexiglas `0.5834 m²` labeled separately |
| Quote handoff badge | `ready_for_quote_preview` implied creatable | `REVIEW_REQUIRED` / `QUOTE_HANDOFF_BLOCKED` when backend blockers present |
| Handoff gate | ProductSystem binding only | `GET /quote-handoff-preview` uses same `evaluate_v4_quote_handoff_blockers` as create-draft-quote |

## Backend canonical values (PBL fixture)

- layers = 3, child parts = 11, real letters = 10, artwork = 1, inner holes = 5
- plexiglas face breakdown = 0.5834 m²
- face_area_m2 gross = 0.6907 m²
- return material ≈ 15.47 ml, LED perimeter ≈ 11.63 m, CNC ≈ 13.62 m
- LED modules = 47 @ 1.44 W → 67.68 W → PSU 87.98 W → [100 W]
- artwork execution = needs_decision
- nesting = preview_only, task generation = dry_run_only

## UI changes

- `IntakeV4ConfirmOperationalSummary.tsx` — structured summary blocks
- `IntakeV4ConfirmStep.tsx` — fetches material breakdown, nesting, quote-handoff-preview; handoff disabled when blockers include artwork undecided
- `intakeV4ConfirmSummary.ts` — view-model builder (geometry, lighting sync, warnings)
- `intakeV4QuoteHandoffReadiness.ts` — blocker formatting and badge labels

## Quote handoff gate alignment

- New endpoint: `GET /api/v1/intake-v4/workspaces/{id}/quote-handoff-preview?client_analysis_hash=`
- Wraps `evaluate_v4_quote_handoff_blockers` (no quote policy change)
- UI `canSubmit` requires `handoff_allowed === true`
- Checkboxes remain visible only when handoff truly allowed; copy clarifies they do not resolve artwork undecided

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_commercial_quote.py::TestIntakeV4CommercialQuoteHandoff::test_quote_handoff_preview_mirrors_create_blockers -q
```

Result: **1 passed**

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4ConfirmSummary.test.ts src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx
```

Result: **9 passed**

## Runtime smoke

### API (workspace `0f300dcf-0b77-4fc1-affd-6e2a20329804`)

- layers=3, real_letters=10, inner_holes=5
- face_area=0.6907, plexiglas=0.5834
- led_perimeter≈11.63, cnc≈13.62, return≈15.47
- `quote-handoff-preview`: handoff_allowed=false, status=REVIEW_REQUIRED, blockers=`artwork_execution_undecided:Layer_x0020_1`

### UI browser

Frontend `:3000` was not reachable during smoke (timeout). Re-verify manually:

`http://localhost:3000/intake-v4-app/0f300dcf-0b77-4fc1-affd-6e2a20329804/operator` → Confirm step.

Expected: operational blocks above, REVIEW_REQUIRED badge, disabled draft quote button, no quote/order creation.

## Files changed

- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_commercial_quote_service.py`
- `backend/routers/intake_v4_workspaces.py`
- `backend/tests/test_intake_v4_commercial_quote.py`
- `frontend/src/lib/intakeV4/intakeV4ConfirmSummary.ts`
- `frontend/src/lib/intakeV4/intakeV4ConfirmSummary.test.ts`
- `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.ts`
- `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts`
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4ConfirmOperationalSummary.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx`

## Boundary

- No quote policy change
- No quote/order/tasks creation in tests or smoke
- No ExecutionPlan / tasks_json / stock / CostEngine / Pricing Registry changes
- No V2/V3/Auth changes
- No push

## Remaining blockers

- Quote policy still blocks draft quote when artwork `needs_decision` (intentional — UI now surfaces this)
- Production task dry-run remains preview-only until dedicated build
- Full browser Confirm smoke pending when frontend dev server is up
