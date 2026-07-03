# BUILD_INTAKE_V4_BACKING_GATE_AND_CNC_UI_DECISION

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `ebcc898` — fix(intake-v4): align CNC perimeter and bevel pass policy |
| Build date | 2026-06-22 |
| Push | **No** |

## Purpose

Close IV4-46499080 blocker: CostEngine ran `back_cut` (phantom **57.26 EUR**) when backing layer was absent and operator had not confirmed Forex backing.

## Root cause

1. Template `comp_spate_litere` always priced `back_cut` via `perimeter_pass_linear_meter` when `cnc_cutting_perimeter_ml` was present.
2. Intake V4 pricing input never set `backing_present=false` explicitly.
3. No `quote_input_line_gate` rule for backing — unlike `face_finish_type`, `illumination_enabled`, etc.
4. Material breakdown already omitted Forex (no `backing_area_m2`); only CostEngine operation + `MAT-SPATE-PVC-LITERE` were ungated.

## Fix (deterministic gate)

| Layer | Change |
|-------|--------|
| `seed_build4_templates.py` | `back_cut` + `MAT-SPATE-PVC-LITERE`: `formula_params.gate = {"backing_present": True}` |
| `quote_input_line_gate.py` | Skip when `gate.backing_present` and `is_backing_present_for_costing(qi)` is false → `gate:backing_absent` |
| `volumetric_quote_input_policy.py` | `is_backing_present_for_costing`: explicit `backing_present` key; V4 `intake_source` without key → false; legacy V2/V3 unset → true |
| `intake_v4_pricing_input_service.py` | Resolve backing from confirmed `layer_role_setup` layer with `confirmed_role=backing`; patch `backing_present`, `backing_material`, `backing_thickness_mm`, force `back_bevel_enabled=false` when absent |

No CostEngine registry, Pricing Registry, ExecutionPlan, or `tasks_json` changes.

## Mandatory audit answers

1. **Where does `back_cut` start?** Template seed `comp_spate_litere` → CostEngine `build_execution_layers_from_components` → formula `perimeter_pass_linear_meter` on workcenter `CNC_ROUTER`.
2. **What activates it?** Previously: presence of `cnc_cutting_perimeter_ml` in quote_input. Now additionally: `is_backing_present_for_costing(qi) == true`.
3. **What was missing in IV4 quote input?** Explicit `backing_present=false` when no confirmed backing layer.
4. **Payload to skip `back_cut`:** `backing_present=false` (V4 always sets this); `back_bevel_enabled=false` default.
5. **Gate location:** pricing input patch + template `formula_params.gate` + `quote_input_line_gate` (CostEngine already calls this — no CostEngine refactor).
6. **Existing conditional pattern?** Yes — `gate.face_finish_type`, `gate.illumination_enabled`, `conditional=paint_finish`, etc.
7. **V2 / QuoteWizard:** V2 sets `back_bevel_enabled` via production spec; backing assumed when key absent (legacy default true). Gate does not break `FULL_QUOTE_INPUT` baseline tests.
8. **V2 compatibility:** Legacy quotes without `backing_present` still run `back_cut`; only explicit `backing_present=false` or V4 patch blocks.

## IV4-46499080 before / after

Workspace: `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2` (IV4-46499080)

| Item | Before (ebcc898) | After (this build) |
|------|------------------|-------------------|
| Backing layers | 0 | 0 |
| `backing_present` | unset | **false** |
| `face_cnc_cut` | ~38.17 EUR (2 passes × 12.725 ml × 1.5) | unchanged |
| `back_cut` | **57.26 EUR phantom** | **skipped** (`gate:backing_absent`, line_total=0) |
| Forex material breakdown | absent | absent |
| `face_cnc_cut` | 38.175 EUR | **38.175 EUR** (unchanged) |

Summary for IV4-46499080:

- **Before:** `back_cut` phantom = **57.26 EUR**
- **After:** `backing_present=false`; `back_cut` skipped / `gate:backing_absent`; `face_cnc_cut` remains **38.175 EUR**; Forex material remains **absent**
| `MAT-SPATE-PVC-LITERE` in CostEngine | could price from face area | skipped with same gate |

## Behavior matrix

### Backing absent / not confirmed

- `backing_present=false`, `back_bevel_enabled=false`
- `back_cut`: not applicable
- Forex material: not applicable
- Face CNC: active (2 passes default face bevel policy)

### Backing present, no bevel

- `backing_present=true`, `back_material=FOREX_10MM`, `back_bevel_enabled=false`
- `cnc_cutting_perimeter_ml=12.725`, passes=3
- `back_cut` = 12.725 × 3 × 1.5 = **57.2625 EUR**

### Backing present, 7 mm bevel

- `backing_present=true`, `back_bevel_enabled=true`, `back_bevel_depth_mm=7`
- passes=5 (3 cut + 2 bevel)
- `back_cut` = 12.725 × 5 × 1.5 = **95.4375 EUR**

## UI status / gap

**Not in this commit.** Review step should eventually show read-only:

- Backing: absent / not confirmed
- Back cut: not applicable
- Face CNC: active, 2 passes
- Backing bevel: not applicable

Operator backing selector + `back_bevel_enabled` capture remain a follow-up build.

## Task dry-run

`forex_backing_cutting` material job is derived from material breakdown rows only. With no Forex row, CNC backing task is not activated from material jobs. Catalog may still list operation keys as candidates in alignment docs — inactive when backing missing.

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py -q
# 22 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pricing_input.py -q
# 7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_quote_input_line_gate.py -q
# 6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_operation_unit_pricing.py::TestUnitPricingCostEngine -q
# 19 passed, 1 failed (test_painting_72_eur — pre-existing, unrelated to backing gate)

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_operation_unit_pricing.py::TestVolumetricUnitPricingIntegration -q
# 2 failed (painting + VINYL_APPLICATION registry — pre-existing)
```

Backing/CNC subset: **PASS**.

## Quote final readiness

Phantom `back_cut` removed for IV4-46499080-like payloads — **quote final can continue past this blocker**.

Separate UI hash-sync gate may still block draft quote on IV4-46499080 (documented in REAL_FILE test pack); that is unrelated to backing CNC costing.

**UI backing / șanfren V4** (operator selector + read-only Review panel) remains a **next build**.

## Files changed

- `backend/services/volumetric_quote_input_policy.py`
- `backend/services/quote_input_line_gate.py`
- `backend/seeds/seed_build4_templates.py`
- `backend/services/intake_v4_pricing_input_service.py`
- `backend/tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py`
- `backend/tests/test_intake_v4_pricing_input.py`
- `backend/tests/test_volumetric_operation_unit_pricing.py`
- `backend/tests/test_quote_input_line_gate.py`
- `docs/qa/BUILD_INTAKE_V4_BACKING_GATE_AND_CNC_UI_DECISION.md`
- `docs/qa/BUILD_INTAKE_V4_REAL_FILE_PRODUCTION_DECISION_TEST_PACK.md`

## Boundary

No ExecutionPlan, `tasks_json`, real task creation, stock consumption, CostEngine registry, Pricing Registry, or frontend UI in scope.
