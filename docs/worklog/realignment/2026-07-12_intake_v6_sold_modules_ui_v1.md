# Worklog — Intake V6 Sold Modules UI V1

**Date:** 2026-07-12
**Build:** `INTAKE_V6_SOLD_MODULES_UI_V1`
**HEAD before:** `6ae2d04`

## Purpose

Expose existing `offer_scope` contract in Intake V6 Step 1 so operators can choose full product or slice-1 component subset (FACE / RETURN-CANT / BACK).

## Files changed

- `backend/schemas/intake_v4.py` — `offer_scope` payload fields + `IntakeV4OfferScopeSaveRequest`
- `backend/schemas/intake_v6.py` — alias export
- `backend/services/intake_v6_workspace_service.py` — readiness gate + `save_offer_scope_for_intake_v6_workspace`
- `backend/routers/intake_v6_workspaces.py` — `PUT .../offer-scope`
- `backend/services/intake_v6_commercial_quote_service.py` — copy `offer_scope` into draft `quote_input`
- `backend/tests/test_intake_v6_offer_scope_persistence.py` — new
- `backend/tests/test_quote_snapshot_component_scope.py` — workspace payload origin case
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopePanel.tsx` — new panel
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopePanel.test.tsx` — new
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx` — mount panel
- `frontend/src/lib/intakeV6/intakeV6Api.ts` — `saveIntakeV6OfferScope`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` — `saveOfferScope`
- `frontend/src/lib/intakeV6/intakeV6Readiness.ts` — gates
- `frontend/src/lib/intakeV6/intakeV6Readiness.test.ts` — extended
- `frontend/e2e/intake-v6-offer-scope-ui-evidence.spec.ts` — screenshot capture
- `docs/qa/intake-v6-sold-modules-ui-v1/screenshots_index.md`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_offer_scope_persistence.py tests/test_quote_snapshot_component_scope.py::test_workspace_payload_offer_scope_without_quote_input -q
# 10 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6OfferScopePanel.test.tsx src/lib/intakeV6/intakeV6Readiness.test.ts
# 11 passed

npx --yes pnpm@8.10.0 run build
# PASS

git diff --check
# clean on task files
```

## Boundary

- No dynamic finish field hiding (V1.1)
- No ProductDefinition / Aggregate / pricing rule changes
- No DB migrations

## Next safe step

V1.1: hide Review finish zones by sold scope with finish_setup invalidation policy.
