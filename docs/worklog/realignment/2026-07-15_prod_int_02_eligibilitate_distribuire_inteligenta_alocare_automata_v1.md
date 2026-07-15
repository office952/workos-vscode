# PROD-INT-02 — Audit logic: eligibilitate, distribuire inteligentă și alocare automată V1

**Task:** PROD-INT-02 — `AUDIT_LOGIC_ELIGIBILITATE_DISTRIBUIRE_INTELIGENTA_SI_ALOCARE_AUTOMATA_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `31a3f82`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `PROD_ROUTING_AUDIT_PASS_READY_FOR_OWNER_DECISIONS`  
**Cod changed:** NO

## Clasificări obligatorii

| Flag | Valoare |
|------|---------|
| MOBILE-T06 | `MOBILE_T06_COMPATIBIL_NUMAI_CU_EXECUTIE_INDIVIDUALA` |
| MOBILE-INT-02 | **BLOCAT** — până la decizii owner + model colaborativ |
| PROD-INT-01 (mod de lucru) | **NOT_PROVEN** în repo — dependență conceptuală neînchisă în cod |

---

## Verdict

WorkOS **nu are** un motor de distribuire inteligentă. Are fundații parțiale: registru operațional (competențe/autorizări), pregătire operații (dependențe/materiale), alocare operațională pe plan (MOBILE-T06), sesiuni ExecutionReality multi-angajat. Lipsesc: nivel competență, atribuție distinctă de competență, încărcare, disponibilitate program/absențe, capacitate utilaj consumată runtime, scor explicabil, propunere/confirmare, realocare, moduri de lucru canonice.

Auditul este **PASS pentru decizii owner** — nu pentru implementare imediată.

---

## Problemele modelului actual

1. **„Primul liber” implicit** — `list_available_tasks` filtrează eligibilii, dar nu ordonează/scorează; angajatul alege vizual.
2. **Eligibilitate neuniformă** — hard la preluare disponibilă; soft la pornire task deja alocat (`OperatorEmployeeGuard` avertizează); absentă la alocare manager.
3. **Competență ≠ atribuție** — ambele se reduc la `skill_code` + `role` text liber; fără rol principal/secundar structurat.
4. **Fără nivel competență** — autorizarea este booleană (are/nu are skill).
5. **Utilaj eligibil ≠ disponibil** — `MachineRegistry.is_available` și `capacity_metadata` nu intră în readiness/alocare.
6. **Fără încărcare** — nu există timp estimat rămas, număr sesiuni simultane, capacitate zilnică.
7. **Fără motor colaborativ** — sesiuni `primary/helper` există, dar fără mod de lucru, loturi, echipă minimă, cerere ajutor.
8. **MOBILE-T06 ≠ politică universală** — valabil doar execuție individuală (1 executant principal, preluare/pornire atomică).
9. **Fără audit decizie alocare** — `assignment_source` + timestamp pe plan; fără excluderi, scor, alternative, confirmare.
10. **Acoperire registru dependentă de seed** — operații fără mapping → eligibilitate `unverified`.

---

## Dicționar canonic (română exclusiv)

| Cod intern propus | Denumire canonică română | Definiție scurtă | Sinonime interzise |
|-------------------|--------------------------|------------------|-------------------|
| `PRODUCTIE_OPERATIE` | Operatie de productie | Unitate executabilă din plan, cu identitate înghețată | task, job, work item |
| `OPERATIE_PREGATITA` | Operatie pregatita | Dependențe/material/producție permisă îndeplinite; poate intra în distribuire | ready, available |
| `OPERATIE_BLOCATA` | Operatie blocata | Nu poate fi alocată/pornită; motiv explicit | blocked, stuck |
| `OPERATIE_DEPENDENTA` | Dependenta | Legătură obligatorie către altă operație | predecessor, dependency |
| `CONDITIE_PORNIRE` | Conditie de pornire | Set complet pentru a începe efectiv execuția | start gate, readiness |
| `COMPETENTA` | Competenta | Abilitate tehnică certificabilă a angajatului | skill, capability |
| `NIVEL_COMPETENTA` | Nivel de competenta | Grad (ex. autonom, avansat) — **NEIMPLEMENTAT** | level, grade |
| `ATRIBUTIE` | Atributie | Responsabilitate oficială a rolului pentru tip operație | assignment role, duty |
| `ROL_PRINCIPAL` | Rol principal | Rol dominant al angajatului în organizare | primary role |
| `ROL_SECUNDAR` | Rol secundar | Rol auxiliar permis la nevoie | secondary role |
| `AUTORIZARE` | Autorizare | Permisiune formală operație/utilaj | authorization, permit |
| `ELIGIBILITATE` | Eligibilitate | Poate/nu poate executa (binar, înainte de scor) | eligibility, qualified |
| `EXECUTANT_ELIGIBIL` | Executant eligibil | Angajat care trece filtrele obligatorii | eligible worker |
| `UTILAJ_ELIGIBIL` | Utilaj eligibil | Poate executa tehnic operația | eligible machine |
| `DISPONIBILITATE` | Disponibilitate | Liber în interval (program, absență, sesiune) | availability |
| `INCARCARE_CURENTA` | Incarcare curenta | Timp/alocări/sesiuni active estimate | workload, load |
| `CAPACITATE_DISPONIBILA` | Capacitate disponibila | Resursă rămasă (om/utilaj/timp) | capacity, slack |
| `PRIORITATE` | Prioritate | Ordine relativă operații/comenzi | priority |
| `TERMEN` | Termen | Dată/limită livrare/montaj | deadline, due date |
| `URGENTA` | Urgenta | Escaladare aprobată explicit | urgent flag |
| `CONTINUITATE_OPERATIONALA` | Continuitate operationala | Preferință același executant/comandă/utilaj | continuity |
| `ALOCARE_PROPUSA` | Alocare propusa | Recomandare motor neconfirmată | proposed assignment |
| `ALOCARE_CONFIRMATA` | Alocare confirmata | Alocare validată (auto sau manager) | confirmed assignment |
| `ALOCARE_AUTOMATA` | Alocare automata | Scriere fără confirmare umană | auto assign |
| `REALOCARE_TEMPORARA` | Realocare temporara | Mutare cu revenire planificată | temp reassign |
| `ALOCARE_SUPLIMENTARA` | Alocare suplimentara | Ajutor/echipă suplimentară | extra assignee |
| `ECHILIBRARE_INCARCARII` | Echilibrarea incarcarii | Optimizare distribuție încărcare | load balancing |
| `RESTRICTIE` | Restrictie | Interdicție medicală/operatională | restriction |
| `MOTIV_EXCLUDERE` | Motiv de excludere | De ce un executant eligibil nu e ales | exclusion reason |
| `SCOR_POTRIVIRE` | Scor de potrivire | Ranking între eligibili (post-filtru) | match score |
| `REGULA_DISTRIBUIRE` | Regula de distributie | Politică aplicată | routing rule |
| `DECIZIE_ALOCARE` | Decizie de alocare | Rezultat final + mod (auto/confirmat/manual) | allocation decision |
| `EXPLICATIE_ALOCARE` | Explicatia alocarii | Text factori pentru operator/manager | explanation |
| `INTERVENTIE_MANUALA` | Interventie manuala | Suprascriere manager auditată | manual override |
| `EXCEPTIE_APROBATA` | Exceptie aprobata | Derogare documentată | approved exception |
| `MOD_LUCRU` | Mod de lucru | Individual / colaborativ / lot / echipă / principal+ajutor | work mode |
| `CERERE_AJUTOR` | Cerere de ajutor | Solicitare colegi calificați | help request |
| `STARE_PREGATIRE` | Stare de pregatire | Pregătită alocare vs pregătită pornire vs blocată | readiness state |

**Denumiri exclusiv în română:** PASS (document audit)  
**Dicționar canonic:** PASS (definit aici; implementare UI/API viitoare)

---

## Model angajat — audit

| Informație | Există | Locație | Clasificare |
|------------|--------|---------|-------------|
| Rol principal (`role` text) | Parțial | `employees.role` | PARTIAL |
| Rol secundar 1/2 | Nu | — | INSUFICIENT |
| Competențe | Da | `employee_skill_authorizations` | PARTIAL (fără nivel) |
| Nivel competență | Nu | — | BLOCANT pentru distribuire avansată |
| Utilaje operate | Da | `employee_resource_authorizations` | PARTIAL |
| Autorizări operație | Da | mapping + explicit list | PARTIAL |
| Restricții medicale | Nu | — | INSUFICIENT |
| Experiență/productivitate/calitate istorică | Nu runtime | — | INSUFICIENT |
| Program/ture/concediu | Nu | `status` enum simplu | INSUFICIENT |
| Absență | Parțial | `on_leave`/`sick` status | PARTIAL |
| Sesiuni active | Da | ExecutionReality | SUFICIENT |
| Alocări curente | Parțial | `assigned_employee_id` plan | PARTIAL |
| Încărcare planificată/reală | Nu | — | INSUFICIENT |
| Locație/echipă | Parțial | `department`, echipe montaj | PARTIAL |

**Model angajati:** **PARTIAL**

---

## Competențe vs atribuții

| Concept | Definiție audit | Stare cod |
|---------|-----------------|-----------|
| **Competența** | Ce poate executa tehnic (ex. modelare cant, sudare, CNC) | `OperationalRegistryService.check_employee_operation_eligibility` — skill/workcenter/resource |
| **Atribuția** | Ce intră în responsabilitatea rolului; poate exista competență fără atribuție principală | **Nu modelată** — `role` liber + skills; fără matrice atribuție |

Influență distribuție (țintă):

| Factor | Stare |
|--------|-------|
| Competență obligatorie | Parțial (mapping `required_skill_codes`) |
| Atribuție principală | Lipsă |
| Atribuție secundară / rezervă | Lipsă |
| Competență ajutor | Lipsă ca tip distinct |
| Autorizare obligatorie | Parțial (mod explicit/hybrid) |

**Competente:** PARTIAL | **Atributii:** INSUFICIENT | **Autorizari:** PARTIAL

---

## Niveluri competență (propunere — fără implementare)

| Nivel propus | Drepturi țintă |
|--------------|----------------|
| Incepator | Asistat, fără operator principal |
| Asistat | Cu supraveghere |
| Autonom | Operator principal standard |
| Avansat | Operator principal + utilaje complexe |
| Instructor | Verificare/coordonare |

**Decizie owner obligatorie** — nu implementăm scala fără aprobare.

---

## Matrice operație–competență (eșantion din catalog + mapping)

| Operatie (RO) | Competenta obligatorie (cod) | Rol principal țintă | Utilaj | Ajutor | Stare mapping |
|---------------|------------------------------|---------------------|--------|--------|---------------|
| Pregătire grafică | SK_GRAPHIC_DESIGN | Grafician | — | Nu | Alias `prepress` |
| Verificare fișier | SK_GRAPHIC_DESIGN | Grafician | — | Nu | Parțial |
| Debitare CNC | SK_CNC_OPERATOR | CNC | WC_CNC_ROUTING | Da manipulare | `cnc_cutting` |
| Modelare cant | SK_LETTER_MODELING | Modelare | WC_LETTER_FORMING | Da | `cant_modelare` |
| Lipire cant/fete | SK_LETTER_CANT_OPERATOR | Operator cant | — | Da | Parțial |
| Montare LED / cablare | SK_ELECTRICIAN | Electrician | WC_LED_ASSEMBLY | Da | `montaj_led` |
| Sudare structură | SK_LOCKSMITH | Lăcătuș | WC_METAL_FAB | Da | `welding` |
| Asamblare litere/casetă | SK_ASSEMBLY | Ansamblare | WC_ASSEMBLY | Da colaborativ | `assembly` |
| Aplicare folie | SK_VINYL_APPLICATOR | Colantator | — | Da | `colantare` |
| Print | SK_PRINT_OPERATOR | Operator imprimantă | WC_PRINT | Nu | Seed existent |
| Laminare | SK_LAMINATOR_OPERATOR | Operator laminator | WC_LAMINATE | Opțional | `laminare` |
| Ambalare | SK_ASSEMBLY | Ansamblare | — | Da | `packaging` |
| Montaj la locație | SK_FIELD_INSTALLER | Montator | Echipă teren | Echipă | `FieldInstallationTeam` |
| Verificare finală | SK_ASSEMBLY / QC | — | — | — | `quality_control` parțial |

Matrice completă necesită **PROD-INT-03** (post-decizii owner), nu implementare acum.

---

## Eligibilitate executant

**Regulă țintă:** binar Eligibil / Neeligibil înainte de orice scor.

**Implementare actuală** (`check_employee_operation_eligibility`):

- Angajat activ
- Mapping operație existent
- Mod skill / explicit / hybrid
- Potrivire skill + workcenter + resource (heuristic `machine_type`)

**Lipsesc din filtru:** program, absență, încărcare max, locație, sesiune incompatibilă, restricții, nivel minim, atribuție.

**Clasificare eligibilitate:** `PARTIAL_BINARA_EXISTA_FARA_NIVEL_SI_INCARCARE`

### Motive neeligibilitate (cod intern → denumire RO)

| Cod intern | Denumire RO | În cod azi |
|------------|-------------|------------|
| `COMPETENTA_LIPSA` | Competenta lipsa | Parțial (`not_authorized`) |
| `NIVEL_INSUFICIENT` | Nivel insuficient | Nu |
| `AUTORIZARE_LIPSA` | Autorizare lipsa | Parțial |
| `ROL_INCOMPATIBIL` | Rol incompatibil | Nu |
| `UTILAJ_NEAUTORIZAT` | Utilaj neautorizat | Parțial (resource) |
| `IN_AFARA_PROGRAMULUI` | In afara programului | Nu |
| `ABSENT` | Absent | Parțial (`employee_inactive`) |
| `ALOCARE_EXCLUSIVA` | Deja alocat exclusiv | Parțial (assignment conflict) |
| `INCARCARE_MAXIMA` | Incarcare maxima atinsa | Nu |
| `LOCATIE_INCOMPATIBILA` | Locatie incompatibila | Nu |
| `OPERATIE_BLOCATA` | Operatie blocata | Da (readiness) |
| `DEPENDENTE_NEINDEPLINITE` | Dependente neindeplinite | Da |
| `ECHIPA_INCOMPLETA` | Echipa incompleta | Nu |
| `RESTRICTIE_OPERATIONALA` | Restrictie operationala | Nu |

---

## Stare pregătire vs alocare vs pornire

| Stare (RO) | Cod readiness actual | Alocare | Pornire |
|------------|----------------------|---------|---------|
| Blocata manual | `blocked_manual` | Nu | Nu |
| In asteptare predecesor | `waiting_predecessor` | Nu | Nu |
| In asteptare material | `waiting_material` | Nu | Nu |
| In asteptare fisier/decizie | `waiting_file` / `waiting_template_decision` | Nu | Nu |
| Eligibila (tehnic) | `eligible` | Da (dacă nealocată) | Da (dacă alocată mie) |
| Nealocata | `unassigned` | Da pool disponibil | Nu direct |
| Alocata altuia | `assigned_not_mine` | Nu | Nu |
| In lucru | `in_progress` | Nu | — |
| Finalizata | `done` | Nu | Nu |

**Dependente:** **SUFICIENT** (`task_readiness_service`, `depends_on_task_ids`)  
**Stare pregătire:** **PARTIAL** (lipsește utilaj/disponibilitate în gate)

---

## Utilaje

| Câmp | Model `MachineRegistry` | Consum runtime alocare |
|------|-------------------------|------------------------|
| Tip/cod/stare | Da | Nu |
| Disponibilitate flag | `is_available` | **Nu consumat** |
| Capacitate | `capacity_metadata` JSON | **Nu consumat** |
| Operatori autorizați | Reverse via registry | Parțial |
| Rezervări/sesiune activă | Nu | Nu |

**Utilaj eligibil** vs **disponibil** vs **recomandat** — **notiuni neimplementate**.

**Model utilaje:** PARTIAL | **Capacitate utilaje:** INSUFICIENT

---

## Mod de lucru

PROD-INT-01 **not proven** în repository. Propuneri canonice (doar audit):

| Mod (RO) | Comportament distribuție |
|----------|--------------------------|
| Executie individuala | 1 executant; MOBILE-T06 acoperă |
| Executie colaborativa | N executanți; sesiuni multiple |
| Executie pe loturi | Sub-seturi operație |
| Executie in echipa | Echipă minimă (ex. montaj) |
| Operator principal cu ajutor | Principal + ajutori separați |

**Clasificare:** `BLOCANT_PENTRU_DISTRIBUIRE_INTELIGENTA` — același flux MOBILE nu poate servi toate modurile.

---

## MOBILE-T06 reclasificare

| Acțiune MOBILE | Mod suportat | Notă |
|----------------|--------------|------|
| Preiau si pornesc | Executie individuala | Primary atomic |
| Preiau sarcina | Executie individuala | Fără sesiune |
| Ma alatur operatiei | — | **Nedefinit** |
| Preiau lotul | — | **Nedefinit** |
| Ma alatur ca ajutor | — | Sesiuni helper există backend, UI absent |
| Confirm participarea | — | **Nedefinit** |

**MOBILE-T06:** `MOBILE_T06_COMPATIBIL_NUMAI_CU_EXECUTIE_INDIVIDUALA`  
**MOBILE-INT-02:** **BLOCAT**

---

## ExecutionReality

| Capabilitate | Stare |
|--------------|-------|
| Sesiuni multiple / rol primary-helper | SUFICIENT (`task_work_session_service`) |
| Alocări viitoare | INSUFICIENT |
| Loturi | INSUFICIENT |
| Explicație alocare | INSUFICIENT |
| Realocare auditată | INSUFICIENT |

**ExecutionReality:** `PARTIAL_PENTRU_DISTRIBUIRE_INTELIGENTA`

---

## Motor distribuție — stadiu

| Etapă conceptuală | Stare |
|-------------------|-------|
| Colectare operații pregătite | Parțial (list available + readiness) |
| Excludere blocate | Da |
| Eligibili angajați | Parțial (boolean, o persoană) |
| Eligibili utilaje | Nu |
| Disponibilitate interval | Nu |
| Combinatii + mod lucru | Nu |
| Scor potrivire | **Nu** |
| Impact operații existente | Nu |
| Propunere / auto / confirmare | Nu (doar self-claim + manager assign) |
| Explicație + recalculare | Nu |

**Alocare automata:** PARTIAL (cazuri individuale MOBILE-T06)  
**Propunere cu confirmare:** INSUFICIENT  
**Scor potrivire:** INSUFICIENT  
**Ajutor:** INSUFICIENT  
**Realocare:** INSUFICIENT  
**Disponibilitate:** INSUFICIENT  
**Incarcare:** INSUFICIENT

---

## Scenarii obligatorii (simulare logică)

| # | Scenariu | Rezultat audit azi |
|---|----------|-------------------|
| 1 | 100 litere, 3 eligibili, colaborativ, loturi, ajutor, realocare | **BLOCANT** — fără mod lot/echipă/scor |
| 2 | Sudare urgentă vs 2× modelare cant | **Nerecomandat auto** — fără motor impact/realocare |
| 3 | CNC, 2 operatori, continuitate vs nivel | **Manual** — eligibili listați, fără scor/explicație |
| 4 | Montaj echipă 3 roluri + șofer | Parțial `FieldInstallationTeam`, fără integrare plan |
| 5 | Laminare, laminator ocupat, print anterior | Dependență da; utilaj ocupat **nu modelat** |
| 6 | Absent planificat | Status employee parțial; fără înlocuitor automat |
| 7 | 2 comenzi urgente, resurse insuficiente | Fără conflict engine — **decizie manager obligatorie** |

---

## Decizii owner obligatorii (22)

1. Scala niveluri competență  
2. Cine validează competența  
3. Ponderea atribuției principale vs competență  
4. Criterii alocare automată vs confirmare  
5. Ordinea criteriilor optimizare (termen vs echilibrare vs continuitate)  
6. Folosire productivitate istorică  
7. Folosire calitate istorică  
8. Folosire cost intern în scor (da/nu)  
9. Prag supraîncărcare  
10. Număr operații simultane max  
11. Politică realocare (când permisă)  
12. Politică ajutor (auto vs recomandare)  
13. Protecție sesiuni active (ex. 10 min rămas)  
14. Prioritate comercială vs operațională  
15. Cine poate marca urgență  
16. Intervenție manuală — câmpuri audit  
17. Explicații vizibile angajatului  
18. Moduri de lucru canonice (PROD-INT-01)  
19. Matrice operație–competență completă  
20. Consum capacitate utilaj în runtime  
21. Integrare program/absențe/pontaj  
22. Relansare MOBILE-INT-02 după model colaborativ  

---

## Model recomandat (conceptual)

```text
Operatie de productie
├── dependente
├── stare de pregatire (alocare / pornire)
├── mod de lucru
├── competente + autorizari + utilaje
├── numar executanti
├── prioritate + termen
├── eligibili (filtru binar)
├── scoruri (doar între eligibili)
├── alocare propusa → confirmata / automata
├── sesiuni + contributii
└── explicatia deciziei

Angajat
├── rol principal + secundare
├── competente + niveluri
├── autorizari + utilaje
├── program + absente
├── incarcare + sesiuni
└── disponibilitate
```

---

## Ordine implementare propusă (post-decizii — fără execuție)

1. Vocabular canonic RO (acest audit)  
2. Matrice operație–competență  
3. Model angajat–competență–utilaj (+ nivel)  
4. Eligibilitate binară completă  
5. Stare pregătire extinsă (utilaj)  
6. Încărcare  
7. Propunere alocare + explicabilitate  
8. Confirmare manager  
9. Alocare automată cazuri sigure  
10. Ajutor + realocare + colaborare  
11. Integrare mobile pe moduri  
12. Gate final distribuție  

---

## Impact suprafețe (fără implementare)

| Suprafață | Ce trebuie (audit) |
|-----------|-------------------|
| Employee Mobile | Moduri distincte; fără scoruri punitive; acțiuni per mod |
| OperatorView | Pregătite, eligibili, recomandare, motive, conflicte |
| Backend | Motor propunere separat de MOBILE-T06 |
| DB | Nivel competență, încărcare, audit decizie — **viitor** |
| Pontaj | Legătură timp planificat/real/ajutor — **INSUFICIENT** azi |

**Frontend assignment authority:** **NO** (mobile rămâne backend-bound)

---

## Riscuri

- Tratarea MOBILE-T06 ca motor universal  
- Alocare manager fără eligibilitate  
- Oscilație realocări fără perioadă stabilitate  
- Confundare competență/atribuție  
- Utilaj liber ≠ operator autorizat  

---

## Următorul task permis

**`OWNER_DECISION_GATE_DISTRIBUIRE_INTELIGENTA_V1`** — decizii pe cele 22 puncte; apoi PROD-INT-03 (matrice + model) sau arhitectură motor.

**MOBILE-INT-02:** rămâne **BLOCAT**.

---

## Opinie sinceră

Fundația MOBILE-T06 și registrul operațional sunt suficiente pentru **execuție individuală controlată**, nu pentru **distribuire inteligentă**. Cel mai mare gap nu este UI, ci absența unui strat decizional: încărcare, mod de lucru, scor explicabil și politici de realocare. Fără decizii owner, orice „algoritm” ar fi arbitrar.

**Roadmap:** Wave 7 + mobile T01–T06 închise; următorul frontiere productiv este distribuția, nu o nouă acțiune mobile.
