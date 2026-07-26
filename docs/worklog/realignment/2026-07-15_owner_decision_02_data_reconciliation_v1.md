# OWNER-DECISION-02 — Decizii owner pentru reconcilierea datelor operaționale

**Task:** OWNER-DECISION-02 — `DECIZII_OWNER_RECONCILIERE_DATE_OPERATIONALE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `b6081c0`  
**Intrări acceptate:** APP-INT-01 @ `bfe20c6` · APP-AUTH-01 @ `357838e` · APP-AUTH-02 @ `b6081c0`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Cod changed:** NO · **DB changed:** NO · **Implementare autorizată:** NO

## Verdict

**`OWNER_DATA_RECONCILIATION_PARTIAL_REMAIN_BLOCKED`**

9 decizii owner documentate cu date reale din APP-AUTH-02; **0 CONFIRMATE**. Reconcilierea datelor, PROD-ARCH-01 și MOBILE-INT-02 rămân **BLOCATE** până la confirmări explicite. Testul proiecției available e clasificat; următorul pas tehnic: **APP-AUTH-02B** (închidere proiecție), nu migrare.

---

## Siguranță repository

| Verificare | Rezultat |
|------------|----------|
| Cod | **NO** |
| DB | **NO** |
| Migrări | **NO** |
| UI/endpoints | **NO** |
| Modificare competențe/exceptii | **NO** |
| Sync registry/JSON | **NO** |
| Reparare test roșu | **NO** (documentat doar) |

---

## Evidență acceptată

| Sursă | Cale |
|-------|------|
| Inventar discrepanțe | `docs/qa/.../app_auth_02/discrepancy_inventory.json` |
| Matrice angajați | `docs/qa/.../app_auth_02/employee_reconciliation_matrix.json` |
| Exceptii eligibilitate | `docs/qa/.../app_auth_02/override_inventory.json` |
| Pachet Sandu | `docs/qa/.../app_auth_02/owner_decision_package.json` |
| Worklog APP-AUTH-02 | `docs/worklog/realignment/2026-07-15_app_auth_02_data_discrepancy_reconciliation_plan_v1.md` |

---

## PRE-GATE — Corectarea raportării severității

### Numărătoare unică (inventar DISC-* @ APP-AUTH-02)

| Severitate | Număr |
|------------|------:|
| CRITICAL | 1 |
| HIGH | 14 |
| MEDIUM | 4 |
| LOW | 0 |
| INFORMATIONAL | 1 |
| **TOTAL** | **20** |

### Clarificări obligatorii

1. **Cei 7 angajați aliniati NU reprezintă 7 discrepanțe LOW.** Calin Cimpean, Octavian Dumitru, Florin CNC, Vali Colantator, Costi Modelator, Andrei Goghi și Chirila Cristian au registry = JSON legacy în matricea angajaților, cu `discrepante_skills: false` și `risc: LOW`. **Niciunul nu are rând DISC-* propriu** în inventar.

2. **Nu există un singur caz informational agregat pentru cei 7.** Singurul rând INFORMATIONAL este **DISC-ATT-020** (pontaj 0 evenimente vs 3 sesiuni in_progress — separare intenționată). Cei 7 aliniați sunt menționați implicit doar în **DISC-EMP-014** (7 angajați fără `user_id`, severitate MEDIUM, un rând agregat pentru identitate Mobile).

3. **De ce footer-ul APP-AUTH-02 raportează `Low discrepancies: 0`:** inventarul documentează **doar conflicte active**, nu „absența conflictului”. Severitatea LOW se rezervă pentru drift terminologic / metadata neautoritativă fără efect execuție imediat. Niciun rând din cele 20 nu a fost clasificat LOW. Alinierea celor 7 angajați este **stare normală observată**, nu discrepanță inventariată.

4. **Cele 20 de rânduri concrete:**

| ID | Severitate | Entitate scurtă |
|----|------------|-----------------|
| DISC-COMP-001 | HIGH | Sandu — competențe registry vs JSON |
| DISC-AUTO-002 | HIGH | Sandu — autorizări utilaj |
| DISC-ELIG-003 … 009 | HIGH (×7) | Sandu — exceptii fără competență (montaj_led = CRITICAL în 006) |
| DISC-TAXO-010 | MEDIUM | SK_COMMERCIAL_TECH taxonomie |
| DISC-EXEC-011, DISC-DEMO-012 | HIGH | /shop-floor mock fallback |
| DISC-EMP-013 | HIGH | Sandu — user dev-admin |
| DISC-EMP-014 | MEDIUM | 7 angajați fără utilizator |
| DISC-EXEC-015, 016 | HIGH | Sandu — alocări CNC/prepress |
| DISC-MCH-017 | MEDIUM | machine_type WC_CNC vs WC_CNC_ROUTING |
| DISC-DEMO-018 | MEDIUM | /employees-records demo |
| DISC-DEMO-019 | HIGH | /tablet paralel demo |
| DISC-ATT-020 | INFORMATIONAL | pontaj separat de sesiuni |

**Notă:** DISC-ELIG-006 este singurul CRITICAL; celelalte 6 exceptii Sandu sunt HIGH. Total: 1+14+4+0+1=20. **Fără modificare retroactivă a JSON-ului probe** — această secțiune clarifică interpretarea footer-ului.

---

## PRE-GATE — Testul roșu `test_available_projection_filters_canonically`

| Câmp | Valoare |
|------|---------|
| Fișier | `backend/tests/test_employee_mobile_task_truth.py` |
| Modul testat | `services.employee_mobile_tasks_service.list_available_tasks` |
| Așteptare | 1 operație print nealocată, `is_available_for_claim=True`, `claimable=True` |
| Izolat | **PASS** |
| Cu suite APP-AUTH-02 | **FAIL** |
| Eroare exactă | `HTTPException 422`: `ORDER_SNAPSHOT_V2_CORRUPT` — `snapshot_v2_json is not valid JSON` pe `order_id=24009` |
| Fixture test | `_seed_employee`, `_seed_print_eligibility`, `_seed_v2_order`, `_delete_order_execution_fixture` |
| Sursă eligibilitate | `OperationalRegistryService.check_employee_operation_eligibility` + seed print |
| Sandu implicat | **Nu** — angajat sintetic „V2 Claimer” |
| Exceptii explicite implicate | **Nu** — seed doar competență print |
| Dependență ordine teste | **Da** — comanda coruptă rămasă de `test_operator_task_truth.py` (snapshot `{not-valid-json`) |
| Risc runtime | Proiecția available încarcă context readiness pe comenzi din pool; o comandă coruptă în DB poate bloca întreg fluxul available |

### Clasificare

| Clasificare | Applicabil |
|-------------|------------|
| **FIXTURE_STATE_BLEED** | **Da (primar)** |
| **AVAILABLE_PROJECTION_DEFECT** | **Da (secundar)** — lipsă izolare fail-closed per-comandă în `_attach_readiness_to_tasks` |
| TEST_CONTRACT_OUTDATED | Nu |
| REGISTRY_LEGACY_DRIFT_EXPOSED | Nu direct |
| EXPLICIT_EXCEPTION_BEHAVIOR_EXPOSED | Nu |
| RUNTIME_DATA_CONTAMINATION | Parțial (doar în DB test partajat) |
| NOT_PROVEN | Nu — reproducibil |

**Acest task nu repară testul.** Defectul de proiecție merită închidere tehnică în **APP-AUTH-02B**, nu migrare date.

---

## Decizia O1 — Identitatea operațională

**Date concrete:** 8 angajați · 1 cu `user_id` (Putaru Sandu → `dev-admin-user-00000000`) · 7 fără · 8 înregistrări HR derivate demo.

| Variantă | Descriere | Risc |
|----------|-----------|------|
| **A (Recomandat)** | `employees.id` = identitate operațională; `user_id` = autentificare; HR 1:1; fără user → profil atelier OK, Mobile personal blocat | Minim dacă raport explicit pentru cei 7 |
| B | HR devine identitate principală | Confuzie cu demo HR |
| C | Identitate persoană nouă deasupra modelelor | Scope mare, amânare |

**Recomandare:** Varianta A.

**Confirmare owner:** ☐ CONFIRMAT ☐ RESPINS ☐ AMÂNAT ☐ NECESITĂ DATE  
**Status gate:** **AMÂNAT**

---

## Decizia O2 — Adevărul competențelor

**Date:** catalog 15 · 30 relații registry · 8 cu JSON legacy · **1 conflict material (Sandu id=4)** · 7 aliniați.

| Variantă | Descriere | Risc |
|----------|-----------|------|
| **A (Recomandat)** | Registry țintă canonică; JSON legacy doar comparație; migrare unică **după** decizii; blocare scrieri legacy; dezactivare fallback; eliminare post-paritate | Controlat cu rollback |
| B | Dual-write permanent | 10 autorități duplicate perpetue |
| C | JSON legacy rămâne autoritate | Contrazice APP-AUTH-01 |

**Recomandare:** Varianta A. **Migrarea NU este autorizată** în acest gate.

**Confirmare owner:** ☐ CONFIRMAT ☐ RESPINS ☐ AMÂNAT ☐ NECESITĂ DATE  
**Status gate:** **AMÂNAT**

---

## Decizia O3 — Cazul Putaru Sandu (id=4)

| Domeniu | Registry | Legacy JSON | Exceptii explicite | Runtime afectat | Confirmare |
|---------|----------|-------------|-------------------|-----------------|------------|
| Operator print | SK_PRINT_OPERATOR | — (absent din legacy) | print, print_roll (cu competență) | T06 ord 92400 in_progress | Owner + manager |
| Epson | MCH-EPSON-60800 | absent | — | Mobile print | Owner |
| Lăcătuș | absent | SK_LOCKSMITH | welding | eligibil welding fără registry | **Owner — competență reală?** |
| Montaj / ansamblare | absent | SK_ASSEMBLY | assembly, packaging, QC | alocări multiple | Owner |
| Colantator | absent | SK_VINYL_APPLICATOR | colantare | eligibilitate | Owner |
| Electrician | absent | SK_ELECTRICIAN | **montaj_led** (CRITICAL) | ord 23150 electrical_wiring | **Owner — prioritar** |
| Montator teren | absent | SK_FIELD_INSTALLER | field_installation | — | Owner |
| Sudură / mese | absent | weld + WA-* | welding | registry fără utilaje sudură | Owner |
| CNC / prepress | absent | — | — | face_cnc_cut, vector_prep in_progress **fără SK_CNC/SK_GRAPHIC** | Manager + owner |
| Centru print | WC_PRINT | — | — | UI panel | Owner |

### Politici owner (alege una)

| Variantă | Comportament | Risc |
|----------|--------------|------|
| **A (Recomandat)** | Confirmare umană fiecare competență/autorizare; păstrează temporar comportament existent; **fără alocare automată**; UI indică discrepanță; exceptiile nu devin adevăr canonic | Lent dar sigur |
| B | Registry câștigă imediat — blochează tot fără SK_* | Poate opri activități reale (montaj, CNC alocat) |
| C | Legacy câștigă — migrare automată JSON | Transformă fixture/seed în adevăr permanent |

**Recomandare:** Varianta A.

**Confirmări separate cerute:**
- Cine confirmă: **owner + manager producție + responsabil tehnic**
- Termen: de stabilit de owner
- Dovezi: fișă competențe, autorizări utilaj, observație șantier
- Comportament temporar: exceptii existente cu raport drift; alocări active (ord 23099, 92400) **nu se șterg automat**
- Operații active: vector_prep in_progress, T06 print — **păstrate până la decizie explicită**

**Confirmare owner:** ☐ CONFIRMAT ☐ RESPINS ☐ AMÂNAT ☐ NECESITĂ DATE  
**Status gate:** **NECESITĂ CONFIRMARE ANGAJAT** (Sandu)

---

## Decizia O4 — Exceptiile de eligibilitate

**Date:** 39 exceptii explicite în eligible-employees · 7 fără competență (toate Sandu) · 6 fără autorizare · `montaj_led` Sandu = CRITICAL.

### Regulă recomandată (neconfirmată)

Lista explicită (`operation_employee_authorizations`) poate:
- **restrânge** eligibilii dintre cei deja calificați;
- **selecta** subset.

**Nu** poate adăuga liber un angajat neeligibil. Adăugarea fără competență necesită **Exceptie temporară de eligibilitate** cu: angajat, operație, competență lipsă, motiv, aprobare manager, validare tehnică, date început/sfârșit, scop, audit, revocare.

**Lipsa autorizării obligatorii nu poate fi exceptată.**

| Variantă | Politică |
|----------|----------|
| **Recomandat** | Reconciliere manuală exceptii existente; fără migrare automată; exceptii fără autorizare → blocate sau investigate prioritar; fără competență → temporar cu avertizare |
| Permisiv | Păstrare hybrid additive permanent |
| Restrictiv | Fail-closed imediat pe toate 7 |

**Confirmare owner:** ☐ CONFIRMAT ☐ RESPINS ☐ AMÂNAT  
**Status gate:** **AMÂNAT**

---

## Decizia O5 — Autorizările

**Date:** 16 autorizări angajat–resursă · 6 exceptii operație fără autorizare · CNC 4020 aliniat (Florin, Andrei).

| Concept | Semnificație propusă |
|---------|---------------------|
| Competență | Poate executa tehnic |
| Autorizare | Permisiune formală |
| Centru de lucru | Zonă/capacitate |
| Utilaj | Resursă concretă |

Operații cu risc: lipsă autorizare → **Neeligibil** · fără exceptie simplă · fără scor · manager vede motivul.

Validare: responsabil tehnic + manager + administrator excepțional.

**Confirmare owner:** ☐ CONFIRMAT ☐ RESPINS ☐ AMÂNAT  
**Status gate:** **AMÂNAT**

---

## Decizia O6 — Suprafețele de execuție și datele demo

| Suprafață | Rol propus | Date APP-AUTH-02 |
|-----------|------------|------------------|
| Employee Mobile v2 | Control canonic angajat (individual) | truth + registry + alocare T06 |
| `/operator` | Control desktop canonic | servicii comune; dovada runtime parțială |
| `/tablet` | **Alege owner:** wrapper tranzitoriu / chiosc / legacy izolat / retragere | DISC-DEMO-019 HIGH — DEMO_OPERATORS |
| `/shop-floor` | Proiecție read-only; **fail-closed** fără mock silent | DISC-EXEC-011, DISC-DEMO-012 |

**5 surse demo:** employeeRecordsData, mockData shop-floor, workstationRouting tablet, useMachinesData enrich, operationalEmployeeRecords.

**Confirmare owner (destinație `/tablet`):** ☐ Wrapper ☐ Chiosc ☐ Legacy izolat ☐ Retragere  
**Status gate:** **AMÂNAT**

---

## Decizie separată — CNC 4020 (`MCH-CNC-4020`)

| Afirmație | Stare |
|-----------|-------|
| Cod canonic MCH-CNC-4020 | Confirmat runtime |
| `machines` deține identitatea | Da |
| `/utilaje` aceeași resursă | Da |
| Autorizare Florin CNC pe același ID | Da |
| Centru de lucru WC_CNC_ROUTING separat | Da |
| `machine_type` liber (WC_CNC) ≠ identitate utilaj | Gap metadata — DISC-MCH-017 |
| Specificații mock UI | Nu sunt adevăr runtime |

**Clasificare gap:** metadata de reconciliat · **nu** conflict identitate.

**Confirmare owner:** ☐ CONFIRMAT ☐ AMÂNAT  
**Status gate:** **AMÂNAT**

---

## Decizie separată — Angajații fără utilizator (7)

| ID | Nume | user_id |
|----|------|---------|
| 1 | Calin Cimpean | null |
| 2 | Octavian Dumitru | null |
| 3 | Florin CNC | null |
| 5 | Vali Colantator | null |
| 6 | Costi Modelator | null |
| 7 | Andrei Goghi | null |
| 8 | Chirila Cristian | null |

**Politică recomandată:** pot exista operațional; pot primi alocări manager; **nu** pot folosi Employee Mobile personal; sesiuni pornite de operator păstrează actorul real; conturi create separat; **fără** auto-provision utilizatori.

**Confirmare owner:** ☐ CONFIRMAT ☐ AMÂNAT  
**Status gate:** **AMÂNAT**

---

## Decizie separată — Pontaj

- Pontajul rămâne adevăr **separat** (0 evenimente luna curentă @ :8001).
- ExecutionReality **nu** devine pontaj salarial automat.
- Sesiuni producție → reconciliere **informativă** viitoare.
- Diferențe **nu** se corectează automat.
- Absențe/program → disponibilitate viitoare (post PROD-ARCH).

**Confirmare owner:** ☐ CONFIRMAT ☐ AMÂNAT  
**Status gate:** **AMÂNAT**

---

## Contract de tranziție (post-decizii — planificat, neactiv)

### Rămâne activ temporar
- Mobile individual (MOBILE-T06)
- Operator canonic (dacă dovada runtime trece după APP-AUTH-02B)
- JSON legacy ca fallback observabil
- Exceptii existente cu raport drift
- Alocări individuale existente (Sandu ord 23099, 92400, etc.)

### Rămâne blocat
- Distribuție inteligentă
- Operații colaborative
- Migrare automată
- Dezactivare fallback
- Ștergere date
- MOBILE-INT-02
- PROD-ARCH-01

### Instrumentare înainte de migrare
- Comparație registry vs legacy (APP-AUTH-03)
- Consumatori fallback
- Exceptii folosite / fără competență
- Autorizări lipsă
- Operații afectate
- Suprafețe demo
- Discrepanțe active

---

## Pachet decizii owner — tabel final

| Decizie | Varianta recomandată | Confirmată | Date afectate | Următorul pas |
|---------|---------------------|------------|---------------|---------------|
| O1 Identitate | A | **NU** | 8 angajați, 7 fără user, Sandu dev-admin | Mapare user planificată Wave R1 |
| O2 Competențe | A (fără migrare acum) | **NU** | 30 relații, Sandu conflict | Confirmare O3 înainte de migrare |
| O3 Sandu | A confirmare umană | **NU** | id=4, 10+ DISC rows | Confirmare manager + owner |
| O4 Exceptii | Regulă restrictivă + reconciliere manuală | **NU** | 39 exceptii, 7+6 Sandu | Inventar excepții formale |
| O5 Autorizări | Separare + fail-closed | **NU** | 16 autorizări, 6 fără auth | Validare RT |
| O6 Suprafețe | Mobile/Operator canonice; tablet TBD; shop-floor fail-closed | **NU** | 5 demo sources | Decizie tablet owner |
| O7 CNC 4020 | Identitate OK; metadata alias | **NU** | MCH-CNC-4020, DISC-MCH-017 | Wave R4 alias |
| O8 Fără user | Operational da, Mobile nu | **NU** | 7 angajați | Provisioning separat |
| O9 Pontaj | Separat de ER | **NU** | 0 evenimente luna curentă | Reguli R1 viitoare |

**Evidență JSON:** `docs/qa/product-system-active-path-isolation-v1/owner_decision_02/owner_decisions.json`

---

## Rezumat gate

| Câmp | Valoare |
|------|---------|
| Decizii confirmate | **0** |
| Decizii amânate | **9** |
| Confirmare angajat necesară | **DA** (Sandu — O3) |
| Validare tehnică necesară | **DA** (proiecție available, machine_type, alocări) |
| Reparare runtime urgentă | **NU** (test = bleed + defect proiecție în test DB; :8001 Sandu e date, nu crash) |
| Implementare autorizată | **NO** |
| PROD-ARCH-01 | **BLOCAT** |
| MOBILE-INT-02 | **BLOCAT** |

---

## Următorul task

**`APP-AUTH-02B-AVAILABLE-PROJECTION-RUNTIME-CLOSURE`**

Motiv: testul proiectiei available este clasificat (FIXTURE_STATE_BLEED + AVAILABLE_PROJECTION_DEFECT); trebuie închis înainte de APP-AUTH-03 parity instrumentation. Deciziile owner rămân 0 CONFIRMATE — nu se deschide migrare.

---

## Opinie sinceră

Inventarul APP-AUTH-02 este solid; footer-ul LOW=0 este **corect** pentru modelul „inventariază conflicte, nu alinierea”. Prioritate owner reală: **O3 Sandu + O4 montaj_led** — restul organizației este deja aliniat registry/JSON. Testul roșu nu implică Sandu pe :8001; indică fragilitate proiecție available în DB partajat pytest — merită APP-AUTH-02B, nu RUNTIME-REPAIR-01 pe date producție.

---

## Checkpoint roadmap

| Task | Status |
|------|--------|
| APP-AUTH-02 | COMPLETE |
| OWNER-DECISION-02 | **COMPLETE (gate documentat, 0 confirmări)** |
| APP-AUTH-02B | **NEXT** |
| APP-AUTH-03 | După 02B + confirmări owner parțiale |
| PROD-ARCH-01 | BLOCAT |

---

## DELIVERY FOOTER

```
Task: OWNER-DECISION-02 — DECIZII_OWNER_RECONCILIERE_DATE_OPERATIONALE_V1
Starting HEAD: b6081c0
Critical discrepancies: 1
High discrepancies: 14
Medium discrepancies: 4
Low discrepancies: 0
Informational discrepancies: 1
Total discrepancies: 20
Available projection test: FIXTURE_STATE_BLEED (+ AVAILABLE_PROJECTION_DEFECT secundar)
Employee identity: AMÂNAT (recomandare A)
Competence authority: AMÂNAT (recomandare A, fără migrare)
Sandu: NECESITĂ CONFIRMARE (recomandare A)
Explicit exceptions: AMÂNAT (reconciliere manuală)
Authorizations: AMÂNAT (separare + fail-closed)
Execution surfaces: AMÂNAT (tablet TBD owner)
CNC 4020: AMÂNAT (identitate OK)
Employees without user: AMÂNAT (operational da, Mobile nu)
Attendance: AMÂNAT (separat ER)
Decisions confirmed: 0
Decisions deferred: 9
Employee confirmation required: YES
Technical validation required: YES
Runtime repair required: NO
Implementation authorized: NO
PROD-ARCH-01: BLOCKED
MOBILE-INT-02: BLOCKED
Next task: APP-AUTH-02B-AVAILABLE-PROJECTION-RUNTIME-CLOSURE
Code changed: NO
DB changed: NO
Commit: YES
Commit hash: <post-commit>
Push: NO
PR: NO
Verdict: OWNER_DATA_RECONCILIATION_PARTIAL_REMAIN_BLOCKED
```
