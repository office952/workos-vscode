# APP-AUTH-01 — Decizii canonice de autoritate: angajați, competențe, utilaje, execuție, pontaj

**Task:** APP-AUTH-01 — `CANONICAL_AUTHORITY_DECISIONS_FOR_EMPLOYEES_SKILLS_MACHINES_EXECUTION_AND_ATTENDANCE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `bfe20c6`  
**Audit bază:** APP-INT-01 @ `bfe20c6`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Cod changed:** NO

## Verdict

**`APP_AUTH_DECISIONS_REQUIRE_DATA_RECONCILIATION`**

28 decizii documentate cu recomandări arhitecturale; **0 CONFIRMED** de owner. Discrepanțe runtime (Sandu registry vs JSON legacy, override explicit fără excepție formală) impun **APP-AUTH-02** înainte de PROD-ARCH-01.

---

## Reguli gate

- Recomandările **nu** sunt decizii confirmate.
- **Implementare autorizată:** **NO**
- **PROD-ARCH-01 / MOBILE-INT-02:** **BLOCAT**

---

## Sumar decizii

| Status | Count |
|--------|-------|
| CONFIRMED | **0** |
| REJECTED | **0** |
| DEFERRED | **24** |
| DATA_REQUIRED | **3** (D6 migrare, D4 taxonomie completă, D9 dovezi autorizări) |
| RUNTIME_PROOF_REQUIRED | **1** (D19 paritate Operator vs Mobile — parțial dovedită) |
| **Total** | **28** |

---

## Contract autoritate — tabel unic (recomandat, NECONFIRMAT)

| Adevăr | Sursă canonică recomandată | Sursă tranzițională | Scriitor canonic | Consumatori | Fail-closed | Migrare |
|--------|---------------------------|---------------------|------------------|-------------|-------------|---------|
| Identitate angajat | `employees.id` | — | HR/admin entities | toate | refuz dacă inexistent/inactiv | Nu |
| Legătură utilizator | `employees.user_id` | — | admin entities | Mobile, auth | Mobile refuz fără mapare | Nu |
| Înregistrare HR | agregat HR viitor 1:1 | `EmployeeRecord` demo | HR module | employees-records | fără scriere în registry | Da |
| Profil operațional | registry + entities | form CSV legacy | registry API + entities | /employees | read registry; warn JSON | Da |
| Catalog competență | catalog registry + SK_* | — | seed/admin registry | eligibilitate | operatie neeligibila | Nu |
| Posesie competență | `employee_skill_authorizations` | `employees.skills` JSON | registry PUT | mobile, operator | fără fallback silent | **Da** |
| Cerință operație | `operation_resource_requirements` | alias ProductSystem | admin registry | readiness, eligibilitate | blocked/unverified | Nu |
| Override eligibilitate | excepție temporară auditată | `operation_employee_authorizations` | manager+RT (viitor) | eligibilitate | refuz fără excepție | **Da** |
| Autorizare formală | relație viitoare dedicată | skill checkbox | HR/RT | CNC/laser/etc. | **eliminatoriu** | Da |
| Centru de lucru | catalog registry WC_* | task machine_type text | admin registry | autorizări angajat | neeligibil | Curățare catalog |
| Utilaj/resursă | `machines.machine_code` | mock specs UI | registry/machines API | utilaje, mapping | indisponibil | Nu |
| Angajat–utilaj | `employee_resource_authorizations` | `employees.machines` JSON | registry PUT | eligibilitate | neeligibil | **Da** |
| Pregătire dependențe | `task_readiness_service` | — | readiness pipeline | mobile truth | blocked | Nu |
| Eligibilitate | serviciu viitor dedicat | hybrid registry+explicit | — (viitor) | distribuție | **fail-closed** | Da |
| Alocare | `execution_task_assignment_service` | scrieri directe plan | assignment service | mobile T06, manager | 409 conflict | Consolidare |
| Stocare alocare | `tasks_json.assigned_employee_id` | — | assignment service | individual | păstrat T06 | Extindere viitoare |
| Sesiune lucru | ExecutionReality | — | ER service | operator, mobile | conflict/409 | Nu |
| Pontaj | `employee_attendance_events` | — | attendance API | attendance, plăți | separat de ER | Nu |
| Disponibilitate | proiecție derivată (viitor) | — | calculat | distribuție | indisponibil | Da |
| Încărcare | proiecție derivată (viitor) | — | calculat | distribuție | — | Da |

**Adevăruri cu surse canonice duplicate propuse astăzi:** **0** (recomandarea elimină dualitatea; starea curentă are **10** conflicte)

---

## Deciziile 1–28 (rezumat)

### D1 — Identitate angajat · **DEFERRED**

| | |
|--|--|
| **Recomandare** | `employees.id` = identitate operațională; `user_id` = legătură autentificare; EmployeeRecord = extensie HR 1:1 |
| **Reguli propuse** | 1 user → max 1 angajat activ; 1 angajat → 1 HR; inactiv = fail-closed execuție |
| **Fail-closed** | Fără `employees.id` valid activ → fără alocare/sesiune |

### D2 — Adevăr HR · **DEFERRED**

| | |
|--|--|
| **Recomandare** | HR canonic separat; registry operațional primește doar proiecții sigure (nume, status operațional) |
| **Interzis în registry** | contract, salariu detaliat, concedii, documente, note disciplinare |
| **Fail-closed** | Demo HR (`employeeRecordsData`) **nu** devine autoritate |

### D3 — Profil operațional angajat · **DEFERRED**

| | |
|--|--|
| **Recomandare** | `/employees` = **agregator/editor** peste registry; **nu** stocare independentă competențe |
| **Tranziție** | formular CSV skills/machines → read-only sau eliminat post-migrare |

### D4 — Rol vs atribuție vs competență · **DATA_REQUIRED**

**Clasificare registry curent (propusă):**

| Intrare | Cod | Clasificare recomandată |
|---------|-----|-------------------------|
| Director comercial / tehnic | SK_COMMERCIAL_TECH | **Rol** — concept mixt invalid ca competență |
| Electrician | SK_ELECTRICIAN | **Competență** |
| Montator | SK_FIELD_INSTALLER | **Competență** |
| Lăcătuș | SK_LOCKSMITH | **Competență** |
| Colantator | SK_VINYL_APPLICATOR | **Competență** |
| Modelare cant litere | SK_LETTER_MODELING | **Competență** |
| Ansamblare | SK_ASSEMBLY | **Competență** |
| CNC router (WC) | WC_CNC_ROUTING | **Centru de lucru** — curățare nume (sună utilaj) |
| Modelare cant litere (WC) | WC_LETTER_FORMING | **Centru de lucru** — suprapunere cu operație |
| CNC 4020 | MCH-CNC-4020 | **Utilaj** |

**Reguli:** Rol ≠ competență; competență ≠ autorizare formală.

### D5 — Catalog competențe · **DEFERRED**

| | |
|--|--|
| **Canonic** | catalog registry + `employee_skill_authorizations` |
| **Scriitori** | admin registry; validare manager+RT (viitor) |
| **Nivel** | LIPSA — pregătit schema, neimplementat |

### D6 — JSON legacy skills · **DATA_REQUIRED**

| | |
|--|--|
| **Politică recomandată** | `ONE_TIME_MIGRATION_THEN_DISABLE` |
| **Precondiție** | raport discrepanțe + aprobare owner |
| **Fail-closed post-migrare** | fără scriere JSON; fallback read cu warning observabil max 1 release |

### D7 — Cerințe operație · **DEFERRED**

| | |
|--|--|
| **Canonic** | `operation_resource_requirements` pe tip/sablon operație |
| **Produs** | compune operații; **nu** duplică cerințe |
| **Angajat** | **nu** deține cerințe |

### D8 — Override eligibilitate explicit · **DEFERRED**

| | |
|--|--|
| **Politică recomandată** | listele explicit **pot restrânge**; adăugare altfel neeligibil = **Exceptie de eligibilitate** formală (motiv, aprobator, interval, audit) |
| **Interzis** | override autorizare obligatorie lipsă |
| **Caz Sandu montaj_led** | **`LEGACY_OVERRIDE_REQUIRES_RECONCILIATION`** — explicit list fără competență registry, fără înregistrare excepție |

### D9 — Autorizări formale · **DATA_REQUIRED**

| | |
|--|--|
| **Recomandare** | relație dedicată `employee_authorizations` (cod, scope, valabilitate, dovadă) |
| **Separare** | competență ≠ autorizare CNC/laser/sudură/înălțime/vehicul |
| **Fail-closed** | autorizare lipsă = eliminatoriu |

### D10 — Catalog centre de lucru · **DEFERRED**

| | |
|--|--|
| **Canonic** | catalog registry WC_* rămâne |
| **Semantica** | zonă logică / grup capacitate — **nu** utilaj, **nu** competență |
| **Curățare** | intrări cu nume de utilaj/operație → reclasificare catalog |

### D11 — Registry utilaje/resurse · **DEFERRED**

| | |
|--|--|
| **Canonic** | tabela `machines` cu `resource_kind` obligatoriu |
| **Tipuri** | Utilaj, Post de lucru, Masă de lucru, Zonă, Echipament, Vehicul, Unealtă |

### D12 — Relație angajat–utilaj · **DEFERRED**

| | |
|--|--|
| **Canonic** | `employee_resource_authorizations` |
| **Tranzițional** | `employees.machines` JSON read-only |
| **Operator principal** | metadata viitoare pe relație/sesiune |

### D13 — machine_type pe task · **DEFERRED**

| | |
|--|--|
| **Problema** | câmp liber amestecă WC, tip utilaj, hint |
| **Recomandare** | separă: tip resursă cerută / utilaj concret selectat / centru de lucru |

### D14 — Pregătire dependențe · **DEFERRED**

| | |
|--|--|
| **Canonic** | `task_readiness_service` |
| **Nu deține** | eligibilitate angajat, disponibilitate, încărcare, echipă |

### D15 — Serviciu eligibilitate (viitor) · **DEFERRED**

| | |
|--|--|
| **Consumă** | cerințe, competențe, autorizări, excepții, status angajat |
| **Nu consumă** | JSON legacy silent |
| **Fail-closed** | date canonice lipsă → Neeligibil + motiv |

### D16 — Autoritate alocare · **DEFERRED**

| | |
|--|--|
| **Canonic writer** | `execution_task_assignment_service` |
| **Metadata** | employee, actor, source, timestamp, reason, previous, mode |
| **Interzis post-transiție** | scrieri directe plan fără serviciu |

### D17 — Stocare alocare · **DEFERRED**

| | |
|--|--|
| **Individual** | `assigned_employee_id` rămâne compatibilitate MOBILE-T06 |
| **Colaborativ** | entități participare separate — **nu** extinde câmpul singur |

### D18 — Sesiune de lucru · **DEFERRED**

| | |
|--|--|
| **Canonic** | ExecutionReality |
| **Unicitate** | o sesiune productivă activă (politică viitoare) |

### D19 — Operator / Mobile / Tablet · **RUNTIME_PROOF_REQUIRED**

| Suprafață | Clasificare recomandată | Autoritate |
|-----------|------------------------|------------|
| Employee Mobile v2 | control execuție canonic mobile | task truth + assignment + ER |
| `/operator` | control execuție desktop | aceleași servicii backend (parțial dovedit) |
| `/tablet` | **transitional wrapper** → retire sau kiosk | **nu** autoritate paralelă |

### D20 — Shop Floor · **DEFERRED**

| | |
|--|--|
| **Proiecție** | da — fără scriere alocări |
| **Fail-closed prod** | **fără fallback mock silent** — eroare vizibilă |

### D21 — Pontaj · **DEFERRED**

| | |
|--|--|
| **Canonic separat** | `employee_attendance_events` |
| **Fără derivare automată** | din ExecutionReality către salariu |

### D22 — Disponibilitate · **DEFERRED**

| | |
|--|--|
| **Recomandare** | `DERIVED_CANONICAL_PROJECTION` + override manager controlat |

### D23 — Încărcare · **DEFERRED**

| | |
|--|--|
| **Recomandare** | proiecție din alocări + durate estimate + sesiuni + capacitate schimb |

### D24 — Izolare demo/mock · **DEFERRED**

| Sursă | Decizie recomandată |
|-------|---------------------|
| `employeeRecordsData` docs/alerts | dev-only / explicit demo |
| `mockData` shop-floor | **runtime blocker în prod** |
| `DEMO_OPERATORS` tablet | legacy isolated |
| mock machine specs | read-only enrich, **nu** autoritate |
| `usePersonalDemoModule` | explicit demo badge obligatoriu |

### D25 — Versionare contracte API · **DEFERRED**

Contracte versionate: profil operațional, competențe, eligibilitate, assignment, session, attendance — **fără rupere MOBILE T01–T06** fără adapter.

### D26 — Matrice scriere (extras)

| Adevăr | Scriitor canonic | Interzis |
|--------|------------------|----------|
| Identitate angajat | entities employees API | Mobile, shop-floor |
| Competență angajat | operational-registry PUT | JSON direct, frontend local |
| Alocare | assignment service | patch plan direct |
| Sesiune | ExecutionReality | tablet demo |
| Pontaj | attendance API | ER complete handler |

### D27 — Matrice citire (extras)

| Consumator | Canonic | Fallback tranzițional | Fail-closed |
|------------|---------|----------------------|-------------|
| Mobile v2 | registry auth + readiness + assignment | — | 409/403 explicit |
| /employees UI | registry panel + entities | CSV form legacy | warning dacă drift |
| /shop-floor | machines + operator tasks | mock → **blocat prod** | empty/error badge |
| Distribuție viitoare | eligibilitate service | **niciun JSON silent** | propunere manager |

### D28 — Ordine tranziție · **DEFERRED**

1. Înghețare scrieri JSON legacy noi  
2. Raport discrepanțe (APP-AUTH-02)  
3. Reconciliere owner (Sandu, etc.)  
4. Migrare one-time → tabele canonice  
5. Adapters read + verificare paritate runtime  
6. Dezactivare fallback  
7. Eligibility service design  
8. Abia apoi PROD-ARCH-01  

---

## Studiu de caz — Putaru Sandu (id=4)

| Lanț | Stare runtime (:8001) |
|------|------------------------|
| `employees` row | activ, `user_id=dev-admin-user-00000000` |
| Registry competențe | **SK_PRINT_OPERATOR** only |
| Legacy JSON skills | SK_LOCKSMITH, SK_ASSEMBLY, SK_ELECTRICIAN, SK_VINYL_APPLICATOR, SK_FIELD_INSTALLER |
| Registry utilaje | MCH-EPSON-60800 |
| Legacy JSON machines | sudură, WA-ASSEMBLY-*, etc. |
| montaj_led eligibil | **DA** — `explicit_override: true`, `skill_match: false` |
| Mobile | user mapat; task truth order 92400 assigned+in_progress |
| UI `/employees` | panou registry arată competențe **diferite** de CSV legacy form |

**De ce eligibil azi?** Lista `operation_employee_authorizations` + mod hybrid (explicit OR skill).  
**Sursă efectivă:** explicit list — **nu** competență registry.  
**Canonic?** **NU** — lipsește Exceptie de eligibilitate auditată.  
**Clasificare:** `LEGACY_OVERRIDE_REQUIRES_RECONCILIATION`.  
**Post-unificare:** fără excepție formală → Neeligibil montaj_led până la reconciliere competențe/autorizări.  
**Preserve temporar?** **DA** pentru runtime individual existent, cu raport drift obligatoriu.

---

## Studiu de caz — CNC 4020 (MCH-CNC-4020)

| Element | Aliniere |
|---------|----------|
| `machines.machine_code` | **MCH-CNC-4020** — canonic |
| Catalog registry resources | același cod |
| `/utilaje` UI | citește `/api/v1/machines` |
| Centru de lucru | WC_CNC_ROUTING |
| Florin CNC autorizat | `employee_resource_authorizations` + legacy JSON **match** |
| Operație cnc_cutting | cere SK_CNC_OPERATOR, MCH-CNC-4020 |
| Eligibili | Florin (3), Andrei Goghi (7) — skill + explicit |

**Duplicări rămase:** mock specs UI; `machine_type` text pe taskuri neuniform.

---

## Decizii pe rută (recomandat)

| Rută | Scop | Scrieri permise | Demo |
|------|------|-----------------|------|
| `/employees` | agregator operațional | entities + registry auth | nu |
| `/employees-records` | vizualizare HR | none (viitor HR module) | explicit |
| `/attendance` | pontaj | attendance API | nu |
| `/utilaje` | registry utilaje | machines/registry | specs mock |
| `/shop-floor` | proiecție | none | fail-closed prod |
| `/operator` | execuție desktop | ER + assignment | nu |
| `/tablet` | kiosk transitional | via operator services | izolat |
| Employee Mobile v2 | execuție individuală | claim/start/complete | nu |

---

## Impact

| Program | Efect |
|---------|-------|
| MOBILE T04–T06 | Valide individual; necesită registry truth stabil |
| PROD-ARCH-01 | **BLOCAT** până APP-AUTH-02 + confirmări owner |
| OWNER-DECISION-01 | Rămâne AMANAT — independent de autoritate |

---

## Următorul task

**`APP-AUTH-02-DATA-DISCREPANCY-AND-RECONCILIATION-PLAN`**

---

## Opinie sinceră

Aplicația are deja **o direcție canonică clară** (registry + assignment service + ER + readiness), dar **nu o aplică strict**. Sandu este simptomul: UI, JSON legacy și explicit lists spun povești diferite. APP-AUTH-02 trebuie să producă raportul de discrepanțe **înainte** de orice migrare sau arhitectură distribuție.

---

## Delivery footer

```
Task: APP-AUTH-01
Starting HEAD: bfe20c6
Employee identity: DEFERRED
HR authority: DEFERRED
Operational employee profile: DEFERRED
Competence authority: DEFERRED
Legacy skills JSON: DATA_REQUIRED
Operation requirements: DEFERRED
Explicit eligibility overrides: DEFERRED
Authorization authority: DATA_REQUIRED
Workcenter authority: DEFERRED
Machine authority: DEFERRED
Employee-machine authority: DEFERRED
Readiness authority: DEFERRED
Eligibility authority: DEFERRED
Assignment authority: DEFERRED
Session authority: DEFERRED
Attendance authority: DEFERRED
Availability authority: DEFERRED
Workload authority: DEFERRED
Shop Floor: DEFERRED
Operator: RUNTIME_PROOF_REQUIRED
Tablet: DEFERRED
Employee Mobile: DEFERRED
Duplicate canonical truths (current state): 10
Data reconciliation required: YES
Implementation authorized: NO
Next task: APP-AUTH-02-DATA-DISCREPANCY-AND-RECONCILIATION-PLAN
Verdict: APP_AUTH_DECISIONS_REQUIRE_DATA_RECONCILIATION
```
