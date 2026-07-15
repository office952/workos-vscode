# OWNER-DECISION-03 — Confirmarea autorităților operaționale reale

**Task:** OWNER-DECISION-03 — `OPERATIONAL_AUTHORITY_CONFIRMATION_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `276fb83` (după MODULE-INT-01 @ `276fb83`; lanț APP-AUTH acceptat neschimbat)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Worktree:** `C:\w\psiso`  
**Owner decision recorded:** 2026-07-15 (răspuns explicit owner — CONFIRM A1–A22)  
**Cod changed:** NO · **DB changed:** NO · **Implementare autorizată:** NO (doar politici confirmate; migrare/distribuire/colaborativ **NU**)

## Verdict

**`OWNER_OPERATIONAL_AUTHORITIES_CONFIRMED`**

**22/22 CONFIRMATE** prin răspuns explicit owner. Politicile canonice de autoritate operațională sunt acceptate. **Migrarea datelor nu este autorizată** (A22:A). **PROD-ARCH-01** și **MOBILE-INT-02** rămân **BLOCATE** până la instrumentare paritate + reconciliere (inclusiv fișa Sandu). **Distribuire inteligentă** și **execuție colaborativă** **NU** sunt autorizate.

---

## Siguranță repository

| Verificare | Rezultat |
|------------|----------|
| Cod aplicație | **NO** |
| DB / migrări | **NO** |
| UI | **NO** |
| Date angajați | **NO** |
| Reconciliere Sandu automată | **NO** |
| Ștergere JSON legacy | **NO** |
| Dezactivare fallback | **NO** |
| Modificare mapping-uri / alocări | **NO** |

---

## Lanț evidență acceptat

| Task | Commit / stare |
|------|----------------|
| APP-INT-01 | `bfe20c6` |
| APP-AUTH-01 | `357838e` |
| APP-AUTH-02 | `b6081c0` |
| OWNER-DECISION-02 | `b38f6a6` |
| APP-AUTH-02B application | `328416b` |
| APP-AUTH-02B docs | `59449bc` |
| APP-AUTH-02C config | `abf1a99` |
| APP-AUTH-02C docs | `6acadc0` (**HEAD gate**) |

**Runtime de încredere:** backend `http://127.0.0.1:8001` (`CANONICAL_BACKEND_PROCESS` via `scripts/dev-backend.ps1`); frontend `http://127.0.0.1:3000`.

**Contract runtime acceptat (APP-AUTH-02B/C):** proiecția Available = `ORDER_LOCAL_FAIL_CLOSED`; comenzi corupte nelegate excluse; comenzi valide vizibile; assigned corrupt = strict 422; Operator Truth strict; fără fallback V2→legacy.

**Pistă separată Module Chain (nu deturnează acest gate):**

| Task | Commit | Verdict | Impact pe O3 |
|------|--------|---------|--------------|
| MODULE-INT-01 | `276fb83` | `MODULE_CHAIN_AUDIT_BLOCKED_STATIC_DEMO_DATA` | **ZERO** — `/modules` nu este sursă de adevăr pentru autorități operaționale |
| MODULE-RUNTIME-01 | — | **DEFERRED** — nu este task activ | Nu deschis |
| MODULE-ARCH-01 | — | **BLOCKED** | Nu deschis |

Constatările despre handoff-uri statice, event stream demo și health misleading pe `/modules` rămân datorie separată (`module-chain/governance debt`, `event/snapshot observability debt`). **Nu** influențează deciziile A1–A22.

**Probe:** `docs/qa/product-system-active-path-isolation-v1/app_auth_02/*.json`, `app_auth_02c_external_http_evidence.json`, `app_int_01_runtime_probe.json`, worklog-uri APP-INT-01 / APP-AUTH-01/02 / OWNER-DECISION-02 / APP-AUTH-02B/C / MODULE-INT-01.

---

## Fapte acceptate (păstrate)

1. 8 angajați operaționali; `employees.id` folosit operațional.
2. Un singur angajat cu legătură utilizator (Sandu → `dev-admin-user-00000000`).
3. Employee Mobile depinde de legătura angajat–utilizator.
4. 8 înregistrări HR; 15 competențe catalog; 30 relații angajat–competență.
5. Toți cei 8 angajați păstrează JSON legacy `skills`.
6. Sandu = singurul caz material de drift competențe/autorizări.
7. 39 mapping-uri explicite operație–angajat (inventar JSON: 42 rânduri = 39 additive + 3 `NARROWING_ONLY`).
8. 7 mapping-uri Sandu fără competență registry; 6 fără autorizare dovedită; `montaj_led` = CRITIC.
9. `machines` = sursa puternică identitate utilaj; `MCH-CNC-4020` aliniat.
10. Catalog centre de lucru = sursa puternică workcenter.
11. `task_readiness_service` = readiness producție; ExecutionReality = Start/Complete.
12. Pontaj separat de sesiuni producție; disponibilitate/încărcare fără model canonic.
13. Employee Mobile + Operator = suprafețe execuție active; Tablet = paralel/tranzitoriu; Shop Floor = proiecție.
14. Închidere runtime Available completă; migrare automată neautorizată.

---

## Pachet decizii A1–A22

**Regulă aplicată:** răspuns owner explicit din 2026-07-15 → toate deciziile marcate **CONFIRMAT**.

### Înregistrare decizie owner (text recepționat)

```text
CONFIRM A1–A22, cu urmatoarele alegeri:
A1: A | A5: A | A6: A | A16 Tablet: A | A22: A
Exceptii sau modificari: Niciuna.

Neautorizat explicit: distribuire inteligenta, executie colaborativa, migrare date.
PROD-ARCH-01 blocat pana la instrumentare paritate + reconciliere autoritati.
MOBILE-INT-02 blocat.
```

**Precizări owner (34 puncte) — rezumat obligatoriu:**

| # | Precizare confirmată |
|---|---------------------|
| 1–3 | `employees.id` identitate canonică; `user_id` legătură autentificare; `EmployeeRecord` extensie HR 1:1, nu înlocuiește identitatea |
| 4–5 | HR separat de operațional; `/employees` = agregator/editor peste registre canonice |
| 6 | Rol, Atribuție, Competență, Autorizare = concepte distincte |
| 7–8 | Catalog + relație angajat–competență = țintă canonică după reconciliere; JSON legacy transitional, fără migrare automată |
| 9–11 | Sandu: varianta A reconciliere umană; competențele/autorizările efective **nu** sunt confirmate prin această decizie; comportament temporar păstrat; fără ștergere alocări; fără alocare automată; mapping-urile nu devin dovadă competență |
| 12–13 | Liste explicite restricție/selectare; excepții viitoare = Exceptie temporară de eligibilitate cu audit |
| 14–18 | Autorizare separată de competență; catalog centre canonic; `machines` identitate utilaj; `MCH-CNC-4020` canonic; relație angajat–resursă canonică |
| 19–23 | Cerințe operație versionate; readiness separat de eligibilitate; alocare serviciu unic; `assigned_employee_id` doar execuție individuală; ExecutionReality Start/Complete |
| 24–28 | Mobile canonic individual; Operator prin aceleași servicii; **Tablet = mod chiosc explicit (A)** fără autoritate paralelă; Shop Floor proiecție fără mock silent |
| 29–31 | Pontaj separat; 7 angajați fără user valizi operațional fără Mobile personal; disponibilitate/încărcare = proiecții viitoare, neimplementate |
| 32–34 | ORDER_LOCAL_FAIL_CLOSED acceptat; assigned strict pe snapshot corupt; A22:A = instrumentare drift + plan paritate + reconciliere controlată, **fără migrare acum** |

### A1 — Identitate angajat operațional

| Câmp | Valoare |
|------|---------|
| Autoritate recomandată | `employees.id` = identitate canonică; `employees.user_id` = legătură autentificare; `EmployeeRecord` = extensie HR 1:1 |
| Opțiuni owner | **A** (recomandat): model de mai sus · **B**: EmployeeRecord primar · **C**: entitate Person nouă |
| Recomandare | **A** |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A2 — Autoritate HR

| Câmp | Valoare |
|------|---------|
| Direcție | HR separat de operațional; HR deține identitate legală, contract, salariu, pontaj payroll, documente private |
| Reguli | date demo HR ≠ autoritate; pagini operaționale nu scriu salariu fără rută HR; pontaj ≠ sesiuni producție |
| Recomandare | Confirmare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A3 — Profil angajat operațional

| Câmp | Valoare |
|------|---------|
| Direcție | `/employees` = agregator/editor peste registre canonice, nu stocare paralelă |
| Agregă | identitate, user, rol, atributii, competențe, autorizări, centre, resurse, stare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A4 — Rol, atributie, competență, autorizare

| Câmp | Valoare |
|------|---------|
| Taxonomie strictă | Rol ≠ competență ≠ autorizare ≠ centru ≠ utilaj ≠ operație |
| Reguli | rol nu dovedește competență; competență nu dovedește autorizare; catalog mixt = reconciliere înainte de migrare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A5 — Autoritate competențe

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): catalog + relație angajat–competență canonică după reconciliere · **B**: dual-write permanent · **C**: JSON legacy autoritate |
| Reguli | JSON transitional; fără migrare automată; eligibilitate viitoare fail-closed |
| Recomandare | **A** |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A6 — Reconciliere Sandu

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): reconciliere umană · **B**: registry câștigă imediat · **C**: legacy câștigă imediat |
| Alegere owner | **A** |
| Comportament temporar (A) | păstrează runtime; arată drift managerului; fără alocare automată; fără migrare JSON; alocările active nu se șterg |
| Competențe/autorizări efective Sandu | **NU confirmate** prin această decizie — validare individuală owner/manager/tehnic/Sandu |
| **Status** | **CONFIRMAT** — varianta A; fișa capabilități **în curs** |

### A7 — Mapping-uri eligibilitate explicite

| Câmp | Valoare |
|------|---------|
| Politică | lista explicită poate restrânge/selecta; nu adaugă silențios fără competență/autorizare |
| Excepție viitoare | `Exceptie temporara de eligibilitate` cu câmpuri audit obligatorii |
| 39 mapping-uri | inventariate; reconciliere manuală; fără bulk-migrate ca dovadă competență |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A8 — Autoritate autorizări

| Câmp | Valoare |
|------|---------|
| Direcție | autoritate dedicată separată de competențe; câmpuri: cod, angajat, scope, utilaj, valabilitate, dovadă, audit |
| Fail-closed | autorizare obligatorie lipsă/expirată → Neeligibil; manager nu ocolește legal/safety prin excepție simplă |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A9 — Autoritate centre de lucru

| Câmp | Valoare |
|------|---------|
| Direcție | catalog workcenter canonic; nu utilaj/competență/operație; intrări mixte = clasificare înainte de migrare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A10 — Autoritate utilaj și resursă

| Câmp | Valoare |
|------|---------|
| Direcție | `machines` = identitate concretă; `resource_kind` viitor obligatoriu |
| CNC 4020 | `MCH-CNC-4020` canonic; gap = metadata/taxonomie (`WC_CNC` vs `WC_CNC_ROUTING`) |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A11 — Autorizare angajat–resursă

| Câmp | Valoare |
|------|---------|
| Direcție | `employee_resource_authorizations` (sau relație registry curentă); JSON resurse = transitional |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A12 — Cerințe operație

| Câmp | Valoare |
|------|---------|
| Direcție | șablon/tip operație deține competență, nivel, autorizare, rol, centru, resursă, mod lucru |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A13 — Autoritate readiness

| Câmp | Valoare |
|------|---------|
| Direcție | `task_readiness_service` canonic pentru readiness producție; separat de eligibilitate/disponibilitate/încărcare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A14 — Autoritate alocare

| Câmp | Valoare |
|------|---------|
| Direcție | un serviciu canonic alocare; toate suprafețele trec prin el; audit complet; `assigned_employee_id` compatibil doar execuție individuală |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A15 — Autoritate sesiune execuție

| Câmp | Valoare |
|------|---------|
| Direcție | ExecutionReality canonic Start/Complete; participare colaborativă viitoare ≠ un singur `assigned_employee_id` |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A16 — Suprafețe execuție

| Suprafață | Direcție confirmată | Status |
|-----------|---------------------|--------|
| Employee Mobile v2 | control execuție individual canonic | **CONFIRMAT** |
| `/operator` | desktop prin aceleași servicii canonice | **CONFIRMAT** |
| `/tablet` | **A** — mod chiosc explicit peste servicii canonice; fără autoritate paralelă alocare/pregătire/sesiuni | **CONFIRMAT** |
| `/shop-floor` | proiecție; fără mock silent în producție | **CONFIRMAT** |

### A17 — Autoritate pontaj

| Câmp | Valoare |
|------|---------|
| Direcție | pontaj canonic separat; ExecutionReality = sesiuni producție; reconciliere viitoare fără suprascriere automată |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A18 — Angajați fără cont utilizator

| Câmp | Valoare |
|------|---------|
| Direcție | 7 angajați valizi operațional; alocare manager da; Mobile personal nu; fără creare automată user |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A19 — Disponibilitate și încărcare

| Câmp | Valoare |
|------|---------|
| Direcție | niciun model canonic acum; direcții viitoare documentate; implementare neautorizată prin confirmare |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A20 — Tranziție legacy și demo

| Câmp | Valoare |
|------|---------|
| Direcție | fără mock silent prod; demo ≠ eligibilitate; JSON observabil; freeze writes viitor; parity înainte de switch |
| **Status** | **CONFIRMAT** — opțiunea **A** |

### A21 — Contract proiecție Available

| Câmp | Valoare |
|------|---------|
| Contract | ORDER_LOCAL_FAIL_CLOSED — dovedit APP-AUTH-02B/C |
| Acceptare owner | Comportament operațional **CONFIRMAT** (puncte 32–33) |
| **Status** | **CONFIRMAT** |

### A22 — Autorizare migrare

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): fără migrare; doar instrumentare + workflow confirmare · **B**: migrare registry imediată · **C**: fallback legacy permanent |
| Recomandare | **A** |
| **Status** | **CONFIRMAT** — opțiunea **A** |

---

## Pachet răspuns owner — RECEPȚIONAT 2026-07-15

```text
CONFIRM A1–A22, cu urmatoarele alegeri:
A1: A
A5: A
A6: A
A16 Tablet: A
A22: A
Exceptii sau modificari: Niciuna.
```

**Toate cele 22 decizii sunt CONFIRMATE.** Fișa Sandu (capabilități individuale) rămâne de completat în APP-AUTH-03 / reconciliere controlată.

---

## Tabel autoritate

| Adevăr | Țintă canonică | Sursă tranzitorie | Writer | Consumatori | Fail-closed |
|--------|----------------|-------------------|--------|-------------|-------------|
| Identitate angajat operațional | `employees.id` | — | HR/admin (create); operațional (profile) | Mobile, Operator, alocare, sesiuni | Da — ID stabil sesiuni istorice |
| Legătură autentificare | `employees.user_id` | — | admin controlled | Employee Mobile | Da — fără user = fără Mobile personal |
| HR privat | `EmployeeRecord` / HR services | demo metadata | HR authority | `/employees-records` | Da — operațional nu scrie salariu |
| Competență (definiție) | catalog competențe | — | registry admin | eligibilitate | Da — competență obligatorie lipsă |
| Competență (posesie) | relație angajat–competență | `employees.skills` JSON | registry (țintă) | eligibilitate, `/employees` | Da — după switch |
| Autorizare formală | registry autorizări (țintă dedicată) | `operation_employee_authorizations` hybrid | registry admin | eligibilitate, alocare | Da — fără bypass safety/legal |
| Mapping explicit eligibilitate | inventar reconciliat | `operation_employee_authorizations` | manager (tranzitor) | hybrid eligibility mode | Parțial — nu dovedește competență |
| Centru de lucru | catalog workcenter | intrări mixte neclasificate | registry admin | operații, autorizări | Da — după migrare |
| Utilaj / resursă | `machines` + `resource_kind` | mock specs UI | registry admin | Operator, Shop Floor, task | Da — inactiv/defect nealocabil |
| Autorizare angajat–resursă | `employee_resource_authorizations` | JSON resurse angajat | registry | Operator, Mobile | Da |
| Cerințe operație | șablon/tip operație versionat | câmpuri dispersate plan | product template | task runtime frozen | Da |
| Readiness producție | `task_readiness_service` | — | readiness pipeline | Mobile, Operator | Da — separat de eligibilitate |
| Eligibilitate angajat | serviciu registry (țintă) | hybrid + JSON + mapping explicit | — (read) | Mobile available, alocare | Da — țintă post-reconciliere |
| Alocare | serviciu canonic alocare (țintă) | `assigned_employee_id` + rute paralele | assignment service | toate suprafețele | Da — audit obligatoriu |
| Sesiune execuție | ExecutionReality | tablet demo | ExecutionReality | Mobile, Operator | Da — protecție sesiune activă |
| Pontaj | `employee_attendance_events` | — | attendance | HR, disponibilitate viitoare | Da — separat sesiuni |
| Proiecție Available | `employee_mobile_tasks_service` ORDER_LOCAL_FAIL_CLOSED | — | — (read) | Employee Mobile | Da — order local exclude |
| Proiecție Shop Floor | read-only canonical | mockData frontend | — | `/shop-floor` | Da — fără mock silent prod |

---

## Tabel rute

| Rută | Scop | Citiri canonice | Scrieri permise | Status tranziție |
|------|------|-----------------|-----------------|------------------|
| `/employees` | agregator profil operațional | employees, registry competențe/autorizări/centre/resurse | edit prin servicii canonice (țintă); JSON legacy încă vizibil | TRANZIȚIE — eliminare stocare paralelă |
| `/employees-records` | HR privat + demo | employees (nume live); rest demo | doar rută HR (țintă) | DEMO parțial — metadata HR neautoritativă |
| `/attendance` | pontaj | `employee_attendance_events` | evenimente pontaj | CANONIC pontaj |
| `/utilaje` | registry utilaje/resurse | `machines` | admin registry | CANONIC identitate resursă |
| `/shop-floor` | proiecție status | `/machines`, `/operator/tasks` | none (țintă) | TRANZIȚIE — mock silent de eliminat |
| `/operator` | control desktop execuție | Operator tasks, ExecutionReality, readiness | start/pause/complete, assign manager | CANONIC parțial — aliniere assignment service |
| `/tablet` | mod chiosc explicit (A) peste servicii canonice | operator tasks via servicii canonice | via performAction — fără autoritate paralelă | **CONFIRMAT** — kiosk mode |
| Employee Mobile v2 | execuție individuală angajat | task truth, eligibility, ExecutionReality | claim, start-from-available, complete | CANONIC individual — necesită user linkage |

---

## Fișă confirmare Sandu (de completat de owner/manager/tehnic/Sandu)

**Nu completată automat.** Evidență registry vs legacy vs mapping @ APP-AUTH-02.

| Capabilitate | Registry | Legacy | Mapping | Autorizare | Decizie owner/tehnic |
|--------------|----------|--------|---------|------------|----------------------|
| Operator print (`SK_PRINT_OPERATOR`) | Da | — | print, print_roll | Da (print) | |
| Modelare cant | Nu | — | — | — | |
| Aplicare folie / colantare | Nu | SK_VINYL_APPLICATOR (legacy) | colantare | Nu | |
| Montaj / assembly | Nu | SK_ASSEMBLY | assembly, packaging, quality_control | Nu (majoritatea) | |
| Montaj LED | Nu | SK_ELECTRICIAN (legacy) | montaj_led | Nu | **CRITIC** |
| Instalare teren | Nu | SK_FIELD_INSTALLER | field_installation | Parțial (competence miss) | |
| Lăcătuș / sudură | Nu | SK_LOCKSMITH | welding | Nu | |
| Electrician | Nu | SK_ELECTRICIAN | montaj_led (indirect) | Nu | |
| Operare CNC | Nu | — | — | — | |
| Resurse registry | MCH-EPSON-60800 | WA-*, MCH-WELD-* (legacy) | — | drift utilaje | |
| Poate independent / asistat / nu poate | — | — | — | — | |
| Autorizare formală există | — | — | — | — | |
| Dovadă / expirare | — | — | — | — | |

**Mapping-uri Sandu fără competență registry (7):** assembly, colantare, field_installation, montaj_led, packaging, quality_control, welding.

**Mapping-uri Sandu fără autorizare dovedită (6):** assembly, colantare, montaj_led, packaging, quality_control, welding.

---

## Tabel mapping-uri explicite

Sursă: `docs/qa/product-system-active-path-isolation-v1/app_auth_02/override_inventory.json` (42 rânduri). APP-AUTH-02 raportează **39** mapping-uri explicite (3× `NARROWING_ONLY` = compatibilitate restricție, nu additive).

| Operație | Angajat | Match competență | Match autorizare | Clasificare tranziție |
|----------|---------|------------------|------------------|------------------------|
| assembly | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| assembly | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| assembly | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION |
| assembly | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cant_modelare | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cant_modelare | Florin CNC | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cnc_cutting | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cnc_cutting | Florin CNC | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| colantare | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| colantare | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| colantare | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION |
| colantare | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cutter_plotter | Calin Cimpean | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| cutter_plotter | Octavian Dumitru | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| field_installation | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| field_installation | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| field_installation | Putaru Sandu | **Nu** | Da | ADDITIVE_WITHOUT_COMPETENCE |
| field_installation | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| laminare | Calin Cimpean | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| laminare | Octavian Dumitru | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| montaj_led | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| montaj_led | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| montaj_led | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION — **CRITIC** |
| montaj_led | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| packaging | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| packaging | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| packaging | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION |
| packaging | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| prepress | Calin Cimpean | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| prepress | Chirila Cristian | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| prepress | Octavian Dumitru | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| print | Calin Cimpean | Da | Da | NARROWING_ONLY |
| print | Octavian Dumitru | Da | Da | NARROWING_ONLY |
| print | Putaru Sandu | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| print_roll | Calin Cimpean | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| print_roll | Octavian Dumitru | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| print_roll | Putaru Sandu | Da | Da | NARROWING_ONLY |
| quality_control | Andrei Goghi | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| quality_control | Costi Modelator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| quality_control | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION |
| quality_control | Vali Colantator | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE |
| welding | Putaru Sandu | **Nu** | **Nu** | ADDITIVE_WITHOUT_AUTHORIZATION |

---

## Implementări blocate

| Item | Motiv |
|------|-------|
| PROD-ARCH-01 | Owner: blocat până la instrumentare paritate + reconciliere autorități |
| MOBILE-INT-02 | Owner: blocat; distribuire inteligentă neautorizată |
| Migrare automată registry/JSON | A22:A confirmat — **migrare NU**; doar instrumentare + plan |
| Execuție colaborativă | Owner: neautorizată prin această decizie |
| Distribuire inteligentă | Owner: neautorizată explicit |
| Ștergere JSON legacy | A22:A — după plan reconciliere controlată |
| Dezactivare fallback mock/demo | A20 confirmat — implementare viitoare APP-AUTH-03+ |
| Fișă Sandu capabilități | A6:A confirmat proces; date individuale **în curs** |
| MODULE-RUNTIME-01 | **DEFERRED** — pistă Module Chain pe pauză |
| MODULE-ARCH-01 | **BLOCKED** |

---

## Rezumat decizii

| Categorie | Număr |
|-----------|------:|
| Total decizii A1–A22 | 22 |
| **CONFIRMATE** | **22** |
| **AMÂNATE** | **0** |
| Fișă Sandu (date individuale) | **în curs** — proces A6 confirmat |

---

## Următorul task

**`APP-AUTH-03-RUNTIME-PARITY-INSTRUMENTATION-PLAN`**

Autorizat: instrumentare drift, flux confirmare Sandu, plan paritate citire, plan reconciliere controlată. **Fără migrare date.**

**PROD-ARCH-01:** **BLOCAT** · **MOBILE-INT-02:** **BLOCAT** · **Migrare:** **NO**

---

## Actualizări canonice

- Creat: `docs/worklog/realignment/2026-07-15_owner_decision_03_operational_authority_confirmation_v1.md`
- Actualizat: `docs/master/workos-e2e/WORKOS_E2E_STATUS.md`
- Actualizat: `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md`

---

## Opinie sinceră

Gate-ul de autoritate operațională este **închis la nivel de politică**: owner a confirmat modelul canonic, separările, suprafețele și contractul Available. Următorul risc nu este ambiguitate arhitecturală, ci **execuția disciplinată**: instrumentare drift (APP-AUTH-03), completarea fișei Sandu fără migrare automată, și respectarea interdicției explicite asupra distribuirii inteligente și execuției colaborative. PROD-ARCH-01 rămâne în afara limitelor până când paritatea runtime demonstrează că registry-ul poate înlocui JSON-ul fără surprize.

---

## Checkpoint roadmap

### Roadmap awareness checkpoint

| Întrebare | Răspuns |
|-----------|---------|
| Cât de bine ține cont de roadmap (1–10) | **10** — confirmări aliniate cu lanțul APP-AUTH; fără salt la PROD-ARCH |
| Poziționarea pasului actual | Politici autoritate **CONFIRMATE**; urmează instrumentare + reconciliere |
| Cât sunt în direcția stabilită | **92/100%** — politică clară; date Sandu + paritate runtime rămân |
| Dead pieces check | JSON legacy 8/8; mapping-uri explicite; Shop Floor mock — toate transitional conform A20/A22 |
| Scope interzis respectat | **DA** |
| De ce următorul task nu sare la implementare | APP-AUTH-03 = instrumentare și plan, nu migrare; PROD-ARCH blocat explicit de owner |

### Datorii canonice actualizate

- **Authority debt:** **22/22 CONFIRMATE** (politică); implementare parity **DESCHISĂ** via APP-AUTH-03
- **Employee/competence/authorization debt:** fișă Sandu de completat; JSON legacy transitional până la reconciliere controlată
- **Execution surface debt:** Tablet **A confirmat**; Shop Floor mock de eliminat în tranziție
- **Module-chain debt (separat):** neschimbat — MODULE-INT-01 pe pauză

---

## Worklog persistent

| Câmp | Valoare |
|------|---------|
| Verificat | Răspuns owner explicit recepționat și mapat pe A1–A22 |
| Terminat | **22/22 CONFIRMATE**; înregistrare 34 precizări; actualizare tabele |
| Rămas | Fișă Sandu capabilități individuale; instrumentare APP-AUTH-03 |
| Blocat | PROD-ARCH-01, MOBILE-INT-02, migrare, distribuire inteligentă, colaborativ |
| Teste | Nu au fost necesare (gate decizie) |
| Fișiere atinse | worklog O3; WORKOS_E2E_STATUS; WORKOS_E2E_TASK_GRAPH |
| Următorul pas | **APP-AUTH-03-RUNTIME-PARITY-INSTRUMENTATION-PLAN** |

---

## DELIVERY FOOTER

```
Task: OWNER-DECISION-03 — OPERATIONAL_AUTHORITY_CONFIRMATION_V1
Starting HEAD: 276fb83
Decisions total: 22
Decisions confirmed: 22
Decisions deferred: 0
Employee identity: CONFIRMAT (A1:A)
HR authority: CONFIRMAT
Operational profile: CONFIRMAT
Taxonomy: CONFIRMAT
Competence authority: CONFIRMAT (A5:A)
Sandu: CONFIRMAT proces A6:A — date individuale IN CURS
Explicit eligibility mappings: CONFIRMAT
Authorization authority: CONFIRMAT
Workcenter authority: CONFIRMAT
Machine/resource authority: CONFIRMAT
Employee-resource authority: CONFIRMAT
Operation requirements: CONFIRMAT
Readiness: CONFIRMAT
Assignment: CONFIRMAT
Execution sessions: CONFIRMAT
Employee Mobile: CONFIRMAT
Operator: CONFIRMAT
Tablet: CONFIRMAT (A — mod chiosc)
Shop Floor: CONFIRMAT
Attendance: CONFIRMAT
Employees without users: CONFIRMAT
Availability: CONFIRMAT (directie, neimplementat)
Workload: CONFIRMAT (directie, neimplementat)
Available projection contract: CONFIRMAT
Migration authorized: NO (A22:A)
Sandu confirmation required: YES (capabilitati individuale)
Technical validation required: NO
PROD-ARCH-01: BLOCKED
MOBILE-INT-02: BLOCKED
MODULE-RUNTIME-01: DEFERRED
MODULE-ARCH-01: BLOCKED
Implementation authorized: NO
Next task: APP-AUTH-03-RUNTIME-PARITY-INSTRUMENTATION-PLAN
Code changed: NO
DB changed: NO
Commit: YES
Push: NO
PR: NO
Verdict: OWNER_OPERATIONAL_AUTHORITIES_CONFIRMED
```
