# BUILD_INTAKE_V4_LIGHTING_MODULE_WATTAGE_SELECTION

## Purpose

Allow Intake V4 operators to select LED module wattage (0.75 W / 1.00 W / 1.44 W) in **ILUMINARE (job-level)** so lighting consumption and PSU sizing reflect production choices.

## Motivation

Generic “Module LED + Warm white” was insufficient for quoting and production prep. Operators must pick module power; previews must recalculate instantly.

## Data model

Persisted on `finish_setup` (existing field + derived counters):

| Field | Role |
|-------|------|
| `led_module_power_w` | Operator selection: `0.75`, `1.0`, or `1.44` (default **1.44**) |
| `led_module_count` | Derived from outer letter perimeter @ 250 mm pitch |
| `estimated_led_watts` | `led_module_count × led_module_power_w` |
| `required_psu_watts` | `estimated_led_watts × 1.30` (30% reserve) |
| `psu_configuration` | Auto from catalog `[60, 100, 160, 200] W` |

Legacy `0.72 W` (V2) normalizes to **0.75 W** on V4. Invalid values snap to **1.44 W**.

## Formulas

```text
led_module_count = ceil(led_perimeter_ml × 1000 / 250)
estimated_led_watts = led_module_count × module_wattage
required_psu_watts = estimated_led_watts × 1.30
psu_configuration = minimal combination from [60, 100, 160, 200] W
```

LED perimeter uses **outer letter perimeter only** — inner holes do not affect module count.

## UI (Intake V4 Review step)

Section **Iluminare (job-level)**:

- Selector **Putere modul LED**: 0.75 / 1.00 / 1.44 W
- Preview shows: perimetru, module count, putere modul, consum LED, PSU cu rezervă 30%, propunere surse
- Changing wattage recalculates preview before save

## PBL reference values (`pbl-layere.svg`, 47 modules)

| Module W | Consum LED | PSU necesar (30%) | Propunere surse |
|----------|------------|-------------------|-----------------|
| 1.44 | 67.68 W | 87.98 W | 100 W |
| 1.00 | 47.00 W | 61.10 W | 100 W |
| 0.75 | 35.25 W | 45.83 W | 60 W |

## Material breakdown / pricing input

- `led_modules` row shows wattage in display name
- `led_total_watts` consumable row (W) for quote preview
- Pricing input includes `led_module_power_w`, `module_wattage`, `led_module_count`, `estimated_led_watts`, `required_psu_watts`, `psu_configuration`

No invented unit prices — missing registry prices remain warnings.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_lighting_module_wattage_selection.py tests/test_intake_v4_pbl_pricing_completeness.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4LedLighting.test.ts src/lib/intakeV4/intakeV4FinishLighting.test.ts
```

## Boundary

- No quote policy change
- No quote/order/task creation
- No ExecutionPlan / `tasks_json`
- No stock consumption
- No Pricing Registry / CostEngine global changes
- No V2/V3/Auth changes
- No push (local commit only)

## Files changed

- `backend/services/intake_v4_led_lighting_service.py` (new)
- `backend/services/intake_v4_pricing_preview_sync_service.py`
- `backend/services/intake_v4_pricing_input_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/schemas/intake_v4.py`
- `backend/tests/test_intake_v4_lighting_module_wattage_selection.py` (new)
- `frontend/src/lib/intakeV4/intakeV4LedLighting.ts` (new)
- `frontend/src/lib/intakeV4/intakeV4FinishLighting.ts`
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/lib/intakeV4/intakeV4FinishPayloadSync.ts`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`
- Frontend tests
