# Intake V6 full stability coherence audit

## Verdict general
- `RISKY`

Baseline-ul confirmat ramane valid:
- ReviewStep foloseste domain-based refresh.
- `markupPercent` null este reparat.
- `markLocalFinishChanged()` / `updateForm(patch)` call-site-uri vechi sunt reparate.
- `taskPreview` si `OrderBoundTaskReadiness` au refresh tintit.
- `footprintOverrideRevision` a fost eliminat.
- `intakeV6PersistedReviewRefetchKey` este legacy/compat.
- `FINISH_SETUP_PERSIST_SUCCESS` este separat de `PERSIST_SUCCESS`.
- finish save nu mai rehidrateaza analyzer state.
- UI/UX nu se redeschide.

Auditul mare nu relitigheaza aceste puncte. Verdictul `RISKY` vine din coerenta sistemului V6 in ansamblu: prea multe boundary-uri active sunt inca aliasate pe V4 sau au fallback-uri volumetric-only care limiteaza extinderea si pot produce drift semantic.

## Tabel fisiere citite

| Fisier | Zona | Motiv |
| --- | --- | --- |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | Review orchestration | baseline, local state, refetch domains, defaults |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx` | Confirm orchestration | preview fetch, workspace dependencies, handoff gating |
| `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` | workspace hook | load/persist/autosave boundary |
| `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.ts` | reducer | hydration and finish-save boundary |
| `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.ts` | Review refetch policy | active refresh mechanism |
| `frontend/src/lib/intakeV6/intakeV6Readiness.ts` | frontend readiness | step access and blockers |
| `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.ts` | handoff surfacing | blocker/warning formatting and UI status |
| `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.ts` | workspace hydration | payload -> analyzer state mapping |
| `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts` | commercial fallback logic | pricing/material/service grouping and defaults |
| `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts` | plugin registry | template variant preparedness |
| `frontend/src/lib/intakeV6/intakeV6ApiAdapter.ts` | workspace bootstrap | default template hardcoding |
| `frontend/src/lib/intakeV6/useModularFormContract.ts` | modular contract loading | contract dependency and failure mode |
| `frontend/src/lib/intakeV6/useModularFormAwareness.ts` | modular preview | read-only contract awareness boundary |
| `frontend/src/lib/intakeV6/intakeV6ModuleActivationPreview.ts` | module activation | hardcoded module states and pending logic |
| `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts` | suggested vs confirmed | artwork-only detection and fallback blocking |
| `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.ts` | operator preview compat | V4 operator-display reuse |
| `frontend/src/lib/intakeV6/intakeV6BackingMode.ts` | finish defaults | backing and emblem fallback defaults |
| `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.ts` | finish sync compat | V4 payload sync reuse |
| `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts` | confirm compat | V4 summary reuse |
| `backend/routers/intake_v6_workspaces.py` | HTTP surface | endpoint types and response models |
| `backend/services/intake_v6_workspace_service.py` | workspace truth | analysis bundle, finish save, readiness, previews |
| `backend/schemas/intake_v6.py` | schema namespace | V4 re-export surface |
| `backend/services/intake_v6_product_pricing_adapter_registry.py` | pricing registry | template builder registry and default fallback |
| `backend/services/intake_v6_pricing_input_service.py` | pricing input | adapter boundary |
| `backend/services/intake_v6_pricing_preview_sync_service.py` | derived finish sync | V4 sync reuse |
| `backend/services/intake_v6_material_breakdown_service.py` | material + nesting | V4 response reuse |
| `backend/services/intake_v6_commercial_quote_service.py` | quote handoff | quote draft, snapshot, legacy linkage |
| `backend/services/intake_v6_internal_draft_quote_policy_service.py` | handoff policy | V4 policy reuse |
| `backend/services/intake_v6_canonical_readiness_service.py` | Product Truth readiness | canonical blockers/warnings merge |
| `backend/services/intake_v6_response_normalization.py` | compat layer | string replacement normalization |
| `backend/services/intake_v6_finish_truth_service.py` | finish truth | V4 finish truth reuse |
| `backend/services/intake_v6_template_option_contract_service.py` | template contract | dossier fallback and V4 contract reuse |

## Flow real gasit

1. Workspace bootstrap porneste din `bootstrapIntakeV6Workspace()` si creeaza workspace cu template hardcodat `TPL-VOLUMETRIC-LETTERS_v2`.
2. Step 1 analizeaza SVG local, apoi `persistIntakeV6AnalysisBundle(...)` persista `svg_source`, `svg_analysis_json`, `layer_role_setup`, `quote_geometry`, `path_geometry_summary`.
3. `PERSIST_SUCCESS` rehidrateaza analyzer/workspace state din payload si muta pasul spre `review` cand analysis + layer roles sunt complete.
4. ReviewStep ramane local-first: `form`, `letterGroups`, `artworkFinishes`, `artworkComplexityDecisions`, `commercialInputs`, cu refresh pe `intakeV6ReviewRefetchDomains.ts`.
5. `saveFinishSetup(...)` foloseste acum `FINISH_SETUP_PERSIST_SUCCESS`, actualizeaza `workspace`, `readiness_status`, `finish_setup`, dar nu rescrie analyzer state.
6. Backend-ul `save_finish_setup_for_intake_v6_workspace(...)` normalizeaza finish setup, reseteaza internal draft confirmation, ruleaza `apply_v6_pricing_preview_derived_state(payload_raw)` si persista.
7. ConfirmStep reconstruieste preview-urile prin 6 fetch-uri paralele: product binding, material breakdown, nesting, pricing preview, priced quote dry run, quote handoff preview.
8. Handoff preview si internal draft policy sunt V6 namespace peste logica V4 + canonical readiness merge.
9. Material breakdown, pricing input preview, confirm summary, operator UI display si diverse finish helpers sunt inca thin wrappers/re-exports peste V4.

## Probleme pe severitate

### Severitate: ridicata

1. **V6 continua sa-si derive prea mult truth din V4, nu din namespace V6 propriu.**
   - `backend/schemas/intake_v6.py` re-exporta aproape tot din V4.
   - `backend/services/intake_v6_finish_truth_service.py` re-exporta direct normalizarea V4.
   - `backend/services/intake_v6_pricing_preview_sync_service.py`, `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.ts`, `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts`, `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.ts` continua acelasi model.
   - Efect: orice schimbare V4 poate altera V6 fara contract V6 explicit.

2. **ConfirmStep inca foloseste un trigger mai larg pe `ws?.updated_at`.**
   - `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx` refetch-uieste toate preview-urile pe `[ws?.id, ws?.updated_at, clientAnalysisHash]`.
   - ReviewStep nu mai are refetch global, dar ConfirmStep inca are un boundary mai gros si poate produce under/over-refresh pe preview-urile care nu depind semantic de orice mutatie de workspace.

3. **Registrul de template/plugin este de facto single-variant.**
   - `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts` are un singur plugin activ: `TPL-VOLUMETRIC-LETTERS_v2`.
   - `backend/services/intake_v6_product_pricing_adapter_registry.py` are un singur adapter activ si `default_intake_v6_product_pricing_adapter()` intoarce mereu primul entry.
   - Efect: pregatirea pentru Vector Litere / Vector Atipic este inca partiala; varianta necunoscuta cade pe fallback volumetric.

4. **Contractul/dossier-ul Product Truth are fallback static, nu boundary ferm.**
   - `backend/services/intake_v6_template_option_contract_service.py` foloseste `FALLBACK_DOSSIER_VARIANTS` si evalueaza contractul prin V4.
   - Daca dossier-ul lipseste sau este incomplet, V6 nu se blocheaza structural; intra pe fallback static.
   - Efect: alinierea la Product Truth ramane partial garantata.

5. **Coverage-ul pentru artwork-only boundary este fragil si neexecutabil complet in mediul curent.**
   - `intakeV6ArtworkOnlyGuard.test.ts` pica din cauza fixture-elor externe lipsa sub `fisiere-teste`, nu din logica testata.
   - Asta lasa un boundary important pentru Vector Atipic / print-polichromie fara regresie automata verde in sesiunea actuala.

### Severitate: medie

6. **Hardcodarile de finish/default normalizeaza silent si volumetric-only.**
   - `IntakeV6ReviewStep.tsx` construieste implicit finish setup cu `oracal_651`, `led_modules`, `forex`, `direct_wall`, `30x30x1.5`, `forex_10_no_bevel`.
   - `frontend/src/lib/intakeV6/intakeV6BackingMode.ts` normalizeaza necunoscutele la `forex_10_no_bevel` si `area_lit`.
   - Efect: variante noi sau payload incomplet sunt absorbite fara semnal clar.

7. **Material + serviciu pentru ofertare sunt clasificate prin regex si fallback.**
   - `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts` mapeaza categorii prin regex si trimite necunoscutele in `boards`.
   - Efect: pregatirea pentru print/laminare/aplicare exista ca intentie, dar boundary-ul nu este suficient de tipat/canonic.

8. **Response normalization pe backend este string-replace based.**
   - `backend/services/intake_v6_response_normalization.py` inlocuieste `V4` cu `V6` in stringuri/list/dict.
   - Efect: compat util, dar fragil pentru extindere si debugging.

9. **Quote handoff si snapshot-ul V6 folosesc structuri V4 active.**
   - `backend/services/intake_v6_commercial_quote_service.py` foloseste `build_v4_quote_draft_payload`, `build_v4_quote_snapshot_payload`, linkage legacy `intake_v4_linkage_v1`.
   - Efect: V6 handoff merge, dar boundary-ul comercial nu este curat separat.

10. **Module activation preview ramane informational si codificat pe module volumetric specifice.**
   - `frontend/src/lib/intakeV6/intakeV6ModuleActivationPreview.ts` decide stari pentru `geometry_svg`, `debitare_fata`, `debitare_spate`, `modelare_cant`, `sistem_led`, `finisaje`, `structura_suport`.
   - Efect: bun ca awareness, dar nu este inca un boundary generic pentru alte produse.

### Severitate: scazuta

11. **Confirm summary si mai multe ecrane de operator raman compat wrappers.**
12. **Unele mesaje/operator hints sunt inca specifice pilotului volumetric actual.**

## Hardcodari gasite

- `frontend/src/lib/intakeV6/intakeV6ApiAdapter.ts`: bootstrap pe `TPL-VOLUMETRIC-LETTERS_v2`.
- `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts`: un singur plugin activ pentru Litere volumetrice.
- `backend/services/intake_v6_product_pricing_adapter_registry.py`: un singur adapter activ; fallback la primul.
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`: defaults volumetric pentru face finish, lighting, mounting, backing, template material.
- `frontend/src/lib/intakeV6/intakeV6BackingMode.ts`: fallback `forex_10_no_bevel`, `area_lit`.
- `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts`: commercial defaults `35 / 0 / 19 / 0` si clasificare regex pentru materiale/operatii.
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts`: mesaje si decizie strans legate de template-ul volumetric curent.
- `frontend/src/lib/intakeV6/intakeV6ModuleActivationPreview.ts`: state machine pe module fixe.

## Dependente fragile

- namespace V6 -> V4 schema re-exports in `backend/schemas/intake_v6.py`
- V6 finish truth -> V4 finish truth in `backend/services/intake_v6_finish_truth_service.py`
- V6 pricing preview derived state -> V4 pricing preview sync in `backend/services/intake_v6_pricing_preview_sync_service.py`
- V6 material breakdown -> V4 material breakdown + response normalization in `backend/services/intake_v6_material_breakdown_service.py`
- V6 quote handoff -> V4 quote draft/snapshot builders in `backend/services/intake_v6_commercial_quote_service.py`
- frontend V6 finish payload sync / confirm summary / operator display -> V4 wrappers
- ConfirmStep depends on six previews succeeding in one effect; one failure nulls broad preview context

## Cod mort / compat legacy

- `intakeV6PersistedReviewRefetchKey` ramane legacy/compat, nu mecanism activ.
- `intake_v4_linkage_v1` este inca citit/migrat in `backend/services/intake_v6_commercial_quote_service.py`.
- `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.ts` si `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts` sunt compat wrappers active.
- `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.ts` este compat wrapper activ.
- `backend/services/intake_v6_response_normalization.py` este un compat layer operational, nu cod mort, dar este debt activ.

## Product Truth / readiness audit

### Ce este bine acum
- ReviewStep nu mai depinde de `workspace.updated_at` pentru refetch global.
- `FINISH_SETUP_PERSIST_SUCCESS` limiteaza finish save la state-ul necesar.
- `backend/services/intake_v6_canonical_readiness_service.py` adauga canonical blockers/warnings peste politica de handoff.
- `backend/services/intake_v6_workspace_service.py` mentine `readiness_status` derivat clar: SVG -> layer roles -> finish confirmed -> ready.

### Ce ramane slab
- Product Truth este inca partial validat prin V4 contract evaluation si fallback dossier static.
- Suggested vs confirmed vs fallback nu sunt complet separate la nivel de produs nou: artwork-only si modular preview sunt puternic volumetric-biased.
- ConfirmStep refetch-uieste preview-uri larg dupa orice `updated_at`, ceea ce nu rupe baseline-ul, dar poate masca dependente semantice prea late.

## Pregatire pentru Vector Litere / Vector Atipic

### Ce exista
- artwork-only guard si warnings pentru fisier non-volumetric
- plugin/adapter registry introdus, chiar daca minimal
- modular contract + modular awareness ca suprafata de extensie

### Ce lipseste
- mai mult de un plugin/adapter activ
- boundary de template necunoscut care sa blocheze clar, nu sa cada pe volumetric fallback
- contract V6 mai putin dependent de V4 pentru variante atipice
- coverage verde pentru artwork-only / mixed-letter / artwork fixtures

Concluzie: pregatirea este **partiala**. Arhitectura indica directia buna, dar implementarea curenta este inca pilot-centric.

## Pregatire pentru print / laminare / aplicare: material + serviciu

### Ce exista
- clasificare frontend pentru filme/laminare/print in `intakeV6OfferCalculator.ts`
- material breakdown si operation rows separate in UI
- artwork-only surfacing si handoff warnings

### Ce lipseste
- tipare canonice separate pentru material vs serviciu din backend, fara regex/fallback
- adaptere de pricing separate pentru produse sau scenarii print-dominante
- boundary mai explicit intre volumetric letters si artwork/print-only products

Concluzie: exista un strat de pregatire util pentru audit si operator awareness, dar nu inca un boundary suficient de robust pentru a considera print/laminare/aplicare ca domeniu curat, extensibil si low-risk.

## Teste rulate

- `pnpm.cmd vitest run src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts src/lib/intakeV6/intakeV6ModuleActivationPreview.test.ts src/lib/intakeV6/intakeV6OfferCalculator.test.ts`
  - passed: reducer, review refetch domains, module activation preview, offer calculator
  - failed: artwork-only guard suite, din cauza fixture-elor lipsa din `fisiere-teste`, nu dintr-o asertie functională demonstrată in output
- `pnpm.cmd exec tsc --noEmit --pretty false`
  - fara erori TypeScript afisate; output-ul a ramas doar cu warning-ul pnpm despre `pnpm.overrides`

## Zone stabile

- ReviewStep stabilization baseline se mentine.
- finish-save hydration boundary nou este coerent.
- workspace reducer si review refetch domain tests sunt verzi.
- module activation preview testele sunt verzi.
- offer calculator tests sunt verzi dupa normalizarea commercial inputs.

## Recomandari pe micro-slice-uri mici

1. **Micro-slice A: restrange trigger-ele ConfirmStep pe preview groups semantice, nu pe `ws.updated_at`.**
   - tinta: `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`
   - scop: reduce risc de stale/overfetch in afara ReviewStep, fara UI changes.

2. **Micro-slice B: introduce explicit `unknown_template` fail-safe in product plugin + pricing adapter registry.**
   - tinta: `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts`, `backend/services/intake_v6_product_pricing_adapter_registry.py`
   - scop: sa nu cada silent pe volumetric fallback cand apare varianta noua.

3. **Micro-slice C: stabilizeaza artwork-only regression fixtures in repo/test harness.**
   - tinta: `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts`
   - scop: coverage verde pentru boundary-ul Vector Atipic / artwork-only.

4. **Micro-slice D: extrage 2-3 constante volumetric implicite intr-un `pilot defaults` owner file explicit.**
   - tinta: ReviewStep defaults + backing defaults + commercial defaults.
   - scop: sa se vada clar ce este pilot fallback si ce este truth canonic.

5. **Micro-slice E: marcheaza explicit in contract response cand se foloseste fallback dossier static.**
   - tinta: `backend/services/intake_v6_template_option_contract_service.py`
   - scop: separa contract adevarat de fallback acceptat temporar.

## Ce NU trebuie facut acum

- nu redeschide refactorul ReviewStep
- nu redesena UI/UX
- nu construi formular nou
- nu intra in ProductAggregate / Task Graph / ExecutionPlan
- nu face pricing rewrite sau CommercialPriceProposal rewrite
- nu muta calculul comercial la ora/minut
- nu incerca acum un mega-port V4 -> V6 pentru toate serviciile

## Next safe step

- Primul micro-slice recomandat: **restrangerea trigger-elor ConfirmStep pe preview groups semantice, dupa modelul ReviewStep, fara a muta responsabilitati de UI sau a reface handoff-ul.**

## Cat sunt in directia stabilita
- `86/100%`

Direcția este corectă și baseline-ul de stabilizare ține. Scorul nu este mai mare fiindcă V6 rămâne încă un strat pilot peste V4, cu pregătire parțială pentru variante noi și cu câteva fallback-uri care pot ascunde drift semantic.