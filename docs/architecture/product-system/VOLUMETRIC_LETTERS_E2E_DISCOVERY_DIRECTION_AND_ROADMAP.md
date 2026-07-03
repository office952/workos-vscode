# Volumetric Letters E2E Discovery Direction and Roadmap

**Date:** 2026-07-01  
**Status:** Docs-only strategic reconciliation  
**Scope:** Volumetric letters E2E direction, implementation order, and re-audit gates  
**Runtime anchor:** `gradi-curat.svg` in Intake V6 workspace `IV6-BB8EE3F8`

---

## Purpose

This document reconciles the new Intake V6 Product Truth contracts, the reusable component contracts, the readiness/UI-state discoveries, the `gradi-curat.svg` audit, and the older WorkOS/ProductSystem architecture documents.

It does not implement anything. It defines the official direction and the order in which implementation may safely proceed.

Core rule:

- start from Intake V6 and Product Truth;
- preserve the existing Straturi / Review / Confirmare flow;
- modularize the existing form gradually;
- do not jump to ProductAggregate, ExecutionPlan, task materialization, machines, employees, or Employee Mobile before Product Truth and snapshots are stable.

---

## E2E Discovered Flow

| Flow layer | Role | What exists now | Validated | Partial | Missing | What must NOT be done yet |
|---|---|---|---|---|---|---|
| Work Intake | captures request context and product intent | legacy Work Intake and V6 entry paths exist | volumetric request can lead into Intake V6 | full V6-native handoff remains transitional | clean canonical bridge from request to V6 Product Truth | do not rebuild Work Intake or force `/price` shortcuts |
| Product System template selection | selects `TPL-VOLUMETRIC-LETTERS_v2` and allowed product path | active template and dossier paths exist | template binding is visible in V6 workspace | old/current docs mix v1 and v2 concepts | owner-approved component contract source of truth | do not use ProductSystem to repair runtime missing truth |
| Intake V6 workspace | runtime workspace for product truth capture | `/intake-v6/:id/operator` flow exists | `IR-MR18L96M` / `IV6-BB8EE3F8` is live and usable | payload still carries V4 aliases and fallback values | canonical Product Truth payload | do not create sessions, quote/order/execution, or materialize |
| SVG upload / SVG Analyzer | parses SVG, geometry, colors, and candidates | upload/analyzer path exists | `gradi-curat.svg` parsed with geometry and groups | analyzer output is suggestion-level truth | clearer source-layer metadata in canonical display contract | do not let analyzer decide commercial truth |
| Layer/group detection | identifies native layers and detected groups | six groups detected for `gradi-curat.svg` | `Layer_x0020_1` source and six groups verified | pseudo-groups remain internal technical identity | durable operator-friendly display everywhere | do not expose `pseudo` as primary operator title |
| Layer role suggestion | proposes `face` / `printed_artwork` roles | auto roles exist | 4 face + 2 printed artwork suggestions verified | suggestions still pending confirmation | confirmed role map | do not treat suggestions as confirmed |
| Operator confirmation | converts suggestion to accepted Product Truth | confirm-all and per-layer role controls exist | flow stays blocked until confirmations | Review cannot safely proceed until layer roles confirmed | explicit Product Truth confirmation object | do not bypass `layer_roles_incomplete` |
| Review tehnic per layer/group | captures finish, return, lighting, mounting | Review sections exist | existing UI has useful controls and payload hydration | fallback/hydrated values can look final | component-owned questions and state labels across Review | do not redesign the wizard or create a separate form |
| Modular Form System | asks component-specific missing inputs | form-contract service exists as read-only contract | field/module mapping direction exists | not all component questions are native/canonical | component-owned questions for face/back/cant/finish/electrical/support/mounting | do not hardcode ad hoc per-product forms |
| Product Truth | canonical confirmed product state | documented target exists | Product Truth boundary is now canonical docs | runtime canonical output is not complete | canonical payload separating suggested/confirmed/fallback/manual/blocked/warning | do not send truth gaps to Pricing Registry |
| ProductDefinition | consumes Product Truth and activates modules | builder direction exists | target architecture says no pricing | current runtime still transitional | consume only canonical Product Truth | do not let ProductDefinition guess missing fields or price |
| ProductSystem / Dossier / active modules | keeps component contracts, variants, and allowed modules | dossier/module docs exist | direction remains valid | some old docs are design-time or legacy | reusable component contract aligned to form fields | do not make dossier runtime execution truth |
| CommercialPriceProposal / Offer | computes client commercial proposal | commercial/internal separation doc exists | no hourly commercial pricing is canonical | legacy cost-plus paths still need separation later | unit-based commercial rules from complete truth | do not price by hour/minute or repair missing truth |
| Quote Snapshot | freezes accepted offer truth | older Step 8 docs and worklogs exist | snapshot freeze direction remains valid | not the current slice | frozen commercial quote snapshot after readiness | do not keep quote dependent on mutable Intake workspace |
| Order Snapshot | freezes accepted order truth | older Step 8/9 docs exist | order snapshot direction remains valid | not the current slice | stable order truth for downstream technical graph | do not read live Intake after order freeze |
| ProductAggregate | technical graph from frozen order/product definition | target docs exist | role is clear as later read model | should not be started before snapshots stabilize | graph from Order Snapshot + modules | FORBIDDEN_NOW if Product Truth / snapshots are unstable |
| Task Graph | derives tasks from components/modules | historical docs mention task graph gaps | DAG direction remains valid | `ProductAggregateTaskRule` still future gap | task DAG from active modules | FORBIDDEN_NOW as a parallel catalog or materialization shortcut |
| ExecutionPlan | schedules tasks and workcenters after order | target docs/worklogs exist | must come after Order/ProductAggregate | current docs note linearization risks | stable DAG and scheduling boundary | FORBIDDEN_NOW before Task Graph and Order Snapshot |
| Workcenters / Utilaje | capacity and execution planning resources | machine/workcenter concepts exist | internal-only planning role is valid | mapping is future | operations-to-workcenter mapping | do not turn machines into client hourly tariff |
| Employees / Skills / Capacity | assignment and capacity planning | employee modules exist elsewhere | must remain downstream execution concern | not part of Intake/Product Truth | skills/capacity after plan exists | do not use employees as quote hourly pricing |
| ExecutionReality | captures actuals after production | older actuals/profitability docs exist | actuals are post-job learning | not current slice | actual time/material feedback loop | do not rewrite accepted commercial price retroactively |
| Employee Mobile later | mobile execution UI for assignments/actuals | exists elsewhere as separate domain | final-final placement confirmed | not part of current product truth work | only after ExecutionPlan/Reality stable | do not enter Employee Mobile now |

Official E2E spine:

```text
Work Intake
-> Product System template selection
-> Intake V6 workspace
-> SVG upload / SVG Analyzer
-> layer/group detection
-> layer role suggestion
-> operator confirmation
-> Review tehnic per layer/group
-> Modular Form System
-> Product Truth
-> ProductDefinition
-> ProductSystem / Dossier / active modules
-> CommercialPriceProposal / Offer
-> Quote Snapshot
-> Order Snapshot
-> ProductAggregate
-> Task Graph
-> ExecutionPlan
-> Workcenters / Utilaje
-> Employees / Skills / Capacity
-> ExecutionReality
-> Employee Mobile later
```

---

## gradi-curat.svg Findings

| Fact | Value |
|---|---|
| file | `gradi-curat.svg` |
| route | `/intake-v6/IR-MR18L96M/operator` |
| workspace | `IV6-BB8EE3F8` |
| template | `TPL-VOLUMETRIC-LETTERS_v2` |
| readiness | `layer_roles_incomplete` |
| detected groups | 6 |
| suggested `face` groups | 4: `maria`, `soare`, `ana`, `gradinita` |
| suggested `printed_artwork` groups | 2: `logo stanga`, `logo dreapta` |
| dimensions | `5086.99 x 600.03 mm` |
| letter count | `19` |
| face area | `1.2638 mp` |
| return perimeter | `29.9098 ml` |
| native source layer | `Layer_x0020_1` |

Micro-slice result:

- `pseudo:*` no longer appears as the primary title in the main Straturi UI;
- `Grup detectat: maria`, `soare`, `ana`, `gradinita`, `logo stanga`, `logo dreapta` are visible;
- `Layer sursa: Layer_x0020_1` is visible;
- `SUGGESTED` and `NEEDS_CONFIRMATION` are visible and distinct;
- internal identities such as `pseudo:maria` remain unchanged;
- the flow remains correctly blocked until operator confirmation.

Mandatory conclusion:

`Pricing Registry este pregatit; blockerul real este Product Truth incomplet / layer_roles_incomplete.`

---

## Old Documentation Reconciliation

| Document | Ce sustine | Este inca valid? | Ce a fost confirmat in runtime/cod? | Ce este depasit? | Ce trebuie pastrat in directia oficiala? | Status |
|---|---|---|---|---|---|---|
| `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md` | Intake V6 produces Product Truth; analyzer suggests; downstream consumes | yes | runtime confirms `layer_roles_incomplete` blocks offer | runtime canonical output not fully implemented | source separation and spine | CANONICAL_DIRECTION |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md` | reusable components compose volumetric Intake V6 | yes | `gradi-curat.svg` validates face/artwork/cant/lighting/mounting component needs | not all component fields exist as canonical runtime fields | component map and boundaries | CANONICAL_DIRECTION |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md` | quote unlock requires Product Truth, not just geometry/prices | yes | UI/API state remains blocked on `layer_roles_incomplete` | none as direction; implementation still partial | blocker taxonomy and quote gates | VALIDATED |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md` | UI must separate suggested/confirmed/fallback/blocked/warning/ready | yes | micro-slice implemented first badges in Straturi/Review display | broader Review/artwork/readiness panel badge coverage still pending | UI state vocabulary | PARTIAL |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_EXISTING_FORM_TO_MODULAR_FORM_UI_CONTRACT.md` | requested exact filename for existing-form contract | no file found in this export | content appears folded into UI State Contract instead | filename/deliverable mismatch | preserve idea: existing UI is kept and modularized | NEEDS_VERIFICATION |
| `docs/architecture/INTAKE_V6_MODULAR_FORM_CONTRACT.md` | Step 5 read-only modular form map from modules to workspace fields | partially | form-contract endpoint/service direction exists | V4 aliasing and Step language are transitional | form contract is complementary, not replacement UI | LEGACY_OR_TRANSITIONAL |
| `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` | commercial pricing must be separated from internal cost/minutes | yes | micro-slices preserved no hourly commercial pricing | legacy cost-plus risks may still exist elsewhere | CommercialPriceProposal vs CostEngine separation | CANONICAL_DIRECTION |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md` | older current state for volumetric v1/process maturity | partially | process discipline and quote gate concepts remain useful | manual baseline, old ports, v1 form/QuoteWizard context are not the current Intake V6 truth | bounded-build caution and no invented geometry | LEGACY_OR_TRANSITIONAL |
| `docs/architecture/realignment/03_PRODUCT_DEFINITION_COMPILER.md` | ProductDefinition compiles product structure and modules, no pricing | yes as target | service exists; direction matches new Product Truth docs | should consume Product Truth, not raw transitional fallback chaos | ProductDefinition after Intake V6 truth | CANONICAL_DIRECTION |
| `docs/architecture/realignment/04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md` | ProductAggregate is later technical read model | yes as target | older docs identify risks of parent-only/parallel paths | implementing now would be premature | Aggregate after Order/ProductDefinition stability | DOCUMENTED_NOT_IMPLEMENTED |
| `docs/architecture/realignment/08_PRICING_REGISTRY_SEPARATION.md` | Pricing Registry separates material, commercial, internal, capacity, analytics | yes as target | current work preserved Pricing Registry boundary | target UI/API separation is not this slice | no Product Truth repair in Pricing Registry | CANONICAL_DIRECTION |
| `docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md` | requested old execution DAG doc | file not found in this export | older worklogs indicate execution/task graph gaps | exact doc absent | preserve principle: ExecutionPlan later, DAG not catalog | NEEDS_VERIFICATION |
| `docs/worklog/realignment/2026-07-01_intake_v6_operator_friendly_labels_state_badges.md` | UI-only micro-slice passed | yes | Straturi visual verification passed | Review live verification limited by correct blocker | labels/badges as first implemented slice | VALIDATED |
| `docs/worklog/realignment/2026-07-01_volumetric_letters_docs_reconciliation.md` | older docs reconciliation and task/machine contracts | partially | identifies ProductAggregateTaskRule and ExecutionPlan gaps | recommends AggregateTaskRule next, but current direction says still not next | gap list as future evidence | PARTIAL |

Rule applied: no historical document is deleted. Documents are reconciled into current official direction.

---

## Direction Conclusion

| Question | Answer |
|---|---|
| Pastram UI-ul Intake V6 existent? | Yes. Straturi / Review / Confirmare stay as the base. |
| Il rescriem sau il modularizam? | Modularize gradually; no greenfield form. |
| Pornim de la ProductAggregate sau de la Intake V6? | Start from Intake V6 and Product Truth. |
| SVG Analyzer decide sau doar sugereaza? | Suggests only; operator confirms. |
| Form System ce rol are? | Asks missing component questions and structures inputs. |
| Product Truth ce rol are? | Canonical confirmed product state before quote/order/execution. |
| ProductDefinition ce rol are? | Consumes Product Truth and activates/deactivates modules; no pricing. |
| ProductSystem / Dossier ce rol are? | Holds reusable component contracts, variants, allowed options, module definitions. |
| Pricing Registry ce rol are? | Supplies prices/configuration coverage; does not resolve missing Product Truth. |
| CommercialPriceProposal ce rol are? | Computes client commercial proposal, not hourly/minute pricing. |
| CostEngine ce rol are? | Internal-only estimates, capacity, efficiency, post-job learning. |
| ProductAggregate cand intra? | After Order Snapshot / stable ProductDefinition, not now. |
| ExecutionPlan cand intra? | After ProductAggregate/Order and stable task graph, not now. |
| Utilajele si angajatii cand intra? | Planning/execution/capacity after task graph; not as client hourly tariff. |
| Employee Mobile cand intra? | Final-final after ExecutionPlan and ExecutionReality are stable. |

Mandatory conclusion:

- pastram UI-ul Intake V6 existent ca baza;
- il modularizam treptat;
- Intake V6 produce Product Truth;
- SVG Analyzer sugereaza, nu decide;
- Form System cere inputurile lipsa;
- operatorul confirma;
- ProductDefinition consuma Product Truth;
- ProductSystem/Dossier pastreaza contractul componentelor;
- Pricing Registry rezolva preturi/configuratii, nu lipsuri de Product Truth;
- CommercialPriceProposal calculeaza pret comercial, nu la ora/minut;
- CostEngine ramane internal-only;
- ProductAggregate vine dupa Order Snapshot;
- ExecutionPlan vine dupa ProductAggregate/Order;
- utilajele si angajatii intra in planificare/executie/capacitate, nu ca tarif orar client;
- Employee Mobile ramane final-final.

---

## Canonical Decisions

| Decision | Final direction | Evidence | What this forbids | Status |
|---|---|---|---|---|
| Intake V6 este entry point | Start E2E implementation from Intake V6 | Product Truth docs, live route | starting from Aggregate/Execution | CANONICAL |
| UI existent se pastreaza | Straturi/Review/Confirmare remain | UI contract + micro-slice | redesign or new wizard | CANONICAL |
| formular modular, nu formular separat per produs | component questions drive form | reusable components contract | duplicated product-specific forms | CANONICAL |
| setari per layer/per group | support per detected group | UI state contract | global-only finish/role truth | CANONICAL |
| pseudo-groups afisate operator-friendly | primary UI uses detected group labels | micro-slice worklog | showing `pseudo:*` as main title | VALIDATED |
| suggested != confirmed | explicit state separation | readiness/UI docs + micro-slice | quote unlock from suggestions | VALIDATED |
| fallback/hydrated != confirmed | fallback visibly separate | UI state docs + micro-slice | treating payload defaults as truth | PARTIAL |
| Product Truth inainte de quote | minimum truth gates quote | readiness boundary | pricing preview from incomplete truth | CANONICAL |
| Pricing Registry nu rezolva lipsa de truth | pricing only after truth | Product Truth and pricing docs | sending layer/finish gaps to registry | CANONICAL |
| CommercialPriceProposal fara hourly pricing | unit/commercial rules, no hour/minute tariff | commercial vs internal cost doc | client hourly pricing | CANONICAL |
| CostEngine internal-only | minutes/capacity internal | Product Truth + pricing docs | replacing commercial price with internal cost | CANONICAL |
| ProductDefinition consuma Product Truth | no guessing | ProductDefinition realignment doc | ProductDefinition inventing missing fields | CANONICAL |
| ProductSystem/Dossier tine contractul | component vocabulary and allowed variants | reusable components + old form contract | dossier as runtime truth override | CANONICAL |
| ProductAggregate later | technical graph after snapshots | aggregate realignment doc | implementing Aggregate before truth/snapshot stability | FORBIDDEN_NOW |
| ExecutionPlan later | after Aggregate/Order/task graph | realignment docs/worklogs | pre-order execution planning | FORBIDDEN_NOW |
| utilaje/workcenters later | planning/capacity only | pricing separation | machine hourly client tariff | LATER |
| angajati/skills/capacity later | execution/capacity only | E2E direction | employee hourly client tariff | LATER |
| Employee Mobile final-final | after execution model is stable | Product Truth and execution docs | entering mobile now | FINAL_FINAL |

---

## Strategic Implementation Roadmap with Re-audit Gates

| Phase | Layer | Goal | Why this comes now | Depends on | Deliverable | Verification method | Re-audit gate | Risk if skipped | Status | Owner GO required? |
|---|---|---|---|---|---|---|---|---|---|---|
| Phase 0 — Preserve and document current Intake V6 truth | Intake V6 docs | keep existing UI; document Straturi/Review/Confirmare; no new form | establishes factual base | existing V6 route/docs | docs contracts | read docs + live route | after docs, verify UI and docs say same thing | redesign from wrong assumptions | NOW | NO |
| Phase 1 — Operator-friendly layer/group truth | Intake V6 UI display | native layer vs detected group clear; `pseudo` not main title; suggested/fallback not confirmed | removes operator ambiguity without logic change | Phase 0 | display labels + badges | focused tests + `gradi-curat.svg` visual audit | after micro-slice, re-audit Straturi + Review and confirm no analyzer/payload/readiness change | operator treats suggestions as truth | NOW | NO |
| Phase 2 — Modular Form component questions | Form System / Review | each component owns required questions: face, back, cant, finish, electrical, support, mounting | next missing truth is form input, not downstream graph | Phase 1 | component question contract/UI slice | UI Review audit + component tests | verify no separate per-product forms and no ad hoc hardcoding | Product Truth remains partial | NEXT | YES |
| Phase 3 — Product Truth canonical output | Intake payload boundary | save canonical truth separating suggested/confirmed/fallback/manual/blocked/warning | ProductDefinition needs clean input | Phase 2 | canonical Product Truth payload contract/runtime | payload audit + quote gate audit | verify quote preview stays blocked until minimum truth; Pricing Registry does not receive truth gaps | downstream invents fields | NEXT | YES |
| Phase 4 — ProductDefinition consumes Product Truth | ProductDefinition | no guessing; activate/deactivate modules; emit blockers/warnings; no pricing | follows canonical truth | Phase 3 | ProductDefinition consumption path | builder audit | verify each module activation has Product Truth source | ProductDefinition becomes hidden form/pricing logic | LATER | YES |
| Phase 5 — ProductSystem / Dossier modular contract | ProductSystem/Dossier | hold component contracts, allowed variants, questions, outputs, active modules | after truth shape is clear | Phase 4 | dossier/component alignment | template/dossier vs Form System audit | verify reusable components and no dead pieces | ProductSystem drifts from runtime form | LATER | YES |
| Phase 6 — CommercialPriceProposal / Offer | Commercial layer | client price from complete Product Truth and Pricing Registry coverage; no hourly pricing | only meaningful after truth is complete | Phase 3/4 | commercial proposal contract/runtime | commercial vs internal cost audit | verify minutes never become client price; truth gaps not pricing issues | wrong pricing philosophy | LATER | YES |
| Phase 7 — Quote Snapshot | Quote | freeze approved offer truth | prevents mutable workspace drift | Phase 6 | quote snapshot | snapshot audit | verify quote no longer depends live on mutable workspace | offer changes after acceptance | LATER | YES |
| Phase 8 — Order Snapshot | Order | freeze accepted order truth for downstream | ProductAggregate needs stable order truth | Phase 7 | order snapshot | quote-vs-order audit | verify layer/component/finish/support decisions survive | execution reads unstable Intake | LATER | YES |
| Phase 9 — ProductAggregate | Technical graph | build graph from Order Snapshot + active modules; no field invention | only after snapshots stable | Phase 8 | aggregate graph | full Intake -> Order Snapshot audit before start | STOP if Product Truth/Order Snapshot unstable | graph repairs Intake incorrectly | FORBIDDEN_NOW | YES |
| Phase 10 — Task Graph / Operations | Operations DAG | tasks from modules; no parallel catalog; T06 vs T19E represented | needs Aggregate graph | Phase 9 | task DAG contract/runtime | aggregate-to-task audit | verify tasks come from active modules | task catalog diverges | FORBIDDEN_NOW | YES |
| Phase 11 — ExecutionPlan | Execution planning | schedule tasks and link workcenters; no Intake influence | needs stable task graph | Phase 10 | ExecutionPlan | Order + Aggregate + Task Graph audit | STOP if task graph unstable | premature materialization | FORBIDDEN_NOW | YES |
| Phase 12 — Utilaje / Workcenters | Capacity/execution | map CNC/modelare/print/laminare/electrica/montaj to capacity | after plan shape exists | Phase 11 | workcenter mapping | operations/workcenters audit | verify not client hourly tariff | machines leak into offer pricing | LATER | YES |
| Phase 13 — Angajati / Skills / Capacity | HR/capacity | skills/roles/capacity for planning/reality | after workcenters | Phase 12 | skills/capacity mapping | HR/skills vs execution audit | verify no commercial hourly pricing | employees become quote tariff | LATER | YES |
| Phase 14 — ExecutionReality | Actuals | actual time/materials; efficiency; internal feedback | after plan execution exists | Phase 11/13 | actuals feedback loop | actuals vs estimates audit | verify actuals do not rewrite accepted offer | retroactive repricing | LATER | YES |
| Phase 15 — Employee Mobile | Mobile execution | assign/start/stop/actuals mobile | only after execution model stable | Phase 14 | mobile execution slice | ExecutionPlan + Reality + permissions audit | STOP if runtime execution unstable | mobile records bad model | FINAL-FINAL | YES |

Any phase that jumps directly into ProductAggregate, ExecutionPlan, task materialization, machines, employees, or Employee Mobile before complete Product Truth is `FORBIDDEN_NOW`.

---

## Re-audit Checkpoint Catalogue

| Checkpoint | When triggered | What to audit | Evidence required | Stop condition | Can proceed if | Owner GO required? |
|---|---|---|---|---|---|---|
| After UI labels/state badges | after micro-slice | Straturi + Review display only | tests, visual route, no payload/analyzer diff | readiness/analyzer changed | labels only changed and blocker remains | NO |
| Before component form implementation | before Phase 2 | existing UI controls vs component questions | UI inventory + reusable component contract | proposes new form or redesign | keeps Review and component ownership | YES |
| After component form implementation | after Phase 2 | form fields, ownership, no ad hoc hardcoding | component tests + `gradi-curat.svg` audit | separate per-product forms appear | questions come from components | YES |
| Before Product Truth canonical payload | before Phase 3 | payload contract and migration risk | schema/docs plan | would break existing workspace | additive/compatible plan exists | YES |
| After Product Truth payload | after Phase 3 | suggested/confirmed/fallback/manual separation | payload sample + readiness tests | quote unlocks too early | blockers remain correct | YES |
| Before ProductDefinition | before Phase 4 | Product Truth completeness | payload + module activation map | ProductDefinition must guess | every activation source is truth | YES |
| Before ProductSystem/Dossier changes | before Phase 5 | dossier vs form fields | template/dossier diff | dossier used as runtime override | dossier only constrains/contracts | YES |
| Before CommercialPriceProposal changes | before Phase 6 | commercial/internal boundary | pricing docs + truth sample | hourly/minute commercial rule appears | unit rules and truth complete | YES |
| Before Quote Snapshot | before Phase 7 | offer freeze semantics | quote payload + snapshot contract | quote still mutable/live-dependent | accepted truth freezes | YES |
| Before Order Snapshot | before Phase 8 | order conversion truth preservation | quote/order comparison | layer/component decisions lost | snapshot preserves decisions | YES |
| Before ProductAggregate | before Phase 9 | Intake -> Order Snapshot stability | full E2E audit | Product Truth or Order Snapshot unstable | frozen order truth exists | YES |
| Before Task Graph | before Phase 10 | aggregate module graph | aggregate audit | tasks from parallel catalog | tasks derive from active modules | YES |
| Before ExecutionPlan | before Phase 11 | task graph DAG stability | task graph audit | linear/unstable task graph | DAG and dependencies are coherent | YES |
| Before utilaje/workcenters | before Phase 12 | operation-to-workcenter mapping | operations mapping | machine rates leak as client pricing | capacity-only semantics clear | YES |
| Before angajati/skills/capacity | before Phase 13 | HR/skills model vs execution | skills/capacity plan | employees become pricing basis | downstream-only model exists | YES |
| Before ExecutionReality | before Phase 14 | actuals vs estimates boundary | execution plan + actuals contract | actuals rewrite offer | actuals internal-only | YES |
| Before Employee Mobile | before Phase 15 | execution runtime and permissions | plan/reality/permissions audit | execution model unstable | stable execution model exists | YES |

---

## Open Gaps After Reconciliation

| Gap | Layer | Severity | Why it matters | Safe next action | Re-audit needed after action? | Should implement now? |
|---|---|---|---|---|---|---|
| `layer_roles_incomplete` | Intake V6 / Straturi | BLOCKER | quote cannot trust product/artwork semantics | keep blocked; improve display only next | YES | NO, unless owner asks confirmation workflow changes |
| face layer confirmation | SVG/Product Truth | BLOCKER | face geometry must be accepted | component questions and confirmation copy | YES | NO |
| printed artwork confirmation | SVG/Finish | BLOCKER | logos affect print/laminate path | extend artwork card badges/copy | YES | YES, UI-only |
| `finish_target` | Finish | BLOCKER | separates face/cant/artwork | docs/UI question contract | YES | NO runtime yet |
| T06 vs T19E | Cant/Finish/Operations | BLOCKER | distinguishes before-forming vs after-body film | component question design | YES | NO |
| per-layer/per-group settings | Review/Form | MAJOR | `gradi-curat.svg` needs group-specific decisions | extend display and form contract | YES | PARTIAL UI-only |
| support/mounting mismatch | Mounting/Support | MAJOR | support activation can drift | audit trigger alignment later | YES | NO |
| selected_layer | SVG/Form | BLOCKER | target layer must be explicit | Product Truth field design | YES | NO |
| pseudo display | UI | MINOR | operator clarity | already improved; extend remaining panels if needed | YES | NO, mostly done |
| readiness badge wording | UI readiness | MINOR | prevents wrong blocker interpretation | apply same vocabulary to readiness summary | YES | YES, UI-only |
| ProductAggregateTaskRule future gap | Aggregate/Tasks | MAJOR | DAG cannot be complete without better rule shape | docs/owner packet later | YES | NO |
| ExecutionPlan DAG future gap | ExecutionPlan | MAJOR | linear task plan loses dependencies | after Aggregate/task graph audit | YES | NO |
| pricing boundary messaging | Commercial UI | MAJOR | Product Truth gaps must not look like pricing issues | copy/badge audit in previews | YES | YES, UI-only |
| utilaje/workcenters mapping future gap | Operations | MAJOR | needed for capacity later | defer until task graph stable | YES | NO |
| angajati/skills/capacity future gap | HR/Execution | MAJOR | needed for assignments/reality | defer until ExecutionPlan stable | YES | NO |

---

## What is NOT the next step

The next step is not:

- ProductAggregate schema change;
- ExecutionPlan DAG;
- task materialization;
- Employee Mobile;
- pricing rewrite;
- CostEngine rewrite;
- QuoteOrchestrator rewrite;
- formular nou de la zero;
- redesign UI mare;
- DB migration;
- seeds/migration fara GO;
- utilaje/angajati ca tarif orar comercial.

---

## Recommended Next Safe Slice

Recommended single next slice:

**UI-only micro-slice: apply the same badge vocabulary to artwork finish cards and the readiness summary panel.**

Why this remains the safest next step:

- impact mic;
- pleaca din Intake V6;
- preserves the existing wizard;
- does not change analyzer logic;
- does not change payload;
- does not change pricing;
- does not change backend;
- does not enter ProductAggregate or ExecutionPlan;
- can be verified on `gradi-curat.svg` without materialization.

Expected verification:

- artwork cards show suggested/fallback/confirmed distinctly;
- readiness summary states Product Truth blockers as Product Truth blockers;
- no Pricing Registry false blame;
- no hourly/minute commercial pricing;
- `layer_roles_incomplete` still blocks until operator confirmation.

---

## Documentation Index After Reconciliation

| Document | Path | Purpose | Owner decision relevance | Status |
|---|---|---|---|---|
| Product Truth contract | `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md` | defines Intake V6 as Product Truth source and source separation | high: controls all downstream order | CANONICAL |
| Reusable components contract | `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md` | defines reusable volumetric components and their truth outputs | high: drives Form System questions | CANONICAL |
| Readiness boundary | `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md` | defines quote/order/execution gates and blocker taxonomy | high: prevents premature quote unlock | VALIDATED |
| UI state contract | `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md` | defines suggested/confirmed/fallback/warning/blocker display vocabulary | medium-high: operator clarity | PARTIAL_IMPLEMENTED |
| Existing form to modular form contract | requested path absent; content folded into UI state contract in this export | preserves existing Intake V6 UI and modularizes it | high: forbids greenfield UI | NEEDS_FILENAME_RECONCILIATION |
| E2E discovery/direction/roadmap doc | `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md` | reconciles E2E direction, old docs, roadmap, re-audit gates | high: controls implementation order | CANONICAL_DIRECTION |

---

## Forbidden Confirmation

This document does not implement and does not authorize:

- backend changes;
- frontend changes;
- DB/schema/seeds/tests changes;
- ProductAggregate changes;
- ExecutionPlan changes;
- CommercialPriceProposal changes;
- CostEngine changes;
- Pricing Registry changes;
- formulas or price changes;
- `/price` shortcuts;
- materialization;
- sessions;
- quote/order/execution creation;
- Employee Mobile;
- hourly commercial pricing.
