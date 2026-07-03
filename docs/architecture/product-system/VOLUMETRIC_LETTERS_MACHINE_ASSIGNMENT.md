# VOLUMETRIC LETTERS MACHINE ASSIGNMENT

## Status

- DOCUMENTED_CONTRACT
- NOT_IMPLEMENTED_FULLY
- NO_MACHINE_ID_ASSIGNMENT_NOW
- NO_EMPLOYEE_ID_ASSIGNMENT_NOW

## Principiu

Contractul curent documenteaza doar:

- `workcenter_code`
- `machine_type`
- `operator_skill`
- `capacity_unit`

Reguli de boundary:

- `machine_id` vine mai tarziu, in scheduling sau dispatch.
- `employee_id` vine mult mai tarziu.
- Employee Mobile ramane final-final.
- Nu se calculeaza comercial la ora.

## Workcenters

| workcenter_code | Rol contractual |
|---|---|
| design_prepress | pregatire fisiere si prepress |
| cnc_router | debitare fata si spate |
| letter_return_forming | modelare cant |
| large_format_print | productie print folie |
| lamination | laminare folie |
| vinyl_cutting | taiere/contur folie |
| vinyl_application | aplicare autocolant sau folie |
| electrical_bench | operatii electrice |
| metal_support_prep | pregatire suport metalic |
| assembly_bench | montaj corp si fixari |
| quality_control | verificari finale |
| packaging_dispatch | optional sau deferred |

## Machine types

| machine_type | Rol contractual |
|---|---|
| pc_prepress | statie pregatire fisiere |
| router_cnc | router CNC |
| letter_bender_cnc | utilaj CNC de modelare cant |
| large_format_printer | imprimanta mare format |
| laminator_160 | laminator |
| plotter_cutter | plotter cutter |
| electrical_bench_tools | banc electric si scule |
| metal_workbench | banc lăcătușerie / suport |
| manual_assembly_bench | masa montaj manual |
| qc_electrical_test | banc sau kit de testare |

## Task matrix

| task_key | owner text | workcenter_code | machine_type | operator_skill | capacity_unit | setup_required | quality_check_required | can_run_parallel | depends_on_task_keys | support condition |
|---|---|---|---|---|---|---:|---:|---:|---|---|
| T01 | Pregatire fisier COREL | design_prepress | pc_prepress | prepress_operator | file | false | false | true | [] | always |
| T02 | Pregatire dwg debitare cnc | design_prepress | pc_prepress | prepress_operator | file | false | false | true | [T01] | always |
| T03 | Pregatire PLT modelare cant | design_prepress | pc_prepress | prepress_operator | file | false | false | true | [T01] | always |
| T04 | Debitare CNC Fata din plexigas cu sanfren | cnc_router | router_cnc | cnc_router_operator | ml | true | false | false | [T02] | always |
| T05 | Debitare CNC Capac din forex 10mm, cu optiune sanfren sau fara sanfren | cnc_router | router_cnc | cnc_router_operator | ml | true | false | false | [T02] | always |
| T06 | Aplicare autocolant pe Cant aluminiu, inainte de procesare la CNC de litere, daca este ales finisajul | vinyl_application | manual_assembly_bench | vinyl_finishing_operator | ml | false | false | false | [T03] | optional |
| T07 | Modelare Cant la CNC de litere | letter_return_forming | letter_bender_cnc | letter_bender_operator | ml | true | false | false | [T03,T06] | always |
| T08 | Se lipeste Cant-ul modelat pe fetele literelor din Plexiglas fixat pe canalul sanfren facut | assembly_bench | manual_assembly_bench | assembly_operator | piece | false | false | false | [T04,T07] | always |
| T09 | Se monteaza electrica selectata in comanda pe spatele din forex de 10mm debitat la cnc | electrical_bench | electrical_bench_tools | electrical_operator | piece | false | false | false | [T05] | always |
| T10 | Se ataseaza 1ml de cablu 2 x 0.75 pentru fiecare litera | electrical_bench | electrical_bench_tools | electrical_operator | ml | false | false | false | [T09] | always |
| T11 | Trigger suport | none | none | none | none | false | false | false | [] | support_only_trigger |
| T11A | Pregatire suport sau bare | metal_support_prep | metal_workbench | metal_fabrication_operator | ml | true | false | true | [] | internal_bars_only |
| T12 | Se confectioneaza sablon de hartie printat la imprimanta | design_prepress | pc_prepress | prepress_operator | mp | false | false | true | [T01] | support_only |
| T13 | Se aliniaza literele pe sablon si se prinde mecanic spatele pe bare | assembly_bench | manual_assembly_bench | premount_assembly_operator | piece | false | false | false | [T11A,T12,T05] | support_only |
| T14 | Se traseaza legaturile electrice intre litere pe bara | electrical_bench | electrical_bench_tools | electrical_operator | ml | false | false | false | [T10,T13] | support_only |
| T15 | Se monteaza transformatorii ascunsi | electrical_bench | electrical_bench_tools | electrical_operator | piece | false | false | false | [T14] | support_only |
| T16 | Se ataseaza cablul de alimentare 220 | electrical_bench | electrical_bench_tools | electrical_operator | ml | false | false | false | [T15] | support_only |
| T17 | Se testeaza electrica | quality_control | qc_electrical_test | qc_electrical_operator | piece | false | true | false | [T10] or [T16] | always |
| T18 | Se prinde corpul format | assembly_bench | manual_assembly_bench | assembly_operator | piece | false | false | false | [T08,T17] | always |
| T19A | Pregatire fisier print folie | design_prepress | pc_prepress | print_prepress_operator | file | false | false | true | [T01] | print_only |
| T19B | Printare folie | large_format_print | large_format_printer | print_operator | mp | true | false | true | [T19A] | print_only |
| T19C | Laminare folie | lamination | laminator_160 | lamination_operator | mp | true | false | true | [T19B] | laminated_print_only |
| T19D | Taiere sau contur folie | vinyl_cutting | plotter_cutter | cutter_operator | piece | true | false | true | [T19C] | optional_print_contour |
| T19E | Aplicare folie sau colant dupa corp format | vinyl_application | manual_assembly_bench | vinyl_finishing_operator | piece | false | true | false | [T18,T19C] or [T18,T19D] | finish_after_assembly |

## Reguli speciale

- T04 si T05 folosesc `cnc_router` si `router_cnc`.
- T07 foloseste `letter_return_forming` si `letter_bender_cnc`.
- T06 foloseste `vinyl_application` inainte de T07.
- T19B foloseste `large_format_print`.
- T19C foloseste `lamination`.
- T19D foloseste `vinyl_cutting` si este optional.
- T19E foloseste `vinyl_application` dupa T18.
- T09, T10, T14, T15, T16 folosesc `electrical_bench`.
- T17 foloseste `quality_control` si `qc_electrical_test`.
- T13 implica `assembly_bench` si dependinta semantica de suportul pregatit.
- T18 foloseste `assembly_bench`.
- T11 este trigger, fara machine.
- T11A este doar pentru bare pregatite intern.

## Explicit forbidden

- no machine_id now
- no employee_id now
- no Employee Mobile
- no commercial hourly pricing
- no materialize
