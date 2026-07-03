# BUILD: Volumetric Quote Finish / Depth / Readiness Alignment

## Problem summary

After WorkIntake V2 production rules, the classic volumetric quote/simulation form (`VolumetricLettersQuoteFlow`) was misaligned with stock white/black aluminum return/cant:

- RAL and tuburi vopsea appeared required without paint finish selected
- Right-side readiness contradicted the form (dual evaluators)
- Duplicate depth fields (`depth_mm` vs `return_depth_mm`) could diverge
- V2 multi-PSU planning was ignored by readiness while CostEngine still uses single `selected_psu_watts`

## Files changed

### Frontend

- `frontend/src/lib/volumetricQuoteInput.ts` — `effectiveReturnDepthMm`, paint gate in prefill warnings and step validation
- `frontend/src/lib/volumetricIntakeFormPrep.ts` — gated RAL/paint missing items, depth alias in simulate prep
- `frontend/src/lib/intakeReadinessStages.ts` — production RAL gate, `flowState` in simulation readiness, depth alias bypass
- `frontend/src/lib/volumetricQuoteFlowState.ts` — spec-aware defaults, depth sync, paint strip in payload, `isSimulateInputReady(spec)`
- `frontend/src/lib/volumetricFrontlitIntake.ts` — `hasValidPsuSelection`, V2 PSU in `collectFrontlitIntakeMissing`
- `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` — unified readiness, hidden paint fields, single depth label

### Backend

- `backend/services/volumetric_quote_input_policy.py` — `is_cant_ral_paint_enabled`, gated metadata warnings
- `backend/services/volumetric_quote_ready_policy.py` — gated RAL blockers, V2 PSU acceptance in geometry blockers

### Tests

- `frontend/src/lib/volumetricIntakeFormPrep.test.ts`
- `frontend/src/lib/intakeReadinessStages.test.ts`
- `frontend/src/lib/volumetricQuoteFlowState.test.ts`
- `frontend/src/lib/volumetricQuoteInput.test.ts`
- `frontend/src/lib/volumetricFrontlitIntake.test.ts`
- `backend/tests/test_volumetric_quote_input_policy.py`
- `backend/tests/test_volumetric_quote_ready_policy.py`

## RAL / paint gate behavior

**Canonical gate:** `volume_finish === "paint_after_face_miter_bond"` (`isCantRalPaintEnabled`).

| Mode | RAL | Tuburi | Blockers |
|------|-----|--------|----------|
| Stock cant (`volume_finish: "none"`, white/black `return_color`) | Not required | Not required | None for paint |
| Paint/RAL cant (`volume_finish: "paint_after_face_miter_bond"`) | Required when tubes > 0 | Required for simulate | RAL blocker if missing |

Stale `paint_tube_count` on stock cant is ignored/stripped — does not trigger RAL warnings or payload fields.

## Stock cant behavior

- Standard white/black return: no RAL, no tuburi, no paint operation in quote form UI
- `CostOptionsPanel` hides RAL and Tuburi vopsea unless paint mode is active
- Simulate payload strips `paint_tube_count`, `paint_ral_code`, `paint_ral_name` when paint mode is off

## Paint / RAL behavior

When `volume_finish: "paint_after_face_miter_bond"`:

- RAL and tuburi fields visible in classic quote form
- `paint_tube_count` required for simulate validation
- RAL required when tubes > 0 (frontend readiness + backend quote_gate)

## Depth canonical field decision

- **Operator label:** Adâncime cant / retur volumetric (mm)
- **Canonical:** `return_depth_mm` (30 / 60 / 80 / 100)
- **Alias:** `depth_mm` — accepted for legacy/envelope; synced to same value on edit and in simulate payload
- Single field in classic quote geometry section; both keys set in payload for CostEngine compatibility

## PSU readiness behavior

- **CostEngine pricing:** unchanged — still uses `selected_psu_watts` (single PSU)
- **Readiness:** satisfied when either:
  - `selected_psu_watts` is set, or
  - V2 planning: `psu_allocation_status === "ok"` and `psu_configuration.length > 0`
- Underpowered or missing PSU still warns

## Right panel readiness behavior

- Single source: `evaluateSimulationReadiness({ productSpec, flowState })`
- Rail “Date pentru simulare” and “Pentru simulare lipsesc” use the same evaluator
- No fallback to stale `prepSummary.missingForSimulate` without flow state
- No false RAL/tuburi blockers for stock cant

## Backend policy status

- `volumetric_quote_input_policy`: RAL metadata warning only when paint mode enabled
- `volumetric_quote_ready_policy`: RAL geometry/metadata blocker gated; V2 PSU combo accepted via `product_spec`
- `volume_finish` in quote_input or product_spec drives paint mode on backend

## Tests run

### Frontend (PASS)

```text
npm run lint — PASS
npx vitest run \
  src/lib/volumetricQuoteInput.test.ts \
  src/lib/volumetricQuoteFlowState.test.ts \
  src/lib/intakeReadinessStages.test.ts \
  src/lib/volumetricIntakeFormPrep.test.ts \
  src/lib/volumetricFrontlitIntake.test.ts
— 66/66 passed
```

### Backend (not run in this environment)

`python` / `py` not available on the build host. Policy tests updated:

- `backend/tests/test_volumetric_quote_input_policy.py`
- `backend/tests/test_volumetric_quote_ready_policy.py`

Run locally:

```bash
cd backend && python -m pytest tests/test_volumetric_quote_input_policy.py tests/test_volumetric_quote_ready_policy.py -q
```

## Remaining gaps

- **CostEngine multi-PSU pricing** — not implemented; V2 `psu_configuration` is planning/display only
- **LED strip pricing handoff** — future work
- **Classic cant vinyl path** — optional colantare cant not exposed in classic quote form
- **V2 paint/RAL cant UI** — paint path exists in spec model; V2 production stage only exposes stock white/black
- **Product001IntakeSpecEditor section 6** — still allows stale paint fields without `volume_finish` selector (classic intake; not changed in this build)
