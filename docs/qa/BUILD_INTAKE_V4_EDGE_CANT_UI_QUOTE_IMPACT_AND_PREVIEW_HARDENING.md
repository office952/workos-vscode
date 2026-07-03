# BUILD_INTAKE_V4_EDGE_CANT_UI_QUOTE_IMPACT_AND_PREVIEW_HARDENING

## Purpose

Harden Intake V4 operator UI, Confirm Summary, Material Breakdown, and Production Preview after the shared edge/cant rules foundation (`0d57ebd`, `f749fa0`). Preview-only — no quote/order/task creation.

## Scope

- Review cant/volum decision card + Oracal 651 quote impact panel
- Confirm Summary cant/volum section
- Material Breakdown grouping and edge row metadata
- Production handoff / task dry-run edge cant preview sections
- Selector hydration + pending-save clarity for backing / emblem / cant finish
- Handoff `face_and_backing_cnc_cut` warning clarification
- Tests + docs

## Files changed

### Frontend

- `frontend/src/lib/intakeV4/intakeV4EdgeCantDisplay.ts` (+ tests)
- `frontend/src/lib/intakeV4/intakeV4EdgeCantDryRunDisplay.ts` (+ tests)
- `frontend/src/lib/intakeV4/intakeV4FinishHydration.ts` (+ tests)
- `frontend/src/lib/intakeV4/intakeV4ConfirmSummary.ts`
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantQuoteImpactPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantOperationPreviewSection.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ConfirmOperationalSummary.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4ProductionHandoffPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4TaskGenerationDryRunPanel.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`

### Backend

- `backend/services/intake_v4_template_option_contract_service.py` (warning text)
- `backend/tests/test_intake_v4_edge_cant_ui_hardening.py`

### Docs

- `docs/architecture/SHARED_EDGE_CANT_RULES.md`
- `docs/qa/BUILD_PRODUCTSYSTEM_SHARED_EDGE_CANT_RULES_FOUNDATION_AND_INTAKE_V4_ALIGNMENT.md` (cross-ref)

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_edge_cant_ui_hardening.py tests/test_shared_edge_cant_rules.py tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_cnc_operation_dry_run.py tests/test_intake_v4_backing_mode.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts src/lib/intakeV4/intakeV4FinishHydration.test.ts src/lib/intakeV4/intakeV4EdgeCantDryRunDisplay.test.ts src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

Targeted suites: PASS.

## Boundary / non-goals

No ExecutionPlan, tasks_json, stock consumption, Pricing Registry, Color Registry, CostEngine, employee assignment, or quote/order creation.

## Next steps

- Optional: material breakdown preview endpoint accepting draft `finish_setup` to remove pending-save lag without save
- PBL runtime UI smoke on live stack when operator validates

## Follow-up fix

See `docs/qa/FIX_INTAKE_V4_OWNER_ORACAL_PRICE_SOURCE_GUARD_FOR_EDGE_CANT.md` — composite owner Oracal `price_source` guard for edge/cant registry override bleed.
