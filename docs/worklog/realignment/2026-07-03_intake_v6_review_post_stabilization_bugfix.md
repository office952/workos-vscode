# Intake V6 Review post-stabilization bugfix

## Problema
- ReviewStep a rămas cu buguri post-refactor după stabilizarea pe refetch domains și rehidratare diferențială.
- În UI, la modificări pe LED / backing / finisaje apărea toast-ul `Salvare finisaje esuata` cu eroarea `Cannot read properties of null (reading 'markupPercent')`.
- ReviewStep mai conținea call site-uri pe vechea semnătură pentru `markLocalFinishChanged(...)` și `updateForm(...)`.
- `Task preview producție` și `OrderBoundTaskReadiness` nu erau refresh-uite coerent pentru toate domeniile relevante.

## Cauza
- După save, ReviewStep citea `commercial_inputs` din payload prin `readIntakeV6OfferCommercialInputs(...)`, care poate întoarce `null` când backend-ul nu persistă încă acea structură.
- Codul salva rezultatul în `nextCommercialInputs` și îl trecea mai departe către `serializeIntakeV6OfferCommercialInputs(...)`, ceea ce ducea la acces pe `markupPercent` din `null`.
- Refactorul de semnături lăsase câteva call site-uri vechi fără `domains`, deci ReviewStep putea rupe runtime-ul în zone mai puțin frecvent utilizate.
- Refetch mapping-ul țintit nu includea `taskPreview` și nici un trigger dedicat pentru `orderBoundReadiness` pe domeniile care chiar influențează preview-urile respective.

## Fișiere citite
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLightingSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OrderBoundTaskReadinessPanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`

## Fișiere modificate
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`

## Fix aplicat
- Am normalizat `nextCommercialInputs` după save cu `resolveIntakeV6OfferCommercialDefaults(...)`, nu cu reader-ul nullable, astfel încât ReviewStep să aibă mereu o structură comercială validă înainte de serialize/compare/update state.
- Am eliminat call site-urile rămase pe vechea semnătură:
  - `markLocalFinishChanged()` fără domenii nu mai există.
  - `updateForm(patch)` fără `options.domains` nu mai există în ReviewStep.
- Am completat maparea domenii -> preview groups ca `taskPreview` să fie refresh-uit pentru domeniile care afectează contractul său API: `lighting`, `face_finish`, `artwork_finish`, `backing`, plus cele deja existente `template` și `sheet_footprint`.
- Am adăugat un refresh group dedicat `orderBoundReadiness` și am legat fetch-ul de `previewRefresh.orderBoundReadiness`, fără revenire la `workspace.updated_at` global.

## Teste rulate
- `get_errors` pe:
  - `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
  - `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.ts`
  - `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`
  - rezultat: fără erori.
- `pnpm.cmd vitest run src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`
  - încercat după modificări; terminalul din sesiune nu a returnat output utilizabil.
- `pnpm.cmd exec tsc --noEmit --pretty false`
  - încercat după modificări; terminalul din sesiune nu a returnat output utilizabil.

## Verificare vizuală
- Ruta verificată: `/intake-v6/IR-MR2MP11C/operator`
- Pas verificat: `Pasul 2 din 3 - review`
- Acțiuni executate live:
  1. `Sistem LED`: `Module LED` -> `Banda LED`
  2. `Sistem LED`: `Banda LED` -> `Module LED`
  3. `Putere modul`: schimbată pe altă valoare disponibilă
  4. `Spate litere`: schimbat pe `Forex 10 mm cu sanfren`
  5. `Adaos %`: modificat în panoul comercial din dreapta
- Rezultat observat:
  - nu a apărut toast `Salvare finisaje esuata`
  - nu a apărut eroarea `Cannot read properties of null (reading 'markupPercent')`
  - selecturile au rămas stabile
  - pagina nu a făcut refresh mare
  - `Calcul live` a rămas funcțional și prețul oficial s-a actualizat la schimbările testate
  - `Detalii tehnice` au rămas accesibile; `Task preview producție` și `Pregătire generare taskuri producție` au rămas populate după save

## Ce a rămas
- În verificarea live, `Task preview` și `OrderBoundTaskReadiness` au rămas prezente și coerente, dar pentru valorile testate nu s-a observat o schimbare textuală explicită în readiness. Triggerul de refresh a fost totuși legat corect în cod.
- Terminalul integrat din sesiune nu a oferit output utilizabil pentru `vitest` și `tsc`, deci validarea executabilă completă rămâne parțială.

## Ce NU am făcut
- Nu am schimbat UI/UX, layout sau texte vizibile în afara comportamentului existent.
- Nu am reintrodus refetch global bazat pe `workspace.updated_at`.
- Nu am făcut refactor mare în ReviewStep.
- Nu am atins ProductAggregate, Task Graph, ExecutionPlan, Employee Mobile, DB migration, seed, pricing rewrite, CostEngine rewrite, CommercialPriceProposal rewrite sau snapshot-urile Quote/Order.

## Forbidden scope check
- Confirmat: niciun element din scope-ul interzis nu a fost modificat.

## Dead pieces check
- Nu am făcut cleanup de piese moarte în afara zonei atinse; m-am limitat la bugfix-ul strict din ReviewStep și helperul de refetch domains.