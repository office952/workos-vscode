# Intake V6 finish-save hydration boundary

## Context
- ReviewStep a fost deja stabilizat pe refetch domains, rehidratare diferențială și bugfix-urile post-stabilizare.
- Cleanup-ul anterior a confirmat că datoria tehnică principală rămasă este la front-end workspace hydration după `saveFinishSetup(...)`.
- Înainte de acest slice, `saveFinishSetup(...)` dispatch-uia același `PERSIST_SUCCESS` folosit și pentru persistarea analysis bundle.

## Cauza
- `saveFinishSetup(...)` din `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` apelează endpoint-ul `PUT /api/v1/intake-v6/workspaces/{workspace_id}/finish-setup` și primește înapoi un `IntakeV6WorkspaceResponse` complet.
- Backend-ul persistă `payload.finish_setup`, resetează `internal_draft_quote_confirmed`, aplică `apply_v6_pricing_preview_derived_state(payload_raw)`, recalculează `readiness_status` și întoarce workspace-ul complet actualizat.
- În front-end, `PERSIST_SUCCESS` trecea acest workspace prin `applyHydratedWorkspace(...)`, care poate rescrie `svg`, `svgSource`, `analyzerReport`, `layerRoleConfirmation`, `layerChips`, `localFileHash`, `unsavedAnalysis` și `currentStep` din payload.
- Pentru finish save, această rehidratare completă nu este necesară: analiza SVG și starea locală a analyzerului erau deja canonice pentru sesiunea curentă, iar mutația semantică ținea de `workspace.payload.finish_setup`, `readiness_status`, `status`, `updated_at` și derived payload asociat preview/pricing.

## Ce am modificat
- Am introdus o cale separată de reducer: `FINISH_SETUP_PERSIST_SUCCESS`.
- `saveFinishSetup(...)` dispatch-uie acum `FINISH_SETUP_PERSIST_SUCCESS`, nu `PERSIST_SUCCESS`.
- Am adăugat `applyFinishSetupPersistedWorkspace(...)` în reducer.
- Noua cale actualizează:
  - `workspace`
  - `error`
  - `phase`
  - `unsavedAnalysis`
  - `currentStep` derivat din readiness doar dacă utilizatorul nu este deja în `review` sau `confirm`
- Noua cale nu mai rehidratează din payload:
  - `svg`
  - `svgSource`
  - `analyzerReport`
  - `layerRoleConfirmation`
  - `layerChips`
  - `localFileHash`
  - `analyzerStatus`
  - `analyzerError`

## Ce am refuzat sa modific
- Nu am schimbat contractul backend al endpoint-ului `finish-setup`.
- Nu am refactorizat `PERSIST_SUCCESS` pentru analysis bundle; acela rămâne corect pentru persistarea analizei SVG.
- Nu am introdus refetch global și nu am readus `workspace.updated_at` ca trigger în ReviewStep.
- Nu am atins ProductAggregate, Task Graph, ExecutionPlan, Employee Mobile, DB migration, seed, pricing rewrite, CostEngine rewrite, CommercialPriceProposal rewrite sau snapshot-uri Quote/Order.
- Nu am modificat UI/UX.

## Fisiere atinse
- `frontend/src/lib/intakeV6/intakeV6Contracts.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`

## Teste
- `pnpm.cmd vitest run src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - passed
- `pnpm.cmd vitest run src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts src/lib/intakeV6/intakeV6FinishHydration.test.ts`
  - toate 3 suite-urile au trecut
- `get_errors` pe fișierele atinse
  - fără erori
- `pnpm.cmd exec tsc --noEmit --pretty false`
  - comanda s-a încheiat fără erori TypeScript afișate; în output a rămas doar warning-ul pnpm despre cheia `pnpm.overrides`

## Riscuri
- Endpoint-ul `finish-setup` continuă să întoarcă workspace complet; guard-ul este doar pe front-end reducer path. Asta este acceptabil pentru slice-ul mic, dar înseamnă că disciplina separării rămâne convențională în client.
- Dacă pe viitor backend-ul va introduce mutații semantice de analyzer în `finish-setup`, această cale dedicată ar trebui reevaluată.
- Nu există încă un test end-to-end pentru `useIntakeV6Workspace` care să acopere hook-ul complet, doar reducer coverage focalizat.

## Next safe step
- Dacă vrei să împingi boundary-ul un pas mai departe fără UI changes, următorul pas sigur este să introduci explicit în hook/reducer noțiunea de persist source (`analysis_bundle` vs `finish_setup`) și eventual un test de hook pentru dispatch path, fără a schimba contractele de UI sau API.