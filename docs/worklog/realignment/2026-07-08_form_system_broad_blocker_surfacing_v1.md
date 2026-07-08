# Form System Broad Blocker Surfacing V1

## HEAD before

- `9fd4f61`

## Problema gasita

Lantul Form System Backbone Awareness era coerent semantic, iar broad/global blockers ramaneau active in model.

Problema ramasa era strict de prezentare in panou:

- lista principala de blockers afisa doar primele 4 randuri
- broad/global blocker-ul `PRODUCT_TRUTH_INCOMPLETE` putea fi impins in afara slice-ului vizibil
- field-level blockers relaxate puteau fi vazute direct, in timp ce broad/global blocker-ul activ putea ramane ascuns

Aceasta nu era o problema de readiness semantics, ci de surfacing UI local.

## Files changed

- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx`
- `docs/worklog/realignment/2026-07-08_form_system_broad_blocker_surfacing_v1.md`

## Behavior before

- `blockerRows` pastrau broad/global blockers in model
- panoul afisa doar `model.blockerRows.slice(0, 4)`
- broad/global blocker-ul putea sa nu fie vizibil daca intra dupa primele 4 randuri

## Behavior after

- lista principala de blockers ramane trunchiata local la primele 4 randuri
- daca exista broad/global blockers care nu intra in slice-ul vizibil, panoul afiseaza explicit o subsectiune mica `Product Truth blockers`
- `PRODUCT_TRUTH_INCOMPLETE` sau echivalent broad/global blocker ramane vizibil explicit in panou daca exista in model
- field-addressed blockers rezolvate de runtime confirmation pot ramane relaxed
- niciun blocker nu este sters din model
- nu se schimba readiness semantics si nu se creeaza Product Truth readiness finala

## Tests run

Din `frontend/`:

```powershell
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneAwareness.test.ts
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx
```

Rezultate:

- panel suite passed: `7` tests
- awareness suite passed: `14` tests
- panel suite rerun passed after awareness check

## Runtime smoke

### `/intake-v6/IR-MRBMAK7Z/operator`

- Review loads
- Form System Backbone panel appears
- panelul poate fi expandat
- Product Truth boundary message ramane vizibil
- SVG field rows arata runtime confirmation unde exista
- matching field-addressed blockers apar relaxed
- broad/global blocker este vizibil explicit prin sectiunea `Product Truth blockers`
- `PRODUCT_TRUTH_INCOMPLETE` este vizibil explicit
- blocker rows nu sunt sterse; panoul raporteaza `Readiness / blockers (9)`
- composition ramane `Litere volumetrice + logo volumetric`

### `/intake`

- `Cerere Noua` modal opens

### `/product-system`

- `Letters: offerable`
- `Logo: candidate / not Work Intake`

## PSU row observation

- In runtime smoke-ul actual, randul `Sursa LED 12V / 2 buc / 67,20 EUR` nu a fost vizibil.
- Observatia a fost doar raportata.
- Nu a fost reparata in acest task, deoarece nu este aceeasi cauza directa cu broad blocker surfacing.

## Forbidden scope confirmation

Acest slice nu modifica:

- Product Truth write
- ProductDefinition write
- Pricing
- Quote / Order
- Execution
- ProductAggregate
- TaskGraph
- ExecutionPlan
- DB / seed / migration
- Logo root
- component root
- component quote
- backend

## Remaining risks

- Broad/global surfacing este rezolvat local in panou, dar lista principala ramane tot o vedere trunchiata, iar contextul complet depinde in continuare de modelul awareness
- PSU row visibility ramane o observatie deschisa separata, fara legatura directa cu acest fix

## Recommended next step

- `WORKOS_SYSTEMS_READINESS_AUDIT_BEFORE_NEXT_IMPLEMENTATION_V1` cu ZIP + screenshots + docs pack