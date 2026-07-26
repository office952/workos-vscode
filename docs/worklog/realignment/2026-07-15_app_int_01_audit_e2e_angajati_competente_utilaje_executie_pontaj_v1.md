# APP-INT-01 — Audit E2E aplicație: angajați, competențe, utilaje, execuție, pontaj

**Task:** APP-INT-01 — `AUDIT_E2E_APLICATIE_ANGAJATI_COMPETENTE_UTILAJE_EXECUTIE_SI_PONTAJ_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `72d9b57`  
**Backend:** `http://127.0.0.1:8001`  
**Frontend:** `http://127.0.0.1:3000`  
**Cod changed:** NO

## Verdict

**`APP_E2E_AUDIT_PASS_READY_FOR_AUTHORITY_DECISIONS`**

Audit complet pe 8 suprafețe + runtime read-only. Autorități duplicate confirmate — **PROD-ARCH-01 rămâne blocat**; următorul pas permis: **APP-AUTH-01**.

---

## Repository safety

- Fără modificări cod aplicație, DB, UI, endpointuri.
- Evidență: probe JSON + 8 screenshot-uri în `docs/qa/product-system-active-path-isolation-v1/`.
- Script captură screenshot: `frontend/scripts/app_int_01_capture_screenshots.cjs` (doar QA, necomitat ca prod).

---

## Runtime ownership

| Resursă | Valoare runtime (:8001) |
|---------|-------------------------|
| Angajați (`employees`) | **8** |
| Operații plan (`/operator/tasks`) | **18** |
| Utilaje/resurse (`machines` + registry) | **14** |
| Evenimente pontaj luna curentă | **0** |
| Sesiuni active probe (T06 in_progress) | order **92400** / Sandu |

Probe: `app_int_01_runtime_probe.json`, `app_int_01_eligibility_probe.json`

---

## Clasificarea rutelor

| Rută | Clasificare | Sursă adevăr efectivă |
|------|-------------|------------------------|
| `/employees` | **ADMIN_REGISTRY** + agregator | `employees` + `operational-registry` autorizări |
| `/employees-records` | **HR_CANONIC** parțial + **DEMO** | Nume live; documente/avansuri/alerte demo |
| `/attendance` | **HR_CANONIC** (pontaj excepții) | `employee_attendance_events` |
| `/utilaje` | **ADMIN_REGISTRY** | `machines` (= registry resurse) |
| `/shop-floor` | **PROIECTIE_CANONICA** | `/machines` + `/operator/tasks`; fallback mock |
| `/operator` | **CONTROL_OPERATIONAL** | ExecutionPlanV2 + ExecutionReality |
| `/tablet` | **PARALEL** / **LEGACY_ACTIV** | Bridge live + `workstationRouting` demo |
| Employee Mobile v2 | **CONTROL_OPERATIONAL** (individual) | `employee_mobile_task_truth/v1` |

---

## Răspunsuri obligatorii (rezumat)

| Întrebare | Răspuns audit |
|-----------|---------------|
| `/employees` registry sau agregator? | **Agregator**: entitate CostEngine + panou registry autorizări |
| `/employees-records` HR canonic? | **Parțial** — lista din angajați live; metadata HR **DEMO** |
| Competențele sunt folosite runtime? | **Da**, dar **dual**: tabele registry + coloane JSON legacy; mod **explicit** ocolește competența |
| Centre de lucru — registry sau etichete? | **Registry catalog** (`operational-registry/catalog`) + autorizări angajat |
| Utilaje autorizate legate prin ID la `/utilaje`? | **Da** — același `machine_code` / `resource_code` (ex. `MCH-CNC-4020`) |
| Niveluri competență? | **LIPSA** — doar cod skill binar |
| Autorizări formale separate de skill? | **Parțial** — `operation_employee_authorizations` + mod hybrid |
| `/shop-floor` proiectie sau autoritate? | **Proiecție** — nu scrie alocări |
| `/operator` ExecutionReality canonic? | **Da** — acțiuni via `/api/v1/operator/tasks` |
| `/tablet` activ/legacy/duplicat? | **Activ cu fallback demo** — nu canonic singur |
| Mobile vs Operator aceleași operații? | **Aceeași plan/sesiune**, **autorități diferite** la start/claim |
| Pontaj derivat din sesiuni? | **NU** — model separat (prezent implicit + excepții) |
| Două modele angajat? | **DA** — `EmployeeDTO` vs `EmployeeRecord` (HR view) |
| Două registre utilaje? | **NU** ca tabele; **DA** ca prezentare (mock specs + registry) |
| Două modele assignment? | **DA** — plan JSON + operator name legacy + mobile claim |
| Două modele sesiune? | **Parțial** — ExecutionReality canonical; tablet demo separat |
| Date demo? | HR records docs, shop-floor mock, tablet demo operators |
| Ce lipsește pentru distribuire inteligentă? | Nivel competență, disponibilitate, încărcare, scor, colaborativ |

---

## `/employees` — Angajați operaționali

### Nivel 1 UI
- Listă angajați LIVE DB; panou detaliu: date firmă, CostEngine, **Autorizări operaționale (registry)**.
- Blocuri: Competențe, Centre de lucru autorizate, Resurse/utilaje autorizate — checkbox-uri din catalog registry.
- Salariu: `cost_lunar_firma` / `salary_amount` din backend entities.
- Screenshot: `app_int_01_screenshots/01_employees.png`

### Nivel 2 Frontend
- `Employees.tsx` → `employeesApi` (`/api/v1/entities/employees`) + `EmployeeOperationalPanel`.
- Panou registry: `operationalRegistryApi.getCatalog/getEmployee/updateEmployeeAuthorizations`.
- Câmpuri formular legacy: `skills`, `machines` ca string CSV — **DUPLICAT** față de registry.

### Nivel 3 Backend
- CRUD: `routers/employees.py`
- Autorizări: `routers/operational_registry.py` → `OperationalRegistryService.set_employee_authorizations`
- Eligibilitate runtime: `check_employee_operation_eligibility` (serviciu, fără endpoint public per angajat)

### Nivel 4 Persistență
- `employees` — identitate + cost
- `employee_skill_authorizations`, `employee_workcenter_authorizations`, `employee_resource_authorizations` — **canonic intenționat**
- `employees.skills`, `employees.machines` — **LEGACY JSON oglindă** (comentariu model: „canonical = authorizations”)

### Nivel 5 Runtime
- 8 angajați live; Sandu (`id=4`) legat `user_id=dev-admin-user-00000000`.
- **Conflict Sandu**: registry autorizări ≠ coloane legacy JSON (vezi secțiune duplicate).

---

## `/employees-records` — Evidență internă HR

### Clasificare câmpuri

| Câmp | Clasificare |
|------|-------------|
| Nume, funcție, departament | **DERIVAT** din `employees` live |
| sumaLunaraInterna | **DERIVAT** (fallback demo dacă lipsă) |
| Documente, alerte, avansuri | **DEMO** (`buildDemoDocumentsForEmployees`) |
| Pontaj lunar în profil | **DERIVAT** din `getMonthlyAttendance` demo |

- `employeeRecordsData.ts` — declară explicit **date demonstrative**.
- `usePersonalDemoModule` — hibrid: angajați live + HR synthetic.
- **NU** este sursă canonică HR completă; **NU** dublează registry operațional (competențe).

---

## `/attendance` — Pontaj

- UI live: `useEmployeeAttendance` → `/api/v1/employee-attendance/events`.
- Model: **prezent implicit** + evenimente excepție (absent, concediu, medical, parțial, overtime).
- **Separat** de ExecutionReality — timpul sesiunii ≠ pontaj salarial automat.
- Runtime: 0 evenimente luna curentă (DB gol, nu demo).
- Screenshot: `03_attendance.png`

---

## `/utilaje`

- `useMachinesData` → `/api/v1/machines` (aceeași tabelă `machines` ca registry).
- `RegistryResourceEditor` pe selecție — scrie via operational-registry.
- Specs/mentenanță/utilizare: **mock enrich** când DB nu are câmpuri.
- **CNC 4020**: `MCH-CNC-4020` — același cod în registry, `/utilaje`, autorizări angajat Florin CNC.
- `WC_CNC_ROUTING` = centru de lucru; `MCH-CNC-4020` = utilaj — **suprapunere conceptuală**, nu duplicate ID.

---

## `/shop-floor`

- `useShopFloorData`: polling `/machines` + `/operator/tasks`.
- Fallback `mockData` dacă mock guard sau eroare.
- **Proiecție** — afișează status derivat; matching utilaj-task prin `machine_type` text (fragil).
- Nu evaluează readiness/eligibilitate propriu.

---

## `/operator`

- `useOperatorData` → `/api/v1/operator/tasks`; acțiuni start/pause/complete → ExecutionReality.
- Eligibilitate angajat la start: `OperatorEmployeeGuard` + registry.
- Assignment: `assigned_employee_id` pe plan + `employee_id` pe sesiune.
- Manager assign panel separat.
- **Același backend** ca Mobile pentru plan, **fluxuri diferite** (Operator start vs Mobile claim/start).

---

## `/tablet`

- `useTabletStationData`: operator tasks live filtrate pe stație + `workstationRouting` demo.
- `DEMO_OPERATORS`, `generateDemoTasks` când live gol.
- Poate apela aceleași acțiuni operator ca `/operator`.
- Clasificare: **PARALEL** — UX atelier, nu sursă unică.

---

## Employee Mobile v2

- Rută: `/employee-app-v2/*`
- Contract: `employee_mobile_task_truth/v1` — readiness, blockers, assignment, claim (T06).
- Eligibilitate: `check_employee_operation_eligibility` la claim/available start.
- **Canonic pentru execuție individuală**; nu colaborativ/loturi.
- Screenshot: `08_employee_mobile_v2.png` (390×844)

---

## Matrice competențe (extras runtime)

| Competență (RO) | Cod | Registry | Folosit eligibilitate | Observație |
|-----------------|-----|----------|----------------------|------------|
| Modelare cant litere | SK_LETTER_MODELING | catalog | Da (cant_modelare) | OK |
| Ansamblare | SK_ASSEMBLY | catalog | Da | OK |
| Electrician | SK_ELECTRICIAN | catalog | Da | OK |
| Montator | SK_FIELD_INSTALLER | catalog | Da | OK |
| Lăcătuș | SK_LOCKSMITH | catalog | Da | OK |
| Colantator | SK_VINYL_APPLICATOR | catalog | Da | OK |
| Director comercial / tehnic | SK_COMMERCIAL_TECH | catalog | **Suspect** | **Rol management etichetat competență** |

**Nivel competență:** LIPSA peste tot.

---

## Matrice centre de lucru vs utilaje

| Centru (WC_*) | Tip audit | Exemplu utilaj același concept |
|---------------|-----------|--------------------------------|
| WC_CNC_ROUTING | Categorie zonă | MCH-CNC-4020 (utilaj) |
| WC_LETTER_FORMING | Categorie + nume operație | MCH-CNC-CANT-LITERE |
| WC_ASSEMBLY | Zonă | WA-ASSEMBLY-01 (post lucru) |

Centre = **registry catalog**; nu sunt utilaje, dar apar ca `machine_type` pe taskuri (`WC_ELECTRICAL`).

---

## Audit E2E — 3 angajați

| Angajat | Rol | Competențe registry | Eligibil CNC | Eligibil modelare | Eligibil montaj LED | Motiv neeligibil |
|---------|-----|---------------------|--------------|-------------------|---------------------|------------------|
| Florin CNC (3) | Operator CNC | SK_CNC_* | **DA** (skill+explicit) | **DA** | **NU** | Lipsă SK_ELECTRICIAN |
| Putaru Sandu (4) | Lăcătuș/Montator | **SK_PRINT only** (registry) | **NU** | **NU** | **DA** (explicit_override!) | Registry decoupled; explicit list |
| Vali Colantator (5) | Colantator | SK_ASSEMBLY, SK_ELECTRICIAN… | **NU** | **NU** | **DA** (skill match) | — |

**Sandu:** legacy JSON încă arată lăcătuș/montaj; registry suprascris (probabil fixture mobile). Eligibil montaj_led cu `skill_match: false`, `explicit_override: true`.

---

## Audit E2E — 3 operații

| Operație | Cerințe registry | Eligibili runtime | Assignment observat |
|----------|------------------|-------------------|---------------------|
| cnc_cutting | SK_CNC_OPERATOR, MCH-CNC-4020 | Florin, Andrei Goghi | — |
| cant_modelare | SK_LETTER_*, MCH-CNC-CANT-LITERE | Florin, Costi | — |
| montaj_led | SK_ELECTRICIAN, WA-ASSEMBLY-* | 4 angajați incl. Sandu explicit | order 23150 assigned Sandu |

Lanț: Product System → plan V2 → readiness (`task_readiness_service`) → assignment JSON → Operator/Mobile → ExecutionReality.

**Rupturi:** explicit override fără competență; legacy JSON nealiniat; shop-floor nu arată eligibilitate.

---

## Autorități duplicate

| # | Adevăr | Sursa 1 | Sursa 2 | Autoritate actuală | Conflict |
|---|--------|---------|---------|-------------------|----------|
| 1 | Competențe angajat | `employee_skill_authorizations` | `employees.skills` JSON | Registry (mobile/operator) vs UI form CSV | **Sandu mismatch** |
| 2 | Utilaje angajat | `employee_resource_authorizations` | `employees.machines` JSON | Registry | Sandu mismatch |
| 3 | Eligibilitate | Skill rules | `operation_employee_authorizations` explicit | Hybrid — explicit câștigă | Montaj fără competență |
| 4 | Assignment | `tasks_json.assigned_employee_id` | `operator_name` / `employee_id` sesiune | Plan + ExecutionReality | Câmpuri paralele |
| 5 | Utilaj registry | `machines` table | `mockData` machine specs | DB + mock UI | Specs demo |
| 6 | Task listă | `/operator/tasks` | Shop floor mapping | Același API | Prezentare diferită |
| 7 | HR angajat | `employees` entities | `EmployeeRecord` demo | Entities live | HR docs demo |
| 8 | Pontaj | Attendance events | ExecutionReality duration | Separate | By design, risc confuzie |
| 9 | Tablet operatori | Registry employees | `DEMO_OPERATORS` | Mixed | Fallback demo |
| 10 | Rol vs competență | `employees.role` text | `SK_COMMERCIAL_TECH` | Neclar | Taxonomie amestecată |

**Duplicate authorities count: 10**

---

## Terminologie (extras)

| Concept | Denumiri găsite | Recomandat RO | Zone |
|---------|-----------------|---------------|------|
| Operatie | task, task_id, process_type | Operatie de productie | plan, mobile, operator |
| Competenta | skill, skills, SK_* | Competenta | registry, employees |
| Utilaj | machine, resource, MCH-* | Utilaj | utilaje, registry |
| Resursa | work_area, WA-* | Resursa / post de lucru | registry |
| Centru de lucru | workcenter, WC_* | Centru de lucru | catalog |
| Alocare | assignment, assigned_employee_id | Alocare | plan JSON |
| Pontaj | attendance | Pontaj | attendance API |
| Sesiune | session, ExecutionReality | Sesiune de lucru | mobile, operator |

---

## Matrice autoritate (recomandări audit — nu decizie)

| Adevăr | Canonic recomandat | Surse actuale | Consumatori | Acțiune ulterioară |
|--------|-------------------|---------------|-------------|-------------------|
| Identitate angajat | `employees.id` | employees | toate | Păstrează |
| Competență | Tabele registry | + JSON legacy | mobile, operator | **Unifică / elimină JSON** |
| Utilaj | `machines.machine_code` | machines | utilaje, registry, auth | Păstrează |
| Autorizare operație | Registry mapping + reguli | + explicit lists | eligibilitate | **APP-AUTH-01** |
| Alocare | `execution_plan.tasks_json` | plan | mobile T06, operator | Păstrează; extinde colaborativ |
| Sesiune | ExecutionReality | ER service | mobile, operator | Păstrează |
| Pontaj | employee_attendance_events | separat | attendance, plăți | Izolează de ER |
| Readiness | task_readiness_service | backend | mobile truth | Păstrează |
| Disponibilitate | — | LIPSA | — | Viitor PROD-ARCH |

---

## Impact programe

| Program | Impact |
|---------|--------|
| PROD-INT-02 | Confirmă: registry parțial, fără motor distribuție |
| OWNER-DECISION-01 | Rămâne AMANAT — audit arată ce există deja |
| MOBILE-T04/T05/T06 | Valide individual; registry drift periculos (Sandu) |
| PROD-ARCH-01 | **BLOCAT** până APP-AUTH-01 |

---

## Screenshot-uri (8)

| Fișier | URL | Viewport |
|--------|-----|----------|
| 01_employees.png | /employees | 1440×900 |
| 02_employees_records.png | /employees-records | 1440×900 |
| 03_attendance.png | /attendance | 1440×900 |
| 04_utilaje.png | /utilaje | 1440×900 |
| 05_shop_floor.png | /shop-floor | 1440×900 |
| 06_operator.png | /operator | 1440×900 |
| 07_tablet.png | /tablet | 1440×900 |
| 08_employee_mobile_v2.png | /employee-app-v2/tasks | 390×844 |

Folder: `docs/qa/product-system-active-path-isolation-v1/app_int_01_screenshots/`

---

## Teste audit

| Suită | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| test_m19_machines_registry_activation | ✓ | 0 | 0 |
| test_employee_mobile_claim_concurrency | ✓ | 0 | 0 |
| test_execution_task_assignment | ✓ | 0 | 0 |
| test_employee_mobile_task_truth | ✓ | 0 | 0 |
| **Total targeted** | **53** | **0** | **0** |

---

## Opinie sinceră

Aplicația **nu are un singur adevăr** pentru competențe/autorizări: registry-ul este intenția corectă, dar coloanele legacy, listele explicit pe operație și fixture-ele mobile pot contrazice UI-ul din `/employees`. Sandu este exemplul concret — montaj LED eligibil fără competență în registry. **Nu construi motor de distribuție** până APP-AUTH-01 nu închide autoritatea. Shop Floor și Tablet sunt utile ca proiecții, nu ca registry nou.

---

## Următorul task

**`APP-AUTH-01-CANONICAL_AUTHORITY_DECISIONS`**

---

## Delivery footer

```
Task: APP-INT-01
Starting HEAD: 72d9b57
Routes: all PARTIAL→PASS (audited with evidence)
Runtime employees: 8
Runtime operations: 18
Runtime machines: 14
Employee model: DUPLICATE
HR model: PARTIAL
Skills: DUPLICATE
Authorizations: PARTIAL
Workcenters: CANONICAL (catalog)
Machines: CANONICAL (single table)
Employee-machine relation: PARTIAL
Dependencies: CANONICAL (readiness service)
Readiness: PARTIAL
Assignment: PARTIAL
Sessions: PARTIAL
Attendance: CANONICAL (separate)
Availability: BLOCKED (missing)
Workload: BLOCKED (missing)
Duplicate authorities: 10
Legacy active surfaces: 4
Demo/mock surfaces: 5
UI screenshots: 8
Tests: PASS (53 targeted)
Code changed: NO
Next task: APP-AUTH-01-CANONICAL_AUTHORITY_DECISIONS
Verdict: APP_E2E_AUDIT_PASS_READY_FOR_AUTHORITY_DECISIONS
```
