# APP-AUTH-03 — Plan de instrumentare paritate runtime (Registry vs Legacy)

**Task:** APP-AUTH-03 — RUNTIME_PARITY_INSTRUMENTATION_PLAN_V1  
**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `3a9c9ea`  
**Verdict:** `APP_AUTH_03_PARITY_INSTRUMENTATION_PLAN_READY`  
**Implementation authorized:** PLAN_ONLY  
**Next task:** APP-AUTH-04-PARITY-CONTRACT-AND-TEST-FOUNDATION  

---

## Verdict

Plan complet de instrumentare OBSERVE_ONLY pentru paritatea registry vs JSON legacy, fără modificări de cod, DB, UI sau runtime. Toate domeniile P1–P12 sunt acoperite; consumatorii și scriitorii sunt inventariați; contractele de evenimente, metricile, fingerprint-ul, confidențialitatea, fluxul Sandu, rollout-ul și gate-urile I1–I8 sunt definite.

---

## Repository safety

- **Cod:** NEATINS  
- **DB:** NEATINS — fără migrări, fără tabele noi  
- **UI:** NEATINS  
- **Endpointuri:** NEATINS  
- **Date runtime:** NEATINS  
- **Loguri în cod:** NEATINS  
- **Joburi programate:** NEATINS  
- **Eligibilitate/alocare:** NEATINS  

---

## Starting HEAD

`3a9c9ea` — OWNER-DECISION-03 (22/22 CONFIRMATE)

**Lanț acceptat:** APP-INT-01 → APP-AUTH-01 → APP-AUTH-02 → OWNER-DECISION-02 → APP-AUTH-02B → APP-AUTH-02C → MODULE-INT-01 (pauză) → OWNER-DECISION-03

**Runtime de încredere:** backend `:8001`, frontend `:3000`, `CANONICAL_BACKEND_PROCESS`

---

## Decizii owner acceptate (A1–A22)

Toate **CONFIRMATE** — nu se redeschid. Rezumat pentru instrumentare:

| # | Direcție canonică |
|---|-------------------|
| A1 | `employees.id` = identitate operațională |
| A2 | `employees.user_id` = legătură autentificare |
| A3 | `EmployeeRecord` = extensie HR 1:1 |
| A4 | `/employees` = agregator/editor peste registre |
| A5 | Catalog competențe + relație angajat–competență = țintă canonică |
| A6 | JSON legacy = sursă tranzitorie observabilă |
| A7 | Sandu necesită reconciliere umană |
| A8 | Mapările explicite ≠ competență automată |
| A9 | Autorizarea separată de competență |
| A10 | Catalog centre de lucru canonic |
| A11 | `machines` = identitate resurse concrete |
| A12 | Relație angajat–resursă = țintă autorizări |
| A13 | Șablon/tip operație = cerințe |
| A14 | `task_readiness_service` = pregătire dependențe |
| A15 | Un singur serviciu va deține alocarea |
| A16 | `assigned_employee_id` compatibil execuție individuală |
| A17 | ExecutionReality = Start/Complete |
| A18 | Mobile + Operator = servicii canonice |
| A19 | Tablet → mod chioșc peste servicii canonice |
| A20 | Shop Floor = proiecție |
| A21 | Pontaj separat |
| A22 | **Nu** se autorizează migrarea acum — doar instrumentare + plan |

**Blocat explicit:** migrare date, modificare competențe/autorizări/mapări, ștergere JSON legacy, blocare fallback-uri, distribuire inteligentă, execuție colaborativă, PROD-ARCH-01, MOBILE-INT-02, MODULE-RUNTIME-01, MODULE-ARCH-01.

---

## Scope boundaries

**În scope:** proiectare instrumentare, contracte, metrici, test plan, runtime proof plan, rollout gates.  
**Out of scope:** implementare, migrări, UI manager, conectare la `/modules`, Module Chain.

---

## Principiul central

```
Rezultat operațional curent
+ Rezultat canonic calculat în umbră
+ Comparație
+ Eveniment de discrepanță
+ Metrici
+ Raport pentru manager
```

Instrumentarea **nu** blochează operații, **nu** schimbă eligibilitatea, **nu** modifică răspunsul Mobile, assignment, sesiuni sau pontaj.

**Mod autorizat:** OBSERVE_ONLY. COMPARE_AND_WARN și ENFORCE_CANONICAL sunt planificate dar **neactivate**.

---

## Arhitectură instrumentare

Pipeline de citire în paritate (ordine obligatorie):

1. Citește rezultatul operațional curent  
2. Calculează rezultatul canonic în umbră  
3. Compară  
4. Emite eveniment de discrepanță (dacă e cazul)  
5. Returnează rezultatul operațional **neschimbat**  
6. Măsoară fallback-ul dacă s-a folosit  

### Componente conceptuale

| Componentă | Responsabilitate | Intrări | Ieșiri | Persistență | Consumatori |
|------------|------------------|---------|--------|-------------|-------------|
| ParityReadService | Orchestrează citire + umbră + comparație | context consumator, employee_id, operation_code | rezultat operațional, umbră, evenimente | logs P1 | toți evaluatorii |
| CompetenceParityEvaluator | P2 competențe | registry, legacy JSON, cerințe operație | COMPETENCE_PARITY_DIFFERENCE | logs | EventPublisher, Sandu report |
| AuthorizationParityEvaluator | P3 autorizări | resource/wc auth, explicit mappings | AUTHORIZATION_PARITY_DIFFERENCE | logs | EventPublisher, EligibilityShadow |
| WorkcenterParityEvaluator | P4 centre | catalog, operații, utilaje | WORKCENTER_PARITY_DIFFERENCE | logs | EventPublisher |
| ResourceParityEvaluator | P5 utilaje/resurse | machines, registry, mock | RESOURCE_PARITY_DIFFERENCE | logs | EventPublisher |
| ExplicitMappingUsageTracker | P6 mapări | operation_employee_authorizations | EXPLICIT_MAPPING_USED + clasificare | logs | EventPublisher, Sandu |
| EligibilityShadowEvaluator | P7 eligibilitate umbră | operational vs canonical rules | ELIGIBILITY_PARITY_DIFFERENCE | logs | EventPublisher, SurfaceParity |
| LegacyFallbackUsageTracker | fallback-uri | consumer path, fallback trigger | LEGACY_FALLBACK_USED | logs | MetricsProjection |
| ExecutionSurfaceParityEvaluator | P8 suprafețe | Mobile/Operator/Tablet/ShopFloor | EXECUTION_SURFACE_PARITY_DIFFERENCE | logs | EventPublisher |
| AssignmentWriterObserver | P9 alocare | writer, before/after | ASSIGNMENT_WRITER_OUTSIDE_AUTHORITY | logs | EventPublisher |
| SessionParityEvaluator | P10 sesiuni | ExecutionReality vs alocare | SESSION_AUTHORITY_DIFFERENCE | logs | EventPublisher |
| AttendanceComparisonObserver | P11 pontaj | prezență vs sesiune | ATTENDANCE_EXECUTION_DIFFERENCE | logs | Sandu report |
| ParityEventPublisher | evenimente versionate | raw discrepancy | event + fingerprint + dedup | logs → DB P4 | Metrics, Report |
| ParityMetricsProjection | agregare metrici | event stream | counters/gauges | metrics backend | alerting, manager |
| ReconciliationReportService | P12 Sandu + manager | toate domeniile | fișă reconciliere | artifact → DB P4 | manager, Sandu flow |

Denumiri finale vor fi verificate la implementare contra stilului repository (`operational_registry_service`, `execution_task_assignment_service`).

---

## P1 — Identitate angajat

**Compară:** `employees.id`, `employees.user_id`, EmployeeRecord, pontaj actor, sesiune, identitate Mobile.  
**Detectează:** angajat fără utilizator (7/8 baseline), utilizator multi-angajat, HR record lipsă/duplicat, actor ≠ angajat.  
**Status:** READY — baseline APP-AUTH-02 `discrepancy_inventory.json`.

---

## P2 — Competențe

**Compară:** catalog competențe, `employee_skill_authorizations`, `employees.skills` JSON, mapări explicite, cerințe operație, listă `/employees`.  
**Detectează:** registry-only, legacy-only, cod/denumire diferită, competențe amestecate cu roluri/autorizări.  
**Caz Sandu:** registry `SK_PRINT_OPERATOR` vs legacy 5 coduri — `DISC-COMP-001` HIGH.  
**Status:** READY

---

## P3 — Autorizări

**Compară:** `employee_resource_authorizations`, workcenter auth, `operation_employee_authorizations`, cerințe operație, utilaj concret.  
**Detectează:** operare fără autorizare, expirată, competență folosită ca autorizare, mapare ocolește autorizarea.  
**Baseline:** 16 resource auth, 6 override fără autorizare.  
**Status:** READY

---

## P4 — Centre de lucru

**Compară:** catalog centre, operații, utilaje, angajați, `machine_type`, constante frontend.  
**Concepte explicite:** WC_CNC, WC_CNC_ROUTING, CNC router, Modelare cant, Asamblare, Print, Laminare, Laser, Sudură.  
**Status:** READY

---

## P5 — Utilaje și resurse

**Compară:** `machines`, registry resources, autorizări, cerințe, Shop Floor, mock specs.  
**CNC 4020:** `IDENTITY_ALIGNED_METADATA_PARTIAL` (APP-AUTH-02).  
**Status:** READY

---

## P6 — Mapări explicite

**Clasificări:** SELECTIE_DINTRE_ELIGIBILI, RESTRANGERE_ELIGIBILITATE, COMPATIBILITATE_TRANZITORIE, ADAUGARE_FARA_COMPETENTA, ADAUGARE_FARA_AUTORIZARE, SCOP_NECUNOSCUT.  
**Baseline:** 39 override, 7 fără competență, 6 fără autorizare.  
**Status:** READY

---

## P7 — Eligibilitate (calcul în umbră)

**Operational:** `OperationalRegistryService.check_employee_operation_eligibility` (hybrid/skill/explicit).  
**Canonic simulat:** reguli stricte competență + autorizare fără bypass explicit neconfirmat.  
**Rezultate:** ALINIAT_ELIGIBIL, ALINIAT_NEELIGIBIL, OPERATIONAL_ELIGIBIL_CANONIC_NEELIGIBIL, OPERATIONAL_NEELIGIBIL_CANONIC_ELIGIBIL, NECALCULABIL_DATE_LIPSA, EXCEPTIE_TRANZITORIE, AUTORIZARE_LIPSA, CERINTA_OPERATIE_LIPSA.  
**Status:** READY

---

## P8 — Suprafețe de execuție

| Suprafață | Autoritate citită | Fallback | Risc |
|-----------|-------------------|----------|------|
| Mobile available/assigned | task truth + registry | none on truth | indirect legacy via hybrid |
| /operator | operator truth + guard | mockData on fail | operator_name legacy |
| /tablet | demo operators | DEMO_OPERATORS | PARALLEL authority |
| /shop-floor | machines + operator | mockData silent | ACTIVE_SILENT_FALLBACK |

**Exclus:** `/modules` — Module Chain pe pistă separată.  
**Status:** READY

---

## P9 — Alocare (observabilitate scrieri)

**Writer canonic:** `execution_task_assignment_service.assign_plan_task`.  
**Observă:** manager assign, Mobile claim, Operator, direct `tasks_json`, seed, tablet demo.  
**Nu unifică** scrierile în acest task.  
**Status:** READY

---

## P10 — Sesiuni și ExecutionReality

**Canonic:** `ExecutionRealityService.start_task` / `end_task`.  
**Detectează:** sesiune fără angajat, actor comun, angajat ≠ alocare, operație neeligibilă, scriere non-canonică.  
**Baseline:** 3 sesiuni active.  
**Status:** READY

---

## P11 — Pontaj

Comparații **informative** only: prezență vs sesiune, absență vs Start, program vs sesiune, total pontaj vs producție.  
**Fără** corecție automată (A21).  
**Status:** READY

---

## P12 — Sandu

Fișă dedicată `employee_id=4`: competențe registry/legacy, autorizări, centre, utilaje, mapări, taskuri, sesiuni, pontaj, utilizator, decizii umane lipsă.  
**Nu** completează automat verdictul.  
**Status:** READY — flux în `sandu_confirmation_flow.json`

---

## Contracte evenimente

12 tipuri versionate `parity_event/v1` — vezi `parity_event_contracts.json`.  
**Exclus:** conectare la `/modules`.

---

## Persistență

| Opțiune | Fază | Autorizare |
|---------|------|------------|
| A — Loguri structurate | P0–P3 | DA (plan) |
| B — Tabelă dedicată discrepanțe | P4+ | NU acum — Gate I4 |
| C — Observability existentă | de evaluat | depinde de autoritate/retenție |

**Recomandare:** A pentru start; B numai după GO owner.

---

## Metrici

20 metrici definite — vezi `parity_metrics_catalog.json`.  
**Praguri alertare:** OWNER_DECISION_REQUIRED — nu se setează arbitrar.

---

## Fingerprint și deduplicare

```
fingerprint = hash(domeniu + employee_id + operation_code + resource_id + canonical_value_hash + transitional_value_hash)
```

- **Nou:** fingerprint nou sau reconciled + valori schimbate  
- **Update:** același fingerprint în fereastră — `last_seen`, `occurrence_count`  
- **Închidere:** reconciled/wont_fix + hash-uri aliniate  
- **Redeschidere:** divergență după close  
- **Anti-spam:** max 1 eveniment/fingerprint/consumator/60s  

---

## Severitate

| Nivel | Exemple |
|-------|---------|
| CRITICAL | Autorizare obligatorie lipsă; identitate greșită în sesiune; operație riscantă neautorizată oferită |
| HIGH | Eligibilitate diferită; mapare fără competență; writer necanonic; suprafețe cu rezultate diferite |
| MEDIUM | Metadata resursă; centru inconsistent; fallback legacy |
| LOW / INFORMATIONAL | Diferențe etichetă; compatibilitate fără impact runtime |

---

## Confidențialitate

| Rol | Poate vedea | Nu poate vedea |
|-----|-------------|----------------|
| Angajat | propriile taskuri operaționale | comparații colegi, scoruri, note HR, autorizări confidențiale |
| Manager | discrepanțe, impact, taskuri afectate | detalii contractuale HR complete |
| HR | legături HR, pontaj permis | dovezi tehnice complete |
| Responsabil tehnic | competențe, autorizări, utilaje, dovezi | date contractuale private |

---

## Proiecție manager (viitoare)

**Rută conceptuală:** `/admin/operational-parity` — **NU** `/modules`.  
**Conținut:** sumar discrepanțe, critice, angajați/operații afectate, mapări, fallback-uri, vechime, status reconciliere, drill-down.

---

## Citire în paritate — consumatori obligatorii

18 consumatori inventariați — `parity_consumer_matrix.json`.  
Prioritate P0: Mobile available, eligibility endpoint.  
Prioritate P1: /employees, /utilaje, registry catalog.

---

## Scriere — observabilitate

14 scriitori inventariați — `parity_writer_matrix.json`.  
Raportează writerii de interzis ulterior: direct `tasks_json`, `employees.skills` JSON, tablet demo.

---

## Feature flags

16 flags — toate `false` în producție până la gate. Vezi `parity_feature_flags.json`.

---

## Performance și siguranță

- Sampling (`parity_sampling_rate`)  
- Feature flags granulare  
- Timeout + circuit breaker pe umbră  
- Batch evaluation pentru scanări Sandu  
- Cache control pe catalog (TTL scurt)  
- Rate limiting pe emitere evenimente  
- Degradare: skip umbră, returnează operațional  
- Fără snapshot-uri HR complete în logs  
- Fără secrete în `metadata_safe`  
- Fără bucle recursive umbră→operațional  

---

## Rollout (planificat, neexecutat)

P0 Contract → P1 Logs dev/test → P2 Umbră Mobile → P3 Consumatori → P4 Manager+DB → P5 Observare → P6 Reconciliere → P7 Migrare GO separat.  
Vezi `parity_rollout_plan.json`.

---

## Test plan

32 scenarii — toate fără mutație operațională în OBSERVE_ONLY. Vezi `parity_test_plan.json`.

---

## Runtime proof plan

14 probe pe `:8001` — Sandu, CNC 4020, Mobile, Operator, Tablet, Shop Floor, Start/Complete, pontaj. Vezi `parity_runtime_proof_plan.json`.

---

## Gate-uri implementare

I1 Contract → I2 dev/test → I3 observe runtime → I4 persistență → I5 manager → I6 Sandu → I7 freeze legacy → I8 migrare.  
**Nu se combină.** Vezi `implementation_gate_matrix.json`.

---

## Decizii owner rămase

1. Durata perioadei de observare (P5)  
2. Praguri alertare metrici  
3. Retenție date (logs vs DB)  
4. GO persistență dedicată (I4)  
5. Cine aprobă discrepanțele (workflow I6)  
6. Acces manager/tehnic/HR (I5)  
7. Rollout pe medii (staging/prod observe)  
8. Momentul freeze legacy writes (I7)  
9. GO migrare (I8)  

---

## Impact asupra roadmap-ului

| Lane | Impact |
|------|--------|
| APP-AUTH | Următorul pas APP-AUTH-04 (contracte + teste foundation) |
| ProductSystem | Cerințe operație — observate în P2/P5, fără modificare |
| Employee Mobile | P2 shadow pe available — fără schimbare răspuns |
| Operator | P3 surface parity |
| Tablet | P3 demo vs canonical — pregătire chioșc A19 |
| Shop Floor | P3 fallback tracking |
| ExecutionReality | P10 session parity |
| Pontaj | P11 separat A21 |
| HR | Acces control în I5/I6 |
| PROD-ARCH-01 | BLOCKED |
| MOBILE-INT-02 | BLOCKED |
| Module Chain | DEFERRED — fără conectare la paritate |

---

## Implementări blocate

Migrare, freeze legacy, source switch, ENFORCE_CANONICAL, PROD-ARCH-01, MOBILE-INT-02, MODULE-RUNTIME-01, MODULE-ARCH-01, `/modules` parity UI.

---

## Next task

**APP-AUTH-04-PARITY-CONTRACT-AND-TEST-FOUNDATION** — poate implementa doar: contracte, feature flags (definite, off), teste. Fără activare producție, fără migrare, fără source switch.

---

## Canonical updates

- `docs/master/workos-e2e/WORKOS_E2E_STATUS.md` — secțiune APP-AUTH-03  
- `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md` — nod APP-AUTH-03  
- Authority debt: 22/22 politică confirmată; paritate runtime = plan READY, implementare APP-AUTH-04

---

## Evidence

`docs/qa/product-system-active-path-isolation-v1/app_auth_03/`:

- `parity_domain_matrix.json`
- `parity_event_contracts.json`
- `parity_metrics_catalog.json`
- `parity_consumer_matrix.json`
- `parity_writer_matrix.json`
- `parity_feature_flags.json`
- `parity_test_plan.json`
- `parity_runtime_proof_plan.json`
- `parity_rollout_plan.json`
- `sandu_confirmation_flow.json`
- `implementation_gate_matrix.json`

---

## Opinie sinceră

Planul este executabil pentru că se sprijină pe evidența APP-AUTH-02 (20 discrepanțe, Sandu, CNC 4020) și pe codul existent (`operational_registry_service`, `execution_task_assignment_service`, `employee_mobile_tasks_service`). Riscul principal nu este tehnic ci de **contaminare**: orice implementare care modifică răspunsul înainte de Gate I7/I8 va invalida observarea. APP-AUTH-04 trebuie să rămână strict foundation (contracte + teste + flags off). Cea mai mare valoare imediată: shadow pe Mobile available + fișa Sandu în P1, pentru că acolo divergența legacy/registry produce efect operațional real fără a fi vizibilă operatorului.

---

## Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Roadmap alignment score | **9/10** |
| Current step | APP-AUTH-03 plan → APP-AUTH-04 foundation |
| În direcția stabilită | **92/100%** |
| Dead pieces | `/modules` Module Chain (HYBRID/static) — explicit exclus; tablet DEMO_OPERATORS — tracked P8 |
| Forbidden scope | confirmat — migrare, PROD-ARCH-01, MOBILE-INT-02, MODULE-RUNTIME-01 |
| Next task foundation-only | APP-AUTH-04 implementează contracte/teste/flags off — nu activează observarea runtime |

---

## Delivery footer

| Field | Value |
|-------|-------|
| Task | APP-AUTH-03 — RUNTIME_PARITY_INSTRUMENTATION_PLAN_V1 |
| Starting HEAD | 3a9c9ea |
| Owner authorities | 22/22 CONFIRMED |
| Parity domains | 12 |
| Consumers inventoried | 18 |
| Writers inventoried | 14 |
| Event contracts | 12 |
| Metrics | 20 |
| Feature flags | 16 |
| Test scenarios | 32 |
| Runtime proof scenarios | 14 |
| Rollout phases | 8 (P0–P7) |
| Implementation gates | 8 (I1–I8) |
| Sandu confirmation flow | READY |
| Identity parity | READY |
| Competence parity | READY |
| Authorization parity | READY |
| Resource parity | READY |
| Eligibility shadow | READY |
| Execution surface parity | READY |
| Assignment writer parity | READY |
| Session parity | READY |
| Attendance comparison | READY |
| Persistence migration | NOT_AUTHORIZED |
| Source switch | NOT_AUTHORIZED |
| Legacy freeze | NOT_AUTHORIZED |
| PROD-ARCH-01 | BLOCKED |
| MOBILE-INT-02 | BLOCKED |
| MODULE-RUNTIME-01 | DEFERRED |
| Implementation authorized | PLAN_ONLY |
| Next task | APP-AUTH-04-PARITY-CONTRACT-AND-TEST-FOUNDATION |
| Code changed | NO |
| DB changed | NO |
