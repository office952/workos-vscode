# VOLUMETRIC LETTERS TASK GRAPH AND MACHINE ASSIGNMENT CONTRACT

## Status

- CANONICAL_DOCS_RECONCILIATION
- DOCUMENTED_TARGET
- CURRENT_CODE_PARTIAL
- NO_RUNTIME_CHANGE
- NEEDS_OWNER_GO_FOR_IMPLEMENTATION

## Scope

Acest document leaga contractele pentru:

- ProductSystem
- Dossier
- Form System
- ProductDefinition
- ProductAggregate
- ExecutionPlan V2
- Pricing Boundary
- Workcenters

## Source map

Surse folosite pentru reconciliere:

- owner memorii si reguli explicite pentru T01-T19E;
- docs existente de arhitectura si app-flows;
- cod real din repo;
- verificari runtime vizuale pentru `/inventory/pricing`, `/product-system`, `/product-system/blueprint-dossier`, `/intake-v6/IR-MQZVC33K/operator`;
- documentele lipsa au fost restaurate in acest slice ca documente noi;
- nu s-a introdus nicio schimbare runtime.

## Current code status

| Layer | Status | Notes |
|---|---|---|
| ProductSystem template | VALIDATED | template si layerele exista in repo si in UI |
| Dossier | PARTIAL | exista, dar `task_rules` sunt inca design-time sau partial executable |
| Form System endpoint | VALIDATED | endpointul exista si este testat |
| ProductDefinition | PARTIAL | activeaza module si deriva suport partial |
| ProductAggregate | PARTIAL | exista, dar contractul `task_rules` este insuficient |
| ProductAggregateTaskRule schema | MISSING/PARTIAL | prea slab pentru DAG si metadata minima |
| ExecutionPlan V2 | PARTIAL linearizes | preview exista, dar linearizeaza taskurile |
| CostEngine | VALIDATED boundary | cost intern, nu pret comercial |
| CommercialPriceProposal | VALIDATED boundary | pret client, fara ore |
| Pricing Registry | VALIDATED boundary | input intern, nu commercial truth |
| UI /inventory/pricing | VALIDATED | truth boundary vizibil |
| ProductSystem UI | VALIDATED | upstream config boundary vizibil |
| Intake V6 Review UI | VALIDATED | blocaje, trigger mismatch si confirmari vizibile |

## Target spine

```text
Intake V6
-> Form System contract
-> ProductSystem Template
-> ProductSystem Dossier
-> ProductDefinition builder
-> ProductAggregate task_contract/task_rules
-> ExecutionPlan V2 preview/planned_tasks
-> later materialization only after GO
-> sessions later
-> actuals later
-> Employee Mobile final-final
```

## Task graph target

### DAG fara suport

```text
T01 -> T02
T01 -> T03
T01 -> T19A -> T19B -> T19C -> T19D optional

T02 -> T04
T02 -> T05

T03 -> T06 optional -> T07
T04 + T07 -> T08

T05 -> T09 -> T10 -> T17

T08 + T17 -> T18
T18 + T19C/T19D daca este print laminat -> T19E
```

### DAG cu suport

```text
T01 -> T02
T01 -> T03
T01 -> T12
T01 -> T19A -> T19B -> T19C -> T19D optional

T02 -> T04
T02 -> T05

T03 -> T06 optional -> T07
T04 + T07 -> T08

T05 -> T09 -> T10

T11A + T12 + T05 -> T13
T10 + T13 -> T14 -> T15 -> T16 -> T17

T08 + T17 -> T18
T18 + T19C/T19D daca este print laminat -> T19E
```

### T19 split

- T19A pregatire fisier print folie
- T19B printare folie
- T19C laminare folie
- T19D taiere sau contur folie optional
- T19E aplicare folie dupa corp format

## Field contract matrix

| Field | Contract status | Notes |
|---|---|---|
| back_bevel_enabled | REQUIRED_NOW_DOCS | exista partial in cod |
| forex_back_has_bevel | CURRENT_ALIAS | alias contractual pentru aceeasi decizie semantica |
| mounting_system | REQUIRED_NOW_DOCS | exista in cod |
| metal_support_required | CURRENT_ALIAS | derivat curent din `mounting_system` |
| has_rear_support | REQUIRED_NOW_DOCS | lipseste in cod |
| support_type | REQUIRED_NOW_DOCS | lipseste in cod |
| support_bar_position | REQUIRED_NOW_DOCS | lipseste in cod |
| support_bar_material | CURRENT_ALIAS | `bar_material` exista partial |
| support_bars_prepared_internally | REQUIRED_NOW_DOCS | lipseste in cod |
| electrical_selected | REQUIRED_NOW_DOCS | lipseste in cod |
| lighting_system_type | CURRENT_ALIAS | exista in cod si UI |
| illuminated | CURRENT_ALIAS | exista in cod si UI |
| per_letter_cable_length_ml | REQUIRED_NOW_DOCS | lipseste in cod |
| inter_letter_cable_type | REQUIRED_NOW_DOCS | lipseste in cod |
| power_cable_length_ml | REQUIRED_NOW_DOCS | lipseste in cod |
| power_cable_type | REQUIRED_NOW_DOCS | lipseste in cod |
| transformer_hidden_mounting | REQUIRED_NOW_DOCS | lipseste in cod |
| finish_enabled | DEFERRED | poate fi derivat sau introdus ulterior |
| finish_material | DEFERRED | astazi este spart partial in campuri mai fine |
| face_finish_type | CURRENT_ALIAS | exista in cod |
| return_finish_type | CURRENT_ALIAS | exista in cod |
| print_required | REQUIRED_NOW_DOCS | lipseste in cod |
| lamination_required | REQUIRED_NOW_DOCS | lipseste in cod |
| finish_apply_stage | REQUIRED_NOW_DOCS | lipseste in cod |
| finish_target | REQUIRED_NOW_DOCS | lipseste in cod |
| selected_layer | REQUIRED_NOW_DOCS | lipseste in cod |
| layer_role_setup | CURRENT_ALIAS | exista in cod si UI |

## ProductAggregateTaskRule target

### Minimal first target fields

- task_key
- label
- sequence
- depends_on_task_keys
- workcenter_code
- condition
- source_module
- provenance
- mini_module_code

### Deferred fields

- machine_type
- operator_skill
- capacity_unit
- setup_required
- quality_check_required
- can_run_parallel
- task_type
- priced_operation
- trigger_condition

## ExecutionPlan target

- consuma snapshot frozen;
- pastreaza DAG-ul;
- nu face linear chain fortat;
- nu inventeaza taskuri din catalog paralel;
- nu materializeaza fara GO.

## Pricing boundary

- CommercialPriceProposal = pret client, fara ore;
- CostEngine = cost intern;
- Pricing Registry = input intern pentru materiale, operatii, workcenter rates si markup policies;
- Form System si Dossier = blockers tehnice sau comerciale de input;
- `/inventory/pricing` nu rezolva lipsuri de suport, DAG sau form fields.

## Gap map

- docs missing resolved by this slice;
- ProductAggregateTaskRule needs future schema contract slice;
- ExecutionPlan DAG future;
- Form System fields future;
- dossier executable task_rules future;
- pricing boundary protected.

## Minimal next safe slice after docs

Recomandare unica:

- ProductAggregateTaskRule schema contract only.

De ce:

- este cel mai mic punct structural care poate ancora DAG-ul inainte de orice schimbare mai larga;
- separa contractul de task graph de implementarea ExecutionPlan;
- reduce drift-ul dintre owner truth, dossier si aggregate;
- nu obliga atingerea CostEngine, CommercialPriceProposal sau materialization.

## Forbidden

- no backend changes
- no frontend changes
- no DB changes
- no schema changes in acest slice
- no seed changes
- no tests changes
- no migrations
- no materialize
- no sessions
- no Employee Mobile
- no machine_id
- no employee_id
- no commercial hourly pricing
- no /price shortcut
- no CostEngine rewrite
- no QuoteOrchestrator rewrite
- no push

## Visual verification

- `/inventory/pricing`
- `/product-system`
- `/product-system/blueprint-dossier`
- `/intake-v6/IR-MQZVC33K/operator`

## Owner decision

Owner trebuie sa aprobe dupa acest slice:

- vocabularul canonical pentru campurile de suport si electrica;
- split-ul T19A-T19E ca adevar operational;
- faptul ca T11 este trigger si T11A este task fizic;
- faptul ca primul slice de cod ulterior trebuie sa fie contractul `ProductAggregateTaskRule`.
