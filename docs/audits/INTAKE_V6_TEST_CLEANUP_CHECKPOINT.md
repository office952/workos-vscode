# WorkOS - Intake V6 Test Cleanup Checkpoint

## 1. Verdict

- Verdict: `PARTIAL`

Motivul verdictului este direct:

- build-ul frontend trece;
- testele V6 active si migrate in acest lot trec;
- runtime-ul Intake V6 stabilizat anterior nu a fost atins;
- dar a ramas in scope un singur test istoric cu naming `IntakeV4`, blocat de o decizie de ownership intre `intakeV6` si `svgAnalyzer`.

## 2. Inventar si rezultat pe categorii

- Teste migrate la V6: `49`
- Teste sterse: `76`
- Teste istorice ramase cu naming V4 in scope: `1`
- Build dupa cleanup: `PASS`
- Teste V6 active si migrate rulate explicit: `PASS`
- Repo-wide TypeScript stabilization: `NOT DONE`

### Interpretare

- `curatat`: shim-urile V6 care doar re-exportau teste V4 au fost eliminate.
- `curatat`: un set mic de teste de lib cu echivalent V6 clar a fost migrat.
- `blocked`: testul V4 ramas cere decizie de ownership intre `intakeV6` si `svgAnalyzer`, nu doar o migrare de naming.

## 3. Teste migrate la V6

- `frontend/src/lib/intakeV6/intakeV4AnalysisIdentity.test.ts` -> `frontend/src/lib/intakeV6/intakeV6AnalysisIdentity.test.ts`
  - Acopera hidratarea hash-ului de analiza si detectia de `unsavedAnalysis` pe fluxul activ V6.
- `frontend/src/lib/intakeV6/intakeV4Readiness.test.ts` -> `frontend/src/lib/intakeV6/intakeV6Readiness.test.ts`
  - Acopera blocarea / permiterea accesului in `review` pe baza persistentei analizei si a hash-ului sincronizat.
- `frontend/src/lib/intakeV6/intakeV4ReturnCantBridge.test.ts` -> `frontend/src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts`
  - Acopera mapping-ul finish-urilor de cant / volum pe bridge-ul compatibil folosit in fluxul activ V6.
- `frontend/src/lib/intakeV6/intakeV4WorkspaceReducer.test.ts` -> `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Acopera reducerul workspace V6: `ANALYZER_START`, `ANALYZER_READY`, hidratare din payload si persistenta hash-ului.
- `frontend/src/lib/intakeV6/intakeV4CncDryRunDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6CncDryRunDisplay.test.ts`
  - Acopera formatter-ele CNC dry-run active pe suprafata V6, inclusiv unitate, fallback de tarif si sursa preview.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDryRunDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6EdgeCantDryRunDisplay.test.ts`
  - Acopera formatter-ele edge-cant dry-run active pe suprafata V6, inclusiv unitate si sursa preview.
- `frontend/src/lib/intakeV6/intakeV4QuantityDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuantityDisplay.test.ts`
  - Acopera formatter-ele de cantitate active pe suprafata V6, inclusiv unitati discrete, rotunjire si eticheta de pierdere.
- `frontend/src/lib/intakeV6/intakeV4QuantityBasisLabels.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuantityBasisLabels.test.ts`
  - Acopera label-urile de quantity basis active pe suprafata V6, inclusiv maparea token-urilor de nesting, LED si PSU.
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts`
  - Acopera afisarea materialelor folosite live pe suprafata V6, inclusiv split-uri de materiale, costuri si fallback-uri.
- `frontend/src/lib/intakeV6/intakeV4MaterialQuoteReviewSnapshot.test.ts` -> `frontend/src/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot.test.ts`
  - Acopera snapshot-ul de review material quote si exportul text aferent pe suprafata V6.
- `frontend/src/lib/intakeV6/intakeV4SheetQuoteReviewDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetQuoteReviewDisplay.test.ts`
  - Acopera statusul de sheet quote review, motivele de manual review si filtrarea motivelor stale pe suprafata V6.
- `frontend/src/lib/intakeV6/intakeV4FaceFinishOptions.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.test.ts`
  - Acopera optiunile de face finish V6, inclusiv picker-ul de culoare, seriile Oracal si latimea implicita de rolă.
- `frontend/src/lib/intakeV6/intakeV4FinishLighting.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishLighting.test.ts`
  - Acopera sincronizarea de finish lighting V6, inclusiv PSU, strip length si split-ul litere/embleme.
- `frontend/src/lib/intakeV6/intakeV4FinishPolicy.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishPolicy.test.ts`
  - Acopera regulile de policy V6 pentru ascunderea finish-ului global si consumul de vinyl pe față.
- `frontend/src/lib/intakeV6/intakeV4LedLighting.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LedLighting.test.ts`
  - Acopera calculele LED V6 pentru module, wattaj si configuratia PSU.
- `frontend/src/lib/intakeV6/intakeV4FinishHydration.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishHydration.test.ts`
  - Acopera hidratarea finish-urilor persistate, detectia de pending-save si cheia de refetch pentru review.
- `frontend/src/lib/intakeV6/intakeV4FinishPayloadSync.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.test.ts`
  - Acopera sincronizarea payload-ului de finish din layer finishes si identitatea starii de finish.
- `frontend/src/lib/intakeV6/intakeV4PayloadHydrate.test.ts` -> `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.test.ts`
  - Acopera hidratarea starii analyzer-shaped din payload si rezolvarea pasului de readiness.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoffReadiness.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.test.ts`
  - Acopera blocker-ele, warning-urile si statusul UI pentru handoff readiness.
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.test.ts`
  - Acopera geometria de ofertare, warning-urile out-of-scope si fallback-ul intre geometria persistata si analyzer-ul local.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoff.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.test.ts`
  - Acopera maparea quote input-ului spre product spec si nav state-ul pentru QuoteWizard.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintSource.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetFootprintSource.test.ts`
  - Acopera optiunile de source pentru sheet footprint si afisarea valorii selectate.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintOverride.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetFootprintOverride.test.ts`
  - Acopera validarea override-ului de sheet footprint.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6EdgeCantDisplay.test.ts`
  - Acopera display-ul edge/cant, formula de cost, breakdown-ul pe layere si normalizarea grupurilor.
- `frontend/src/lib/intakeV6/intakeV4FaceBackPrepCostDraftDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay.test.ts`
  - Acopera cost draft display pentru face/back prep, verificarea perimetrului si fallback-urile de cost.
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LetterGroups.test.ts`
  - Acopera return finish-ul implicit pentru grupurile noi de litere.
- `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts`
  - Acopera labels, split-ul de operații și formatarea operator-facing pentru UI display.
- `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.test.ts`
  - Acopera bridge-ul activ V6 pentru confirmarea rolurilor de layer si maparea spre setup-ul persistabil V6.
- `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts` -> `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnosticBoundary.test.ts`
  - Acopera explicit boundary-ul V6 dintre analyzer-ul real si diagnosticul artwork/logo pentru warning-uri raster, mismatch Corel si fallback-uri fara report.
- `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6GeometryMetricDisplayBoundary.test.ts`
  - Acopera explicit boundary-ul V6 dintre analyzer-ul real, quote geometry si geometry metric display pentru perimetre, cant si fallback-ul de material breakdown.

## 4. Teste sterse

### 4.1. Shim-uri V6 sterse ca redundante

Aceste fisiere nu contineau teste reale, ci doar re-export de forma `export * from './intakeV4...test'`.
Ele adaugau zgomot, dublau naming-ul istoric si nu ofereau valoare separata fata de testul sursa.

- `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnostic.test.ts`
- `frontend/src/lib/intakeV6/intakeV6CncDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.test.ts`
- `frontend/src/lib/intakeV6/intakeV6EdgeCantDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6EdgeCantDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishHydration.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishPolicy.test.ts`
- `frontend/src/lib/intakeV6/intakeV6GeometryMetricDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LedLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LetterGroups.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot.test.ts`
- `frontend/src/lib/intakeV6/intakeV6NearestOracalColor.test.ts`
- `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuantityBasisLabels.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuantityDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetFootprintOverride.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetFootprintSource.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetQuoteReviewDisplay.test.ts`

### 4.2. Shim-uri V6 sterse si recreate ca teste V6 reale

Shim-ul a fost eliminat, iar fisierul a fost recreat ca test V6 nativ:

- `frontend/src/lib/intakeV6/intakeV6AnalysisIdentity.test.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.test.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
- `frontend/src/lib/intakeV6/intakeV6CncDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6EdgeCantDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuantityDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuantityBasisLabels.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetQuoteReviewDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishPolicy.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LedLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishHydration.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.test.ts`
- `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.test.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetFootprintSource.test.ts`
- `frontend/src/lib/intakeV6/intakeV6SheetFootprintOverride.test.ts`
- `frontend/src/lib/intakeV6/intakeV6EdgeCantDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LetterGroups.test.ts`
- `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.test.ts`

### 4.3. Teste V4 sterse ca duplicate legacy

Dovada pentru stergere:

- fie exista deja test V6 nativ care acopera comportamentul activ;
- fie testul V4 tocmai a fost migrat la nume si importuri V6;
- nu a fost lasat niciun gol de acoperire pe comportamentul activ validat in acest lot.

- `frontend/src/lib/intakeV6/intakeV4AnalysisIdentity.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6AnalysisIdentity.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4ClientSvgImport.test.ts`
  - Sters ca duplicat al testului canonic `intakeV6ClientSvgImport.test.ts`, care acopera aceleasi trei scenarii active.
- `frontend/src/lib/intakeV6/intakeV4Readiness.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6Readiness.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4ReturnCantBridge.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6ReturnCantBridge.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4WorkspaceReducer.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6WorkspaceReducer.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4CncDryRunDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6CncDryRunDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDryRunDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6EdgeCantDryRunDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4QuantityDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6QuantityDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4QuantityBasisLabels.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6QuantityBasisLabels.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6LiveMaterialsUsedDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4MaterialQuoteReviewSnapshot.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6MaterialQuoteReviewSnapshot.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4SheetQuoteReviewDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6SheetQuoteReviewDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FaceFinishOptions.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FaceFinishOptions.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FinishLighting.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FinishLighting.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FinishPolicy.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FinishPolicy.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4LedLighting.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6LedLighting.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FinishHydration.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FinishHydration.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FinishPayloadSync.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FinishPayloadSync.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4PayloadHydrate.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6PayloadHydrate.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoffReadiness.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6QuoteHandoffReadiness.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6QuoteGeometry.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoff.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6QuoteHandoff.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintSource.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6SheetFootprintSource.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintOverride.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6SheetFootprintOverride.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4OperatorRoutes.test.ts`
  - Sters ca `DELETE_DUPLICATE_LEGACY` dupa confirmarea ca `intakeV6OperatorRoutes.test.ts` acopera complet comportamentul si include fallback suplimentar.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6EdgeCantDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4FaceBackPrepCostDraftDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6FaceBackPrepCostDraftDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6LetterGroups.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6OperatorUiDisplay.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
  - Sters dupa migrarea 1:1 la `intakeV6LayerRoleBridge.test.ts`.
- `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
  - Sters dupa crearea testului canonic `intakeV6ArtworkLogoDiagnosticBoundary.test.ts` care acopera complet contractul boundary V6.
- `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
  - Sters dupa crearea testului canonic `intakeV6GeometryMetricDisplayBoundary.test.ts` care acopera complet contractul boundary V6.

## 5. Teste ramase cu naming V4

Aceste teste exista in continuare in scope. In faza curenta nu au fost sterse orb, deoarece fie testeaza contracte compat explicite, fie au ramas pentru o decizie separată de ownership in jurul `svgAnalyzer`.

### 5.1. Componente `intake-v6` ramase cu naming V4

După Lot 2C.3 nu mai există component tests cu naming `IntakeV4` în `frontend/src/components/workos/intake-v6`.

- component tests V4 ramase: `0`
- actiune urmatoare: nu mai este necesar un lot de componente; frontul ramas este doar trierea testelor de lib compat si relocation-ul `LayerRoleDisplay`.

### 5.2. Lib tests ramase cu naming V4

Pentru aceste fisiere:

- motiv: testeaza fie contracte compat justificate, fie un helper care cere task separat de relocation in scope-ul `svgAnalyzer`;
- actiune urmatoare: `BLOCKED_NEEDS_DECISION` doar pentru separarea finală intre compat coverage justificat si relocation de ownership.

- `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`

## 6. Validari

### Build

- `npm.cmd run build`: `PASS`

### Teste V6 tintite / active

- `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
- Status: `PASS`
- Rezultat: `6` fisiere, `26` teste

### Teste migrate validate separat

- `npm.cmd exec vitest run src/lib/intakeV6/intakeV6AnalysisIdentity.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts`
- Status: `PASS`
- Rezultat: `2` fisiere, `9` teste

### TypeScript global

- Ultimul rezultat repo-wide confirmat ramane `TSC_EXIT:2`.
- In sesiunea curenta de cleanup, comanda de rerulare a `tsc` nu a returnat output terminal utilizabil pentru o captură nouă completă, dar nimic din validările executabile din acest task nu a indicat o regresie în runtime-ul V6.
- Verdict pentru acest checkpoint: `NOT DONE`

### Scan final

- Scanul final al referintelor istorice a fost confirmat prin inventarul de fisiere ramas in scope.
- Clasificare:
  - `curatat`: shim-urile V6 redundante si duplicatele V4 migrate la V6
  - `ramas justificat`: `0` marcate explicit in acest lot
  - `ramas nejustificat`: `0` shim-uri cunoscute ramase
  - `blocked`: `6` teste V4 ramase, care necesita lot separat de migrare sau decizie

## Lib V4 Tests Inventory — IntakeV6 compat / svgAnalyzer boundary

- Verdict: `INVENTORY_ONLY`
- Count lib V4 tests at start: `31`
- Count lib V4 tests after task: `6`
- Component tests V4 remaining: `0`
- Lib tests V4 remaining: `6`

Nota:

- familiile si inventarul per-file de mai jos raman snapshot-ul istoric al auditului initial pe `31` fisiere; statusul curent dupa loturile ulterioare este sintetizat in count-urile de mai sus si in sectiunea `Lib Cleanup Batch A`.

Test families:

- `svgAnalyzer dependent`: `intakeV4ArtworkLogoDiagnostic.test.ts`, `intakeV4GeometryMetricDisplay.test.ts`, `intakeV4LayerRoleDisplay.test.ts`
- `compat justified`: `intakeV4ConfirmSummary.test.ts`, `intakeV4LayerRoleOptions.test.ts`, `intakeV4NearestOracalColor.test.ts`

Files classified `MIGRATE_TO_V6_NOW`:

- `0`

Files classified `KEEP_COMPAT_TEST_JUSTIFIED`:

- `3`
- `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`

Files classified `DELETE_DUPLICATE_LEGACY`:

- `0`

Files classified `BLOCKED_BY_SVG_ANALYZER_CONTRACT`:

- `4`
- `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
- `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`

Files classified `BLOCKED_NEEDS_RUNTIME_DECISION`:

- `0`

Per-file inventory:

- `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts` — tests `buildIntakeV4ArtworkLogoDiagnostic`; V6 module exists, no V6 test exists; imports `svgAnalyzer` and legacy SVG fixtures; active V6-adjacent behavior but through analyzer boundary; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `BLOCKED_BY_SVG_ANALYZER_CONTRACT`.
- `frontend/src/lib/intakeV6/intakeV4CncDryRunDisplay.test.ts` — tests CNC dry-run display formatters; V6 module exists, no V6 test exists; no `svgAnalyzer`; imports V4 helper directly; no legacy fixtures; covers active V6 display behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts` — tests `buildIntakeV4ConfirmSummary`; V6 module exists, no V6 test exists; no `svgAnalyzer`; imports V4 API payload types; uses legacy payload fixtures; covers compat payload summarization still exercised in V6 flow; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `KEEP_COMPAT_TEST_JUSTIFIED`.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDisplay.test.ts` — tests edge-cant display view-model helpers; V6 module exists, no V6 test exists; no `svgAnalyzer`; direct V4 helper import; no legacy fixtures; covers active V6 formatting logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDryRunDisplay.test.ts` — tests edge-cant dry-run formatters; V6 module exists, no V6 test exists; no `svgAnalyzer`; no legacy fixtures; active V6 behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4FaceBackPrepCostDraftDisplay.test.ts` — tests face/back prep draft display resolution; V6 module exists, no V6 test exists; no `svgAnalyzer`; imports compat API response type; no fixture file dependency; active V6 behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4FinishHydration.test.ts` — tests persisted finish selectors and pending-save detection; V6 module exists, no V6 test exists; no `svgAnalyzer`; uses legacy payload fixtures; covers persisted compat contract still present in V6 runtime; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `KEEP_COMPAT_TEST_JUSTIFIED`.
- `frontend/src/lib/intakeV6/intakeV4FinishPayloadSync.test.ts` — tests finish payload sync helpers; V6 module exists, no V6 test exists; no `svgAnalyzer`; imports V4 finish setup shape; no fixture files; covers active V6 sync behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts` — tests geometry metric display builder; V6 module exists, no V6 test exists; imports `svgAnalyzer`, layer-role confirmation and SVG fixtures; covers active metrics but through analyzer contract; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `BLOCKED_BY_SVG_ANALYZER_CONTRACT`.
- `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts` — tests layer-role confirmation bridge; V6 module exists, no V6 test exists; imports analyzer draft/types; no file fixtures but analyzer contract is direct; covers compat bridge behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `BLOCKED_BY_SVG_ANALYZER_CONTRACT`.
- `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts` — tests layer-role display rows and counts; V6 module exists, no V6 test exists; imports `svgAnalyzer` and SVG fixtures; covers active display behavior through analyzer output; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `BLOCKED_BY_SVG_ANALYZER_CONTRACT`.
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts` — tests layer-role option catalog parity; V6 module exists, no V6 test exists; no direct `svgAnalyzer` runtime dependency; uses shared option catalog as legacy fixture surface; covers compat label alignment; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `KEEP_COMPAT_TEST_JUSTIFIED`.
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.test.ts` — tests letter-group derivation and default return finish assignment; V6 module exists, no V6 test exists; no direct `svgAnalyzer` import in the test; uses lightweight mock report structures; covers active V6 helper behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.test.ts` — tests live-material row builders; V6 module exists, no V6 test exists; no `svgAnalyzer`; no legacy fixtures; covers active V6 display logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4MaterialQuoteReviewSnapshot.test.ts` — tests material quote snapshot builders and formatter text; V6 module exists, no V6 test exists; no `svgAnalyzer`; no fixture files; covers active V6 logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts` — tests nearest Oracal color matching and application helpers; V6 module exists, no V6 test exists; no `svgAnalyzer`; uses shared color registry data; active feature but still a compat color-contract reference; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `KEEP_COMPAT_TEST_JUSTIFIED`.
- `frontend/src/lib/intakeV6/intakeV4OperatorRoutes.test.ts` — tests operator route builders; V6 module exists and `frontend/src/lib/intakeV6/intakeV6OperatorRoutes.test.ts` already exists; no `svgAnalyzer`; no legacy fixtures; covers active V6 route-building semantics with only naming/prefix differences; duplicate V6 test: `yes`; TypeScript local errors: `none`; decision: `DELETE_DUPLICATE_LEGACY`.
- `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.test.ts` — tests operator UI display formatters; V6 module exists, no V6 test exists; no `svgAnalyzer`; no fixture files; covers active V6 behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4PayloadHydrate.test.ts` — tests hydration from persisted analyzer payload and readiness-step resolution; V6 module exists, no V6 test exists; no direct `svgAnalyzer` import; uses legacy payload contract fixtures; covers compat hydration boundary still consumed by V6 runtime; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `KEEP_COMPAT_TEST_JUSTIFIED`.
- `frontend/src/lib/intakeV6/intakeV4QuantityBasisLabels.test.ts` — tests quantity-basis label mapping; V6 module exists, no V6 test exists; no `svgAnalyzer`; no legacy fixtures; covers active V6 helper behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4QuantityDisplay.test.ts` — tests quantity/pricing formatters; V6 module exists, no V6 test exists; no `svgAnalyzer`; no fixture files; covers active V6 display logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.test.ts` — tests quote geometry extraction and warning resolution; V6 module exists, no V6 test exists; no direct `svgAnalyzer` import in the test body; uses mock analyzer-shaped data only; covers active V6 logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoff.test.ts` — tests quote input to product-spec and nav-state mapping; V6 module exists, no V6 test exists; no `svgAnalyzer`; no fixture files; covers active V6 logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4QuoteHandoffReadiness.test.ts` — tests blocker formatting and handoff UI status resolution; V6 module exists, no V6 test exists; no `svgAnalyzer`; no fixture files; covers active V6 readiness logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintOverride.test.ts` — tests sheet-footprint override validation; V6 module exists, no V6 test exists; no `svgAnalyzer`; no legacy fixtures; covers active V6 validation logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4SheetFootprintSource.test.ts` — tests sheet-footprint source options and selected-display resolution; V6 module exists, no V6 test exists; no `svgAnalyzer`; uses V4 API candidate types as lightweight fixtures; covers active V6 helper behavior; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.
- `frontend/src/lib/intakeV6/intakeV4SheetQuoteReviewDisplay.test.ts` — tests sheet quote review status and stale-snapshot reasoning; V6 module exists, no V6 test exists; no `svgAnalyzer`; uses V4 API candidate fixtures; covers active V6 review logic; duplicate V6 test: `no`; TypeScript local errors: `none`; decision: `MIGRATE_TO_V6_NOW`.

TypeScript filtered result:

- terminal command executed: `./node_modules/.bin/tsc.cmd -p tsconfig.app.json --noEmit --pretty false | Select-String ...`
- repo-wide `tsc` remains red outside this scope with `TSC_EXIT:2`
- local audit result for the migrated Lib 3 slice: `get_errors` on the `4` new V6 tests returned `No errors found`
- practical interpretation for this inventory: no file-specific TypeScript diagnostics were attributed to the migrated Lib 3 slice during this task; the blocking TypeScript surface remains outside these files or at broader repo level

svgAnalyzer dependency result:

- direct `svgAnalyzer` / analyzer-contract dependence identified in `4` files: `intakeV4ArtworkLogoDiagnostic.test.ts`, `intakeV4GeometryMetricDisplay.test.ts`, `intakeV4LayerRoleBridge.test.ts`, `intakeV4LayerRoleDisplay.test.ts`
- these files also rely on SVG fixtures or analyzer-shaped contracts and should not be migrated in the same lot as pure formatter/display helpers

Changes made:

- no runtime, UI, pricing, Product System, backend or component-test code was changed
- no legacy lib tests were deleted in this task
- updated this checkpoint with the lib-test inventory and classification only

Next recommended lot:

- `Lot Lib 1 — simple non-svg migrations`: `intakeV4CncDryRunDisplay.test.ts`, `intakeV4EdgeCantDryRunDisplay.test.ts`, `intakeV4QuantityDisplay.test.ts`
- hold `intakeV4OperatorRoutes.test.ts` as the first duplicate-removal candidate, but only in a dedicated cleanup lot after an explicit 1:1 proof pass against `intakeV6OperatorRoutes.test.ts`
- create a separate boundary task for the `svgAnalyzer` cluster; do not mix it with the simple lib migration lot

## Lot Lib 1 — Simple non-svg migrations

- Verdict: `PASS`

Teste migrate:

- `frontend/src/lib/intakeV6/intakeV4CncDryRunDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6CncDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDryRunDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6EdgeCantDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4QuantityDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuantityDisplay.test.ts`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/lib/intakeV6/intakeV4CncDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4EdgeCantDryRunDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4QuantityDisplay.test.ts`

Validari:

- `vitest Lot Lib 1`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6CncDryRunDisplay.test.ts src/lib/intakeV6/intakeV6EdgeCantDryRunDisplay.test.ts src/lib/intakeV6/intakeV6QuantityDisplay.test.ts`
  - Rezultat: `3` fisiere, `8` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
  - Observatie: au ramas warning-urile istorice CSS minify, dynamic-import/static-import si chunk-size, fara blocaj de build.
- `tsc global`: `NOT DONE`
  - repo-wide TypeScript ramane cunoscut cu `TSC_EXIT:2` din zone istorice din afara acestui lot
- `tsc Lot Lib 1`: `PASS`
  - `get_errors` pentru `intakeV6CncDryRunDisplay.test.ts`, `intakeV6EdgeCantDryRunDisplay.test.ts` si `intakeV6QuantityDisplay.test.ts` a returnat `No errors found`
  - nu au ramas diagnostice locale atribuite celor 3 teste migrate
- `scan final Lot Lib 1`: `PASS`
  - scanul pe fisierele V6 migrate nu a returnat markeri `intakeV4|IntakeV4|intake-v4|INTAKE_V4`
  - fisierele V4 corespondente nu mai exista

Count V4 tests ramas:

- `component`: `0`
- `lib`: `28`
- `total`: `28`

Probleme ramase:

- `tsc` repo-wide ramane rosu din zone istorice fara legatura cu Lot Lib 1
- testele lib V4 ramase sunt acum `28`, impartite in continuare intre fronturi `compat justified`, `duplicate legacy` si `svgAnalyzer` boundary

Urmatorul lot recomandat:

- `Lot Lib 2` numai pentru helper-e simple fara `svgAnalyzer`, de exemplu `intakeV4EdgeCantDisplay.test.ts`, `intakeV4FaceBackPrepCostDraftDisplay.test.ts`, `intakeV4QuantityBasisLabels.test.ts`

## Lot Lib 2 — Display, snapshot and labels migrations

- Verdict: `PASS`

Teste migrate:

- `frontend/src/lib/intakeV6/intakeV4QuantityBasisLabels.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuantityBasisLabels.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4MaterialQuoteReviewSnapshot.test.ts` -> `frontend/src/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot.test.ts`
- `frontend/src/lib/intakeV6/intakeV4SheetQuoteReviewDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetQuoteReviewDisplay.test.ts`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/lib/intakeV6/intakeV4QuantityBasisLabels.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.test.ts`
- `frontend/src/lib/intakeV6/intakeV4MaterialQuoteReviewSnapshot.test.ts`
- `frontend/src/lib/intakeV6/intakeV4SheetQuoteReviewDisplay.test.ts`

Validari:

- `vitest Lot Lib 2`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6QuantityBasisLabels.test.ts src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts src/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot.test.ts src/lib/intakeV6/intakeV6SheetQuoteReviewDisplay.test.ts`
  - Rezultat: `4` fisiere, `21` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
  - Observatie: au ramas warning-urile istorice CSS minify, dynamic-import/static-import si chunk-size, fara blocaj de build.
- `tsc global`: `NOT DONE`
  - repo-wide TypeScript ramane cunoscut cu `TSC_EXIT:2` din zone istorice din afara acestui lot
- `tsc Lot Lib 2`: `PASS`
  - `get_errors` pentru `intakeV6QuantityBasisLabels.test.ts`, `intakeV6LiveMaterialsUsedDisplay.test.ts`, `intakeV6MaterialQuoteReviewSnapshot.test.ts` si `intakeV6SheetQuoteReviewDisplay.test.ts` a returnat `No errors found`
  - nu au ramas diagnostice locale atribuite celor 4 teste migrate
- `scan final Lot Lib 2`: `PASS`
  - scanul pe fisierele V6 migrate nu a returnat markeri `intakeV4|IntakeV4|intake-v4|INTAKE_V4`
  - fisierele V4 corespondente nu mai exista

Count V4 tests ramas:

- `component`: `0`
- `lib`: `24`
- `total`: `24`

Probleme ramase:

- `tsc` repo-wide ramane rosu din zone istorice fara legatura cu Lot Lib 2
- testele lib V4 ramase sunt acum `24`, impartite in continuare intre fronturi `compat justified`, `duplicate legacy`, `svgAnalyzer` boundary si helper-e simple inca nemigrate

Urmatorul lot recomandat:

- `Lot Lib 3` numai pentru helper-e simple fara `svgAnalyzer`, de exemplu `intakeV4EdgeCantDisplay.test.ts`, `intakeV4FaceBackPrepCostDraftDisplay.test.ts`, `intakeV4LetterGroups.test.ts`

## Lot Lib 3 — Finish, lighting and policy migrations

- Verdict: `PASS`

Teste migrate:

- `frontend/src/lib/intakeV6/intakeV4FaceFinishOptions.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV4FinishLighting.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV4FinishPolicy.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishPolicy.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LedLighting.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LedLighting.test.ts`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/lib/intakeV6/intakeV4FaceFinishOptions.test.ts`
- `frontend/src/lib/intakeV6/intakeV4FinishLighting.test.ts`
- `frontend/src/lib/intakeV6/intakeV4FinishPolicy.test.ts`
- `frontend/src/lib/intakeV6/intakeV4LedLighting.test.ts`

Validari:

- `vitest Lot Lib 3`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6FaceFinishOptions.test.ts src/lib/intakeV6/intakeV6FinishLighting.test.ts src/lib/intakeV6/intakeV6FinishPolicy.test.ts src/lib/intakeV6/intakeV6LedLighting.test.ts`
  - Rezultat: `4` fisiere, `17` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
  - Observatie: au ramas warning-urile istorice CSS minify, dynamic-import/static-import si chunk-size, fara blocaj de build.
- `tsc global`: `NOT DONE`
  - repo-wide TypeScript ramane cunoscut cu `TSC_EXIT:2` din zone istorice din afara acestui lot
- `tsc Lot Lib 3`: `PASS`
  - `get_errors` pentru `intakeV6FaceFinishOptions.test.ts`, `intakeV6FinishLighting.test.ts`, `intakeV6FinishPolicy.test.ts` si `intakeV6LedLighting.test.ts` a returnat `No errors found`
  - nu au ramas diagnostice locale atribuite celor 4 teste migrate
- `scan final Lot Lib 3`: `PASS`
  - scanul pe fisierele V6 migrate nu a returnat markeri `intakeV4|IntakeV4|intake-v4|INTAKE_V4`
  - fisierele V4 corespondente nu mai exista

Count V4 tests ramas:

- `component`: `0`
- `lib`: `20`
- `total`: `20`

Probleme ramase:

- `tsc` repo-wide ramane rosu din zone istorice fara legatura cu Lot Lib 3
- testele lib V4 ramase sunt acum `20`, impartite in continuare intre fronturi `compat justified`, `duplicate legacy`, `svgAnalyzer` boundary si helper-e simple inca nemigrate

Urmatorul lot recomandat:

- lot separat, explicit, fara a amesteca `svgAnalyzer` cu helper-ele simple ramase

## Lib Cleanup Batch A — Hydration, payload, handoff, geometry-lite and route duplicate

- Verdict: `PARTIAL`
- Start count V4:
  - component: `0`
  - lib: `20`
  - total: `20`
- End count V4:
  - component: `0`
  - lib: `11`
  - total: `11`
- Lib 4 results:
  - migrated: `4`
  - blocked: `0`
  - deleted: `4`
  - vitest: `PASS` (`4` fisiere, `19` teste)
  - scan: `PASS`
- Lib 5 results:
  - migrated: `4`
  - blocked: `1` (`frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts` -> `BLOCKED_BY_SVG_ANALYZER_CONTRACT`)
  - deleted: `4`
  - vitest: `PASS` (`4` fisiere, `14` teste)
  - scan: `PARTIAL` (fisierele migrate sunt curate; markerii ramasi apartin fisierului blocat `intakeV4GeometryMetricDisplay.test.ts`)
- Route duplicate cleanup:
  - decision: `DELETE_DUPLICATE_LEGACY`
  - deleted: `1`
  - assertions moved: `0`
  - vitest: `PASS`
  - scan: `PASS`
- Validari finale:
  - V6 active: `PASS` (`6` fisiere, `26` teste)
  - build: `PASS`
  - tsc global: `NOT DONE` (ultimul status repo-wide confirmat ramane `TSC_EXIT:2`; rerularea Batch A nu a produs un transcript terminal nou stabil, dar nu a indicat regresii locale)
  - tsc Batch A: `PASS` (`get_errors` curat pe toate fisierele migrate; nu au aparut diagnostice locale in felia Batch A)
- Files migrated:
  - `frontend/src/lib/intakeV6/intakeV4FinishHydration.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishHydration.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4FinishPayloadSync.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4PayloadHydrate.test.ts` -> `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteHandoffReadiness.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteHandoff.test.ts` -> `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4SheetFootprintSource.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetFootprintSource.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4SheetFootprintOverride.test.ts` -> `frontend/src/lib/intakeV6/intakeV6SheetFootprintOverride.test.ts`
- Files deleted:
  - `frontend/src/lib/intakeV6/intakeV4FinishHydration.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4FinishPayloadSync.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4PayloadHydrate.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteHandoffReadiness.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4QuoteHandoff.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4SheetFootprintSource.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4SheetFootprintOverride.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4OperatorRoutes.test.ts`
- Files blocked:
  - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts` -> `BLOCKED_BY_SVG_ANALYZER_CONTRACT`
- Probleme ramase:
  - repo-wide `tsc` ramane rosu in afara scope-ului Batch A
  - au ramas `11` lib tests V4: `4` pe boundary `svgAnalyzer`, `3` compat-justified si `4` helper-e simple inca migrabile
  - scanul Lib 5 continua sa vada markeri V4 doar in fisierul blocat `GeometryMetricDisplay`
- Urmatorul front recomandat:
  - lot separat pentru helper-ele simple ramase: `EdgeCantDisplay`, `FaceBackPrepCostDraftDisplay`, `LetterGroups`, `OperatorUiDisplay`
  - task separat pentru boundary-ul `svgAnalyzer`
  - pastreaza distinct frontul `compat justified`

## Lib Cleanup Batch B — Simple remaining helpers, compat decisions and svgAnalyzer boundary inventory

- Verdict: `PASS`
- Start count V4:
  - component: `0`
  - lib: `11`
  - total: `11`
- End count V4:
  - component: `0`
  - lib: `7`
  - total: `7`
- B1 simple helpers:
  - migrated: `4`
  - blocked: `0`
  - deleted: `4`
  - vitest: `PASS` (`4` fisiere, `16` teste)
  - scan: `PASS`
- B2 compat decisions:
  - migrated: `0`
  - kept compat justified: `3`
  - deleted: `0`
  - blocked: `0`
  - vitest: `N/A` (nu au fost mutate teste; au ramas explicit ca `KEEP_COMPAT_TEST_JUSTIFIED`)
  - scan: `EXPECTED_V4_REMAINS` (markerii au ramas doar in cele 3 fisiere pastrate compat)
- B3 svgAnalyzer boundary:
  - files classified: `4`
  - decision: `BLOCKED_BY_SVG_ANALYZER_CONTRACT`
  - next task needed: audit separat pentru boundary-ul `svgAnalyzer`, fara implementare agresiva in acest batch
- Validari finale:
  - V6 active: `PASS` (`6` fisiere, `26` teste)
  - build: `PASS`
  - tsc global: `NOT DONE` (`TSC_EXIT:2` ramane repo-wide din zone istorice din afara scope-ului)
  - tsc Batch B: `PASS_WITH_BLOCKED_BOUNDARY` (nu au ramas diagnostice locale pe fisierele migrate; filtrarea a mai returnat doar `intakeV4GeometryMetricDisplay.test.ts`, fisier blocat intentional)
- Files migrated:
  - `frontend/src/lib/intakeV6/intakeV4EdgeCantDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6EdgeCantDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4FaceBackPrepCostDraftDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LetterGroups.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LetterGroups.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.test.ts` -> `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts`
- Files deleted:
  - `frontend/src/lib/intakeV6/intakeV4EdgeCantDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4FaceBackPrepCostDraftDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LetterGroups.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.test.ts`
- Files kept compat:
  - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
- Files blocked:
  - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
- Probleme ramase:
  - repo-wide `tsc` ramane rosu in afara scope-ului Batch B
  - cele `3` teste compat raman pe loc pana la o decizie explicită de contract V6 versus garanție compat
  - cele `4` teste boundary raman blocate pe contractele `svgAnalyzer`
- Urmatorul front recomandat:
  - prompt separat pentru `svgAnalyzer boundary` care sa auditeze exclusiv `ArtworkLogoDiagnostic`, `GeometryMetricDisplay`, `LayerRoleBridge` si `LayerRoleDisplay`
  - prompt separat, daca vrei reducerea count-ului sub `7`, pentru o decizie dedicată asupra celor `3` teste compat păstrate

  ## SVG Analyzer Boundary Review — Remaining Intake V4 lib tests

  - Verdict: `PARTIAL`
  - Start count:
    - component: `0`
    - lib: `7`
    - total: `7`
  - End count:
    - component: `0`
    - lib: `6`
    - total: `6`
  - Tests reviewed:
    - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
  - Decisions:
    - `MIGRATE_TO_V6_NOW`:
      - `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts` -> `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.test.ts`
    - `CREATE_V6_BOUNDARY_TEST`:
      - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
      - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
    - `KEEP_COMPAT_TEST_JUSTIFIED`:
      - `0`
    - `MOVE_TO_SVG_ANALYZER_TEST_SCOPE`:
      - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `BLOCKED_NEEDS_CONTRACT_DECISION`:
      - `0`
    - `DELETE_DUPLICATE_LEGACY`:
      - `0`
  - Implementation done:
    - created `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.test.ts`
    - deleted `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
  - Implementation skipped:
    - nu am implementat boundary tests pentru `ArtworkLogoDiagnostic` si `GeometryMetricDisplay`; verdictul este clar, dar stergerea variantelor V4 cere dovada separata de contract boundary V6↔svgAnalyzer
    - nu am mutat `LayerRoleDisplay` in `src/lib/svgAnalyzer`; necesita task separat de relocation pentru a evita amestecul de ownership in acest lot
  - Boundary findings:
    - `LayerRoleBridge` este un bridge V6 activ, cu helper V6 propriu, fara fixture-heavy analyzer contract; migrarea 1:1 a fost curata
    - `GeometryMetricDisplay` verifica un contract activ V6, dar il exercita prin `analyzeSvgString`, `buildLayerRoleConfirmationDraft`, `resolveQuoteGeometryForWorkspace` si fixture-uri reale; apartine unui test boundary explicit, nu unei simple redenumiri
    - `ArtworkLogoDiagnostic` verifica atat output brut analyzer (`report.layers`, `report.parts`, `report.elements`) cat si adaptarea spre diagnostic/operator metrics; este boundary V6↔svgAnalyzer, nu test pur compat
    - `LayerRoleDisplay` nu are consumatori V6 directi gasiti in runtime, iar aceleasi helper-e sunt folosite de teste din `src/lib/svgAnalyzer`; ownership-ul curent este amestecat si justifica mutare separata de scope
  - svgAnalyzer coupling findings:
    - `intakeV6` consuma activ `svgAnalyzer` in runtime prin `intakeV6ClientSvgImport.ts`, `intakeV6PayloadHydrate.ts`, `intakeV6LayerRoleBridge.ts`, `intakeV6QuoteGeometry.ts` si `useIntakeV6Workspace.ts`
    - `intakeV6GeometryMetricDisplay.ts` este surface V6 activ folosit de componente/runtime, dar implementeaza in continuare mapping peste helper-ul V4
    - `intakeV6ArtworkLogoDiagnostic.ts` si `intakeV6LayerRoleDisplay.ts` nu exporta inca nume V6 curate pentru helper-ele principale; boundary naming-ul ramane parțial legacy
    - `src/lib/svgAnalyzer` contine deja teste care importa helper-ele `LayerRoleDisplay`, semn ca responsabilitatea actuala este traversata intre namespace-uri
  - Validari:
    - boundary tests current: `PASS` (`4` fisiere, `12` teste) in forma initiala V4
    - migrated/boundary tests: `PASS` (`intakeV6LayerRoleBridge.test.ts` + cele `3` boundary tests ramase = `4` fisiere, `12` teste)
    - V6 active: `PASS` (`6` fisiere, `26` teste)
    - build: `PASS`
    - tsc global: `NOT DONE` (`TSC_EXIT:2`; transcriptul stabil a confirmat statusul repo-wide istoric si a aratat `125` erori in `44` fisiere dupa migrarea bridge-ului)
    - tsc boundary filtered: `PARTIAL` (ultimul transcript util a ramas cu diagnostice doar in `intakeV4ArtworkLogoDiagnostic.test.ts`, `intakeV4GeometryMetricDisplay.test.ts` si `intakeV4LayerRoleDisplay.test.ts`; diagnosticul nou introdus initial in `intakeV6LayerRoleBridge.test.ts` a fost reparat, iar rerularea ulterioara a filtrarii a ramas instabilă in terminal)
  - Files changed:
    - `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleBridge.test.ts`
    - `docs/audits/INTAKE_V6_TEST_CLEANUP_CHECKPOINT.md`
  - Files intentionally left:
    - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
  - Next recommended task:
    - creeaza un lot boundary V6 dedicat pentru `ArtworkLogoDiagnostic` si `GeometryMetricDisplay`, cu teste denumite explicit boundary si aliasuri V6 curate doar pe suprafetele folosite activ
    - creeaza separat un task `svgAnalyzer test relocation` pentru `LayerRoleDisplay`, fiindca ownership-ul curent este mai aproape de `svgAnalyzer` decat de runtime-ul activ Intake V6

  ## SVG Analyzer Boundary Tests V6 — ArtworkLogoDiagnostic and GeometryMetricDisplay

  - Verdict: `PASS`
  - Start count:
    - component: `0`
    - lib: `6`
    - total: `6`
  - End count:
    - component: `0`
    - lib: `4`
    - total: `4`
  - Boundary tests created:
    - `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnosticBoundary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV6GeometryMetricDisplayBoundary.test.ts`
  - V4 tests deleted:
    - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
  - V4 tests kept:
    - `0` pentru scope-ul acestui task; cele 3 compat-justified si `LayerRoleDisplay` au ramas intentionat in afara task-ului
  - LayerRoleDisplay status:
    - `UNTOUCHED` — `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts` a ramas neatins pentru task separat `MOVE_TO_SVG_ANALYZER_TEST_SCOPE`
  - Implementation notes:
    - numele `Boundary` a fost ales deliberat fiindca ambele teste exercită analyzer real si adaptarea contractului catre helper-ele V6
    - `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnostic.ts` a primit doar aliasuri V6 stricte de export pentru builder si constante, fara logica noua
    - testele noi folosesc helper-ele V6, `report.layerRoleConfirmation` si semnatura actuala a `resolveQuoteGeometryForWorkspace`, evitand drift-ul de tip din testele V4 istorice
  - Validari:
    - boundary V6 tests: `PASS`
      - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6ArtworkLogoDiagnosticBoundary.test.ts src/lib/intakeV6/intakeV6GeometryMetricDisplayBoundary.test.ts`
      - rezultat: `2` fisiere, `9` teste
      - rerulare dupa stergerea V4: `PASS`
    - V6 active: `PASS`
      - `6` fisiere, `26` teste
    - build: `PASS`
    - tsc global: `NOT DONE`
      - `TSC_EXIT:2` ramane istoric repo-wide
      - in acest task, terminalul a ramas instabil pentru transcriptul global complet, dar nu au aparut regresii executabile in slice-ul atins
    - tsc task filtered: `PASS`
      - `get_errors` pe `intakeV6ArtworkLogoDiagnostic.ts`, `intakeV6ArtworkLogoDiagnosticBoundary.test.ts` si `intakeV6GeometryMetricDisplayBoundary.test.ts` a returnat `No errors found`
      - transcriptul shell pentru filtrarea `tsc` a ramas inconsistent in aceasta sesiune si nu a produs un output scoped fiabil
    - scan V4 markers: `PASS`
      - scanul pe fisierele relevante nu a returnat output; fisierele V6 noi au ramas fara markeri V4, iar corespondentele V4 nu mai exista
  - Files changed:
    - `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnostic.ts`
    - `frontend/src/lib/intakeV6/intakeV6ArtworkLogoDiagnosticBoundary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV6GeometryMetricDisplayBoundary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4ArtworkLogoDiagnostic.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4GeometryMetricDisplay.test.ts`
    - `docs/audits/INTAKE_V6_TEST_CLEANUP_CHECKPOINT.md`
  - Files intentionally untouched:
    - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
    - `src/lib/svgAnalyzer/**`
  - Remaining V4 tests:
    - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
  - Next recommended task:
    - task separat pentru `MOVE_TO_SVG_ANALYZER_TEST_SCOPE` pe `LayerRoleDisplay`
    - dupa aceea, front separat pentru cele `3` teste compat-justified ramase, doar cu decizie explicită de contract

  ## SVG Analyzer Relocation — LayerRoleDisplay

  - Verdict: `BLOCKED`
  - Start count:
    - component: `0`
    - lib: `4`
    - total: `4`
  - End count:
    - component: `0`
    - lib: `4`
    - total: `4`
  - Decision:
    - `BLOCKED_NEEDS_CONTRACT_DECISION`
    - motivul este local si verificabil: testul verifica rows/counts derivate din analyzer, dar helper-ul testat traieste inca in `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`, foloseste `INTAKE_V4_LAYER_ROLE_OPTIONS`, iar `frontend/src/lib/intakeV6/intakeV6LayerRoleDisplay.ts` este doar re-export peste aceeasi suprafata
  - New svgAnalyzer test:
    - `none`
  - V4 test deleted:
    - `none`
  - V4 test kept:
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - a ramas fiindca relocarea curata ar cere mai intai extragerea sau reclasificarea helper-ului din `intakeV6` in `svgAnalyzer`, iar acest task nu permite schimbare de ownership fara decizie explicita
  - Implementation notes:
    - testul actual acopera `buildLayerRoleRowsForDisplay`, `countArtworkLayers` si `countProductionGeometryLayers`
    - helper-ul nu este adapter runtime Intake V6; nu am gasit consumatori runtime V6 pentru aceste functii
    - exista deja teste in `src/lib/svgAnalyzer/analyzer` care folosesc aceste helper-e prin importuri legacy (`ana-maria-layer-roles.test.ts`, `svgAnalyzerRegressionGate.test.ts`, `ana-maria-corel-perimeter-diagnostic.test.ts`), ceea ce confirma ca ownership-ul este amestecat, nu clar relocabil
    - conform regulii task-ului, nu am mutat testul orb cat timp helper-ul traieste doar in `src/lib/intakeV6`
  - Validari:
    - relocated test:
      - `NOT RUN` (nu a fost creat niciun test nou in `svgAnalyzer`)
    - V6 active:
      - `PASS` (`6` fisiere, `26` teste)
    - build:
      - `PASS`
    - tsc global:
      - `NOT DONE` / istoric `TSC_EXIT:2`
      - si in aceasta sesiune transcriptul complet a ramas instabil in terminal
    - tsc task filtered:
      - `NOT RELIABLE_FROM_TERMINAL`
      - comanda a produs output instabil/trunchiat; nu am facut editari de cod in scope-ul helper-ului sau al testului
    - scan V4 markers:
      - `EXPECTED_V4_REMAINS`
      - nu exista test nou in `svgAnalyzer`; fisierul V4 ramas continua justificat sa contina markerii legacy
  - Files changed:
    - `docs/audits/INTAKE_V6_TEST_CLEANUP_CHECKPOINT.md`
  - Files intentionally untouched:
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`
    - `frontend/src/lib/intakeV6/intakeV6LayerRoleDisplay.ts`
  - Remaining V4 tests:
    - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
    - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
  - Next recommended task:
    - contract/ownership decision separat pentru `LayerRoleDisplay`: fie extragerea helper-ului in `src/lib/svgAnalyzer`, fie mentinerea lui explicita ca surface compat in `intakeV6`
    - doar dupa acea decizie are sens relocarea sau stergerea testului V4

## Final Compat Contract Decision — Remaining Intake V4 lib tests

- Verdict: `PARTIAL`
- Start count:
  - component: `0`
  - lib: `4`
  - total: `4`
- End count:
  - component: `0`
  - lib: `1`
  - total: `1`
- Final per-file decisions:
  - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts` -> `CREATE_V6_COMPAT_CONTRACT_TEST`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts` -> `BLOCKED_NEEDS_OWNERSHIP_DECISION`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts` -> `CREATE_V6_COMPAT_CONTRACT_TEST`
  - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts` -> `CREATE_V6_COMPAT_CONTRACT_TEST`
- New V6 compat contract tests:
  - `frontend/src/lib/intakeV6/intakeV6ConfirmSummaryCompatContract.test.ts`
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleOptionsCompatContract.test.ts`
  - `frontend/src/lib/intakeV6/intakeV6NearestOracalColorCompatContract.test.ts`
- V4 tests deleted after proof:
  - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
- V4 test kept:
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
  - a ramas singurul test V4 din scope fiindca helper-ul testat traieste in continuare in `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`, iar aceleasi helper-e sunt consumate si din teste `svgAnalyzer`; nu exista inca o granita de ownership suficient de clara pentru migrare sau relocare sigura
- Implementation notes:
  - `ConfirmSummary` a fost promovat la compat contract V6 fiindca `buildIntakeV6ConfirmSummary` este consumat activ in runtime-ul Intake V6, chiar daca implementarea ramane alias peste helper-ul V4
  - `LayerRoleOptions` a fost promovat la compat contract V6 fiindca `INTAKE_V6_LAYER_ROLE_OPTIONS` este consumat activ in pasul `IntakeV6SvgAnalyzerStep.tsx`, iar testul valideaza exact override-urile operator-facing si paritatea de catalog
  - `NearestOracalColor` a fost promovat la compat contract V6 fiindca exista deja o suprafata V6 dedicata, iar utilitarul ramane parte din ecosistemul helper-elor Intake V6 chiar daca nu are un call-site runtime V6 textual direct
  - `LayerRoleDisplay` nu a fost redenumit si nu a fost sters fiindca asta ar masca o problema de ownership intre `intakeV6` si `svgAnalyzer`, nu ar rezolva-o
- Validari:
  - new compat contract tests: `PASS`
    - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6ConfirmSummaryCompatContract.test.ts src/lib/intakeV6/intakeV6LayerRoleOptionsCompatContract.test.ts src/lib/intakeV6/intakeV6NearestOracalColorCompatContract.test.ts`
    - rezultat: `3` fisiere, `15` teste
    - rerulare dupa stergerea V4: `PASS`
  - V6 active: `PASS`
    - `6` fisiere, `26` teste
  - build: `PASS`
  - tsc global: `NOT DONE`
    - transcriptul repo-wide ramane istoric instabil; o tentativa prin `npm.cmd exec tsc -- -p tsconfig.app.json --noEmit` nu a produs transcript util in acest task
  - tsc task filtered: `NOT RELIABLE_FROM_TERMINAL`
    - tentativa filtrata a ramas instabila si chiar a lovit o rezolvare de PATH inconsistenta pentru `npm.cmd`; nu a existat insa nicio eroare locala in fisierele noi conform `get_errors`
  - scan V4 markers: `EXPECTED_SINGLE_REMAINING_V4`
    - scanul final a raportat markeri doar in `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
  - final count: `PASS`
    - component: `0`
    - lib: `1`
    - total: `1`
- Files changed:
  - `frontend/src/lib/intakeV6/intakeV6ConfirmSummaryCompatContract.test.ts`
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleOptionsCompatContract.test.ts`
  - `frontend/src/lib/intakeV6/intakeV6NearestOracalColorCompatContract.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4ConfirmSummary.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4NearestOracalColor.test.ts`
  - `docs/audits/INTAKE_V6_TEST_CLEANUP_CHECKPOINT.md`
- Files intentionally untouched:
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleDisplay.ts`
  - `src/lib/svgAnalyzer/**`
- Remaining V4 tests:
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
- Next recommended task:
  - task separat de `ownership extraction` sau `scope relocation` pentru `LayerRoleDisplay`, pornind de la helper-ul `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`, nu doar de la numele testului

## Final Cleanup Closeout — Intake V4 Test Naming

- Verdict: `CLOSED_WITH_DOCUMENTED_COMPAT_EXCEPTION`
- Final count:
  - component V4: `0`
  - lib V4: `1`
  - total V4: `1`
- Remaining V4 test:
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
- Remaining V4 decision:
  - `KEEP_COMPAT_TEST_JUSTIFIED`
- Reason:
  - helper ownership is mixed between `intakeV6` and `svgAnalyzer`
  - direct relocation would require architecture ownership decision
  - test remains as a documented compatibility/ownership exception
- Validari:
  - remaining V4 test: `PASS` (`1` fisier, `3` teste)
  - V6 compat contract tests: `PASS` (`3` fisiere, `15` teste)
  - V6 active: `PASS` (`6` fisiere, `26` teste)
  - build: `PASS`
  - tsc global: `NOT DONE` / `STATUS_ONLY_UNRELIABLE_FROM_TERMINAL`
  - tsc filtered: `NOT RELIABLE FROM TERMINAL`; `get_errors` pe fisierele de closeout a returnat `No errors found`
- Cumulative totals:
  - migrated/resolved: `49`
  - deleted: `76`
  - remaining: `1`
- What is closed:
  - component V4 cleanup
  - lib V4 cleanup except documented LayerRoleDisplay exception
  - V6 compat contracts for previous V4 compat helpers
  - svgAnalyzer boundary tests for artwork/geometry
- What is not closed:
  - ownership decision for LayerRoleDisplay helper
  - repo-wide TypeScript historical red state
- Final recommendation:
  - do not treat the remaining file as cleanup debt
  - treat it as an explicit architecture/ownership decision item

## LayerRoleDisplay Ownership Decision

- Verdict: `BLOCKED_NEEDS_ARCHITECTURE_GO`
- Start count:
  - component V4: `0`
  - lib V4: `1`
  - total V4: `1`
- End count:
  - component V4: `0`
  - lib V4: `1`
  - total V4: `1`
- Ownership decision:
  - `BLOCKED_NEEDS_ARCHITECTURE_GO`
- Reason:
  - `buildLayerRoleRowsForDisplay` combina tipuri `svgAnalyzer` cu label-uri operator din `INTAKE_V4_LAYER_ROLE_OPTIONS`, deci nu apartine natural exclusiv `svgAnalyzer`
  - `countArtworkLayers` si `countProductionGeometryLayers` sunt pure peste `SvgAnalysisCoreReport`, dar sunt pachetizate impreuna cu helper-ul de display compat
  - call-site-urile reale gasite sunt doar teste: un test din `intakeV6` si trei teste din `svgAnalyzer`; nu exista consumatori runtime care sa impuna un nou surface public
  - testele `svgAnalyzer` care ar justifica extragerea importa prin namespace-ul compat `@/lib/intakeV4/*`, iar rularea lor actuala pica deja la rezolvare de import pentru `intakeV4LayerRoleBridge`; asta arata ca problema depaseste `LayerRoleDisplay` si cere decizie mai larga despre namespace-ul compat dintre `intakeV4`, `intakeV6` si `svgAnalyzer`
- Implementation done:
  - `none`
- Implementation skipped:
  - nu am extras helper-ul in `svgAnalyzer`
  - nu am creat modul shared neutru
  - nu am mutat sau sters testul V4 ramas
- New helper location:
  - `none`
- Wrappers kept:
  - `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleDisplay.ts`
- Test changes:
  - `none`
- Validari:
  - old V4 test: `PASS`
    - `npm.cmd exec vitest run src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
    - rezultat: `1` fisier, `3` teste
  - new ownership test: `NOT CREATED`
  - svgAnalyzer call-site tests: `FAIL_PREEXISTING_COMPAT_IMPORT_RESOLUTION`
    - `npm.cmd exec vitest run src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts`
    - toate trei pica la `Failed to resolve import "@/lib/intakeV4/intakeV4LayerRoleBridge"`
  - V6 compat contract tests: `PASS`
    - `3` fisiere, `15` teste
  - V6 active: `PASS`
    - `6` fisiere, `26` teste
  - build: `PASS`
  - tsc global: `NOT RELIABLE_FROM_TERMINAL`
    - tentativa de rulare prin `tsc.cmd` nu a produs un transcript stabil in shell-ul curent
  - tsc filtered: `NOT RELIABLE_FROM_TERMINAL`
    - `get_errors` pe `intakeV4LayerRoleDisplay.test.ts`, `intakeV4LayerRoleDisplay.ts` si `intakeV6LayerRoleDisplay.ts` a returnat `No errors found`
- Cumulative totals:
  - migrated/resolved: `49`
  - deleted: `76`
  - remaining: `1`
- Final recommendation:
  - pastreaza `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts` ca exceptie compat documentata pana la un task arhitectural separat pentru namespace-ul `@/lib/intakeV4/*`
  - nu trata fisierul ramas ca debt de cleanup de naming; trateaza-l ca debt de architecture ownership si compat namespace

## Compat Namespace Ownership Audit

- Verdict: `BLOCKED_NEEDS_ARCHITECTURE_GO`
- Audit doc:
  - `docs/audits/INTAKE_V4_COMPAT_NAMESPACE_OWNERSHIP_AUDIT.md`
- Impact on cleanup:
  - no change to final V4 count
  - remaining V4 test remains documented compat/ownership exception
- Next recommended task:
  - architecture decision task for compat namespace `@/lib/intakeV4/*`, covering `LayerRoleBridge`, `QuoteGeometry`, and `LayerRoleDisplay` together instead of extracting one helper in isolation

## Compat Namespace Bridge Restoration

- Verdict: `PASS`
- Shims restored:
  - `src/lib/intakeV4/intakeV4LayerRoleBridge.ts`
  - `src/lib/intakeV4/intakeV4QuoteGeometry.ts`
  - `src/lib/intakeV4/intakeV4LayerRoleDisplay.ts`
- Cleanup count impact:
  - none
- Final V4 test count:
  - component: `0`
  - lib: `1`
  - total: `1`
- Audit doc:
  - `docs/audits/INTAKE_V4_COMPAT_NAMESPACE_OWNERSHIP_AUDIT.md`
- Note:
  - this restores compatibility imports only
  - it does not migrate or delete the documented LayerRoleDisplay V4 exception

## Lot 2A — Component tests migration

- Verdict: `PASS`

Teste migrate:

- `frontend/src/components/workos/intake-v6/IntakeV4MaterialBreakdownPanel.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4LiveCalculationSummary.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4GeometryPanel.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4OperatorGeometrySummaryCard.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/components/workos/intake-v6/IntakeV4MaterialBreakdownPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4LiveCalculationSummary.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4GeometryPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4OperatorGeometrySummaryCard.test.tsx`

Validari:

- `vitest Lot 2A`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`
  - Rezultat: `4` fisiere, `23` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
- `tsc global`: `NOT DONE`
  - `TSC_EXIT:2`
  - Diagnozele ramase sunt in afara Lot 2A; niciun diagnostic nu mai pointeaza la cele 4 fisiere migrate.
- `tsc Lot 2A`: `PASS`
  - Filtrarea output-ului `tsc` pe cele 4 fisiere migrate nu a returnat match-uri.
- `scan final`: `PASS`
  - Scanul de naming limitat la cele 4 fisiere migrate nu a returnat referinte `IntakeV4|intakeV4|intake-v4|INTAKE_V4`.

Probleme ramase:

- teste istorice `IntakeV4*` raman in continuare in `frontend/src/components/workos/intake-v6` in afara Lot 2A;
- `tsc` repo-wide ramane rosu din zone legacy si din suprafete care nu au fost in scope pentru acest lot.

Urmatorul lot recomandat:

- `Lot 2B`: realizat ulterior in acest document; urmatorul pas efectiv este `Lot 2C`.

## Lot 2B — Operator component tests migration

- Verdict: `PASS`

Teste migrate:

- `frontend/src/components/workos/intake-v6/IntakeV4OperatorUiPolish.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6OperatorUiPolish.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4OperatorWorkSummary.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.test.tsx`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/components/workos/intake-v6/IntakeV4OperatorUiPolish.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4OperatorWorkSummary.test.tsx`

Validari:

- `vitest Lot 2B`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6OperatorUiPolish.test.tsx src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.test.tsx`
  - Rezultat: `2` fisiere, `7` teste
- `vitest Lot 2A regression`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`
  - Rezultat: `4` fisiere, `23` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
- `tsc global`: `NOT DONE`
  - `TSC_EXIT:2`
  - Repo-ul ramane rosu din zone istorice din afara Lot 2B.
- `tsc Lot 2B`: `PASS`
  - Filtrarea output-ului `tsc` pe `IntakeV6OperatorUiPolish.test.tsx`, `IntakeV6OperatorWorkSummary.test.tsx`, `IntakeV4OperatorUiPolish.test.tsx`, `IntakeV4OperatorWorkSummary.test.tsx` nu a returnat diagnostice.
- `scan final Lot 2B`: `PASS`
  - Scanul pe `IntakeV6OperatorUiPolish.test.tsx` si `IntakeV6OperatorWorkSummary.test.tsx` nu a returnat referinte `IntakeV4|intakeV4|intake-v4|INTAKE_V4`.

Probleme ramase:

- `tsc` repo-wide ramane rosu in afara scope-ului acestui lot;
- mai exista `10` component tests si `31` lib tests cu naming V4 in zona Intake V6 compat.

Urmatorul lot recomandat:

- `Lot 2C`: migrarea component-testelor V4 ramase care lovesc direct suprafata activa V6, incepand cu `IntakeV4ArtworkFinishSection.test.tsx`, `IntakeV4BackingAndEmblemSection.test.tsx`, `IntakeV4CncOperationPreviewSection.test.tsx`, `IntakeV4ConfirmStep.test.tsx`.

## Lot 2C.1 — Confirm and finish component tests migration

- Verdict: `PASS`

Teste migrate:

- `frontend/src/components/workos/intake-v6/IntakeV4ArtworkFinishSection.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4LetterGroupFinishesSection.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4ConfirmStep.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/components/workos/intake-v6/IntakeV4ArtworkFinishSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4LetterGroupFinishesSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4ConfirmStep.test.tsx`

Validari:

- `vitest Lot 2C.1`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
  - Rezultat: `3` fisiere, `9` teste
- `vitest Lot 2A regression`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`
  - Rezultat: `4` fisiere, `23` teste
- `vitest Lot 2B regression`: `PASS`
  - `npm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6OperatorUiPolish.test.tsx src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.test.tsx`
  - Rezultat: `2` fisiere, `7` teste
- `vitest V6 active`: `PASS`
  - `npm.cmd exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
- `tsc global`: `NOT DONE`
  - `TSC_EXIT:2`
  - Repo-ul ramane rosu din zone istorice din afara Lot 2C.1.
- `tsc Lot 2C.1`: `PASS`
  - Filtrarea output-ului `tsc` pe `IntakeV6ConfirmStep.test.tsx`, `IntakeV6ArtworkFinishSection.test.tsx`, `IntakeV6LetterGroupFinishesSection.test.tsx`, `IntakeV4ConfirmStep.test.tsx`, `IntakeV4ArtworkFinishSection.test.tsx`, `IntakeV4LetterGroupFinishesSection.test.tsx` nu a returnat diagnostice.
- `scan final Lot 2C.1`: `PASS`
  - Scanul pe fisierele Lot 2C.1 nu a returnat referinte `IntakeV4|intakeV4|intake-v4|INTAKE_V4`.

Probleme ramase:

- `tsc` repo-wide ramane rosu in afara scope-ului acestui lot;
- mai exista `7` component tests si `31` lib tests cu naming V4 in zona Intake V6 compat.

Urmatorul lot recomandat:

- `Lot 2C.2`: migrarea urmatorului grup de component tests V4 ramase din zona Confirm / Finish, fara extindere in alte suprafete.

## Lot 2C.2 — Backing, CNC, edge and sheet component tests migration

- Verdict: `PASS`

Teste migrate:

- `frontend/src/components/workos/intake-v6/IntakeV4BackingAndEmblemSection.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6BackingAndEmblemSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4CncOperationPreviewSection.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6CncOperationPreviewSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4EdgeCantReviewCard.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6EdgeCantReviewCard.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4ReviewBackingSelect.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4SheetFootprintOverridePanel.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6SheetFootprintOverridePanel.test.tsx`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/components/workos/intake-v6/IntakeV4BackingAndEmblemSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4CncOperationPreviewSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4EdgeCantReviewCard.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4ReviewBackingSelect.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4SheetFootprintOverridePanel.test.tsx`

Validari:

- `vitest Lot 2C.2`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6BackingAndEmblemSection.test.tsx src/components/workos/intake-v6/IntakeV6CncOperationPreviewSection.test.tsx src/components/workos/intake-v6/IntakeV6EdgeCantReviewCard.test.tsx src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/components/workos/intake-v6/IntakeV6SheetFootprintOverridePanel.test.tsx`
  - Rezultat: `5` fisiere, `17` teste
- `regression Lot 2A`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`
  - Rezultat: `4` fisiere, `23` teste
- `regression Lot 2B`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6OperatorUiPolish.test.tsx src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.test.tsx`
  - Rezultat: `2` fisiere, `7` teste
- `regression Lot 2C.1`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
  - Rezultat: `3` fisiere, `9` teste
- `vitest V6 active`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
  - Observatie: au ramas warning-urile istorice CSS minify si chunk-size, fara blocaj de build.
- `tsc global`: `NOT DONE`
  - `TSC_EXIT:2`
  - Repo-ul ramane rosu din zone istorice din afara Lot 2C.2.
- `tsc Lot 2C.2`: `PASS`
  - `get_errors` pe cele 5 fisiere migrate nu a returnat diagnostice.
  - Filtrarea `tsc --pretty false` pe fisierele `IntakeV6*` / `IntakeV4*` ale lotului nu a produs niciun match pentru aceste path-uri.
- `scan final Lot 2C.2`: `PASS`
  - Scanul strict pe fisierele Lot 2C.2 nu a returnat referinte `IntakeV4|intakeV4|intake-v4|INTAKE_V4`.

Count V4 tests ramas:

- `component`: `2`
- `lib`: `31`
- `total`: `33`

Probleme ramase:

- `tsc` repo-wide ramane rosu in afara scope-ului acestui lot;
- au ramas doar cele doua component tests de cost-draft si grupul separat de lib tests compat/legacy.

Urmatorul lot recomandat:

- `Lot 2C.3`: migrarea `IntakeV4FaceBackPrepCostDraftPanel.test.tsx` si `IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx`, fara extindere in zonele de lib compat.

## Lot 2C.3 — Final component tests migration

- Verdict: `PASS`

Teste migrate:

- `frontend/src/components/workos/intake-v6/IntakeV4FaceBackPrepCostDraftPanel.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6FaceBackPrepCostDraftPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx` -> `frontend/src/components/workos/intake-v6/IntakeV6FaceBackPrepCostDraftSummaryCard.test.tsx`

Teste blocate:

- `0`

Teste sterse:

- `frontend/src/components/workos/intake-v6/IntakeV4FaceBackPrepCostDraftPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx`

Validari:

- `vitest Lot 2C.3`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6FaceBackPrepCostDraftPanel.test.tsx src/components/workos/intake-v6/IntakeV6FaceBackPrepCostDraftSummaryCard.test.tsx`
  - Rezultat: `2` fisiere, `8` teste
- `regression Lot 2A`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx src/components/workos/intake-v6/IntakeV6GeometryPanel.test.tsx src/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard.test.tsx`
  - Rezultat: `4` fisiere, `23` teste
- `regression Lot 2B`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6OperatorUiPolish.test.tsx src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.test.tsx`
  - Rezultat: `2` fisiere, `7` teste
- `regression Lot 2C.1`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
  - Rezultat: `3` fisiere, `9` teste
- `regression Lot 2C.2`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/components/workos/intake-v6/IntakeV6BackingAndEmblemSection.test.tsx src/components/workos/intake-v6/IntakeV6CncOperationPreviewSection.test.tsx src/components/workos/intake-v6/IntakeV6EdgeCantReviewCard.test.tsx src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/components/workos/intake-v6/IntakeV6SheetFootprintOverridePanel.test.tsx`
  - Rezultat: `5` fisiere, `17` teste
- `vitest V6 active`: `PASS`
  - `node_modules/.bin/vitest.cmd run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts src/lib/intakeV6/intakeV6ReturnFinishRules.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts`
  - Rezultat: `6` fisiere, `26` teste
- `build`: `PASS`
  - `npm.cmd run build`
  - Observatie: au ramas warning-urile istorice CSS minify si chunk-size, fara blocaj de build.
- `tsc global`: `NOT DONE`
  - `TSC_EXIT:2`
  - Repo-ul ramane rosu din zone istorice din afara loturilor migrate.
- `tsc Lot 2C.3`: `PASS`
  - `get_errors` pe `IntakeV6FaceBackPrepCostDraftPanel.test.tsx` si `IntakeV6FaceBackPrepCostDraftSummaryCard.test.tsx` nu a returnat diagnostice.
  - Filtrarea `tsc --pretty false` pe `IntakeV6.*test.tsx|IntakeV4.*test.tsx` nu a returnat diagnostice noi pentru fisierele migrate din Lot 2C.3; `TSC_EXIT:2` ramane din afara acestei felii.
- `scan final component scope`: `PASS`
  - Scanul pe toate `*.test.tsx` din `src/components/workos/intake-v6` nu a mai returnat markeri `IntakeV4|intakeV4|intake-v4|INTAKE_V4`.

Count V4 tests ramas:

- `component`: `0`
- `lib`: `31`
- `total`: `31`

Probleme ramase:

- `tsc` repo-wide ramane rosu in afara scope-ului acestui lot;
- toate testele V4 ramase sunt acum exclusiv in `src/lib/intakeV6` si cer triere separată intre compat justificat si migrare V6 completă.

Urmatorul front recomandat:

- decizie separată pentru frontul de lib compat `src/lib/intakeV6/intakeV4*.test.ts`; zona de component tests Intake V6 este închisă.

## 7. Ce ramane in afara scope-ului

- `frontend/src/lib/svgAnalyzer`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/components/workos/employee-mobile*`
- `frontend/src/pages/Orders*`
- `frontend/src/pages/Quotes*`
- alte erori repo-wide TypeScript din afara zonei `intake-v6`

## 8. Concluzie practica

Acest lot a eliminat zgomotul cel mai ieftin si mai sigur din testele istorice Intake V4 ramase in zona Intake V6:

- au fost eliminate shim-urile V6 inutile care doar re-exportau teste V4;
- un nucleu de teste de lib active a fost mutat la naming si importuri V6 canonice;
- build-ul si testele V6 relevante trec;
- runtime-ul V6 stabilizat anterior nu a fost afectat.

Faza nu este inchisa complet pentru `PASS`, deoarece a ramas un volum semnificativ de teste V4 in scope care cer migrare coordonata sau decizie explicita de compatibilitate legacy.
