# FIX_LIGHTING_MODULE_COUNT_REAL_RUNTIME_PARITY_WITH_V2

## Purpose

Complete Intake V3 Operator Lighting runtime flow for `TPL-VOLUMETRIC-LETTERS`: controlled module power, geometry-based module count suggestion (V2 formula), explicit unavailable-geometry messaging, and volumetric front-lit defaults — without backend contract or PSU allocator changes.

## Problem observed (runtime / screenshot)

On real Operator Workspace Lighting tab:

- `Module power (W)` was a free empty input
- `Module count` was empty
- `LED system` required manual selection
- No geometry suggestion panel
- Badge: `NEEDS MODULE SETUP`
- `modules_per_letter` looked like a primary field though it is not used for calculation

Prior build `BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES` (`38320df`) implemented derivation logic and tests, but runtime still felt manual because:

1. UI did not constrain module power to V2 options
2. No message when geometry perimeter was missing (silent null suggestion)
3. Volumetric template still showed generic illumination / LED system controls
4. Real dev workspace lacks classified letter perimeter in geometry snapshot

## Owner clarification (integrated)

- Current template: illumination for **front-lit letter face only**
- Other illumination variants → separate templates (out of scope)
- Module power options: **0.72 W**, **1 W**, **1.44 W**
- V2 perimeter formula is canonical for module count
- `modules_per_letter` is not calculation source

## V2 audit findings

| Topic | V2 behavior |
|-------|-------------|
| Module count formula | `ceil(letter_perimeter_m × 1000 / 100)` via `computeLedModuleCountFromPerimeter()` |
| LED pitch | 75 mm module + 25 mm gap = **100 mm** (`VOLUMETRIC_LED_PITCH_MM`) |
| Scope | Job-level total letter perimeter, not per-letter |
| Module power | `LED_MODULE_POWER_OPTIONS`: 0.72 / 1 / 1.44 W; default **1.44 W** |
| LED system | V2 front-lit intake uses `led_modules` (UI label "Module LED") |
| `modules_per_letter` | Not used for module count derivation |
| PSU reserve (V2) | 15% (`PSU_HEADROOM_RATIO`) — V3 intentionally uses 30% (unchanged here) |
| Tests | `lightingPlanning.test.ts`, `volumetricFrontlitIntake.test.ts`, `volumetricQuoteInput` helpers |

## V3 audit — root cause

| Question | Answer |
|----------|--------|
| Why no suggestion in runtime? | `buildLightingModuleCountSuggestion()` returned null — real workspace geometry snapshot has **no** `total_letter_perimeter_ml` / face perimeter |
| Missing geometry data or wiring bug? | **Both**: wiring incomplete (no unavailable message, free module power input, generic template UX); dev data lacks classified perimeter |
| `state.geometryMetrics` on real workspace? | Yes, `snapshot_available=true`, but perimeters empty |
| Why empty perimeter? | Path perimeter classification `classification_available=false`, layer roles / face cutting not classified |
| Lighting tab loads geometry? | Yes — `lighting: ["geometry"]` lazy load |
| `buildLightingModuleCountSuggestion()` called? | Yes in `IntakeV3OperatorLightingTab` |
| Why silent before fix? | UI rendered `null` suggestion with no explanation |

Runtime probe (2026-06-19):

```
GET /api/v1/intake-v3/workspaces/e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf/geometry-metrics-snapshot
  snapshot_available=True, total_letter_perimeter_ml=null, geometry_status=geometry_partial

GET .../geometry-path-perimeter-classification
  classification_available=False, classification_status=missing
```

## Fix applied

### Frontend

1. **`lightingModuleCountDerivation.ts`**
   - Perimeter fallback chain: `total_letter_perimeter_ml` → `face_cutting_perimeter_ml` → `cutting_perimeter_ml` → snapshot classification → path classification response
   - `resolveLightingGeometryPerimeterState()` for loading / available / unavailable messaging

2. **`operatorLightingPlanForm.ts`**
   - Re-export `LED_MODULE_POWER_OPTIONS`; validate controlled power on save
   - `applyVolumetricLettersLightingFormDefaults()` — frontlit + modules + 1.44 W when empty
   - `lightingStatusLabel()` — `Apply module suggestion` when suggestion exists but count empty

3. **`IntakeV3OperatorLightingSetupCard.tsx`**
   - Module power **select** (0.72 / 1 / 1.44 W)
   - Volumetric scope note + fixed LED modules (face)
   - Geometry suggestion panel with pitch + Apply
   - Amber unavailable message when perimeter missing
   - Hide `modules_per_letter` for volumetric template

4. **`IntakeV3OperatorLightingTab.tsx`**
   - Pass template code, path classification, geometry loading state
   - Apply volumetric defaults after plan load

### Backend

No changes.

## Tests

### Frontend unit

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/lightingModuleCountDerivation.test.ts src/lib/intakeV3/operatorLightingPlanForm.test.ts
```

Result: **22 passed**

### Frontend app

```powershell
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx -t "lighting|Lighting|geometry"
```

Result: **3 passed** (setup form, suggestion apply, geometry unavailable message)

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q
```

Result: **36 passed**

## Runtime smoke

| Check | Result |
|-------|--------|
| Backend `/health` | 200 |
| Frontend `:3000` | 200 |
| Real workspace geometry snapshot | `snapshot_available=true`, perimeter **missing** |
| Path perimeter classification | `classification_available=false` |
| Expected UI after fix | Module power select + defaults + **geometry unavailable message** (not silent) |
| Suggestion on real workspace | **Not yet** — requires classified face perimeter in Geometry tab |

PSU regression (unit): 120×1.44 W → 224.64 W required @30% → **260 W** PSU; 186×1.44 W → **360 W** — unchanged allocator.

## Boundary confirmations

- No CostEngine changes
- No inventory mutation / StockMovement
- No ExecutionTask / ExecutionPlan
- No PO / SupplierOrder
- No UI Atoms recomposition
- No reserve 30% vs 15% change
- No PSU allocator change
- Materials read-only preserved
- Quote guarded preserved
- Technical route preserved

## Remaining / next steps

1. **Dev workspace data**: classify face cutting layers in Geometry so perimeter populates (`layer_role_confirmation` + path classification)
2. **Owner decision**: reserve 30% (V3) vs 15% (V2) — documented, not changed
3. After operator confirms perimeter + Apply suggestion flow on real data → visual acceptance / Atoms 3-step

## Proposed commit message

```
fix(intake-v3): show lighting module suggestions from geometry
```

(No commit performed — awaiting explicit approval.)
