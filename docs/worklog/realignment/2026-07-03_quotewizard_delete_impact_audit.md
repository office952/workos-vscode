# 2026-07-03 QuoteWizard Delete Impact Audit

## 1. Context

Audit read-only pentru intrebarea owner: putem sterge tot ce inseamna `QuoteWizard`, daca pare parte dintr-un flow vechi?

Concluzie executiva: **nu stergem acum**. `QuoteWizard` nu este mecanismul V6 oficial pentru pret final, dar este inca importat si folosit runtime in pagina Oferte pentru `Oferta noua`, flow generic/non-V6 si flow volumetric legacy/compat. V6 trebuie deconectat semantic de QuoteWizard, dar delete complet ar rupe `/quotes`, teste frontend si smoke-uri legacy.

Boundary respectat: nu am sters fisiere, nu am modificat UI, flow comercial, pricing logic, statusuri, backend, DB schema, seed, ProductAggregate, Task Graph, ExecutionPlan sau Employee Mobile. Singura modificare este acest worklog.

## 2. Inventar aparitii

Termeni cautati in repo: `QuoteWizard`, `Quote Wizard`, `quoteWizard`, `quote_wizard`, `PricingWizard`, `QuoteEditor`, `QuotePricing`, `OfferPricing`, `VolumetricLettersQuoteFlow`, `openAdhocWizard`, `setShowWizard`, `setWizardSource`, `wizardSource`, `onQuoteCreated`.

Exclude intentionat: `node_modules`, `dist`, `coverage`, `__pycache__`, `.git`. `logs` si `.pytest_cache` apar in backend search ca artefacte runtime/cache; le clasific separat ca non-source.

| Path | Linie/context | Tip | Runtime activ? | V6 sau generic? | Poate fi eliminat? |
| --- | --- | --- | --- | --- | --- |
| `frontend/src/App.tsx` | `/quotes/:quoteId` si `/quotes` randeaza `Quotes`; nu exista `/quote-wizard` | route | Da | generic + V6 detail host | Nu; ruta Quotes ramane. |
| `frontend/src/pages/Quotes.tsx` | import `QuoteWizard` | runtime import | Da | generic + legacy handoff | Nu fara inlocuitor. |
| `frontend/src/pages/Quotes.tsx` | `openAdhocWizard()` | handler UI | Da | generic/manual quote | Nu; butonul `Oferta noua` depinde de el. |
| `frontend/src/pages/Quotes.tsx` | render `<QuoteWizard>` pentru `volumetricWorkspaceOpen` | runtime modal | Da | legacy volumetric/intake handoff | Nu fara migrare legacy. |
| `frontend/src/pages/Quotes.tsx` | render `<QuoteWizard>` in pagina Oferte | runtime modal | Da | generic/manual | Nu fara nou ManualQuote flow. |
| `frontend/src/components/workos/QuoteWizard.tsx` | componenta principala | component React | Da | generic + volumetric legacy routing | Nu acum; este cod activ. |
| `frontend/src/components/workos/QuoteWizard.tsx` | `priceQuote(...)` -> `/api/v1/entities/quotes/price` | API client call | Da | generic/non-V6 | Nu fara inlocuitor pentru quote manual. |
| `frontend/src/components/workos/QuoteWizard.tsx` | branch volumetric -> `VolumetricLettersQuoteFlow` | runtime routing | Da | volumetric legacy/compat | Nu fara migrare V2/V4. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | `Replaces generic QuoteWizard UX... Legacy compatibility path` | component React | Da | legacy volumetric, non-V6 official | Nu acum; legacy path activ/testat. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | `costSimulationApi.simulate` | API read/preview | Da | volumetric legacy | Nu daca pastram V2/V4 smoke. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | `priceQuote(...)` commercial quote | API write generic | Da | legacy/generic volumetric | Nu fara replacement. |
| `frontend/src/components/workos/templateIntakeWorkspace/QuoteHandoffPanel.tsx` | imports `VolumetricLettersQuoteFlow` | embedded component | Da pentru workspace template | generic/legacy volumetric | Nu fara audit dedicat. |
| `frontend/src/pages/IntakeDetail.tsx` | `buildQuoteWizardNavStateFromIntake` | nav-state helper | Da pentru legacy intake | V2/V4/generic | Nu fara replacing navigation state. |
| `frontend/src/pages/IntakeDetail.tsx` | `onContinueToQuoteWizard={handleOpenPreliminaryQuote}` | UI callback | Da | legacy intake to quote | Nu fara UI migration. |
| `frontend/src/lib/commercialSpineNavigation.ts` | `buildQuoteWizardNavStateFromIntake` | navigation helper | Da | generic/legacy | Rename/deprecate, nu delete acum. |
| `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.ts` | alias `buildV4QuoteWizardNavState as buildV6QuoteWizardNavState` | compat helper | Partial/legacy naming | V6 naming compat, not official V6 write | Curatare separata; nu delete direct. |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx` | `handleOpenQuoteWizard` name | misleading local name | Da ca functie, dar creeaza draft V6 | V6 draft, nu QuoteWizard UI | Rename safe later, nu delete. |
| `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx` | no `QuoteWizard` import; uses dry-run/write/handoff | V6 commercial spine | Da | V6 | Nu depinde de QuoteWizard. |
| `frontend/src/lib/quoteCommercialGuidance.ts` | copy `Calculeaza pretul in QuoteWizard` | UI guidance | Da pentru generic/guarded flows | generic/legacy | Curatare copy dupa decizie. |
| `frontend/src/api/quotes.ts` | `QuotePricingInput`, `QuotePricingError`, comment `QuoteWizard / volumetric flow` | API/types | Da | generic quote pricing | Nu; generic `/quotes/price` depinde de tipuri. |
| `frontend/src/components/workos/QuoteRevisionDialog.tsx` | imports `QuotePricingError` | API error handling | Da | generic quote revision | Nu este QuoteWizard UI; nu sterge. |
| `frontend/src/components/workos/QuoteSendDialog.tsx` | imports `QuotePricingError` | API error handling | Da | generic send/log | Nu este QuoteWizard UI; nu sterge. |
| `frontend/src/lib/volumetricQuoteInput.ts` | helpers `quote_input` for QuoteWizard | helper | Da via QuoteWizard/Volumetric flow | legacy volumetric | Nu fara replacing volumetric legacy. |
| `frontend/src/lib/volumetricQuoteFlowState.ts` | comment/opened QuoteWizard mode | state helper | Da | legacy volumetric | Rename later. |
| `frontend/src/lib/volumetricIntakeFormPrep.ts` | `canContinueToQuoteWizard` | helper contract | Da in legacy intake prep | legacy | Rename/migrate later. |
| `frontend/src/lib/intakeVolumetricSpec.ts` | Intake -> QuoteWizard mapping comment/tests | helper | Da/legacy | V2/volumetric | Nu fara migration. |
| `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` | `onContinueToQuoteWizard` + multiple copy mentions | component | Da where editor active | legacy volumetric | Not delete; copy rename later. |
| `frontend/src/components/workos/Product001IntakeSpecEditor.HEAD.tsx` | same legacy copy/callback in conflict/artifact file | source artifact | Probabil nu imported | legacy | Verify zero-import before delete; not now. |
| `frontend/src/components/workos/Product001IntakeSpecEditor.MIXED.tsx` | same legacy copy/callback in conflict/artifact file | source artifact | Probabil nu imported | legacy | Candidate cleanup only after reference check. |
| `frontend/src/components/workos/VectorStudioPanel.tsx` | copy mentions manual QuoteWizard | UI copy | Da if panel active | legacy/generic | Copy cleanup later. |
| `backend/routers/quotes.py` | `QuotePricing` and `/entities/quotes/price` implementation | backend generic pricing | Da | generic/non-V6 | Nu; not QuoteWizard service, but wizard depends on it. |
| `backend/services/quote_orchestrator.py` | `QuotePricing`, generic quote pricing | backend service | Da | generic/non-V6 | Nu. |
| `backend/data_models/product_contracts.py` | `QuotePricing` dataclass | shared model | Da | generic CostEngine/quotes | Nu; search term false-positive for wizard delete. |
| `backend/services/intake_v6_commercial_quote_service.py` | active V6 `human_summary` says `QuoteWizard` | backend copy | Da in V6 quote notes | V6 copy only | Clean copy separately; not delete QuoteWizard. |
| `backend/services/intake_v6_quote_to_order_service.py` | blocker says `price the quote in QuoteWizard or freeze...` | backend copy | Da on error path | V6 copy only | Clean copy separately. |
| `backend/services/intake_v6_priced_quote_dry_run_service.py` | no QuoteWizard dependency | V6 service | Da | V6 | No dependency. |
| `backend/services/intake_v6_priced_quote_write_service.py` | no QuoteWizard dependency; writes from backend dry-run | V6 service | Da | V6 | No dependency. |
| `backend/services/intake_v6_offer_handoff_service.py` | no QuoteWizard dependency; create/reuse draft + write totals | V6 service | Da | V6 | No dependency. |
| `backend/services/intake_v4_commercial_quote_service.py` | doc/copy `QuoteWizard handoff` | backend legacy | Da for V4 | V4 legacy | Do not delete without V4 migration. |
| `backend/services/intake_v4_quote_to_order_service.py` | errors require pricing in QuoteWizard | backend legacy | Da for V4 | V4 legacy | Copy/flow migration later. |
| `backend/services/intake_v4_template_option_contract_service.py` | `quote_wizard_default` contract | backend legacy contract | Da for V4 contract | V4 legacy | Not delete until V4 retired. |
| `backend/services/intake_v3_quote_pricing_handoff_service.py` | pricing handoff schema/service | backend legacy | Da for V3 | V3 legacy | Not part of QuoteWizard UI delete. |
| `backend/scripts/seed_commercial_e2e_fixture.py` | WorkIntake V2 -> QuoteWizard fixture | seed/test fixture | Used by E2E | V2 legacy | Not delete while smoke exists. |
| `backend/logs/*`, `backend/backend3.log` | persisted V6 notes mentioning QuoteWizard | runtime logs | No source authority | artifact | Ignore for code delete; useful evidence of active copy. |
| `backend/.pytest_cache/*` | cached test ids | cache | No | test artifact | Ignore. |
| `frontend/src/components/workos/QuoteWizard.vatGovernance.test.tsx` | imports/renders QuoteWizard | test | Yes in test suite | generic | Would fail on delete. |
| `frontend/src/components/workos/QuoteWizard.volumetricRouting.test.tsx` | imports/renders QuoteWizard | test | Yes in test suite | generic + volumetric | Would fail on delete. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow*.test.tsx` | imports/renders flow | test | Yes | legacy volumetric | Would fail if flow removed. |
| `frontend/src/pages/Quotes*.test.tsx` | mocks `QuoteWizard` | tests | Yes | Quotes page generic/V6 host | Would need update if deleted. |
| `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts` | V2 -> QuoteWizard smoke | E2E | Yes when run | V2 legacy | Would fail or need retirement. |
| `frontend/e2e/intake-v4-commercial-handoff.spec.ts` | V4 Confirm -> draft quote -> QuoteWizard | E2E | Yes when run | V4 legacy | Would fail or need migration. |
| `docs/architecture/**`, `docs/audit/**`, `docs/qa/**`, `docs/product-system/**`, `docs/recovery/**`, `docs/worklog/**` | many QuoteWizard mentions | docs/history | No runtime | mixed legacy/V6 notes | Update gradually; not a blocker for runtime delete, but required for clean delete. |

No active matches found for `PricingWizard`, `QuoteEditor`, `OfferPricing`, `setShowWizard`, `setWizardSource`, `wizardSource` in the searched source surfaces. `QuotePricing` is a generic backend/frontend pricing model name, not a QuoteWizard component.

## 3. Runtime usage

1. QuoteWizard can be opened from `/quotes` through the visible `Oferta noua` button in `Quotes.tsx`.
2. QuoteWizard can also open from `/quotes` when navigation state has `openWizard`, produced by legacy intake handoff helpers.
3. For volumetric templates, `QuoteWizard` routes internally to `VolumetricLettersQuoteFlow`.
4. `VolumetricLettersQuoteFlow` can also be embedded directly in `QuoteHandoffPanel` and in legacy intake shell tests.
5. Generic non-volumetric `QuoteWizard` uses `priceQuote()` -> `POST /api/v1/entities/quotes/price`.
6. Successful creation calls `onCreated`/`onOpenCreatedQuote`, refreshes Quotes, and navigates to `/quotes/{quote_code}`.

Answers to the runtime questions:

| Question | Answer |
| --- | --- |
| De unde se poate deschide QuoteWizard? | Din `/quotes` via `Oferta noua`; din legacy intake handoff nav-state; pentru volumetric via internal routing to `VolumetricLettersQuoteFlow`. |
| Exista buton vizibil care il deschide? | Da: `Oferta noua` in pagina Oferte. |
| Este folosit pentru `Oferta noua`? | Da. |
| Este folosit pentru flow non-V6? | Da: generic/manual quote creation si legacy volumetric/V2/V4 handoff. |
| Este folosit pentru V6? | Nu ca mecanism oficial de finalizare pret. Exista doar naming/copy/compat helper vechi in jurul V6. |
| Daca il stergem, ce pagina crapa? | `Quotes.tsx` nu mai compileaza din cauza importului si renderului; `/quotes` pierde `Oferta noua`; legacy intake handoff catre `/quotes` cu `openWizard` se rupe. |
| Daca il stergem, ce teste crapa? | `QuoteWizard*.test.tsx`, mai multe `Quotes*.test.tsx` care mock-uiesc wizard-ul, `VolumetricLettersQuoteFlow*.test.tsx` daca este inclus in delete, E2E V2/V4 QuoteWizard handoff. |

## 4. V6 dependency check

V6 oficial nu depinde de QuoteWizard pentru pret final.

| Suprafata V6 | Depinde de QuoteWizard? | Observatie |
| --- | --- | --- |
| Intake V6 -> create draft | Nu functional; functie locala se numeste `handleOpenQuoteWizard`, dar apeleaza `createIntakeV6DraftQuote`. | Rename/copy cleanup separat. |
| Q-V6 quote cards | Nu. | `Quotes.tsx` foloseste detectie V6 si `IntakeV6QuoteCommercialSpinePanel`. |
| `IntakeV6QuoteCommercialSpinePanel` | Nu. | Importa V6 API: dry-run/write/handoff/snapshot/review/approval/accept/convert. |
| `handoff-to-offer` | Nu. | Creeaza/reutilizeaza draft si apeleaza V6 priced write. |
| `priced-quote/write` | Nu. | Recalculeaza dry-run server-side si scrie totaluri oficiale. |
| `priced-quote-dry-run` | Nu. | Calculeaza backend-only cu `CommercialPriceProposalService`. |
| Quote Snapshot V2 | Nu. | Cere write provenance V6, nu frontend preview. |
| Quote to order V6 | Nu functional. | Are copy de eroare care mentioneaza QuoteWizard. |

Raspunsuri explicite:

- V6 importa QuoteWizard direct? **Nu in componentele/serviciile V6 oficiale de pricing.** Exista alias/nav-state legacy `buildV6QuoteWizardNavState` si nume local `handleOpenQuoteWizard`, dar acestea nu sunt writer-ul V6.
- V6 are nevoie de QuoteWizard pentru pret final? **Nu.** Pretul final vine din `priced-quote-dry-run` + `priced-quote/write`.
- V6 poate functiona complet fara QuoteWizard? **Da pentru commercial spine/priced quote/write/snapshot/order gates**, dar pagina `/quotes` ca modul intreg nu poate compila fara inlocuirea importului generic.
- Exista copy activ care mentioneaza QuoteWizard in V6? **Da.** `intake_v6_commercial_quote_service.py` si `intake_v6_quote_to_order_service.py` contin copy activ.
- Trebuie curatata separat? **Da, cu GO owner pentru copy/UI semantics.** Eliminarea termenului nu trebuie sa elimine validarea comerciala.

## 5. Generic/non-V6 dependency check

QuoteWizard este inca necesar pentru:

- creare oferta manuala din butonul `Oferta noua`;
- oferta adhoc/generic fara Intake V6;
- template-uri non-V6 care folosesc `/api/v1/entities/quotes/price`;
- flow legacy volumetric prin `VolumetricLettersQuoteFlow`;
- WorkIntake V2 -> QuoteWizard finish display smoke;
- Intake V4 commercial handoff smoke;
- unele texte/gates pentru V3/V4 pricing review.

Backend-ul nu are serviciu `QuoteWizard`, dar generic route-ul `/api/v1/entities/quotes/price` si `QuoteOrchestrator` sunt inca active si nu trebuie sterse ca parte din delete-ul componentului.

Propunere de etichetare daca ramane temporar:

1. `ManualQuoteWizard` daca owner vrea sa pastreze rolul de oferta manuala.
2. `GenericQuoteWizard` daca rolul principal este generic/non-V6.
3. `LegacyQuoteWizard` daca decizia de produs este ca toate flow-urile noi merg spre Commercial Flow si wizard-ul exista doar pentru compat.

Preferinta audit: **GenericQuoteWizard** sau **ManualQuoteWizard** sunt mai putin toxice decat `LegacyQuoteWizard`, pentru ca butonul `Oferta noua` este inca functional, nu doar istoric.

## 6. Ce s-ar rupe daca stergem

Delete direct al `frontend/src/components/workos/QuoteWizard.tsx` ar rupe:

1. Build/compile: `Quotes.tsx` importa componenta.
2. `/quotes`: butonul `Oferta noua` nu mai are modal.
3. Legacy intake handoff cu `openWizard` catre `/quotes`.
4. Volumetric legacy routing, daca se sterge si `VolumetricLettersQuoteFlow` sau daca ramane doar prin QuoteWizard.
5. Teste unitare `QuoteWizard.vatGovernance.test.tsx` si `QuoteWizard.volumetricRouting.test.tsx`.
6. Teste `Quotes*.test.tsx` care mock-uiesc `QuoteWizard` sau verifica `Oferta noua opens generic quote wizard`.
7. E2E `work-intake-v2-to-quote-finish-display.spec.ts`.
8. E2E `intake-v4-commercial-handoff.spec.ts`.
9. Documentatie si worklogs care inca descriu QuoteWizard ca parte din V2/V3/V4/generic quote handoff.

Delete al termenului `QuoteWizard` din V6 copy fara schimbare functionala ar fi mai sigur, dar este un micro-slice separat de copy/semantics.

## 7. Conditii pentru delete safe

Delete complet devine sigur numai cand toate conditiile sunt adevarate:

1. Nu exista importuri runtime catre `QuoteWizard`.
2. Nu exista render `<QuoteWizard>` in `Quotes.tsx` sau alta pagina.
3. `Oferta noua` are inlocuitor functional pentru manual/generic quote creation.
4. Legacy intake handoff nu mai trimite `openWizard` sau are inlocuitor.
5. `VolumetricLettersQuoteFlow` este fie migrat, fie decuplat si pastrat independent.
6. V2/V4 E2E QuoteWizard smoke-uri sunt migrate/retrase explicit.
7. Testele frontend nu mai mock-uiesc/importa `QuoteWizard`.
8. `/api/v1/entities/quotes/price` are un caller nou sau este scos din scope prin decizie separata.
9. Copy V6 activa nu mai mentioneaza QuoteWizard.
10. Docs/QA/worklogs actuale sunt actualizate sau marcate legacy.
11. `Product001IntakeSpecEditor.*` artifact files au zero-import/reference check inainte de cleanup.
12. Owner a aprobat replacement-ul pentru oferta manuala.

Pentru ca mai multe conditii lipsesc, verdictul este: **NU STERGEM ACUM**.

## 8. Recomandare A/B/C/D

Recomandare: **Varianta B acum, apoi D; C doar cu GO owner.**

| Varianta | Verdict |
| --- | --- |
| A - Stergere completa acum | Respins. Cod runtime activ si teste active depind de QuoteWizard. |
| B - Deconectare din V6, pastrare generic/legacy | Recomandata imediat. V6 nu trebuie sa foloseasca termenul sau mecanismul QuoteWizard pentru pret final. |
| C - Rename controlat | Acceptabil cu GO owner: `QuoteWizard` -> `ManualQuoteWizard` sau `GenericQuoteWizard`. Are impact pe multe importuri/teste. |
| D - Inlocuire treptata | Recomandata ca directie: nou Commercial Pricing Flow pentru manual/generic, apoi stergere reala. |

Plan sigur:

1. Curata copy V6 care mentioneaza QuoteWizard, fara schimbare de flow.
2. Adauga CTA V6 separat `Creeaza oferta pretuita` cand owner aproba.
3. Pastreaza `QuoteWizard` pentru `Oferta noua` generic pana exista replacement.
4. Optional rename controlat la `ManualQuoteWizard`/`GenericQuoteWizard` cu teste dedicate.
5. Stergere doar dupa trecerea conditiilor de delete safe.

## 9. Ce NU am modificat

- Nu am sters fisiere.
- Nu am modificat UI.
- Nu am modificat copy runtime.
- Nu am modificat flow comercial.
- Nu am modificat pricing logic.
- Nu am modificat statusuri.
- Nu am modificat backend.
- Nu am facut migration DB.
- Nu am facut seed.
- Nu am intrat in ProductAggregate, Task Graph, ExecutionPlan sau Employee Mobile.
- Nu am rulat actiuni browser mutative.

## 10. Next safe step

Micro-slice recomandat dupa GO owner:

1. Copy-only V6 cleanup: inlocuieste `Requires pricing review in QuoteWizard` cu termenii reali `Flux comercial V6` / `scriere totaluri` / `pricing review`.
2. Rename local non-functional in V6 `handleOpenQuoteWizard` -> `handleCreateDraftQuote`, cu test focused pe Confirm Step.
3. Documenteaza `QuoteWizard` ca generic/manual legacy, nu V6.
4. Separat, proiecteaza replacement pentru `Oferta noua` inainte de orice delete.

## Roadmap awareness checkpoint

- Intake V6 ramane entry point.
- V6 nu trebuie sa depinda de QuoteWizard legacy.
- Eliminarea termenului QuoteWizard nu inseamna eliminarea validarii comerciale.
- `CommercialPriceProposal` calculeaza pret comercial, nu la ora/minut.
- Draft quote nu inseamna oferta finala.
- Order apare doar dupa oferta acceptata.
- ProductAggregate / Task Graph / ExecutionPlan raman out of scope.
- UI/UX nu se modifica fara GO owner.

## Verificare

Audit static prin VS Code search/read si citiri targetate. Validarea post-edit pentru acest worklog:

```powershell
git diff --check -- docs/worklog/realignment/2026-07-03_quotewizard_delete_impact_audit.md
```
