# VOLUMETRIC LETTERS WITHOUT REAR SUPPORT MEMORIU

## Status

- DOCUMENTED_CONTRACT
- NOT_IMPLEMENTED_FULLY
- NEEDS_OWNER_GO_FOR_CODE

## Scop

Acest document descrie contractul tinta pentru varianta de litere volumetrice fara suport pe spate.

Documentul este contract de reconciliere, nu declaratie de implementare completa.

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

Pentru varianta fara suport:

- T11 este trigger inactiv;
- T11A-T16 sunt inactive.

## Reguli ferme

- `has_rear_support=false`.
- `metal_support_required=false`.
- `mounting_system` nu este `steel_bars`, `aluminum_bars` sau `premount`.
- T11-T16 sunt inactive.
- T10 ramane obligatoriu.
- T17 vine dupa T10.
- T18 vine dupa T08 si T17.
- T19E vine dupa T18.
- Fara pricing comercial la ora.

## DAG fara suport

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

## Form System fields

Contractul de campuri ramane acelasi ca vocabular, dar campurile de suport sunt inactive sau deferred cand `support=false`:

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

Interpretare pentru varianta fara suport:

- campurile de suport nu trebuie sa activeze ramura T11-T16;
- campurile de electrica si finisaj raman relevante;
- campurile de print si laminare raman relevante pentru T19A-T19E.

## ProductSystem modules

Active in varianta fara suport:

- file_preparation active
- cnc_face_plexi_beveled active
- cnc_back_forex active
- back_bevel_decision active
- aluminum_return_forming active
- return_finish_before_forming active
- electrical_on_forex_back active
- per_letter_wiring active
- electrical_testing active
- final_body_assembly active
- print_laminate_production active
- finish_application_after_assembly active

Inactive in varianta fara suport:

- rear_support_premount inactive
- paper_template inactive
- support_bar_preparation inactive
- support_bar_fixing inactive
- support_bar_wiring inactive
- hidden_transformer_mounting inactive
- power_feed_220v inactive

## ProductDefinition expectations

- dezactiveaza suportul;
- nu emite T11-T16;
- pastreaza T10;
- pozitioneaza T17 dupa T10;
- nu introduce ramura de suport cand `has_rear_support=false`.

## ProductAggregate expectations

- `task_rules` trebuie sa poata exprima explicit ramura fara suport;
- task graph fara suport nu contine T11-T16;
- T10 si T17 raman prezente.

## ExecutionPlan expectations

- `planned_tasks` fara T11-T16;
- T10 prezent;
- T17 dupa T10;
- T18 dupa T08 si T17;
- fara materializare.

## Forbidden

- no materialize
- no sessions
- no Employee Mobile
- no machine_id
- no employee_id
- no commercial hourly pricing
