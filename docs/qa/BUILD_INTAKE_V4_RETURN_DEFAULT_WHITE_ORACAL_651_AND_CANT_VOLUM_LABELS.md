# BUILD_INTAKE_V4_RETURN_DEFAULT_WHITE_ORACAL_651_AND_CANT_VOLUM_LABELS

## Purpose

Align Intake V4 operator UI for cant / volum finish with owner wording: default **Alb** for missing values, **Oracal 651** instead of **Colantat**, and **cant / volum** instead of **return** in all user-facing labels. Internal `return_*` fields and payloads remain unchanged.

## Owner decisions

1. **Default cant / volum = Alb** (`white_aluminum`) when no persisted value — never overwrite saved selections.
2. **Colantat → Oracal 651** in dropdown, summaries, warnings, and material breakdown display names (`oracal_wrapped` + series 651 internally).
3. **return → cant / volum** in operator UI (titles use **Cant / volum** where appropriate).

## Internal mapping preserved

| Internal | Operator label |
|----------|----------------|
| `white_aluminum` | Alb |
| `black_aluminum` | Negru |
| `gold_aluminum` | Auriu |
| `mirror_silver` / `standard_aluminum` | Argintiu |
| `ral_paint` | Vopsit RAL |
| `oracal_wrapped` (+ `651`) | Oracal 651 |
| `same_as_face` / `none` / `unspecified` | legacy internal only |

Fields unchanged: `return_finish_type`, `return_oracal_code`, `return_oracal_name`, `return_material`, API payloads.

## Files changed

### Frontend

- `frontend/src/lib/intakeV4/intakeV4ReturnFinishOptions.ts` — default constant, cant/volum label constants, Oracal 651 labels
- `frontend/src/lib/intakeV4/intakeV4ReturnCantBridge.ts` — hydrate missing → `white_aluminum`
- `frontend/src/lib/intakeV4/intakeV4LetterGroups.ts` / `intakeV4ArtworkFinish.ts` — new row defaults
- `frontend/src/components/workos/intake-v4/IntakeV4ReturnCantFields.tsx` — dropdown + picker labels
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` — global cant / volum fallback section
- `frontend/src/components/workos/intake-v4/IntakeV4ConfirmOperationalSummary.tsx` — confirm summary labels
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx` — perimeter label
- `frontend/src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.tsx` — intro text
- `frontend/src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.tsx` — intro text
- Tests: `IntakeV4ReturnCantFields.test.ts`, `intakeV4ReturnFinishOptions.test.ts`, `intakeV4ReturnCantBridge.test.ts`, `intakeV4LetterGroups.test.ts`

### Backend (display labels only)

- `backend/services/intake_v4_finish_truth_service.py` — `format_intake_v4_return_finish_operator_label`, default `white_aluminum`
- `backend/services/intake_v4_material_breakdown_service.py` — cant / volum material row display names
- `backend/schemas/intake_v4.py` — schema defaults `white_aluminum` (prior commit)
- Tests: `test_intake_v4_finish_truth.py`, `test_intake_v4_material_breakdown.py`

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4ReturnFinishOptions.test.ts src/lib/intakeV4/intakeV4ReturnCantBridge.test.ts src/lib/intakeV4/intakeV4LetterGroups.test.ts src/components/workos/intake-v4/IntakeV4ReturnCantFields.test.tsx
# 14 passed

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_finish_truth.py tests/test_intake_v4_material_breakdown.py::TestIntakeV4FinishStateTruthMaterialBreakdown -q
# 9 passed
```

## Runtime smoke (PBL `IV4-4B172FD4`)

Manual checklist on Review / Confirm with dev stack:

1. Dropdown **Tip finisaj cant / volum**: Alb, Negru, Auriu, Argintiu, Vopsit RAL, Oracal 651 — no Colantat, no Return.
2. Oracal 651 opens **Culoare Oracal 651 cant** picker; warning **Culoare Oracal 651 nedecisă.**
3. Confirm Summary: **Cant / volum litere**, **Cant / volum total**, artwork line uses **cant / volum**.
4. Persisted workspace values preserved on reload (PBL has saved finishes — not reset to Alb).
5. Fresh / missing value defaults to Alb (unit tests + new workspace path).

No quote, order, tasks, ExecutionPlan, stock consumption exercised in this build.

## Boundary

- UI wording + default only — no quote policy, Pricing Registry, CostEngine global, V2/V3/Auth, DB migration, or aggressive field renames.
- Consumables logic (`aa2fdf1`) unchanged except shared operator label paths in material breakdown display names.
- No push in this build.

## Next steps

- Optional: extend Confirm Step integration test for rendered summary labels.
- Frontend Typecheck Debt Audit (repo-wide TS gate).
