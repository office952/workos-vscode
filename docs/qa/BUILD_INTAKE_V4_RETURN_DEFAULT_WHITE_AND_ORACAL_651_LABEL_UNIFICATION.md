# BUILD_INTAKE_V4_RETURN_DEFAULT_WHITE_AND_ORACAL_651_LABEL_UNIFICATION

## Purpose

Default Intake V4 return/cant finish to **Alb** (`white_aluminum`) for new or missing values, and relabel the Oracal wrapped cant option from **Colantat** to **Oracal 651** in operator-facing UI.

## Owner decision

1. **Default cant = Alb** (`white_aluminum`) when no persisted `return_finish_type`.
2. **User-facing label** for `oracal_wrapped` / series 651 = **Oracal 651** (not Colantat).

Dropdown `TIP FINISAJ CANT`:

```txt
Alb
Negru
Auriu
Argintiu
Vopsit RAL
Oracal 651
```

## Default Alb — behavior

Applied only when value is **missing/empty** (not when persisted):

- New letter groups from analyzer
- New artwork rows from analyzer
- Empty global finish setup (Review fallback)
- Payload hydration without `return_finish_type` string

**Not overwritten:** `oracal_wrapped`, `mirror_silver`, `black_aluminum`, `standard_aluminum` (legacy), etc.

## Internal mapping (preserved)

| Internal | UI label |
|----------|----------|
| `white_aluminum` | Alb |
| `black_aluminum` | Negru |
| `gold_aluminum` | Auriu |
| `mirror_silver` / `standard_aluminum` | Argintiu |
| `ral_paint` / `painted` | Vopsit RAL |
| `oracal_wrapped` | Oracal 651 (+ color picker) |

## Files changed

| Area | File |
|------|------|
| Options + labels | `frontend/src/lib/intakeV4/intakeV4ReturnFinishOptions.ts` |
| Hydration bridge | `frontend/src/lib/intakeV4/intakeV4ReturnCantBridge.ts` |
| Letter groups | `frontend/src/lib/intakeV4/intakeV4LetterGroups.ts` |
| Artwork | `frontend/src/lib/intakeV4/intakeV4ArtworkFinish.ts` |
| Review defaults | `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` |
| Cant fields UI | `frontend/src/components/workos/intake-v4/IntakeV4ReturnCantFields.tsx` |
| Schema defaults | `backend/schemas/intake_v4.py` |

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4ReturnFinishOptions.test.ts src/lib/intakeV4/intakeV4ReturnCantBridge.test.ts src/lib/intakeV4/intakeV4LetterGroups.test.ts src/components/workos/intake-v4/IntakeV4ReturnCantFields.test.tsx
```

## Runtime smoke

Workspace `IV4-4B172FD4` — verify dropdown labels and Oracal 651 picker after frontend reload. Persisted PBL values (e.g. `oracal_wrapped`) remain on reload.

## Boundary

- No quote policy / order / tasks / stock / Pricing Registry / CostEngine / V2/V3 / Auth
- No DB migration of existing workspaces
- No push in this build
