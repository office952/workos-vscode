# TPL-VOLUMETRIC-LETTERS — Task Logic Without Shared Support

**Template:** `TPL-VOLUMETRIC-LETTERS`  
**Variantă:** litere volumetrice luminoase **fără suport comun pe spate**  
**Data:** 2026-06-17  
**Status:** documentație operațională — Intake V3 / ProductSystem  
**Boundary:** nu modifică runtime execution, CostEngine, pricing, inventory, Employee Mobile sau DB

---

## 1. Scope

Acest document descrie logica operațională pentru **litere volumetrice luminoase individuale**, fără suport comun pe spate.

Este valabil pentru lucrări unde literele **nu** sunt montate în atelier pe:

- bare metalice;
- panou Dibond / ACM / Alucobond;
- casetă;
- altă structură comună pe spate.

Literele sunt produse ca unități individuale, pregătite pentru livrare sau montaj pe șantier, fără integrare electrică pe un suport comun în atelier.

Pentru lucrări **cu suport comun**, logica trebuie analizată separat — vezi secțiunea **Open questions**.

---

## 2. Principiu important

**Ordinea taskurilor nu este o listă statică.**

Este un **catalog de operații** cu:

- condiții de activare;
- dependențe;
- posibilitate de paralelizare;
- skill-uri / stații necesare;
- logică operațională documentată.

Template-ul **nu hardcodează persoane**.

Persoane precum Florin, Călin, Octavian, Goghi, Cristi pot fi exemple operaționale curente în atelier, dar template-ul trebuie să lucreze cu:

- **skill-uri** (ce competență cere operația);
- **stații** (unde se execută);
- **eligibilitate** (cine poate fi asignat);
- **asignare** manuală sau automată ulterioară.

Dacă logica de producție rămâne neclară pentru un caz concret, **STOP** — cere decizie owner. Nu inventa reguli operaționale.

---

## 3. Roluri / skill-uri, fără hardcodare persoane

| Operație (concept) | Skill / stație sugerată |
|--------------------|-------------------------|
| Verificare grafică / vectorizare | `graphic_design` / `vector_preflight` |
| Pregătire fișiere CNC debitare | `cnc_file_preparation` |
| Pregătire fișier / traseu modelare cant | `return_forming_file_preparation` |
| Debitare CNC față / spate | `cnc_router_operation` |
| Modelare canturi aluminiu | `return_forming_machine_operation` |
| Colantare cant la banc | `vinyl_application_workbench` |
| Lipire cant / asamblare corp literă | `letter_assembly` |
| Montaj LED / cablare / test aprindere | `led_installation` / `electrical_wiring_basic` |
| Colantare finală fețe | `face_vinyl_application` |
| Infoliere stretch + pregătire colet | `packing_preparation` |

**Notă operațională curentă:** în prezent, Florin poate fi bifat pentru CNC / pregătire fișiere / modelare cant — aceasta este **asignare operațională**, nu regulă de template.

---

## 4. Flux general — fără suport comun

Listă de bază (se modifică în funcție de finisajul cantului):

```text
1. Verificare grafică / vectorizare
2. Confirmare model producție din vector
3. Pregătire fișiere CNC pentru debitare față/spate
4. Pregătire fișier / traseu pentru modelare cant
5. Debitare față plexiglas și spate Forex la CNC
6. Modelare canturi aluminiu
7. Lipire canturi pe fețele din plexiglas
8. Montaj LED, cablare LED și test aprindere fiecare literă
9. Asamblare litere pe spate Forex
10. Colantare finală fețe litere, dacă este specificată în comandă
11. Infoliere cu folie stretch și pregătire colet pentru livrare / montaj
```

**Variante de finisaj cant** care modifică fluxul:

| Variantă cant | Efect asupra fluxului |
|---------------|------------------------|
| **Cant colantat** (Oracal / folie) | apare task `Colantare cant la banc de lucru` **înainte** de modelare |
| **Cant necolantat** | fără task colantare cant; modelare direct după pregătire traseu |
| **Cant vopsit** | fără colantare cant; vopsire cant **după** asamblare, cu protecție față |

Pașii 3–4 pot rula **în paralel** cu colantarea cantului (când cantul este colantat), dacă datele de finisaj și material sunt deja clare.

---

## 5. Pregătire grafică vs pregătire fișiere CNC

**Grafica** este făcută de persoane cu skill de grafică / vectorizare (`graphic_design`, `vector_preflight`).

**Pregătirea fișierelor pentru CNC** este operație tehnică **separată** (`cnc_file_preparation`).

**Pregătirea fișierului / traseului pentru modelarea cantului** este tot operație tehnică (`return_forming_file_preparation`), executată de persoana eligibilă pentru CNC / modelare cant.

Nu se hardcodează Florin — în situația curentă poate fi asignat la aceste operații.

**Output așteptat:**

- fișiere CNC pentru debitare față plexiglas;
- fișiere CNC pentru debitare spate Forex;
- fișier / traseu pentru modelare cant.

---

## 6. Colantare cant — ramura cant colantat

**Condiție de activare:** finisajul cantului este Oracal / folie / colantare (`return_finish_type` = oracal_wrapped / colantat).

**Task:**

```text
Colantare cant la banc de lucru
```

**Reguli:**

- se face în atelier, la **banc de lucru**;
- **nu** se face la CNC;
- **nu** se face la mașina de modelare cant;
- se face **înainte** de modelare cant;
- poate porni când sunt clare: adâncime cant, material/folie, culoare, ml estimat, material disponibil;
- poate merge **în paralel** cu pregătirea fișierelor CNC.

**Dependență:**

```text
Modelare canturi aluminiu
  depinde de Colantare cant la banc de lucru
  DOAR dacă return_finish_type = oracal_wrapped / colantat
```

---

## 7. Cant necolantat

**Condiție:** nu există finisaj de colantare pe cant.

**Task `Colantare cant la banc de lucru`:** **nu se generează**.

**Flux:**

```text
Pregătire fișier / traseu cant
  → Modelare canturi aluminiu
```

Modelarea cantului depinde de:

- fișier / traseu cant pregătit;
- material cant disponibil;
- adâncime cant confirmată.

**Nu** depinde de task de colantare.

---

## 8. Cant vopsit

**Condiție:** finisajul cantului este vopsire (`return_finish_type` = painted / RAL).

**Regulă:** cantul **NU** se vopsește înainte de modelare.

**Secvență pentru cant vopsit:**

1. cantul se **modelează**;
2. se **lipește** pe fața din plexiglas;
3. litera se **asamblează** pe spatele Forex;
4. se **protejează fața**;
5. se **vopsește cantul**;
6. se lasă la **uscat**;
7. se **îndepărtează protecția** de pe față.

**Task recomandat unic:**

```text
Protejare față, vopsire cant litere și îndepărtare protecție după uscare
```

**Checklist operator:**

- aplică folie de protecție pe fața literei;
- vopsește cantul conform culorii specificate;
- lasă vopseaua să se usuce;
- îndepărtează protecția după uscare;
- verifică fața să rămână curată / nevopsită.

**Dacă și fața trebuie colantată:** taskul de colantare finală fețe apare **doar după** vopsire, uscare și îndepărtarea protecției.

---

## 9. Montaj LED, cablare LED și test aprindere

**Regulă:** LED-urile se montează pe **spatele Forex**.

**Task:**

```text
Montaj LED, cablare LED și test aprindere fiecare literă
```

**Instrucțiune:**

- montează modulele LED pe spatele Forex;
- realizează cablarea LED;
- verifică **fiecare literă individual** dacă se aprinde;
- lasă cablul necesar pentru conectare ulterioară.

**Pentru varianta fără suport comun:**

- **nu** se montează sursele pe suport în atelier;
- sursele calculate se includ în taskul final de pregătire colet (secțiunea 12).

---

## 10. Asamblare litere pe spate Forex

**Definiție:** asamblarea înseamnă atașarea corpului literei format din:

- față plexiglas;
- cant aluminiu lipit;

pe spatele din Forex pe care sunt deja montate și testate LED-urile.

**Prindere:** autoforante mici cu cap îngropat.

**Checklist:**

- atașează corpul față + cant pe spatele Forex;
- folosește autoforante mici cu cap îngropat;
- verifică lipiturile cantului;
- verifică să nu iasă lumină pe la cant / lipituri / îmbinări;
- dacă este bifat, vopsește capetele autoforantelor la culoarea cantului.

**Opțiune comandă:**

```text
paint_recessed_screw_heads_to_return_color: true | false
```

---

## 11. Colantare finală fețe litere

**Condiție de activare:** apare **doar** dacă în comandă este specificat că fețele se colantează / infoliază (`face_vinyl_enabled` / finisaj față Oracal 8500 sau echivalent).

Dacă **nu** este specificat, taskul **nu** se generează.

**Regulă generală:**

```text
Colantarea finală a fețelor se face după asamblarea literei.
```

**Regulă suplimentară pentru cant vopsit:**

```text
Dacă return_finish_type = painted ȘI face_vinyl_enabled = true,
colantarea fețelor se face după:
  vopsirea cantului → uscare → îndepărtarea protecției de pe față
```

Această regulă este adevăr operațional owner — **nu** este încă reflectată în execution plan runtime WorkOS actual.

---

## 12. Infoliere cu folie stretch și pregătire colet pentru livrare / montaj

**Înlocuiește** orice denumire generică de tip „Ambalare / predare”.

**Task final:**

```text
Infoliere cu folie stretch și pregătire colet pentru livrare / montaj
```

**Instrucțiune:**

- protejează fiecare literă cu folie stretch;
- pregătește coletul pentru livrare sau montaj;
- **include sursele calculate** în colet;
- include accesoriile necesare, dacă sunt prevăzute în lucrare;
- include observații pentru montaj, dacă există.

**Pentru fără suport comun:**

- sursele **nu** se montează pe suport în atelier;
- sursele se **includ în colet** la acest pas.

---

## 13. Task generation rules

Reguli pentru generatorul viitor de taskuri (catalog operațional, nu listă statică).

### `return_vinyl_application` (Colantare cant la banc)

| | |
|---|---|
| **Active if** | cantul este colantat / Oracal / folie |
| **Inactive if** | cant necolantat; cant vopsit; cant = finisaj material existent (fără folie) |
| **Depends on** | material cant disponibil, adâncime confirmată, ml estimat |
| **Blocks** | `return_forming` (modelare cant) — doar când activ |

### `return_painting_after_assembly`

| | |
|---|---|
| **Active if** | cantul este vopsit |
| **Depends on** | asamblare litere pe spate Forex |
| **Preview / real** | task real la Order → ExecutionPlan; în Intake V3 = preview seed only |

### `face_vinyl_application` (Colantare finală fețe)

| | |
|---|---|
| **Active if** | fața este colantată / infoliată conform comenzii |
| **Depends on** | asamblare litere; + `return_painting_after_assembly` dacă cant vopsit |
| **Inactive if** | fața nu este specificată pentru colantare în comandă |

### `electrical_source_mounting` (Cablare / surse pe suport)

| | |
|---|---|
| **Inactive for** | **fără suport comun** (acest document) |
| **Alternative** | montaj LED + cablare LED + cablu lăsat; surse în pregătire colet |
| **Active for** | suport comun — document separat, neanalizat aici |

### `packaging` / dispatch prep

| | |
|---|---|
| **Display name** | `Infoliere cu folie stretch și pregătire colet pentru livrare / montaj` |
| **Includes** | surse calculate, accesorii, note montaj |
| **Depends on** | toate taskurile de finisaj și asamblare relevante pentru comandă |

---

## 14. Open questions

- **Suport comun pe spate** (bare metalice, panou Dibond/ACM/Alucobond, casetă, structură comună): logica **nu** este definită în acest document. Trebuie analizată separat, inclusiv când apare task `electrical_source_mounting` și cum se repartizează sursele.
- **Paralelizare exactă** între colantare cant și pregătire CNC: confirmare owner pentru capacitate atelier și reguli de blocare material.
- **Custom pe literă** (finisaje diferite per literă): în afara pilotului all/group — scope viitor Intake V3.

---

## 15. Boundary

Acest document este **doar documentație operațională** pentru Intake V3 / ProductSystem / dossier viitor.

**Nu schimbă:**

- execution plan runtime;
- task generator actual (`volumetric_conditional_plan_tasks_service`, `task_dependency_rules_service`);
- CostEngine;
- pricing;
- inventory / StockMovement;
- Employee Mobile;
- schema DB.

**Legătură cu builduri existente:**

- Owner rules parțial documentate în `backend/data_models/intake_v3_contracts.py` (`OWNER_OPERATIONAL_RULE_DETAILS`);
- Gap față de runtime: build viitor `AUDIT/FIX — Volumetric execution task order and electrical source handling`.

**Următor pas recomandat:** mapare aceste reguli în catalog operațional condiționat (operație + condiție + dependență + motiv), nu listă statică de pași.
