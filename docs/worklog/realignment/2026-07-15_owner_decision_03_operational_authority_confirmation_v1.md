# OWNER-DECISION-03 — Confirmarea autorităților operaționale reale

**Task:** OWNER-DECISION-03 — `OPERATIONAL_AUTHORITY_CONFIRMATION_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `276fb83` (după MODULE-INT-01 @ `276fb83`; lanț APP-AUTH acceptat neschimbat)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Worktree:** `C:\w\psiso`  
**Cod changed:** NO · **DB changed:** NO · **Implementare autorizată:** NO

## Verdict

**`OWNER_OPERATIONAL_AUTHORITIES_PARTIAL_REMAIN_BLOCKED`**

22 decizii de autoritate operațională documentate ca hartă unică; **0 CONFIRMATE**. Sandu necesită reconciliere umană; Tablet necesită alegere owner explicită. PROD-ARCH-01 și MOBILE-INT-02 rămân **BLOCATE**.

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

**Regulă:** fără răspuns owner explicit → **AMANAT**. Niciun rând marcat **CONFIRMAT** în această sesiune.

### A1 — Identitate angajat operațional

| Câmp | Valoare |
|------|---------|
| Autoritate recomandată | `employees.id` = identitate canonică; `employees.user_id` = legătură autentificare; `EmployeeRecord` = extensie HR 1:1 |
| Opțiuni owner | **A** (recomandat): model de mai sus · **B**: EmployeeRecord primar · **C**: entitate Person nouă |
| Recomandare | **A** |
| **Status** | **AMANAT** |

### A2 — Autoritate HR

| Câmp | Valoare |
|------|---------|
| Direcție | HR separat de operațional; HR deține identitate legală, contract, salariu, pontaj payroll, documente private |
| Reguli | date demo HR ≠ autoritate; pagini operaționale nu scriu salariu fără rută HR; pontaj ≠ sesiuni producție |
| Recomandare | Confirmare |
| **Status** | **AMANAT** |

### A3 — Profil angajat operațional

| Câmp | Valoare |
|------|---------|
| Direcție | `/employees` = agregator/editor peste registre canonice, nu stocare paralelă |
| Agregă | identitate, user, rol, atributii, competențe, autorizări, centre, resurse, stare |
| **Status** | **AMANAT** |

### A4 — Rol, atributie, competență, autorizare

| Câmp | Valoare |
|------|---------|
| Taxonomie strictă | Rol ≠ competență ≠ autorizare ≠ centru ≠ utilaj ≠ operație |
| Reguli | rol nu dovedește competență; competență nu dovedește autorizare; catalog mixt = reconciliere înainte de migrare |
| **Status** | **AMANAT** |

### A5 — Autoritate competențe

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): catalog + relație angajat–competență canonică după reconciliere · **B**: dual-write permanent · **C**: JSON legacy autoritate |
| Reguli | JSON transitional; fără migrare automată; eligibilitate viitoare fail-closed |
| Recomandare | **A** |
| **Status** | **AMANAT** |

### A6 — Reconciliere Sandu

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): reconciliere umană · **B**: registry câștigă imediat · **C**: legacy câștigă imediat |
| Comportament temporar (A) | păstrează runtime; arată drift managerului; fără alocare automată; fără migrare JSON |
| **Status** | **NECESITA CONFIRMARE UMANA** |

### A7 — Mapping-uri eligibilitate explicite

| Câmp | Valoare |
|------|---------|
| Politică | lista explicită poate restrânge/selecta; nu adaugă silențios fără competență/autorizare |
| Excepție viitoare | `Exceptie temporara de eligibilitate` cu câmpuri audit obligatorii |
| 39 mapping-uri | inventariate; reconciliere manuală; fără bulk-migrate ca dovadă competență |
| **Status** | **AMANAT** |

### A8 — Autoritate autorizări

| Câmp | Valoare |
|------|---------|
| Direcție | autoritate dedicată separată de competențe; câmpuri: cod, angajat, scope, utilaj, valabilitate, dovadă, audit |
| Fail-closed | autorizare obligatorie lipsă/expirată → Neeligibil; manager nu ocolește legal/safety prin excepție simplă |
| **Status** | **AMANAT** |

### A9 — Autoritate centre de lucru

| Câmp | Valoare |
|------|---------|
| Direcție | catalog workcenter canonic; nu utilaj/competență/operație; intrări mixte = clasificare înainte de migrare |
| **Status** | **AMANAT** |

### A10 — Autoritate utilaj și resursă

| Câmp | Valoare |
|------|---------|
| Direcție | `machines` = identitate concretă; `resource_kind` viitor obligatoriu |
| CNC 4020 | `MCH-CNC-4020` canonic; gap = metadata/taxonomie (`WC_CNC` vs `WC_CNC_ROUTING`) |
| **Status** | **AMANAT** |

### A11 — Autorizare angajat–resursă

| Câmp | Valoare |
|------|---------|
| Direcție | `employee_resource_authorizations` (sau relație registry curentă); JSON resurse = transitional |
| **Status** | **AMANAT** |

### A12 — Cerințe operație

| Câmp | Valoare |
|------|---------|
| Direcție | șablon/tip operație deține competență, nivel, autorizare, rol, centru, resursă, mod lucru |
| **Status** | **AMANAT** |

### A13 — Autoritate readiness

| Câmp | Valoare |
|------|---------|
| Direcție | `task_readiness_service` canonic pentru readiness producție; separat de eligibilitate/disponibilitate/încărcare |
| **Status** | **AMANAT** |

### A14 — Autoritate alocare

| Câmp | Valoare |
|------|---------|
| Direcție | un serviciu canonic alocare; toate suprafețele trec prin el; audit complet; `assigned_employee_id` compatibil doar execuție individuală |
| **Status** | **AMANAT** |

### A15 — Autoritate sesiune execuție

| Câmp | Valoare |
|------|---------|
| Direcție | ExecutionReality canonic Start/Complete; participare colaborativă viitoare ≠ un singur `assigned_employee_id` |
| **Status** | **AMANAT** |

### A16 — Suprafețe execuție

| Suprafață | Direcție recomandată | Status parțial |
|-----------|---------------------|----------------|
| Employee Mobile v2 | control execuție individual canonic | **AMANAT** |
| `/operator` | desktop canonic dacă aceleași servicii | **AMANAT** |
| `/tablet` | owner alege **A/B/C/D** — recomandare A sau B; **nu completat automat** | **NECESITA CONFIRMARE UMANA** |
| `/shop-floor` | proiecție; fără mock silent; erori vizibile | **AMANAT** |

### A17 — Autoritate pontaj

| Câmp | Valoare |
|------|---------|
| Direcție | pontaj canonic separat; ExecutionReality = sesiuni producție; reconciliere viitoare fără suprascriere automată |
| **Status** | **AMANAT** |

### A18 — Angajați fără cont utilizator

| Câmp | Valoare |
|------|---------|
| Direcție | 7 angajați valizi operațional; alocare manager da; Mobile personal nu; fără creare automată user |
| **Status** | **AMANAT** |

### A19 — Disponibilitate și încărcare

| Câmp | Valoare |
|------|---------|
| Direcție | niciun model canonic acum; direcții viitoare documentate; implementare neautorizată prin confirmare |
| **Status** | **AMANAT** |

### A20 — Tranziție legacy și demo

| Câmp | Valoare |
|------|---------|
| Direcție | fără mock silent prod; demo ≠ eligibilitate; JSON observabil; freeze writes viitor; parity înainte de switch |
| **Status** | **AMANAT** |

### A21 — Contract proiecție Available

| Câmp | Valoare |
|------|---------|
| Contract | ORDER_LOCAL_FAIL_CLOSED — dovedit APP-AUTH-02B/C |
| Acceptare owner comportament operațional | **AMANAT** (dovadă tehnică există; confirmare owner lipsește) |

### A22 — Autorizare migrare

| Câmp | Valoare |
|------|---------|
| Opțiuni | **A** (recomandat): fără migrare; doar instrumentare + workflow confirmare · **B**: migrare registry imediată · **C**: fallback legacy permanent |
| Recomandare | **A** |
| **Status** | **AMANAT** |

---

## Pachet răspuns owner (de completat)

```text
CONFIRM A1–A22, with the following choices:
A1: A
A5: A
A6: A
A16 Tablet: <A/B/C>
A22: A
Exceptions or amendments:
<text>
```

**Nu completați Tablet automat.** Trimiteți răspunsul explicit pentru a marca **CONFIRMAT** pe deciziile dorite.

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
| `/tablet` | kiosk / wrapper / legacy | operator tasks + demo routing | via performAction | **BLOCAT decizie** — A/B/C/D neales |
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
| PROD-ARCH-01 | Autorități operaționale neconfirmate |
| MOBILE-INT-02 | Distribuire/colaborativ neautorizat |
| Migrare automată registry/JSON | A22 neconfirmat; Sandu nereconciliat |
| Execuție colaborativă | OWNER-DECISION-01 + A14/A15 neconfirmate |
| Distribuire inteligentă | OWNER-DECISION-01 AMÂNAT |
| Ștergere JSON legacy | A20/A22 neconfirmate |
| Dezactivare fallback mock/demo | A20/A16 neconfirmate; dovadă runtime parțială |
| Eligibilitate canonică fail-closed | A5/A6/A7/A8 neconfirmate |
| Unificare assignment service | A14 neconfirmat |
| Model disponibilitate/încărcare | A19 neconfirmat |
| MODULE-RUNTIME-01 | **DEFERRED** — pistă Module Chain pe pauză; nu task activ |
| MODULE-ARCH-01 | **BLOCKED** — handoff-uri statice, health misleading, 0/22 confirmate |

---

## Rezumat decizii

| Categorie | Număr |
|-----------|------:|
| Total decizii A1–A22 | 22 |
| **CONFIRMATE** | **0** |
| **AMÂNATE** | 20 |
| **NECESITA CONFIRMARE UMANA** | 2 (A6 Sandu, A16 Tablet) |

---

## Următorul task

**`OWNER_DECISION_REQUIRED`** — owner trebuie să confirme explicit pachetul A1–A22 (minim A1, A5, A6, A16 Tablet, A22 + restul direcțiilor).

După confirmarea direcțiilor obligatorii dar înainte de reconciliere Sandu completă: **`APP-AUTH-03-RUNTIME-PARITY-INSTRUMENTATION-PLAN`**.

**PROD-ARCH-01:** **BLOCAT** · **MOBILE-INT-02:** **BLOCAT**

---

## Actualizări canonice

- Creat: `docs/worklog/realignment/2026-07-15_owner_decision_03_operational_authority_confirmation_v1.md`
- Actualizat: `docs/master/workos-e2e/WORKOS_E2E_STATUS.md`
- Actualizat: `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md`

---

## Opinie sinceră

WorkOS are acum o hartă de autoritate suficient de clară pentru a opri auditul general și a forța decizii. Riscul principal nu este lipsa documentației, ci **confirmarea owner** pentru Sandu și Tablet, plus acceptarea explicită că 7 angajați operaționali rămân fără Mobile personal până la creare controlată de conturi. Contractul Available dovedit tehnic (APP-AUTH-02B/C) reduce presiunea runtime, dar nu înlocuiește reconcilierea competențelor. Recomandarea agentului: confirmați **A1/A5/A6/A22** și alegeți **Tablet A sau B** într-o singură sesiune owner scurtă, apoi treceți la instrumentare parity (APP-AUTH-03), nu la PROD-ARCH-01.

---

## Checkpoint roadmap

### Roadmap awareness checkpoint

| Întrebare | Răspuns |
|-----------|---------|
| Cât de bine ține cont de roadmap (1–10) | **9** — gate-ul respectă lanțul APP-AUTH, nu sare la PROD-ARCH, separă MODULE-INT-01 |
| Poziționarea pasului actual | După APP-AUTH-02C (runtime closure) și MODULE-INT-01 (audit paralel); **înainte** de APP-AUTH-03 și orice implementare |
| Cât sunt în direcția stabilită | **85/100%** — hartă autoritate completă; lipsesc doar confirmările owner (Sandu, Tablet) |
| Dead pieces check | `mockData` shop-floor/tablet demo; JSON `skills`/`machines` pe toți cei 8 angajați; 39 mapping-uri fără excepție formală |
| Scope interzis respectat | **DA** — zero cod/DB/UI/migrări/alocări/Sandu |
| De ce următorul task nu sare la implementare | Fără CONFIRMAT pe A1/A5/A6/A22 și fără fișă Sandu completată, orice migrare sau PROD-ARCH ar îngheța drift greșit ca adevăr canonic |

### Datorii canonice actualizate

- **Authority debt:** 0/22 CONFIRMATE; 4 autorități duplicate majore; Sandu + Tablet blochează paritatea
- **Employee/competence/authorization debt:** JSON legacy pe 8/8 angajați; 7 mapping-uri Sandu fără competență; 6 fără autorizare; `montaj_led` CRITIC
- **Execution surface debt:** Tablet neales (A/B/C/D); Shop Floor mock silent; Operator/Mobile parțial aliniate
- **Module-chain debt (separat):** MODULE-INT-01 — nu amestecat în O3

- Wave execuție angajați: **blocată** pe autoritate + Sandu.
- APP-AUTH-02 **închis** (proiecție Available).
- Următorul unlock: confirmări owner → APP-AUTH-03 → reconciliere controlată → abia apoi PROD-ARCH-01.

---

## Worklog persistent

| Câmp | Valoare |
|------|---------|
| Verificat | Lanț APP-INT-01 → APP-AUTH-02C; probe runtime @ :8001; mapping-uri APP-AUTH-02; separare MODULE-INT-01 |
| Terminat | Gate A1–A22 documentat; tabele autoritate/rute/Sandu/mapping; pachet răspuns owner |
| Rămas | 0 CONFIRMATE; fișă Sandu goală; alegere Tablet |
| Blocat | PROD-ARCH-01, MOBILE-INT-02, migrare, MODULE-ARCH-01 |
| Decizii owner lipsă | Toate A1–A22; minim A1, A5, A6, A16 Tablet, A22 |
| Teste | Nu au fost necesare (gate documentar; probe existente APP-AUTH-02C) |
| Fișiere atinse | worklog O3; WORKOS_E2E_STATUS; WORKOS_E2E_TASK_GRAPH |
| Următorul pas | **OWNER_DECISION_REQUIRED** |

---

## DELIVERY FOOTER

```
Task: OWNER-DECISION-03 — OPERATIONAL_AUTHORITY_CONFIRMATION_V1
Starting HEAD: 276fb83
Decisions total: 22
Decisions confirmed: 0
Decisions deferred: 22
Employee identity: AMANAT
HR authority: AMANAT
Operational profile: AMANAT
Taxonomy: AMANAT
Competence authority: AMANAT
Sandu: NECESITA CONFIRMARE UMANA
Explicit eligibility mappings: AMANAT
Authorization authority: AMANAT
Workcenter authority: AMANAT
Machine/resource authority: AMANAT
Employee-resource authority: AMANAT
Operation requirements: AMANAT
Readiness: AMANAT
Assignment: AMANAT
Execution sessions: AMANAT
Employee Mobile: AMANAT
Operator: AMANAT
Tablet: NECESITA CONFIRMARE UMANA
Shop Floor: AMANAT
Attendance: AMANAT
Employees without users: AMANAT
Availability: AMANAT
Workload: AMANAT
Available projection contract: AMANAT
Migration authorized: NO
Sandu confirmation required: YES
Technical validation required: NO
PROD-ARCH-01: BLOCKED
MOBILE-INT-02: BLOCKED
MODULE-RUNTIME-01: DEFERRED
MODULE-ARCH-01: BLOCKED
Implementation authorized: NO
Next task: OWNER_DECISION_REQUIRED
Code changed: NO
DB changed: NO
Commit: YES
Commit hash: <post-commit>
Push: NO
PR: NO
Verdict: OWNER_OPERATIONAL_AUTHORITIES_PARTIAL_REMAIN_BLOCKED
```
