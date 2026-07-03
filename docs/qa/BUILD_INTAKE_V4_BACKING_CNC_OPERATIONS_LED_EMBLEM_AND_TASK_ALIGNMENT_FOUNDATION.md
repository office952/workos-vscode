# BUILD: Intake V4 backing, CNC operations, emblem LED & task alignment foundation

## Purpose

Scoped foundation on `local/integration-pr4-plus-svg-path` after shared CNC model (`ea623c2`, `259d836`):

- Backing selector (none / Forex 10 mm no bevel / with bevel)
- CNC operation rows separate from material rows in material breakdown
- Shared LED area density (60 module/m²) for emblem lighting
- LED litere vs emblemă vs total separation
- Task dry-run gap documented (compatibility fallback mapping)

## Owner decisions (summary)

| Topic | Rule |
|-------|------|
| Față litere | Plexiglas 3 mm; debitare + șanfren față obligatoriu (operații separate) |
| Backing | Forex 10 mm optional: none / no bevel / with bevel |
| Forex CNC passes | 5 passes, `owner_pass_override=true` (not strict ceil(10/3.5)) |
| LED litere | Perimeter + pitch (250 mm) |
| LED emblemă | `ceil(outbox_area_m2 × 60)` — shared rule, not in template |
| Preview | No stock consumption, no tasks, no invented CNC rates |

## Implemented

### Backend

- `intake_v4_backing_mode_service.py` — `backing_mode` resolution vs layer-role fallback
- `shared_led_lighting_density_rules.py` — `LED_AREA_DENSITY_MODULES_PER_SQM = 60`
- `IntakeV4FinishSetup`: `backing_mode`, `emblem_lighting_mode`, letter/emblem/total LED counts
- Material breakdown: backing from finish, Plexiglas/Forex labels, `operation_rows` from shared CNC model
- `led_total_watts` consumable row: `informational_only` — no double cost with LED modules buc
- Pricing preview sync: emblem modules + backing geometry patch
- Task dry-run: compatibility fallback marker `legacy_parallel_mapping` (used only when `operation_rows` are unavailable)

### Frontend

- `IntakeV4BackingAndEmblemSection` in Review (backing + emblem lighting)
- `intakeV4BackingMode.ts`, `sharedLedLightingDensity.ts`
- Confirm summary: Plexiglas 3 mm față, backing/bevel labels, LED litere/emblemă/total
- Material breakdown: "Operații CNC — preview ofertare", station/skill/machine/pricing hints
- Geometry panel: "Perimetru LED litere / exterior"

### Docs

- `docs/architecture/LED_LIGHTING_DENSITY_RULES.md`
- This QA doc

## Pending

| Area | Status |
|------|--------|
| Task dry-run CNC | Still uses V3 catalog parallel mapping (`face_and_backing_cnc_cut` bundle); `cnc_preview_row_to_task_candidate_hints()` not wired into dry-run candidates |
| Production preview | Coherent quantities via shared model in material breakdown; full task preview split pending catalog bundle split |
| TPL-CNC-CUTTING-SERVICE UI | `build_cutting_service_preview_bundle()` exists; no operator UI |
| Runtime smoke PBL | Manual verification on `IV4-4B172FD4` recommended after stack start |

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_backing_mode.py tests/test_shared_led_lighting_density_rules.py tests/test_shared_cnc_operation_model.py -q
```

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4BackingAndEmblemSection.test.tsx src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

## Boundaries (confirmed)

- No quote/order/task creation
- No ExecutionPlan / `tasks_json`
- No stock consumption
- No Pricing Registry writes
- No CostEngine global changes
- No employee assignment
- No push (this build)

## LED cost double-count audit

- `led_modules` buc row: priced via registry when available
- `led_total_watts` W row: `price_source=informational_only`, `estimated_cost=None` — excluded from material total aggregation
- Watts retained for PSU calculation in finish sync

## Task-generator alignment

- **Material breakdown CNC source:** `shared_cnc_operation_model.build_volumetric_letters_cnc_operation_rows`
- **Task dry-run CNC source:** `operation_rows` canonical; compatibility fallback token `legacy_parallel_mapping` only when rows are missing.

## Next recommended build

Wire task dry-run CNC candidates from `operation_rows` / `cnc_preview_row_to_task_candidate_hints()` and split V3 catalog `face_and_backing_cnc_cut` into face/backing operation codes.

## Post-smoke fixes (FIX_INTAKE_V4_EMBLEM_LED_PSU_AND_BACKING_FOREX_MATERIAL_ROW)

### Emblem `area_lit` W/PSU recalculation

- Root cause: `estimated_led_watts` / `required_psu_watts` / `psu_configuration` treated as operator-set when they matched letter-only derived values; emblem modules updated but watts/PSU stayed stale.
- Fix: `sync_intake_v4_finish_lighting` detects stale letter-derived totals when emblem adds modules (or `area_lit`) and recalculates watts, required PSU (+30%), and auto PSU proposal from catalog.
- PBL expected with `area_lit`: 59 modules → 84.96 W → 110.45 W required PSU; adhesive 11.8 ml.

### Forex backing material fallback

- Root cause: `backing_area_m2` missing on PBL quote geometry; CNC backing ops appeared but `forex_backing` material row omitted.
- Fix: `resolve_backing_material_area_m2()` — when backing active, fallback to **plexiglas sheet nesting quoteable area** (`sheet_face_qty`), warning `backing_area_fallback_used`. Gross `face_area_m2` only if nesting area unavailable.
- PBL expected: Forex 10 mm / spate litere ≈ 0.5834 m² (nesting quoteable), CNC rows unchanged.

### Task dry-run

- Compatibility fallback token **`legacy_parallel_mapping`** retained for backward compatibility (field alias added in newer builds).

### Runtime smoke (targeted, post-fix)

- Workspace `IV4-4B172FD4` — verify `area_lit` watts/PSU/adhesive and Forex material row with fallback warning.
- Backend restart required if stack was stale pre-`ddfa6c1`.
