# VOLUMETRIC LETTERS WITH REAR SUPPORT MEMORIU

## Status

- DOCUMENTED_CONTRACT
- NOT_IMPLEMENTED_FULLY
- NEEDS_OWNER_GO_FOR_CODE

## Scop

Acest document descrie contractul tinta pentru varianta de litere volumetrice cu suport pe spate, structura de premontaj sau bare metalice.

Acesta este un document de reconciliere contractuala. Nu declara implementare completa in cod. Nu autorizeaza materializare, sessions, machine_id assignment sau employee_id assignment.

## Lista owner pastrata ca exprimare operationala

1. T01 Pregatire fisier COREL
2. T02 Pregatire dwg debitare cnc
3. T03 Pregatire PLT modelare cant
4. T04 Debitare CNC Fata din plexigas cu sanfren
5. T05 Debitare CNC Capac din forex 10mm, cu optiune sanfren sau fara sanfren
6. T06 Aplicare autocolant pe Cant aluminiu, inainte de procesare la CNC de litere, daca este ales finisajul
7. T07 Modelare Cant la CNC de litere
8. T08 Se lipeste Cant-ul modelat pe fetele literelor din Plexiglas fixat pe canalul sanfren facut
9. T09 Se monteaza electrica selectata in comanda pe spatele din forex de 10mm debitat la cnc
10. T10 Se ataseaza 1ml de cablu 2 x 0.75 pentru fiecare litera, necesar inclusiv pentru pasul 14, dar chiar si fara existenta lui 14, cablurile se ataseaza la fel
11. T11 Daca literele se monteaza pe suport, de exemplu bare metalice, implica taskuri suplimentare
12. T12 Se confectioneaza sablon de hartie printat la imprimanta
13. T13 Se aliniaza literele pe sablon si se prinde mecanic cu autoforante spatele din forex 10mm pe bare
14. T14 Se traseaza legaturile electrice intre litere pe bara superioara sau inferioara cu cablu 2 x 0.75
15. T15 Se monteaza transformatorii, ascunsi in spatele literelor sa nu se vada
16. T16 Se ataseaza cablul de alimentare 220 de minim 5ml, daca nu este specificat altfel cu cablu 2 x 1.5
17. T17 Se testeaza electrica
18. T18 Se prinde corpul format din fata Plexiglas si cantul lipit de spatele din forex
19. T19 Se pot colanta literele 641, 651, 8500, Printat laminat

## Reguli ferme

- T11 este trigger de ramura, nu task fizic.
- T11-T16 sunt active doar cand varianta are suport pe spate.
- T10 este obligatoriu pentru electrica indiferent de suport.
- T05 depinde de decizia `back_bevel_enabled` sau `forex_back_has_bevel`.
- T06 este aplicare autocolant pe cant inainte de modelare si este diferit semantic de T19E.
- T19 se sparge in T19A, T19B, T19C, T19D, T19E.
- T19A-T19D pot rula devreme fata de corpul fizic al literei.
- T19E este aplicare folie dupa corp format si depinde de T18.
- T19E depinde suplimentar de T19C sau T19D cand exista varianta print laminat.
- Fara pricing comercial la ora.

## DAG cu suport

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

## Form System fields

Campurile de contract pentru aceasta varianta trebuie sa poata exprima:

- has_rear_support
- metal_support_required
- mounting_system
- support_type
- support_bar_position
- support_bar_material
- support_bars_prepared_internally
- forex_back_has_bevel
- back_bevel_enabled
- electrical_selected
- illuminated
- lighting_system_type
- per_letter_cable_length_ml
- inter_letter_cable_type
- power_cable_length_ml
- power_cable_type
- transformer_hidden_mounting
- finish_enabled
- finish_material
- face_finish_type
- return_finish_type
- print_required
- lamination_required
- finish_apply_stage
- finish_target
- selected_layer
- layer_role_setup

Observatie de reconciliere:

- In codul actual, `mounting_system` si derivarea `metal_support_required` exista partial.
- `back_bevel_enabled` exista partial.
- `layer_role_setup` exista partial.
- Campurile electrice fine si print split raman contract documentat, nu implementare completa.

## ProductSystem modules

Modulele contractuale necesare pentru varianta cu suport sunt:

- file_preparation
- cnc_face_plexi_beveled
- cnc_back_forex
- back_bevel_decision
- aluminum_return_forming
- return_finish_before_forming
- electrical_on_forex_back
- per_letter_wiring
- rear_support_premount
- paper_template
- support_bar_preparation
- support_bar_fixing
- support_bar_wiring
- hidden_transformer_mounting
- power_feed_220v
- electrical_testing
- final_body_assembly
- print_laminate_production
- finish_application_after_assembly

## ProductDefinition expectations

- activeaza suportul cand `has_rear_support=true` sau cand `mounting_system` cere bare/premontaj;
- activeaza T11-T16 doar in ramura cu suport;
- cere blockers expliciti daca lipsesc datele de suport;
- pastreaza T10 obligatoriu indiferent de suport;
- nu introduce pricing comercial la ora.

## ProductAggregate expectations

- `task_rules` trebuie sa poata exprima DAG real, nu doar ordine liniara;
- `task_rules` trebuie sa poata transporta metadata operationala minima;
- `task_rules` trebuie sa diferentieze T06 de T19E;
- `task_rules` trebuie sa poata exprima ramura de suport fara materializare.

## ExecutionPlan expectations

- consuma snapshot frozen drept sursa de adevar;
- pastreaza DAG-ul cu suport;
- nu materializeaza;
- nu creeaza sessions;
- nu atribuie `machine_id`;
- nu atribuie `employee_id`.

## Workcenter si machine assignment

- se documenteaza doar `workcenter_code` si `machine_type`;
- nu se face `machine_id` assignment in acest contract;
- `operator_skill` si `capacity_unit` pot exista ca metadata de planificare, nu ca assignment runtime;
- employee assignment ramane ulterior si separat de Employee Mobile.

## Forbidden

- no materialize
- no sessions
- no Employee Mobile
- no machine_id
- no employee_id
- no commercial hourly pricing
