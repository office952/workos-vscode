# APP-AUTH-02 — Inventar complet de discrepanțe și plan de reconciliere

**Task:** APP-AUTH-02 — `DATA_DISCREPANCY_AND_RECONCILIATION_PLAN_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `357838e`  
**Audit bază:** APP-INT-01 @ `bfe20c6` · APP-AUTH-01 @ `357838e`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Backend:** `http://127.0.0.1:8001` · **Frontend:** `http://127.0.0.1:3000`  
**Cod changed:** NO · **DB changed:** NO · **Implementare autorizată:** NO

## Verdict

**`APP_AUTH_02_RECONCILIATION_PLAN_READY_FOR_OWNER`**

Inventarul de discrepanțe este complet pentru runtime-ul curent (8 angajați, 14 operații mapate, 39 override-uri explicite). Reconcilierea **nu** poate continua fără decizii owner (Sandu, taxonomie, override policy, demo isolation). PROD-ARCH-01 și MOBILE-INT-02 rămân **BLOCAT**.

---

## Siguranță repository

| Verificare | Rezultat |
|------------|----------|
| Cod modificat | **NO** |
| DB modificat | **NO** |
| Migrări | **NO** |
| Seeds | **NO** |
| UI/endpoints | **NO** |
| Sincronizare registry/JSON | **NO** |
| Eliminare override/fallback | **NO** |

---

## Intrări acceptate

| Sursă | Referință |
|-------|-----------|
| APP-INT-01 worklog | `docs/worklog/realignment/2026-07-15_app_int_01_audit_e2e_angajati_competente_utilaje_executie_pontaj_v1.md` |
| APP-AUTH-01 worklog | `docs/worklog/realignment/2026-07-15_app_auth_01_canonical_authority_decisions_v1.md` |
| Probe runtime APP-INT-01 | `docs/qa/.../app_int_01_runtime_probe.json`, `app_int_01_eligibility_probe.json` |
| Probe APP-AUTH-02 | `docs/qa/.../app_auth_02/*.json` |
| Screenshots APP-INT-01 | `docs/qa/.../app_int_01_screenshots/` (8 fișiere) |

---

## Numărători runtime (exacte @ :8001, 2026-07-15)

| Metrică | Valoare |
|---------|---------|
| Angajați | 8 |
| Utilizatori legați de angajați | 1 |
| Angajați fără utilizator | 7 |
| Utilizatori legați la mai mulți angajați | 0 |
| Rânduri înregistrare HR (derivat demo) | 8 |
| Angajați fără înregistrare HR derivată | 0 |
| Intrări catalog competențe | 15 |
| Relații angajat–competență (registry) | 30 |
| Angajați cu competențe legacy JSON | 8 |
| Angajați cu conflict registry vs JSON (competențe) | 1 (Sandu) |
| Angajați cu conflict registry vs JSON (utilaje) | 1 (Sandu) |
| Centre de lucru (catalog) | 14 |
| Utilaje/resurse | 14 |
| Autorizări angajat–resursă | 16 |
| Mapări operație | 14 |
| Override-uri explicite (eligible cu `explicit_override`) | 39 |
| Override-uri fără competență registry | 7 (toate Sandu) |
| Override-uri fără autorizare resursă | 6 |
| Alocări active (`assigned_employee_id` setat) | 7 |
| Sesiuni active (`in_progress`) | 3 |
| Evenimente pontaj luna curentă | 0 |
| Autorități duplicate (program) | 10 |
| Discrepanțe documentate | 20 |

---

## Sumar severitate

| Severitate | Count |
|------------|-------|
| CRITICAL | 1 |
| HIGH | 14 |
| MEDIUM | 4 |
| LOW | 0 |
| INFORMATIONAL | 1 |

---

## Autorități duplicate (10) — fără decizie automată

| # | Domeniu | Sursa A | Sursa B | Efect |
|---|---------|---------|---------|-------|
| 1 | Competențe | `employee_skill_authorizations` | `employees.skills` JSON | Eligibilitate/UI diverg |
| 2 | Utilaje | `employee_resource_authorizations` | `employees.machines` JSON | Autorizare resursă diverg |
| 3 | Eligibilitate | reguli competență | `operation_employee_authorizations` | Override additive |
| 4 | Alocare | plan JSON | operator fields | Drift assignment |
| 5 | Alocare | assignment service | mobile claim direct | Parțial consolidat T06 |
| 6 | HR | `employees` live | `EmployeeRecord` demo | Confuzie HR |
| 7 | Shop Floor | API live | `mockData` fallback | Date neautoritative |
| 8 | Tablet | operator tasks | `DEMO_OPERATORS` | Suprafață paralelă |
| 9 | Pontaj | `employee_attendance_events` | ExecutionReality (display) | Separat by design |
| 10 | Profil | registry panel | form CSV legacy | Scrieri ne-sincronizate |

---

## Tabel complet discrepanțe

| ID | Domeniu | Entitate | Sursa A | Valoare A | Sursa B | Valoare B | Tip | Severitate | Efect runtime | Confirmare necesară | Rezolvare propusă |
|----|---------|----------|---------|-----------|---------|-----------|-----|------------|---------------|---------------------|-------------------|
| DISC-COMP-001 | Competențe | Putaru Sandu (id=4) | registry skills | SK_PRINT_OPERATOR | employees.skills | locksmith, assembly, electrician, vinyl, montator | COMPETENCE_VALUE_CONFLICT | HIGH | Mobile/eligibilitate citește registry; form arată legacy | Owner | Wave R3 — sursă canonică per angajat |
| DISC-AUTO-002 | Autorizări | Putaru Sandu (id=4) | registry resources | MCH-EPSON-60800 | employees.machines | sudură, mese ansamblare | AUTHORIZATION_SCOPE_CONFLICT | HIGH | Neeligibil resursă reală dacă fail-closed | Owner | Wave R3 — aliniere relații |
| DISC-ELIG-003 | Eligibilitate | Sandu / assembly | explicit list | listed | registry | fără SK_ASSEMBLY | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil ansamblare | Owner | Excepție formală sau eliminare listă |
| DISC-ELIG-004 | Eligibilitate | Sandu / colantare | explicit list | listed | registry | fără SK_VINYL_APPLICATOR | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil colantare | Owner | Idem |
| DISC-ELIG-005 | Eligibilitate | Sandu / field_installation | explicit list | listed | registry | fără SK_FIELD_INSTALLER | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil montaj teren | Owner | Idem |
| DISC-ELIG-006 | Eligibilitate | Sandu / montaj_led | explicit list | listed | registry | fără SK_ELECTRICIAN | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | **CRITICAL** | Eligibil electric fără competență | Owner | Excepție auditată sau restaurare competențe |
| DISC-ELIG-007 | Eligibilitate | Sandu / packaging | explicit list | listed | registry | fără SK_ASSEMBLY | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil ambalare | Owner | Idem |
| DISC-ELIG-008 | Eligibilitate | Sandu / quality_control | explicit list | listed | registry | fără SK_ASSEMBLY | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil QC | Owner | Idem |
| DISC-ELIG-009 | Eligibilitate | Sandu / welding | explicit list | listed | registry | fără SK_LOCKSMITH | EXPLICIT_OVERRIDE_WITHOUT_COMPETENCE | HIGH | Eligibil sudură | Owner | Idem |
| DISC-TAXO-010 | Taxonomie | SK_COMMERCIAL_TECH | catalog skills | Director comercial/tehnic | semantica | Rol management | ROLE_COMPETENCE_MIX | MEDIUM | Folosit ca competență la Chirila | Owner | Mutare catalog roluri |
| DISC-EXEC-011 | Execuție | /shop-floor | useShopFloorData | DB | mockData | alerte demo | MOCK_FALLBACK_ON_ACTIVE_SURFACE | HIGH | UI neautoritar | Owner | Fail-closed Wave R5 |
| DISC-DEMO-012 | Demo | /shop-floor | mockData.ts | fallback silent | rută activă | live expected | MOCK_FALLBACK_ON_ACTIVE_SURFACE | HIGH | Contaminare vizuală | Owner | Izolare demo |
| DISC-EMP-013 | Identitate | Sandu | employees.user_id | dev-admin-user | rol așteptat | angajat producție | IDENTITY_MISMATCH | HIGH | Mobile mapare admin→Sandu | Owner | User dedicat sau deconectare |
| DISC-EMP-014 | Identitate | 7 angajați | user_id | null | Mobile | link necesar | MISSING_LINK | MEDIUM | Fără acces Mobile canonic | Owner | Wave R1 mapare |
| DISC-EXEC-015 | Alocare | Sandu / face_cnc_cut | assigned_employee_id | 4 | registry | fără SK_CNC | ASSIGNMENT_SOURCE_CONFLICT | HIGH | CNC alocat greșit | Manager + Owner | Reassign Florin CNC |
| DISC-EXEC-016 | Alocare | Sandu / vector_prep | sesiune in_progress | activ | registry | SK_PRINT vs prepress | ASSIGNMENT_SOURCE_CONFLICT | HIGH | Sesiune activă nevalidă | Manager | Stop + reassign |
| DISC-MCH-017 | Utilaj | machine_type task | plan | WC_CNC | catalog | WC_CNC_ROUTING | MACHINE_TYPE_CONFLICT | MEDIUM | Mapare ambiguă | Tehnic | Alias Wave R4 |
| DISC-DEMO-018 | Demo | /employees-records | employeeRecordsData | HR demo | employees | operațional | DEMO_DATA_ON_ACTIVE_SURFACE | MEDIUM | Confuzie HR | Owner | Badge + izolare |
| DISC-DEMO-019 | Demo | /tablet | DEMO_OPERATORS | demo | /operator | live | EXECUTION_SURFACE_CONFLICT | HIGH | Suprafață paralelă | Owner | Retire sau wrapper |
| DISC-ATT-020 | Pontaj | luna curentă | attendance | 0 events | ER sessions | 3 in_progress | ATTENDANCE_LINK_CONFLICT | INFORMATIONAL | Separat by design | Tehnic | Reguli viitoare R1 |

**Artefact JSON complet:** `docs/qa/product-system-active-path-isolation-v1/app_auth_02/discrepancy_inventory.json`

---

## Matrice angajat cu angajat (8/8)

| Angajat | User | Înregistrare HR | Rol | Competențe registry | Competențe legacy | Centre autorizate | Utilaje autorizate | Override operații | Discrepanțe | Risc |
|---------|------|-----------------|-----|---------------------|-------------------|-------------------|--------------------|--------------------|-------------|------|
| Calin Cimpean | — | derivat demo | Grafician/Operator | SK_GRAPHIC, PRINT, LAMINATOR, CUTTER, QUOTING | = registry | WC_PRINT, LAMINATE, CUT | Epson, Laminator, Plotter | prepress, print, laminare, cutter | 0 | LOW |
| Octavian Dumitru | — | derivat demo | Grafician/Operator | = Calin | = registry | = Calin | = Calin | = Calin | 0 | LOW |
| Florin CNC | — | derivat demo | Operator CNC | SK_CNC, SK_CNC_PREP, SK_LETTER_CANT | = registry | WC_CNC_ROUTING, WC_LETTER_FORMING | MCH-CNC-4020, MCH-CNC-CANT-LITERE | cnc_cutting, cant_modelare | 0 | LOW |
| **Putaru Sandu** | dev-admin | derivat demo | Lăcătuș/Montator | **SK_PRINT only** | locksmith, assembly, vinyl, electrician, montator | **WC_PRINT** | **Epson only** vs legacy sudură/mese | 8 explicit (7 fără competență) | **skills+machines+override+assign** | **CRITICAL** |
| Vali Colantator | — | derivat demo | Colantator/Montator | assembly, vinyl, electrician, montator | = registry | assembly, vinyl, LED, field | rigid laminator, mese | montaj_led, colantare, etc. | 0 | LOW |
| Costi Modelator | — | derivat demo | Modelator/Colantator | + SK_LETTER_MODELING | = registry | letter forming, assembly, vinyl, LED | cant litere, masă 1 | cant_modelare, montaj_led | 0 | LOW |
| Andrei Goghi | — | derivat demo | Producție/CNC | + SK_CNC_OPERATOR | = registry | CNC, assembly, LED, field | CNC 4020, masă 2 | cnc_cutting, montaj_led | 0 | LOW |
| Chirila Cristian | — | derivat demo | Direct comercial/tehnic | SK_COMMERCIAL_TECH, QUOTING | = registry | — | — | prepress | taxonomie SK_COMMERCIAL | LOW |

**JSON:** `employee_reconciliation_matrix.json`

---

## Pachet reconciliere Sandu

| Câmp | Valoare |
|------|---------|
| ID angajat | 4 |
| ID utilizator | `dev-admin-user-00000000` |
| Înregistrare HR | derivată demo (`employeeRecordsData`) |
| Rol entities | Lăcătuș / Montator |
| Competențe registry | SK_PRINT_OPERATOR |
| Competențe legacy JSON | SK_LOCKSMITH, SK_ASSEMBLY, SK_VINYL_APPLICATOR, SK_ELECTRICIAN, SK_FIELD_INSTALLER |
| Centre registry | WC_PRINT |
| Utilaje registry | MCH-EPSON-60800 |
| Utilaje legacy | MCH-WELD-STEEL, MCH-WELD-ALU, WA-WELD-TABLE, WA-ASSEMBLY-01/02 |
| Scriitor registry | `OperationalRegistryService.set_employee_authorizations` (nu sincronizează JSON) |
| Consumatori | eligibilitate, Mobile truth, `/employees` panel, Operator assignment |
| Clasificare | **LEGACY_OVERRIDE_REQUIRES_RECONCILIATION** |

### Task-uri runtime Sandu

| Task | Order | Status | Operație | Observație |
|------|-------|--------|----------|------------|
| vector_prep | 23099 | in_progress | prepress | Sesiune activă — competență grafică lipsă registry |
| face_cnc_cut | 23099, 23150 | assigned | cnc_cutting | Alocare CNC fără SK_CNC |
| return_profile_forming | 23099 | assigned | cant_modelare | — |
| electrical_wiring | 23150 | assigned | montaj_led | Depinde override explicit |
| T-M06-CLAIM-POLICY | 92400 | in_progress | print | Claim policy probe — SK_PRINT valid |
| T-M05B | 92350 | done | print | Probe concurență |

### `montaj_led` — răspunsuri explicite (11)

| # | Întrebare | Răspuns |
|---|-----------|---------|
| 1 | De ce este Sandu eligibil? | Listă explicită `operation_employee_authorizations` + mod **hybrid** (explicit OR competență) |
| 2 | Override narrowing sau additive bypass? | **Additive bypass** — adaugă eligibilitate fără competență registry |
| 3 | Serviciu aplicator | `OperationalRegistryService.get_eligible_employees_for_operation` / `check_employee_operation_eligibility` |
| 4 | Ocolește competența? | **Da** — registry are doar SK_PRINT; cerut SK_ELECTRICIAN |
| 5 | Ocolește autorizarea? | **Da** — fără resursă WC_LED / utilaj electric autorizat |
| 6 | Vizibil în `/employees`? | Panel registry arată SK_PRINT; form legacy arată competențe montaj |
| 7 | Vizibil în detaliu task? | Eligibilitate backend da; UI Operator nu expune override explicit |
| 8 | Approver / motiv / expirare? | **Null** — fără metadate excepție |
| 9 | Task-uri dependente | `electrical_wiring` ord 23150; `led_installation` ord 23099 (nealocat încă) |
| 10 | Fail-closed ar elimina muncă legitimă? | **Posibil da** dacă legacy JSON reflectă adevărul operațional — necesită confirmare owner |
| 11 | Cine confirmă competența reală? | **Owner + manager producție** (confirmare înregistrare angajat) |
| 12 | Regulă compatibilitate temporară | Păstrare override **doar** cu excepție auditată până la restaurare registry aliniat la legacy JSON confirmat |

**Nu se rezolvă automat** — status: `OWNER_CONFIRMATION_REQUIRED`

---

## Pachet reconciliere CNC 4020 (`MCH-CNC-4020`)

| Aspect | Stare |
|--------|-------|
| Identitate cod | **Aliniat** — `machines`, registry, `/utilaje`, autorizări Florin + Andrei |
| Rând machine | id=1, cnc_router, WC_CNC_ROUTING, capacity_metadata complet |
| resource_kind | machine |
| Operații dependente | `cnc_cutting` — Florin, Andrei eligibili cu competență |
| Cerințe operație | SK_CNC_OPERATOR + resursă MCH-CNC-4020 |
| machine_type task | **Conflict** — plan folosește `WC_CNC` text (DISC-MCH-017) |
| UI mock specs | `useMachinesData` enrich — DEV_ONLY, nu autoritate |
| Runtime status/capacity | metadata DB prezent; shop-floor nu consumă încă |
| Clasificare | **IDENTITY_ALIGNED_METADATA_PARTIAL** |

---

## Taxonomie rol / competență / atribuție

| Cod actual | Denumire actuală | Clasificare reală | Catalog țintă propus | Migrare necesară | Confirmare |
|------------|------------------|-------------------|----------------------|------------------|------------|
| SK_LETTER_MODELING | Modelare cant litere | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_ASSEMBLY | Asamblare | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_ELECTRICIAN | Electrician | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_FIELD_INSTALLER | Montator | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_LOCKSMITH | Lăcătuș | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_VINYL_APPLICATOR | Colantator | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_COMMERCIAL_TECH | Director comercial / tehnic | **ROL** | roluri_organizație | **Da** | OWNER_CONFIRMATION_REQUIRED |
| SK_PRINT_OPERATOR | Operator print | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| SK_CNC_OPERATOR | CNC | COMPETENȚĂ | catalog_competențe | Nu | SAFE_MIGRATION_CANDIDATE |
| WC_METAL_FAB | Sudare | CENTRU_DE_LUCRU | catalog_workcenters | Nu | SAFE_MIGRATION_CANDIDATE |
| WC_LAMINATE | Laminare | CENTRU_DE_LUCRU | catalog_workcenters | Nu | SAFE_MIGRATION_CANDIDATE |

---

## Inventar override explicit

**Total intrări eligible cu flag explicit:** 39 · **Sandu fără competență:** 7 · **Sandu fără autorizare resursă:** 6

| Operație | Angajat | Match competență | Match autorizare | Clasificare | Risc |
|----------|---------|------------------|------------------|-------------|------|
| montaj_led | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | CRITICAL |
| assembly | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | HIGH |
| welding | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | HIGH |
| colantare | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | HIGH |
| packaging | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | HIGH |
| quality_control | Sandu | Nu | Nu | ADDITIVE_WITHOUT_AUTHORIZATION | HIGH |
| field_installation | Sandu | Nu | Da | ADDITIVE_WITHOUT_COMPETENCE | HIGH |
| print | Sandu | Da | Da | ADDITIVE_WITH_VALID_COMPETENCE | LOW |

**JSON complet:** `override_inventory.json`

**Politică:** niciun override additive fără competență/autorizare **nu** este safe automat.

---

## Matrice angajat–resursă (rezumat)

| Angajat | Resursă | Registry | Legacy | UI | Conflict |
|---------|---------|----------|--------|-----|----------|
| Sandu | MCH-EPSON-60800 | Da | Nu | Da | Nu |
| Sandu | MCH-WELD-STEEL | Nu | Da | form | **Da** |
| Sandu | WA-ASSEMBLY-01 | Nu | Da | form | **Da** |
| Florin | MCH-CNC-4020 | Da | Da | Da | Nu |
| Vali | WA-ASSEMBLY-01 | Da | Da | Da | Nu |

**JSON:** `machine_reconciliation_matrix.json` → `employee_resource`

---

## Reconciliere identitate

| Întrebare | Răspuns |
|-----------|---------|
| Un utilizator poate acționa ca mai mulți angajați? | **Nu** dovedit (1 user → 1 angajat); dev-admin → Sandu |
| Un angajat poate avea mai mulți utilizatori? | **Nu** — câmp singular `user_id` |
| HR record greșit? | Posibil confuzie demo — **nu** dovedit link greșit |
| Nume ca fallback identitate? | Da în UI Operator (`operator_name` legacy) |
| Email ca identitate? | Parțial auth; `auth_email` null pe angajați |
| Demo operatori colidează? | Tablet DEMO_OPERATORS — suprafață separată |
| Inactivi referențiați? | **Nu** în probe |
| Sesiuni istorice stabile? | employee_id pe ER; redenumire angajat afectează display |

**Status reconciliere identitate:** **PARTIAL** (Sandu user + 7 fără link)

---

## Suprafețe execuție

| Suprafață | Autorități citite | Scrieri | Fallback | Conflict | Tranziție recomandată |
|-----------|-------------------|---------|----------|----------|------------------------|
| Employee Mobile v2 | mobile task truth, registry eligibility, assignment, ER | claim, start, complete | none on truth | indirect registry vs JSON | Canonic individual |
| /operator | operator tasks, ER, assignment | start/pause/complete, manager assign | mockData if fail | operator_name legacy | Canonic desktop |
| /tablet | operator tasks, workstationRouting | via performAction | DEMO_OPERATORS, generateDemoTasks | PARALLEL authority | Retire sau kiosk wrapper |
| /shop-floor | machines, operator tasks | none | mockData silent | ACTIVE_SILENT_FALLBACK | Fail-closed prod |

**JSON:** `execution_surface_matrix.json`

---

## Pontaj

- Pontaj rămâne **separat** de ExecutionReality (by design APP-AUTH-01 D21).
- 0 evenimente luna curentă — **nu** blochează execuția.
- Viitor: Wave R1 — legături employee_id stabile; **interzis** derivare pontaj din ER.

**Status:** **PARTIAL** (reguli viitoare only)

---

## Inventar demo/mock

| Fișier | Rută | Clasificare | Badge | Participă eligibilitate |
|--------|------|-------------|-------|-------------------------|
| employeeRecordsData.ts | /employees-records | EXPLICIT_DEMO_MODE | parțial | Nu |
| mockData.ts | /shop-floor | ACTIVE_SILENT_FALLBACK | uneori | Nu direct |
| workstationRouting.ts | /tablet | LEGACY_ACTIVE | demo | Da (routing) |
| useMachinesData mock enrich | /utilaje | DEV_ONLY_SAFE | — | Nu |
| operationalEmployeeRecords.ts | /employees-records | EXPLICIT_DEMO_MODE | — | Nu |

---

## Impact consumatori (switch canonic propus)

| Switch propus | Consumatori impactați |
|---------------|----------------------|
| skills → registry only | /employees, Mobile, eligibilitate, Operator lists |
| machines → registry only | /employees, /utilaje auth display, eligibilitate resursă |
| override → excepții auditate | toate mapările operație, readiness distribuție viitoare |
| fail-closed shop-floor | /shop-floor, manager dashboards |
| tablet retire | /tablet, kiosk flows |

---

## Valuri reconciliere (R0–R10)

| Val | Nume | Acțiuni (plan only) |
|-----|------|---------------------|
| R0 | Freeze and observe | raport discrepanțe; fără switch |
| R1 | Identitate | user/HR/pontaj links |
| R2 | Taxonomie | SK_COMMERCIAL_TECH, WC naming |
| R3 | Competențe + autorizări | registry vs JSON; Sandu |
| R4 | Utilaj/resursă | MCH-CNC-4020; machine_type alias |
| R5 | Suprafețe execuție | tablet, shop-floor mock |
| R6 | Read parity | adapters; drift metrics |
| R7 | Write freeze | stop JSON writes |
| R8 | Migrare | one-time post owner |
| R9 | Fallback disable | fail-closed |
| R10 | Legacy removal | post proof |

**JSON:** `reconciliation_waves.json` (11 valuri)

---

## Matrice candidat migrare

| Domeniu | Source | Target | Transformare | Risc pierdere | Impact runtime | Rollback | Aprobare |
|---------|--------|--------|--------------|---------------|----------------|----------|----------|
| Competențe angajat | employees.skills JSON | employee_skill_authorizations | copy distinct per angajat | mediu (Sandu) | eligibilitate | restore JSON backup | Owner |
| Utilaje angajat | employees.machines JSON | employee_resource_authorizations | copy codes | mediu | autorizare resursă | restore JSON | Owner |
| Override explicit | operation_employee_authorizations | excepții auditate | metadata approver/reason | scăzut | eligibilitate | revert rows | Owner |
| HR demo | EmployeeRecord demo | HR module viitor | manual 1:1 | scăzut | employees-records | keep demo | Owner |
| machine_type plan | WC_CNC text | WC_CNC_ROUTING alias | mapping table | scăzut | task display | alias revert | Tehnic |

---

## Matrice fail-closed (plan — neaplicat)

| Domeniu | Condiție | Comportament propus |
|---------|----------|---------------------|
| Identitate angajat | id invalid/inactiv | refuz alocare/sesiune |
| Competență | conflict registry/JSON | neeligibil + flag manager |
| Autorizare | conflict resursă | neeligibil |
| Utilaj | cod ambiguu | blocked task |
| Cerință operație | gap mapping | readiness blocked |
| Alocare | fără eligibilitate | refuz assign/claim 409 |
| Sesiune | conflict ER | 409 conflict |
| Pontaj | fără link angajat | refuz scriere pontaj |

---

## Pachet decizii owner (6)

| ID | Titlu | Înregistrări | Recomandare |
|----|-------|--------------|-------------|
| OD-01 | Competențe canonice Sandu | id=4 registry vs legacy | Restaurare registry aliniat la Lăcătuș/Montator confirmat |
| OD-02 | Politică override montaj_led | explicit fără SK_ELECTRICIAN | Excepție auditată sau eliminare până la reconciliere |
| OD-03 | Taxonomie SK_COMMERCIAL_TECH | Chirila id=8 | Clasificare Rol |
| OD-04 | Migrare JSON skills/machines | 1 angajat conflict | ONE_TIME_MIGRATION post Sandu |
| OD-05 | Tranziție Tablet | DEMO_OPERATORS | Retire sau paritate servicii |
| OD-06 | Shop Floor mock | mockData fallback | Fail-closed producție |

**JSON:** `owner_decision_package.json`

---

## Teste (read-only, fără fix)

| Suite | Passed | Failed | Skipped | Collection errors |
|-------|--------|--------|---------|-------------------|
| test_operational_authorization_foundation.py | ✓ | — | — | 0 |
| test_operational_resource_registry.py | ✓ | — | — | 0 |
| test_operator_task_truth.py | ✓ | — | — | 0 |
| test_employee_mobile_task_truth.py | 34 | **1** | — | 0 |
| test_employee_attendance_events.py | ✓ | — | — | 0 |
| **Total targeted** | **73** | **1** | **0** | **0** |

**Eșec:** `test_available_projection_filters_canonically` — clasificare **RUNTIME_PROOF_MISSING** / caracterizare Mobile available vs registry Sandu; **nu** remediat în APP-AUTH-02.

---

## Evidență UI (reutilizare APP-INT-01)

| URL | Entitate | Sursă backend | Adevăr afișat | Conflict | ID | Opinion |
|-----|----------|---------------|---------------|----------|-----|---------|
| /employees | Sandu | registry panel | SK_PRINT | form legacy montaj | DISC-COMP-001 | `01_employees.png` |
| /employees-records | Sandu | demo HR | documente fictive | vs operational | DISC-DEMO-018 | `02_employees_records.png` |
| /utilaje | CNC 4020 | /machines | MCH-CNC-4020 | mock enrich UI | — | `04_utilaje.png` |
| /operator | Sandu tasks | operator tasks | alocări 23099 | CNC/prepress fără competență | DISC-EXEC-015/016 | `06_operator.png` |
| Employee Mobile | Sandu T06 | mobile truth | print in_progress | registry SK_PRINT only | DISC-COMP-001 | `08_employee_mobile_v2.png` |
| /tablet | demo | workstationRouting | DEMO | vs operator live | DISC-DEMO-019 | `07_tablet.png` |
| /shop-floor | fallback | mockData | alerte | live DB | DISC-EXEC-011 | `05_shop_floor.png` |
| /attendance | linkage | attendance API | 0 events | ER sessions separate | DISC-ATT-020 | `03_attendance.png` |

---

## Autorizare implementare

| Item | Valoare |
|------|---------|
| Implementare cod | **NO** |
| Migrare | **NO** |
| Switch sursă canonică | **NO** |
| Următor task | **OWNER-DECISION-02-DATA-RECONCILIATION** |

---

## Opinie sinceră

Sandu este **singurul angajat cu drift material** registry↔legacy; probabile cauze: test MOBILE-T06/T05B care a rescris registry la SK_PRINT fără sync JSON. Override-urile explicite par **seed/fixture legacy** care permit producția demo să continue — **periculos** dacă fail-closed se aplică fără reconciliere. CNC 4020 este modelul pozitiv de aliniere. Prioritate owner: **OD-01 + OD-02** înainte de orice migrare JSON.

---

## Checkpoint roadmap

| Program | Status |
|---------|--------|
| APP-INT-01 | COMPLETE |
| APP-AUTH-01 | COMPLETE |
| APP-AUTH-02 | **COMPLETE** (plan) |
| OWNER-DECISION-02 | **NEXT** |
| PROD-ARCH-01 | BLOCAT |
| MOBILE-INT-02 | BLOCAT |

---

## DELIVERY FOOTER

```
Task: APP-AUTH-02 — DATA_DISCREPANCY_AND_RECONCILIATION_PLAN_V1
Starting HEAD: 357838e
Runtime employees: 8
Employees with user link: 1
Employees without user link: 7
EmployeeRecord rows: 8
Competence catalog: 15
Employee-competence relations: 30
Employees with legacy skills: 8
Registry/legacy competence conflicts: 1
Machines/resources: 14
Employee-resource authorizations: 16
Explicit operation overrides: 39
Overrides without competence: 7
Overrides without authorization: 6
Duplicate authorities: 10
Critical discrepancies: 1
High discrepancies: 14
Medium discrepancies: 4
Low discrepancies: 0
Sandu: LEGACY_OVERRIDE_REQUIRES_RECONCILIATION
CNC 4020: IDENTITY_ALIGNED_METADATA_PARTIAL
Identity reconciliation: PARTIAL
Competence reconciliation: BLOCKED
Authorization reconciliation: BLOCKED
Machine reconciliation: PARTIAL
Execution surface reconciliation: BLOCKED
Attendance reconciliation: PARTIAL
Reconciliation waves: 11
Owner decisions required: 6
Implementation authorized: NO
Code changed: NO
DB changed: NO
Next task: OWNER-DECISION-02-DATA-RECONCILIATION
Commit: YES
Commit hash: <post-commit>
Push: NO
PR: NO
Verdict: APP_AUTH_02_RECONCILIATION_PLAN_READY_FOR_OWNER
```
