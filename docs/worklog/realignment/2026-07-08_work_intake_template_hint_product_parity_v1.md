# Work Intake Template Hint Product Parity V1

Date: 2026-07-08

## Owner issue

Owner reported that Work Intake `/intake` -> `Cerere Noua` -> `Pas 2/3` -> `Hint Product System optional` was not speaking the same language as Product System.

Observed mismatch before fix:
- `Analyzer-first` already looked acceptable.
- `TPL-VOLUMETRIC-LETTERS_v2` was close, but did not explicitly carry the full Product System parity framing.
- `TPL-VOLUMETRIC-LOGO_v1` was presented with weaker wording and relied on stale/raw description semantics instead of clearly stating that it is still a Product Template candidate with `Work Intake NU`.

## Product System parity rule applied

Both runtime cards remain Product Templates.

- `TPL-VOLUMETRIC-LETTERS_v2`
  - Product Template
  - Activ pentru ofertare
  - Work Intake DA
  - root direct permis
- `TPL-VOLUMETRIC-LOGO_v1`
  - Product Template
  - Candidat compozitie
  - Work Intake NU
  - analyzer / linked composition only
  - root direct blocat pana la owner GO

No change was made to root activation, quote/order behavior, execution, DB, pricing, or Product System structure.

## Root cause

The Work Intake modal already consumed Product Template availability data, but the card UI rendered:
- raw `template.description`
- a minimal `quote_offerable` badge

It did not surface the richer parity semantics already available in the tracked frontend type contract:
- `product_system_role`
- `display_group`
- `ui_description`

## Before -> after modal copy

Before:
- Letters card relied on generic family + description presentation.
- Logo card allowed its meaning to collapse toward generic candidate wording and stale description tone.

After:
- `Analyzer-first`
  - `Recomandat`
  - `SVG-ul decide compozitia: logo, litere, sau litere + logo.`
- `TPL-VOLUMETRIC-LETTERS_v2`
  - `Product Template`
  - `Product Template activ pentru litere volumetrice. Porneste cerere directa pentru root-ul ofertabil curent.`
  - `Work Intake DA`
  - `Root direct: permis`
  - `Activ pentru ofertare`
- `TPL-VOLUMETRIC-LOGO_v1`
  - `Product Template`
  - `Product Template logo volumetric. Disponibil pentru analyzer / linked composition. Nu porneste oferta directa.`
  - `Work Intake NU`
  - `Root direct: blocat pana la owner GO`
  - `Candidat compozitie`

## Files changed

- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/components/workos/NewIntakeDialog.test.tsx`
- `docs/worklog/realignment/2026-07-08_work_intake_template_hint_product_parity_v1.md`

## Tests run

Focused frontend test:

```powershell
Set-Location frontend
npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx
```

Result:
- PASS
- 13 tests passed

## Runtime proof

### `/intake`

Verified in real browser from the running frontend/backend:
- modal reached `Pas 2/3`
- `Analyzer-first` remains recommended
- Letters card shows Product Template + Work Intake DA + direct root permitted
- Logo card shows Product Template + Work Intake NU + direct root blocked until owner GO
- Logo card wording no longer presents it as a lesser component object

### `/product-system`

Verified in real browser:
- `TPL-VOLUMETRIC-LETTERS_v2` displayed under products with `Produs ofertabil` and `Work Intake DA`
- `TPL-VOLUMETRIC-LOGO_v1` displayed under products with `In pregatire` and `Work Intake NU`
- Logo remains shown as product, not component

### `/intake-v6/IR-MRBMAK7Z/operator`

Verified in real browser:
- `Compozitie produs propusa` still shows `Litere volumetrice + logo volumetric`
- `Logo 1` still shows `Confirmat in Pasul 1`
- `Logo 2` still shows `Confirmat in Pasul 1`
- no standalone Logo root surfaced during this check

Could not confirm the owner-quoted PSU strings in the current runtime session:
- `Surse: 200W + 100W`
- `Sursa LED 12V / 2 buc / 67.2 EUR`

Those exact strings were not visible on the checked Review/Confirmare surfaces in this session.

## Forbidden scope confirmation

Not touched:
- Logo root activation
- standalone Logo request enablement
- component root / component quote semantics
- Quote / Order / Execution logic
- ProductAggregate / TaskGraph / ExecutionPlan
- DB / seed / migration
- pricing rate logic
- Product System redesign
- Work Intake flow redesign
