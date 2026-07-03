# TPL-VOLUMETRIC-LETTERS — Operation Catalog

**Status:** documentation — catalog operațional condiționat  
**Nu este:** listă statică de pași; nu este execution plan runtime

---

## Schema unei operații

Fiecare intrare din catalog definește:

| Field | Descriere |
|-------|-----------|
| `operation_code` | identificator stabil |
| `display_name` | etichetă operator (RO) |
| `purpose` | de ce există operația |
| `active_if` | condiții activare |
| `inactive_if` | condiții dezactivare |
| `required_inputs` | date obligatorii din intake |
| `depends_on` | operații precedente |
| `parallelizable_with` | poate rula în paralel |
| `required_skill` | skill code |
| `required_station` | station code |
| `produces` | output operație |
| `checklist` | pași operator |
| `not_allowed_to_do` | anti-pattern |
| `execution_boundary` | preview seed vs task real |

**STOP:** dacă `active_if` / `inactive_if` sunt neclare pentru un caz → owner decision, nu inventa.

---

## Operation flags (implementat)

`derive_operation_flags_from_finishes()` mapează finisaje → activare operații:

| Flag | Condiție |
|------|----------|
| `return_vinyl_application_required` | return wrapped |
| `return_painting_after_assembly_required` | return painted |
| `face_vinyl_application_required` | face vinyl activ |
| `face_vinyl_after_return_painting` | face vinyl + return painted |
| `psu_packed_at_packaging` | illuminated, no shared support |
| `electrical_source_mounting_allowed` | illuminated + shared support |

---

## 1. `graphic_vector_preflight`

| Field | Value |
|-------|-------|
| **display_name** | Verificare grafică / vectorizare |
| **purpose** | Validează SVG, straturi, pregătire pentru model producție |
| **active_if** | vector asset uploadat sau pathway vector |
| **inactive_if** | — |
| **required_inputs** | `VectorAsset`, eventual `RawSvgAnalysis` |
| **depends_on** | — |
| **parallelizable_with** | — |
| **required_skill** | `graphic_design`, `vector_preflight` |
| **required_station** | `graphics_workstation` |
| **produces** | SVG validat, layer map, warnings |
| **execution_boundary** | Intake zone; seed în ProductionHandoff |

---

## 2. `confirmed_production_model`

| Field | Value |
|-------|-------|
| **display_name** | Confirmare model producție din vector |
| **purpose** | Operator confirmă 18/27/9 (sau alte valori) |
| **active_if** | raw analysis disponibil sau review manual |
| **inactive_if** | — |
| **required_inputs** | `ConfirmedProductionModel`, `LetterModel`, `CutContourModel` |
| **depends_on** | `graphic_vector_preflight` (recomandat) |
| **required_skill** | `graphic_design`, `vector_preflight` |
| **required_station** | `graphics_workstation` |
| **produces** | model confirmat, readiness litere OK |
| **not_allowed_to_do** | auto-confirmare din raw contour count |

---

## 3. `cnc_file_preparation`

| Field | Value |
|-------|-------|
| **display_name** | Pregătire fișiere CNC pentru debitare față/spate |
| **purpose** | Fișiere tehnice pentru router |
| **active_if** | model confirmat, dimensiuni OK |
| **depends_on** | `confirmed_production_model` |
| **parallelizable_with** | `return_vinyl_application_workbench` (dacă cant colantat) |
| **required_skill** | `cnc_file_preparation` |
| **required_station** | `cnc_preparation_station` |
| **produces** | fișiere față plexiglas, spate Forex |

---

## 4. `return_forming_file_preparation`

| Field | Value |
|-------|-------|
| **display_name** | Pregătire fișier / traseu pentru modelare cant |
| **purpose** | Traseu pentru mașina de modelare cant |
| **active_if** | return depth confirmat |
| **depends_on** | `confirmed_production_model` |
| **parallelizable_with** | `cnc_file_preparation`, `return_vinyl_application_workbench` |
| **required_skill** | `return_forming_file_preparation` |
| **required_station** | `cnc_preparation_station` |
| **produces** | fișier/traseu cant |

---

## 5. `return_vinyl_application_workbench`

| Field | Value |
|-------|-------|
| **display_name** | Colantare cant la banc de lucru |
| **purpose** | Oracal 651 pe bandă plată înainte de modelare |
| **active_if** | `return_finish_type` = colantat / Oracal / folie |
| **inactive_if** | cant necolantat; cant vopsit; finisaj material fără folie |
| **required_inputs** | return depth, material/culoare, ml estimat |
| **depends_on** | finisaj cant confirmat (nu depinde de CNC față) |
| **parallelizable_with** | `cnc_file_preparation`, `face_and_backing_cnc_cut` (dacă inputs clare) |
| **required_skill** | `vinyl_application_workbench` |
| **required_station** | `workbench` |
| **not_allowed_to_do** | la CNC; la mașina de modelare cant |

---

## 6. `face_and_backing_cnc_cut`

| Field | Value |
|-------|-------|
| **display_name** | Debitare față plexiglas și spate Forex la CNC |
| **purpose** | Debitare componente principale |
| **active_if** | fișiere CNC pregătite |
| **depends_on** | `cnc_file_preparation` |
| **required_skill** | `cnc_router_operation` |
| **required_station** | `cnc_router` |
| **produces** | fețe debitate, spate Forex debitat |

---

## 7. `return_side_forming`

| Field | Value |
|-------|-------|
| **display_name** | Modelare canturi aluminiu |
| **purpose** | Formare cant din bandă/aluminiu |
| **active_if** | material cant disponibil |
| **depends_on** | `return_forming_file_preparation`; + `return_vinyl_application_workbench` dacă cant colantat |
| **required_skill** | `return_forming_machine_operation` |
| **required_station** | `return_forming_machine` |

---

## 8. `return_face_bonding`

| Field | Value |
|-------|-------|
| **display_name** | Lipire canturi pe fețele din plexiglas |
| **purpose** | Corp literă față + cant |
| **depends_on** | `face_and_backing_cnc_cut` (față); `return_side_forming` (cant modelat) |
| **required_skill** | `letter_assembly` |
| **required_station** | `assembly_bench` |

---

## 9. `led_installation_wiring_and_light_test`

| Field | Value |
|-------|-------|
| **display_name** | Montaj LED, cablare LED și test aprindere fiecare literă |
| **purpose** | Iluminare pe spate Forex |
| **active_if** | iluminare activă în comandă |
| **depends_on** | `face_and_backing_cnc_cut` (spate Forex) |
| **required_skill** | `led_installation`, `electrical_wiring_basic` |
| **required_station** | `electrical_bench` |
| **checklist** | montează LED pe Forex; cablare; test fiecare literă; lasă cablu conectare |
| **not_allowed_to_do** | montaj surse pe suport (fără suport comun) |

---

## 10. `letter_assembly_no_shared_support`

| Field | Value |
|-------|-------|
| **display_name** | Asamblare litere pe spate Forex |
| **purpose** | Corp față+cant pe Forex cu LED |
| **active_if** | variantă fără suport comun |
| **depends_on** | `return_face_bonding`; `led_installation_wiring_and_light_test` |
| **required_skill** | `letter_assembly` |
| **required_station** | `assembly_bench` |
| **checklist** | atașează corp față+cant; autoforante cap îngropat; verifică lumină la cant; vopsește capete șuruburi dacă `paint_recessed_screw_heads_to_return_color` |

---

## 11. `return_painting_after_assembly`

| Field | Value |
|-------|-------|
| **display_name** | Protejare față, vopsire cant litere și îndepărtare protecție după uscare |
| **purpose** | Finisaj cant vopsit |
| **active_if** | `return_finish_type` = painted |
| **inactive_if** | cant colantat sau necolantat |
| **depends_on** | `letter_assembly_no_shared_support` |
| **required_skill** | `vinyl_application_workbench` sau skill vopsire (TBD registry) |
| **checklist** | protecție față; vopsire cant; uscare; îndepărtare protecție; verifică față curată |

---

## 12. `face_vinyl_application_final`

| Field | Value |
|-------|-------|
| **display_name** | Colantare finală fețe litere |
| **purpose** | Oracal 8500 / folie pe față |
| **active_if** | `face_vinyl_enabled` sau comandă specifică față colantată |
| **inactive_if** | față necolantată în comandă |
| **depends_on** | `letter_assembly_no_shared_support`; + `return_painting_after_assembly` dacă cant vopsit |
| **required_skill** | `face_vinyl_application` |
| **required_station** | `workbench` |
| **not_allowed_to_do** | înainte de asamblare; înainte de vopsire cant (dacă cant vopsit) |

---

## 13. `stretch_wrap_and_delivery_mounting_package`

| Field | Value |
|-------|-------|
| **display_name** | Infoliere cu folie stretch și pregătire colet pentru livrare / montaj |
| **purpose** | Protecție transport + predare |
| **active_if** | lucrare completă pentru livrare/montaj |
| **depends_on** | `face_vinyl_application_final` (dacă activ); `return_painting_after_assembly` (dacă activ); asamblare completă |
| **required_skill** | `packing_preparation` |
| **required_station** | `packing_area` |
| **checklist** | folie stretch; surse calculate în colet; accesorii; note montaj |
| **execution_boundary** | surse **în colet** pentru fără suport comun |

---

## Operații excluse (fără suport comun)

| operation_code | Motiv |
|----------------|-------|
| `electrical_source_mounting` | inactive — surse în colet, nu pe suport |

---

## Legături

- Skills: [../../../05_SKILLS_STATIONS_AND_ASSIGNMENT_BOUNDARY.md](../../../05_SKILLS_STATIONS_AND_ASSIGNMENT_BOUNDARY.md)
- Detaliu: [TASK_LOGIC_NO_SHARED_SUPPORT.md](./TASK_LOGIC_NO_SHARED_SUPPORT.md)
- Execution boundary: [06_TASK_SEED_AND_EXECUTION_BOUNDARY.md](./06_TASK_SEED_AND_EXECUTION_BOUNDARY.md)
