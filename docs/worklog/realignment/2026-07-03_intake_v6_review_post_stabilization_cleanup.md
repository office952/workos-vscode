# Intake V6 Review post-stabilization cleanup

## Context
- ReviewStep a fost stabilizat în două etape:
  - refetch domains + rehidratare diferențială
  - bugfix post-stabilizare pentru `markupPercent`, call-site-uri vechi, `taskPreview` sub-refreshed și `OrderBoundTaskReadiness` stale
- Auditul local a confirmat că direcția este bună, dar au rămas câteva datorii mici care pot crea confuzie sau pot favoriza regresii.

## Ce am găsit
- `footprintOverrideRevision` din ReviewStep era dead state după trecerea la `bumpPreviewRefresh(["sheet_footprint"])`.
- `intakeV6PersistedReviewRefetchKey` a rămas export compat/legacy și testat cu limbaj care putea sugera fals că acesta este mecanismul curent pentru ReviewStep.
- `PERSIST_SUCCESS` din workspace reducer încă face workspace-level hydration prin `applyHydratedWorkspace(...)` după finish save; asta este recomandare de follow-up, nu un fix sigur de micro-slice.
- Nu există infrastructură ușoară deja pregătită pentru un test direct de ReviewStep/autosave fără setup suplimentar mai mare.
- Pattern-urile comerciale active relevante sunt în ReviewStep și ConfirmStep; helperul legacy nu mai este folosit de ReviewStep în producție.

## Ce am modificat
- Am eliminat dead state-ul `footprintOverrideRevision` din ReviewStep și incrementarea lui din `handleSheetFootprintOverrideSaved`.
- Am păstrat refresh-ul țintit actual pe `bumpPreviewRefresh(["sheet_footprint"])`.
- Am marcat explicit `intakeV6PersistedReviewRefetchKey` ca export legacy compat în `intakeV6FinishHydration.ts`.
- Am aliniat testul vechi din `intakeV6FinishHydration.test.ts` ca să descrie helperul ca mecanism legacy compat, nu ca mecanism curent al ReviewStep.
- Am adăugat acoperire locală în `intakeV6OfferCalculator.test.ts` pentru normalizarea sigură a inputurilor comerciale când persisted commercial inputs lipsesc sau există.

## Ce am lăsat doar recomandare
- Nu am separat `finish-save hydration` de `analysis hydration` în `useIntakeV6Workspace.ts` / `intakeV6WorkspaceReducer.ts`.
- Motiv: schimbarea ar intra într-un refactor de reducer și contract de hydration care depășește slice-ul mic și sigur cerut acum.
- Recomandarea rămâne: o cale locală de finish-save hydration care să nu rehidrateze larg analyzer/workspace state dacă payload-ul de analiză nu s-a schimbat semantic.

## Fișiere atinse
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6FinishHydration.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishHydration.test.ts`
- `frontend/src/lib/intakeV6/intakeV6OfferCalculator.test.ts`

## Teste rulate
- Static diagnostics (`get_errors`) pe toate fișierele atinse: fără erori.
- `pnpm.cmd vitest run src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts src/lib/intakeV6/intakeV6FinishHydration.test.ts src/lib/intakeV6/intakeV6OfferCalculator.test.ts`
  - `intakeV6ReviewRefetchDomains.test.ts`: a rulat și a trecut.
  - `intakeV6FinishHydration.test.ts`: blocat de alias resolution existent în harness (`@/lib/intakeSvgContracts`).
  - `intakeV6OfferCalculator.test.ts`: blocat de alias resolution existent în harness (`@/lib/companyCommercialSettings`).
- `pnpm.cmd --dir frontend exec tsc --noEmit --pretty false`
  - comanda a întors doar warning-ul pnpm din sesiune, fără rezultat final utilizabil; nu o consider validare completă.

## Riscuri rămase
- `PERSIST_SUCCESS` încă trece prin workspace-level hydration și rămâne cea mai importantă datorie tehnică deschisă pe felia asta.
- Test harness-ul frontend are în continuare probleme de alias resolution care reduc valoarea validării automate locale pentru aceste teste.
- Nu există încă un test direct de ReviewStep/autosave.

## Next safe step
- Implementarea unui follow-up mic pe reducer/workspace hydration, separat de ReviewStep UI, cu test focalizat pentru finish-save care nu rescrie larg analyzer state când payload-ul de analiză nu s-a schimbat.