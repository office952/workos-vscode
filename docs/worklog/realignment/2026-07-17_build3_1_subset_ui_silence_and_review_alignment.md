# Build 3.1 — Subset UI silence and Review alignment

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `3e2fc87` |
| End HEAD | *(filled after commit)* |
| Verdict | `BUILD3_1_SUBSET_UI_ALIGNMENT_COMPLETE_WITH_GUARDS` |

## Owner rejection (accepted as GO)

CANT-only downstream was correct, but UI still showed Iluminare/Montaj tabs, mounting blockers, and full-product-ish Confirmare. Build 3 visual closeout: **NU**.

## Root cause

1. **Tabs:** Configurare tab list always golden Finisaje/Iluminare/Montaj from contract; sold scope only hid fields inside tabs.
2. **Readiness:** `MOUNTING_SOLUTION_MISSING` came from capture/finish_setup prep signals without consulting `offer_scope` — **BACKEND_READINESS_SCOPE_LEAKAGE** (fixed at capture filter, not CSS-masked).
3. **Confirmare:** compact hint used full template `component_count` + unscoped modular pending lines.

## Chosen fixes

| Area | Fix |
|------|-----|
| Tabs | `filterReviewTabsBySoldScope` + clamp active tab after scope switch |
| Capture fatals | `intake_v6_subset_capture_filter.py` strips mounting/lighting/out-of-scope codes for `component_subset` |
| Read model | Same filter applied so Review banner matches readiness |
| Confirm | Scope summary mounted; hint = `Configurație: {preset}`; pending count scoped |
| SVG inputs | Operator keeps `intake-v6-svg-input`; preview/change use distinct test ids (intentional dual upload surfaces) |

## Files changed

- `frontend/src/lib/intakeV6/intakeV6SoldScopeVisibility.ts` (+ tests)
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/useIntakeV6FinalHandoff.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6FinalConfigurationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersFileConfirmPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.tsx`
- `backend/services/intake_v6_subset_capture_filter.py` (new)
- `backend/services/form_system_runtime_capture_read_model_service.py`
- `backend/services/intake_v6_canonical_readiness_service.py` (read-model already filters)
- `backend/tests/test_intake_v6_canonical_readiness_spine.py`
- Evidence + this worklog

## E2E workspaces (real SVG UI)

| Scope | Workspace | Tabs |
|-------|-----------|------|
| Full | `50c51bee-d199-4198-9257-e577d622f65a` | Finisaje+Iluminare+Montaj |
| FACE | `49f68a3c-4b9a-4336-9804-2a8f3b189580` | Finisaje only |
| CANT | `7d6931bf-282e-4358-9def-24c95680a49e` | Finisaje only; no mounting fatal |
| FACE+CANT | `ae170557-240c-465a-a5fa-cf467f7c44f1` | Finisaje only; adhesive ×1 |

Scope switch full↔CANT: PASS. Responsive CANT: PASS.

## Tests

- Vitest sold-scope tabs: PASS
- Pytest readiness spine + Build 1/3 isolation: PASS
- Playwright Build 3.1 E2E: PASS

## Guards / exclusions

- Confirm technical accordion may still list modular modules under „Detalii tehnice” (collapsed diagnostics).
- Full product still surfaces mounting readiness when prep active (expected).
- No PD/Aggregate/CPP/formula/price/schema changes.
- No Build 4.

## Next step

Owner visual re-acceptance for CANT-only + Confirmare. **STOP.**
