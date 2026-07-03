# HOTFIX: WorkIntake V2 primary edit route (TPL-VOLUMETRIC-LETTERS)

## Problem

From **Work Intake** list, the primary edit action (**Instrumentează Comanda**) always opened the classic `/intake/:id` form, even for `TPL-VOLUMETRIC-LETTERS` intakes where **WorkIntake V2** is the active operator flow per architecture lock (`6c52e9f`).

## Route before / after

| Context | Before | After |
|---------|--------|-------|
| Volumetric intake primary CTA (list panel) | `/intake/{code}` | `/intake-v2/{code}` |
| Non-volumetric intake primary CTA | `/intake/{code}` | `/intake/{code}` (unchanged) |
| New intake with `litere_volumetrice` family | `/intake/{code}` | `/intake-v2/{code}` |
| Legacy route | `/intake/:id` | **Still exists** — secondary link from V2 |

## Template detection rule

Uses existing `shouldUseVolumetricIntakePage` / `intakeEditUsesWorkIntakeV2`:

- `confirmedTemplateCode === TPL-VOLUMETRIC-LETTERS`, **or**
- no confirmed template and `productFamily` is litere volumetrice (`isLitereVolumetriceFamily`)

Route param: **intake code** (`IR-…`, `WI-…`) — same as `WorkIntakeV2` loader (`intakes.find(r => r.id === id)`).

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/volumetricIntakeRoute.ts` | `resolveIntakeEditPath`, path builders, primary label helper |
| `frontend/src/lib/volumetricIntakeRoute.test.ts` | Routing helper tests |
| `frontend/src/pages/WorkIntake.tsx` | Primary + ready-for-quote actions use resolver |
| `frontend/src/pages/WorkIntake.routing.test.tsx` | List panel navigation tests |
| `frontend/src/components/workos/NewIntakeDialog.tsx` | Pass `productFamily` to `onCreated` for post-create routing |
| `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx` | Legacy link label + V2 subtitle |
| `frontend/src/pages/WorkIntakeV2.tsx` | Legacy fallback link label |

## Legacy fallback behavior

- `/intake/:id` **not removed** — `IntakeDetail` + volumetric workspace unchanged.
- V2 header link: **Formular legacy (compatibilitate)** → `/intake/{code}`.
- No second primary button on list; legacy is not promoted as equal to V2.

## Tests run

```text
npx vitest run src/lib/volumetricIntakeRoute.test.ts src/pages/WorkIntake.routing.test.tsx src/pages/WorkIntakeV2.test.tsx
npm run lint (changed TS files)
```

## Remaining gaps

- **ClientWorkspace** / **Dashboard** links still use `/intake/:id` — out of scope for this hotfix.
- Direct navigation / bookmarks to `/intake/:id` still open classic form (intentional legacy path).
- No auto-redirect from `IntakeDetail` → V2 on direct URL load (avoid breaking deep links).
