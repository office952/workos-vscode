# FIX_INTAKE_V4_PRODUCTION_PREVIEW_TECHNICAL_LABEL_CLEANUP

## Root cause

Production handoff material jobs displayed raw `quantity_basis` tokens (e.g. `perimeter_with_waste`) as subtitles. Material breakdown already mapped some tokens locally; production preview did not.

## Tokenuri curățate (UI only — chei interne neschimbate)

| Token intern | Label operator |
|--------------|----------------|
| `perimeter_with_waste` | Cant / volum pentru preț (+20% pierdere) |
| `sheet_nesting_role_split_quote_estimate` | Nesting placă — estimare ofertă |
| `led_modules_perimeter_pitch_estimate` | Module LED — estimare după perimetru |
| `psu_configuration_quote_estimate` | Sursă LED — estimare ofertă |

Unknown `*_quote_estimate` → **Estimare ofertă** (nu afișăm snake_case).

## Implementare

- Shared formatter: `frontend/src/lib/intakeV4/intakeV4QuantityBasisLabels.ts`
- Used by `IntakeV4MaterialBreakdownPanel` and `IntakeV4ProductionHandoffPreviewPanel`
- No formula / quantity / cost changes

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuantityBasisLabels.test.ts src/components/workos/intake-v4/IntakeV4ProductionHandoffPreviewPanel.test.tsx src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

## Runtime smoke

PBL `IV4-4B172FD4` — production preview material jobs show operator labels; no raw `perimeter_with_waste` in UI.

## Boundary

No quote/order/tasks, ExecutionPlan, tasks_json, stock, Pricing Registry, CostEngine, quote policy, V2/V3/Auth. No push in this build.
