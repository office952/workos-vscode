# BUILD_INTAKE_V4_RETURN_FINISH_OPTIONS_RAL_AND_ORACAL_651_ALIGNMENT

## Purpose

Simplify Intake V4 **Cant / Volum — Tip finisaj cant** to operator-facing choices aligned with production language, while preserving legacy payload compatibility.

## Before / after options

| Before (V2 `ARTWORK_RETURN_FINISH_OPTIONS` in V4) | After (V4 only) |
|-----------------------------------------------------|-----------------|
| La fel ca fața | *(removed from UI)* |
| Colantat Oracal | **Colantat** |
| RAL vopsit | **Vopsit RAL** |
| Aluminiu alb | **Alb** |
| Aluminiu negru | **Negru** |
| Aluminiu oglindă/argintiu | **Argintiu** |
| Aluminiu standard (stoc) | **Argintiu** (legacy mapping) |
| Nespecificat | *(removed from UI)* |
| — | **Auriu** (new UI; `gold_aluminum` token) |

## Internal mapping

| UI | `return_finish_type` | Extra persisted fields |
|----|----------------------|-------------------------|
| Alb | `white_aluminum` | — |
| Negru | `black_aluminum` | — |
| Auriu | `gold_aluminum` | `materialCode=gold` in cant bridge |
| Argintiu | `mirror_silver` | — |
| Vopsit RAL | `ral_paint` | `return_oracal_code` + `return_oracal_name` (RAL code) |
| Colantat | `oracal_wrapped` | `materialCode=651`, `return_oracal_code` (Oracal 651 color) |

### Legacy display (not offered as new options)

- `standard_aluminum` → Argintiu
- `painted` / `ral_paint` → Vopsit RAL
- `oracal_wrapped` → Colantat Oracal 651
- `same_as_face` / `none` → legacy warning label

## V2 RAL source reused

- `ColorRegistrySelect` with `filter={{ system: "RAL", usageScope: "return" }}` — same component/registry as V2 `LetterGroupReturnCantFields`
- Oracal 651 via `ColorRegistrySelect` with `series: "651"` — no 641 series in V4 cant UI

## UI surfaces updated

- `IntakeV4ReturnCantFields` — new V4-only control (letter groups, artwork, global fallback)
- `IntakeV4LetterGroupFinishesSection`, `IntakeV4ArtworkFinishSection`, `IntakeV4ReviewStep`
- `intakeV4ConfirmSummary` — user-friendly cant labels

## Backend compatibility

- Schema: optional `return_oracal_code` / `return_oracal_name` on artwork + global finish setup; `return_oracal_name` on letter groups
- `intake_v4_finish_adapter`: RAL code preserved on painted returns; `gold_aluminum` treated as raw material
- No Pricing Registry / CostEngine / quote policy changes

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_return_finish_adapter.py -q
```

Result: **2 passed**

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4ReturnFinishOptions.test.ts src/components/workos/intake-v4/IntakeV4ReturnCantFields.test.tsx
```

Result: **7 passed**

## Runtime smoke

Manual on workspace `IV4-4B172FD4` → Review → Cant / volum:

- Dropdown shows only: Alb, Negru, Auriu, Argintiu, Vopsit RAL, Colantat
- Colantat shows Oracal 651 color picker + warning if color missing
- Vopsit RAL shows RAL registry selector
- Alb/Negru/Auriu/Argintiu — no RAL/Oracal extra inputs

## Boundary

- No quote/order/tasks, ExecutionPlan, tasks_json, stock consumption
- V2/V3/Auth unchanged (`ARTWORK_RETURN_FINISH_OPTIONS` untouched)
- No push

## Remaining blockers

- `gold_aluminum` shares generic return material pricing with other raw aluminum finishes until dedicated rates exist
- Dedicated Oracal color still optional with warning (not blocking save)
