# INTAKE V6 PRODUCT TRUTH CONTRACT

## 1. Status

- CANONICAL_DOCS_CONTRACT
- DOCUMENTED_TARGET
- CURRENT_CODE_PARTIAL
- NO_RUNTIME_CHANGE
- NEEDS_OWNER_GO_FOR_IMPLEMENTATION

## 2. Purpose

Acest document defineste contractul central pentru Product Truth in Intake V6.

Field, row, section, material, commercial and downstream confirmation rules are specified by:

`docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Principiile de baza sunt:

- Intake V6 este locul in care se captureaza Product Truth pentru litere volumetrice.
- SVG Analyzer detecteaza, masoara si sugereaza, dar nu inlocuieste formularul.
- Form System completeaza exact ce SVG-ul nu poate sti din geometrie si layere.
- Operatorul confirma adevarul final inainte de handoff.
- ProductDefinition activeaza sau dezactiveaza module pe baza Product Truth, fara pricing si fara DB writes.
- ProductAggregate si ExecutionPlan vin mai tarziu si nu trebuie sa inventeze cereri lipsa.
- Pricing Registry nu rezolva lipsuri de Product Truth; el ramane registry intern pentru pricing si cost intern.

## 3. Correct spine

```text
Intake V6 / Product Truth
-> SVG Analyzer / Layer Role Analysis
-> Form System Modular Contract
-> Operator Confirmation / Review
-> ProductDefinition Builder
-> ProductSystem Modules
-> ProductAggregate Technical Graph later
-> CommercialPriceProposal / EstimatedInternalCost
-> Quote Snapshot
-> Order Snapshot
-> ExecutionPlan later
-> Materialization only after GO
-> Employee Mobile final-final
```

## 4. Source separation

| Source | What it can know | What it cannot know | Allowed output | Forbidden output |
|---|---|---|---|---|
| SVG Analyzer | SVG parse, layer names, geometry, colors, stroke/fill, scale confidence, auto-role suggestions, warnings | commercial decisions, finish intent, support intent, mounting intent, final print policy, electrical topology | geometry truth draft, layer role candidates, warnings, blockers, ProductDefinition hints | client price, support activation by itself, mounting truth by itself |
| Form System | missing product fields, module configuration, option choices, explicit booleans and enums | raw geometry discovery, automatic commercial approval, execution planning | canonical field values, module gates, unresolved field checklist | invented geometry, invented task graph |
| Operator Review | confirmation of layer roles, finish truth, mounting truth, support truth, electrical truth, final readiness | internal cost formulas, execution materialization | confirmed truth, blockers, warnings, unresolved decisions | pricing rule substitution, hidden auto-approval |
| ProductDefinition | module activation, canonical values normalization, derived deterministic flags | pricing, commercial offer, DB writes, execution materialization | read-only module activation state, validation, derived support branch, product role outputs | quote total, order creation, task materialization |
| ProductSystem | upstream template/module structure, module decomposition, dossier guidance | runtime truth capture for a specific job, quote freeze, execution reality | module vocabulary, upstream component/material/operation structure | runtime override of missing intake truth |
| ProductAggregate | technical graph from accepted ProductDefinition and module structure | filling missing product inputs, commercial decisions, runtime field invention | technical graph later, aggregate structure later | invented finish/support/electrical truth |
| CommercialPriceProposal | client price from accepted product truth and commercial rules, no hourly client pricing | missing product truth repair, support or finish conflict resolution | commercial lines, commercial totals, commercial blockers | Product Truth substitution, internal cost replacement |
| CostEngine / EstimatedInternalCost | internal cost estimate, internal operation costing, rate consumption, profitability context | client-facing commercial truth, intake field repair | estimated internal cost, margin confidence, internal warnings | commercial hourly pricing, replacement for product truth |
| Pricing Registry | internal material pricing, operation rates, workcenter/internal rates, markup policies, template coverage | layer role decisions, finish target decisions, support decisions, electrical decisions | internal pricing inputs, coverage status, missing price entries | resolving intake blockers, deciding selected_layer |
| ExecutionPlan | downstream planning after frozen quote/order truth, DAG preservation later | intake truth capture, commercial approval, field invention | execution planning later | pre-order truth capture, pre-order materialization |

Reguli ferme:

- SVG Analyzer detecteaza si sugereaza, nu decide comercial.
- Form System cere inputurile lipsa.
- Operatorul confirma adevarul.
- ProductDefinition activeaza sau dezactiveaza module, nu calculeaza pret.
- ProductAggregate construieste technical graph, nu inventeaza cereri lipsa.
- CommercialPriceProposal calculeaza pret client, fara ore comerciale.
- CostEngine este intern.
- Pricing Registry este registry intern si nu rezolva layer, finish sau support blockers.
- ExecutionPlan vine dupa Order Snapshot.

## 5. Product Truth areas

| Truth area | Source: SVG / Form / Operator / Derived / ProductSystem / Pricing Registry | Required before quote? | Required before order? | Required before execution? | Current status | Missing |
|---|---|---|---|---|---|---|
| geometry truth | SVG + Derived + Operator | yes | yes | yes | PARTIAL | stricter scale and unit acceptance gate |
| layer role truth | SVG + Operator | yes | yes | yes | VALIDATED | native persistence of unresolved reasons could be clearer |
| material truth | Form + ProductSystem + Derived | yes | yes | yes | PARTIAL | explicit print, support and electrical material semantics |
| face truth | Form + Operator + SVG hint | yes | yes | yes | PARTIAL | finish_target and selected_layer semantics |
| back truth | Form + Operator | yes | yes | yes | PARTIAL | explicit Forex with or without bevel semantic alias cleanup |
| return/cant truth | Form + Operator + Derived | yes | yes | yes | PARTIAL | cant-target truth and autocolant-on-cant semantics |
| finish truth | Form + Operator | yes | yes | yes | PARTIAL | finish_apply_stage and per-layer targeting |
| print/lamination truth | Form + Operator + SVG hint | conditional | yes if applicable | yes if applicable | MISSING | print_required, lamination_required, target truth |
| lighting truth | Form + Operator + Derived | conditional | yes if applicable | yes if applicable | PARTIAL | clearer distinction for lighting variants |
| electrical truth | Form + Operator | conditional | yes if applicable | yes if applicable | PARTIAL | cable lengths, cable types, hidden transformer placement |
| support truth | Form + Operator + Derived | conditional | yes if applicable | yes if applicable | PARTIAL | support type, bar position, internal vs external prep |
| mounting truth | Form + Operator | yes | yes | yes | PARTIAL | native trigger alignment vs derived support flag |
| commercial readiness truth | Operator + Derived | yes | no | no | PARTIAL | explicit unresolved decision object |
| blockers | SVG + Operator + Derived | yes | yes | yes | VALIDATED | central typed blocker contract still partial |
| warnings | SVG + Operator + Derived | yes | yes | yes | VALIDATED | consolidation across V6 native contract still partial |
| unresolved decisions | Operator + Derived | yes | yes | yes | PARTIAL | first-class persisted decision list |

## 6. SVG Analyzer contract

| Capability | Current status | Product Truth contribution | Must be confirmed by operator? | Cannot decide | Required future action |
|---|---|---|---|---|---|
| parse SVG | VALIDATED | reads source artifact | no | product options | keep |
| parse layers | VALIDATED | identifies layer boundaries | yes | final production meaning | keep |
| read layer names | VALIDATED | captures semantic hints | yes when ambiguous | commercial interpretation | keep |
| detect path geometry | VALIDATED | geometry candidate extraction | yes | final module activation by itself | keep |
| compute bounding boxes | VALIDATED | width and height inputs | yes when scale confidence is weak | quote approval alone | keep |
| compute area | VALIDATED | face area input | yes when geometry confidence is not high | finish and print policy | keep |
| compute perimeter | VALIDATED | perimeter input for cant and face rules | yes when benchmark confidence is medium | commercial line approval | keep |
| detect holes/islands | PARTIAL | subpath and inner-hole hinting | yes | final illumination cut semantics | strengthen explicit hole or island contract |
| detect text vs curves | PARTIAL | flags text not converted to paths | yes | production readiness by itself | keep warning contract |
| detect colors | VALIDATED | finish and artwork hint | yes | finish target policy | keep |
| detect stroke/fill | VALIDATED | paint evidence | yes | final finish or print selection | keep |
| detect units/scale | VALIDATED | dimension confidence basis | yes when low confidence | auto-accept geometry | block when confidence is not acceptable |
| suggest layer roles | VALIDATED | candidate product semantics | yes | final role truth | keep |
| confirm layer roles | VALIDATED | creates accepted layer role truth | yes | pricing | keep |
| persist confirmed roles | VALIDATED | stores layer role truth in workspace | no after confirmation | commercial decisioning | keep |
| map layer to face | VALIDATED | face candidate routing | yes | finish details | keep |
| map layer to back | VALIDATED | back candidate routing | yes | backing mode policy | keep |
| map layer to return/cant | VALIDATED | cant candidate routing | yes | cant finish policy | keep |
| map layer to finish | MISSING | no native finish-target truth today | yes | finish target, finish stage | introduce explicit form truth later |
| map layer to print | PARTIAL | artwork or vinyl hinting | yes | print_required and lamination_required | add explicit print truth fields |
| map layer to support | PARTIAL | support_panel and frame hints only | yes | rear support branch activation | separate support semantics from layer hint |
| map layer to mounting | MISSING | none | yes | mounting truth | keep in Form |
| detect artwork-only | VALIDATED | blocker and warning path | yes | template switch or commercial decision | keep |
| detect unknown layers | VALIDATED | unresolved layer truth | yes | ignore policy | keep |
| produce blockers | VALIDATED | readiness blockage | no additional confirmation after shown | final commercial override | keep |
| produce warnings | VALIDATED | caution signals | yes when warning changes truth | final module activation | keep |
| provide pricing inputs | PARTIAL | geometry and role-derived hints only | yes | final pricing truth | keep as hint only |
| provide ProductDefinition inputs | PARTIAL | geometry and role hints | yes for non-geometric semantics | full product truth | keep with Form completion |
| provide ProductSystem module hints | PARTIAL | upstream module suggestions | yes | runtime truth override | keep informational only |

## 7. Modular Form System contract

| Module | Fields required | Can come from SVG? | Must be asked in Form? | Must be confirmed by Operator? | Derived fields | Feeds ProductDefinition as | Current status |
|---|---|---|---|---|---|---|---|
| Base product module | template_code, workspace identity, route intent | no | yes when route is ambiguous | yes | none | source_context, template_code | PARTIAL |
| SVG/layer role module | vector_file, layer_role_setup | partly | yes for confirmation workflow | yes | role candidates only | geometry gate and layer role truth | VALIDATED |
| Geometry module | width_mm, height_mm, letter_count, letter_perimeter_m, letter_face_area_m2 | yes | only for correction or override | yes | unit normalization | geometry_inputs, canonical_values | VALIDATED |
| Face module | face_finish_type | no | yes | yes | none | face component activation and finish values | PARTIAL |
| Back module | backing_mode | no | yes | yes | back_bevel_enabled may follow backing selection but remains explicit | back component activation | PARTIAL |
| Return/cant module | return_depth_mm, return_finish_type, volum_aluminum_module_template_code | partly for geometry only | yes | yes | volum_aluminum_module_template_code may be derived from return settings | return module activation | VALIDATED |
| Lighting/electrical module | lighting_system_type when illuminated; led counts and PSU | no | yes | yes | led counts and PSU class can be partially derived | LED module activation | PARTIAL |
| Finish module | mounting_system, mounting_template_enabled, mounting_template_area_m2, letter_group_finishes | no | yes | yes | mounting_template_area_m2 minimum can be derived | finish summary and mounting-related flags | PARTIAL |
| Print/lamination module | print_required, lamination_required, target | only artwork hints | yes | yes | none | future print-related activation | MISSING |
| Rear support module | mounting_system plus support details | no | yes | yes | metal_support_required, bar_material defaults | support branch activation | PARTIAL |
| Mounting module | mounting_system and mounting specifics | no | yes | yes | support branch boolean | mounting truth and support gate | PARTIAL |
| Commercial offer readiness module | finish confirmed, operator confirm, blockers clear | no | yes | yes | readiness flags | readiness only, not pricing or tasks | PARTIAL |

## 8. Volumetric variants without separate forms

Formular separat pe fiecare tip de litera se evita prin activare de module, nu prin template nou pentru fiecare combinatie. Un singur Product Truth contract decide ce se activeaza, ce ramane inactiv si ce devine blocker.

### 1. Litera simpla neluminoasa

- module active: geometry_svg, debitare_fata, modelare_cant, debitare_spate, finisaje
- required Product Truth: geometry, face finish, cant depth, cant finish, backing mode
- source of truth: SVG pentru geometrie; Form plus Operator pentru restul
- ProductDefinition activation: face, back, cant active; LED and support inactive
- blockers: missing face_finish_type, return_depth_mm, return_finish_type, backing_mode
- forbidden shortcuts: nu se deduce automat finisajul din culoare

### 2. Litera luminoasa fara suport

- module active: geometry_svg, debitare_fata, modelare_cant, debitare_spate, sistem_led, finisaje
- required Product Truth: geometry plus lighting_system_type, led configuration, PSU selection
- source of truth: SVG pentru geometrie; Form plus Operator pentru iluminare
- ProductDefinition activation: LED active; support inactive
- blockers: missing lighting decision, missing electrical detail truth
- forbidden shortcuts: nu se deduce electrica doar din faptul ca exista goluri interioare

### 3. Litera luminoasa cu suport

- module active: geometry_svg, debitare_fata, modelare_cant, debitare_spate, sistem_led, finisaje, structura_suport
- required Product Truth: geometry, lighting truth, mounting_system, support truth
- source of truth: Form plus Operator pentru support si mounting; Derived pentru metal_support_required
- ProductDefinition activation: support branch active cand mounting_system cere bare sau premontaj
- blockers: missing support_type, support_bar_position, support_bar_material, support_bars_prepared_internally
- forbidden shortcuts: nu se activeaza suportul doar dintr-un layer support_panel

### 4. Litera cu print laminat

- module active: geometry_svg, debitare_fata, modelare_cant, debitare_spate, finisaje, print or lamination truth later
- required Product Truth: print_required, lamination_required, target, geometry
- source of truth: SVG da doar artwork hints; Form plus Operator decid
- ProductDefinition activation: activeaza materiale si operatii de print numai dupa adevar explicit
- blockers: lipsa print_required sau lamination_required
- forbidden shortcuts: nu se presupune print doar din policromie

### 5. Litera cu autocolant pe cant

- module active: geometry_svg, modelare_cant, finisaje
- required Product Truth: return_depth_mm, return_finish_type, finish_target pentru cant
- source of truth: SVG doar pentru geometrie; Form plus Operator pentru cant finish
- ProductDefinition activation: return module si finish related values
- blockers: lipsa finish_target sau finish_apply_stage pentru cant
- forbidden shortcuts: nu se copiaza automat face_finish_type pe cant

### 6. Litera cu finisaj pe layer selectat

- module active: geometry_svg, debitare_fata sau finisaje in functie de tinta
- required Product Truth: selected_layer, finish_target, finish_apply_stage
- source of truth: Operator plus Form
- ProductDefinition activation: aplica activarea doar pe componentele vizate
- blockers: selected_layer lipsa sau finish_target lipsa
- forbidden shortcuts: Pricing Registry nu alege layerul

### 7. Litera cu suport dar bare externalizate

- module active: geometry_svg, debitare_fata, modelare_cant, debitare_spate, finisaje, structura_suport
- required Product Truth: mounting_system, support truth, support_bars_prepared_internally=false
- source of truth: Form plus Operator
- ProductDefinition activation: support branch activa, dar pregatirea interna ramane distincta
- blockers: lipsa distinctiei internal versus external prep
- forbidden shortcuts: nu se materializeaza procurement sau scheduling

### 8. Litera cu spate Forex cu sau fara sanfren

- module active: geometry_svg, debitare_spate, debitare_fata, modelare_cant, finisaje
- required Product Truth: backing_mode, back_bevel_enabled sau forex_back_has_bevel semantic alias
- source of truth: Form plus Operator
- ProductDefinition activation: back module cu varianta corecta
- blockers: lipsa deciziei de bevel pentru spate
- forbidden shortcuts: nu se deduce bevel automat din materialul Forex

## 9. Critical missing decisions

| Missing decision/input | Correct source | Why it matters | Blocks quote? | Blocks order? | Blocks execution? | Severity | Safe direction |
|---|---|---|---|---|---|---|---|
| selected_layer | Operator | decide tinta reala pentru finish sau print | yes | yes | yes | BLOCKER | persist explicit layer target |
| finish_target | Form + Operator | separa fata, spate, cant, artwork | yes | yes | yes | BLOCKER | add explicit target field contract |
| finish_apply_stage | Form | separa before-forming, before-assembly, after-assembly | conditional | yes | yes | MAJOR | document as runtime truth |
| print_required | Form + Operator | artwork hint nu este decizie finala | yes | yes | yes | BLOCKER | explicit boolean |
| lamination_required | Form + Operator | print nu implica mereu laminare | conditional | yes | yes | MAJOR | explicit boolean |
| support_type | Form + Operator | mounting_system singur este prea grosier | yes when support active | yes | yes | BLOCKER | explicit support taxonomy |
| support_bar_position | Operator | conteaza pentru executie si cablaj | no | yes | yes | MAJOR | explicit operator truth |
| support_bar_material | Form + Operator + Derived | poate avea default, dar cere confirmare | conditional | yes | yes | MAJOR | derive default then confirm |
| support_bars_prepared_internally | Operator | schimba ramura operationala mai tarziu | no | yes | yes | MAJOR | explicit bool |
| per_letter_cable_length_ml | Derived + Operator | afecteaza electrica si intern consum | conditional | yes | yes | MAJOR | derive estimate then confirm |
| inter_letter_cable_type | Form | trebuie material si executie corecta | conditional | yes | yes | MAJOR | explicit field |
| power_cable_length_ml | Form + Operator | depinde de alimentare si context de montaj | conditional | yes | yes | MAJOR | explicit field |
| power_cable_type | Form | material si siguranta | conditional | yes | yes | MAJOR | explicit field |
| transformer_hidden_mounting | Operator | conteaza pentru executie si aspect final | no | yes | yes | MAJOR | explicit operator truth |
| T06 vs T19E distinction | Form + ProductSystem | separa autocolant pe cant de aplicare folie dupa corp format | yes when finish active | yes | yes | BLOCKER | preserve as distinct semantic branches |
| T19A-T19E split | ProductSystem + Form | print and laminate path needs separate truth | yes when print active | yes | yes | BLOCKER | document and later encode separately |
| back_bevel_enabled / forex_back_has_bevel | Form + Operator | evita ambiguitate pe spate Forex | conditional | yes | yes | MAJOR | keep explicit semantic alias until unified |
| mounting_system vs metal_support_required trigger mismatch | Derived + contract alignment | debt de tranzitie intre intake si module link | yes for support clarity | yes | yes | BLOCKER | migrate to native mounting trigger later |
| V6 native contract vs V4 aliasing | Schema contract | reduce claritatea si trasabilitatea V6 | no immediate in all cases | yes | yes | MAJOR | continue V6-native contract migration |
| downstream owner-pending commercial rules | Commercial layer | quote final poate ramane blocat chiar cu Product Truth corect | yes | no | no | BLOCKER | keep explicit downstream blockers |

## 10. Boundary with /inventory/pricing

### 10.1 Belongs in Pricing Registry

- materials;
- operation rates;
- workcenter/internal rates;
- markup policies;
- missing price entries;
- template coverage.

### 10.2 Does NOT belong in Pricing Registry

- layer role confusion;
- finish_target missing;
- selected_layer missing;
- mounting_system missing;
- support type missing;
- cable specs missing;
- transformer_hidden_mounting;
- T06/T19E semantic gap;
- T19A-T19E task split;
- ProductDefinition blockers.

### 10.3 Must be blocked in Intake V6

- unconfirmed layer roles;
- unconfirmed finish setup;
- missing support decisions;
- missing electrical decisions;
- missing material decisions;
- missing geometry scale/unit confidence.

### 10.4 CostEngine internal only

- minutes;
- capacity;
- internal operation costing;
- workcenter rates;
- overhead;
- profitability.

## 11. ProductDefinition handoff

ProductDefinition primeste din Product Truth:

- geometry inputs validate;
- layer role truth confirmat;
- finish setup confirmat;
- mounting truth;
- lighting and backing truth;
- derived canonical values.

ProductDefinition activeaza:

- module always_on;
- conditional modules precum sistem_led;
- support branch derivata din mounting_system;
- inactive modules cand conditiile nu sunt indeplinite.

ProductDefinition blocheaza:

- lipsa campurilor required pentru modulele active;
- configuratii invalide sau incomplete pentru handoff;
- lipsa geometry gate cand geometry_svg nu este complet.

ProductDefinition nu calculeaza:

- pret comercial;
- cost intern final;
- markup comercial;
- reprice client.

ProductDefinition nu materializeaza:

- taskuri runtime;
- comanda;
- stoc;
- sessions;
- machine_id;
- employee_id.

Debt explicit pastrat:

- support branch derivata din mounting_system este corecta ca directie, dar ramane datoria de tranzitie `mounting_system` versus `metal_support_required`.
- V6 aliasing peste V4 ramane debt de contract public.
- `geometry_svg` este gate, nu priced task.
- ProductDefinition nu face pricing si nu scrie DB.

## 12. Current code maturity

| Layer | Current maturity | Status | Notes |
|---|---|---|---|
| Intake V6 workspace | real runtime flow | PARTIAL | V6 surface real, dar multe contracte publice raman V4-aliased |
| SVG Analyzer | mature analyzer path | VALIDATED | parse, geometry, color, warnings, auto-role suggestions |
| Layer role confirmation | operator-backed | VALIDATED | confirmare si persistare exista |
| Modular Form System | read-only contract plus runtime coupling | PARTIAL | 7 module active documentate, field gaps raman |
| Operator Review | real gating step | VALIDATED | finish confirm si final confirm exista |
| ProductDefinition | read-only builder | VALIDATED | no pricing, no DB writes, support derivation partial |
| ProductSystem modules | upstream module authority | VALIDATED | module vocabulary si linkage upstream exista |
| CommercialPriceProposal | separated commercial layer | VALIDATED | fara commercial hourly pricing |
| Pricing Registry | internal registry boundary | VALIDATED | nu este canonical commercial truth |
| CostEngine | internal estimate layer | VALIDATED | internal only boundary |
| ProductAggregate later | downstream technical graph | PARTIAL | nu trebuie sa inventeze cereri lipsa |
| ExecutionPlan later | downstream planning | PARTIAL | vine doar dupa snapshoturi frozen |

## 13. Next implementation slices

### 1. Intake V6 Product Truth docs — this slice

- scop: contract central docs-only pentru Product Truth
- de ce vine in aceasta ordine: fixeaza vocabularul si boundary-urile inainte de cod
- forbidden scope: no backend, no frontend, no DB, no schema, no materialize

### 2. Form System field contract docs

- scop: detaliere fina pe fields, aliases si ownership
- de ce vine in aceasta ordine: dupa contractul central, pentru a evita campuri contradictorii
- forbidden scope: no runtime change, no DB, no pricing rewrite

### 3. SVG/layer role contract hardening

- scop: clarificare pe holes, finish targeting, artwork-only, unknowns
- de ce vine in aceasta ordine: numai dupa ce Product Truth si field ownership sunt clare
- forbidden scope: no commercial shortcut, no task materialization

### 4. tests-only safety net

- scop: capturare de regresii pe contractele deja acceptate
- de ce vine in aceasta ordine: dupa ce docs contract sunt aprobate
- forbidden scope: no business logic rewrite, no schema migration

### 5. ProductDefinition blockers

- scop: aliniere a blocker-elor cu Product Truth acceptat
- de ce vine in aceasta ordine: ProductDefinition consuma contractul, nu il defineste
- forbidden scope: no pricing changes, no DB writes expansion

### 6. ProductAggregateTaskRule contract

- scop: contract downstream pentru technical graph si DAG
- de ce vine in aceasta ordine: vine dupa Product Truth si ProductDefinition blockers
- forbidden scope: no ExecutionPlan rewrite yet, no materialization

### 7. ExecutionPlan DAG preservation

- scop: pastrare a DAG-ului downstream fara linearizare abuziva
- de ce vine in aceasta ordine: cere task contract stabil mai intai
- forbidden scope: no sessions, no machine assignment, no employee assignment

### 8. Runtime materialization later

- scop: numai dupa acceptarea contractelor upstream si downstream
- de ce vine in aceasta ordine: este cel mai tarziu pas pentru a evita runtime drift
- forbidden scope: no Employee Mobile coupling yet, no push toward dispatch now

## 14. Forbidden scope

- no backend changes;
- no frontend changes;
- no DB;
- no schema;
- no seed;
- no tests;
- no materialize;
- no sessions;
- no Employee Mobile;
- no machine_id;
- no employee_id;
- no commercial hourly pricing;
- no CostEngine rewrite;
- no QuoteOrchestrator rewrite;
- no push.

## 15. Owner decision required

- owner trebuie sa aprobe contractul Product Truth;
- dupa aprobare, urmatorul pas sigur este Form System field contract docs sau tests-only safety net;
- nu ProductAggregate inca, daca Product Truth nu este acceptat.