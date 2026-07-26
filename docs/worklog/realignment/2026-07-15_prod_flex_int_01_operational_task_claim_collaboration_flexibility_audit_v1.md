# PROD-FLEX-INT-01 — Operational task claim and collaboration flexibility audit v1

**Task:** `PROD-FLEX-INT-01` — `OPERATIONAL_TASK_CLAIM_AND_COLLABORATION_FLEXIBILITY_AUDIT_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `5930efc`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `PROD_FLEX_INT_01_AUDIT_READY_FOR_OWNER_DECISIONS`  
**Next:** `OWNER-DECISION-06-OPERATIONAL-FLEXIBILITY-AND-COLLABORATION-CONTRACT`

**Scope:** Read-only audit — no code, DB, Product System, Execution Plan, task, Sandu, eligibility, or implementation changes.

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/prod_flex_int_01/` (19 JSON artifacts)

**Upstream:** MOBILE-T06 claim policy · APP-AUTH-06F Sandu plan (parallel, do not conflate)

---

## Executive answer

**Poate WorkOS susține fluxul țintă?** **PARȚIAL — da ca fundație, nu ca produs complet.**

| Etapă țintă | Stare |
|-------------|-------|
| Task READY (fără assignment) | **PARTIAL** — operator: `eligible`; mobile per-angajat: `unassigned` până la claim |
| ELIGIBLE | **IMPLEMENTED** — registry skill/explicit/hybrid |
| PRELUARE (claim) | **IMPLEMENTED** — MOBILE-T06, lock concurrency |
| ASSIGN manual manager | **IMPLEMENTED** — `PATCH .../assign` |
| Start singur | **IMPLEMENTED** — start assigned / start-from-available |
| AJUTOR | **NOT_IMPLEMENTED** |
| PARTICIPANTI multipli | **PARTIAL** — `execution_reality` multi-session; mobile blochează join |
| SESIUNI individuale | **IMPLEMENTED** backend; mobile doar `primary` |
| PROGRES cantitativ (40 litere) | **NOT_IMPLEMENTED** |
| COMPLETE operatie | **PARTIAL** — boolean task când toate sesiunile închise |

**Concluzie:** Direcția `READY → ELIGIBLE → PRELUARE → AJUTOR → PARTICIPARE` **poate fi construită peste sistemul existent**, dar **nu fără decizii owner (D1–D24)** și **fără remedieri la join/help/progress** — nu e nevoie de rescriere Product System pentru persoane.

---

## Owner truth alignment

| # | Principiu | Audit |
|---|-----------|-------|
| 1 | Aplicația maleabilă | **DA** la assignment/sessions — **NU** la quantity/help |
| 2 | Angajat = post + skills + utilaje + zone | **DA** — Operational Registry + `/employees` |
| 3 | Product System fără persoane nominale | **CONFIRMAT** — 0 `employee_id` |
| 4 | Fără hardcode IDs/echipe/număr rigid PS | **CONFIRMAT** în PS; rigiditate în plan `assigned_employee_id` |
| 5 | 1 / N angajați / ajutor ulterior | **PARTIAL** — N doar prin API reality, nu mobile |
| 6 | Fără auto-dispatch agresiv | **CONFIRMAT** — nu există motor |
| 7 | Flux READY→ELIGIBLE→CLAIM→SESSIONS | **PARTIAL** |
| 8–15 | Manager assign, claim, participanți, sesiuni, progres operație | Vezi workstreams |

---

## WORKSTREAM 1 — Product System

**Inspectat:** `product_definition_builder_service`, `execution_plan_v2_materialize_service`, `mini_module_registry_volumetric_v2`, contract docs volumetric.

| Întrebare | Răspuns |
|-----------|---------|
| Persoane nominale? | **NU** |
| Stabilește număr oameni? | **NU** |
| Numere fixe hardcodate? | **NU** în compiler |
| Roluri fixe blochează execuția? | Roluri **operation_code** / `process_type` — nu persoane |
| Individual-only declarat? | **NU** structurat |
| Lucru paralel? | **DOC_ONLY** (`VOLUMETRIC_LETTERS_MACHINE_ASSIGNMENT.md`) |
| Unitate progres / cantitate? | **NU** pe task materializat |
| Snapshot înghețat | Cerințe operaționale + graf — **fără echipă** |

### Tabel obligatoriu (extras)

| Fișier/model | Câmp/regulă | Dinamic | Hardcodat | Autoritate corectă | Risc |
|--------------|-------------|---------|-----------|-------------------|------|
| `ProductDefinitionOperationRole` | `operation_code` | Da | Nu | Da | LOW |
| `operational_tasks[]` materializat | `process_type`, `machine_type`, `depends_on` | Da | Nu | Da | LOW |
| Contract doc T06/T07 | operator role labels | Nu | Da (doc) | Referință | MEDIUM drift |

**Principiu verificat:** Product System definește operație + skill/post/utilaj — **nu decide cine lucrează**. **PASS.**

---

## WORKSTREAM 2 — Execution Plan

| Întrebare | Răspuns |
|-----------|---------|
| Un singur `assigned_employee_id`? | **DA** — cardinalitate 0..1 |
| Semnificație câmp | **Shortcut legacy + coordonator plan** — nu proprietar exclusiv runtime |
| Plan fără angajat? | **DA** |
| READY fără assignment? | **DA** (vedere operator) |
| Assignment în snapshot înghețat? | **NU** — doar `tasks_json` operațional mutabil |
| Schimbare assignment modifică snapshot identitate? | **NU** (MOBILE-T06) |
| Participanți multipli pe plan? | **NU** |
| min/recommended people? | **NU** |
| Progres cantitativ? | **NU** |

---

## WORKSTREAM 3 — READY și dependențe

**Serviciu canonic:** `task_readiness_service.py`

**READY azi** = `readiness_status: eligible` când:
- predecesori satisfăcuți
- materiale neblocante
- porți pregătire (CNC/vinyl/template) OK
- **nu** depinde de assignment în vederea operator (`employee_id=None`)

**Cu `employee_id`:** task neatribuit → `unassigned`, `is_startable: false` — intentional până la claim.

| Suprafață | READY meaning | Sursă | Diferență | Risc |
|-----------|---------------|-------|-----------|------|
| Operator / Execution | eligible global | `evaluate_all_task_readiness` | startable fără assignee | MEDIUM |
| Employee Mobile | eligible doar dacă assigned=self | truth + readiness | vocabular | LOW |
| Available pool | eligible + unassigned + registry | `list_available_tasks` | nu e etichetat READY | MEDIUM |
| Shop Floor | mock fallback | `useShopFloorData` | non-truth | HIGH |

**Calculat, nu stocat.** **Fără mock în backend readiness.**

---

## WORKSTREAM 4 — Eligibility

**Serviciu:** `operational_registry_service.py` — moduri `skill | explicit | hybrid`.

- **Filtru** pentru pool available — nu auto-assign
- **Multi-angajat:** `get_eligible_employees_for_operation` → listă
- **Boolean** — fără ranking
- **Mapping explicit** poate exclude competent uncatalogued (risc owner S3:B)
- **Sandu:** doar dev fixture + parity observe — **fără logică specială producție**

---

## WORKSTREAM 5 — Available task și claim

| Concept | Clasificare |
|---------|-------------|
| Claim real | **IMPLEMENTED** |
| Self-assignment | **IMPLEMENTED** |
| Preluare task READY neatribuit | **IMPLEMENTED** |
| Concurrency | **IMPLEMENTED** (MOBILE-T06) |
| Claim blochează alți participanți în pool | **CONTRADICTORY** vs D6 |
| Unclaim | **NOT_IMPLEMENTED** |
| Shop Floor claim | **NOT_IMPLEMENTED** / mock |

---

## WORKSTREAM 6 — Assignment manual

**3 căi mutație:** manager assign · claim-only · start-from-available (assign+start).

- **Reassign:** da (manager, `allow_reassign=True`) înainte de finalizare
- **Unassign:** **NU** (doar rollback intern start eșuat)
- **Istoric:** `assignment_source`, `assignment_updated_at`
- **Conflict:** 409 + lock per `(order_id, task_id)`

---

## WORKSTREAM 7 — Participanți multipli

- **Reality:** 0..N sesiuni / `task_id`; `role: primary|helper`; `session_type: work|assist`
- **Plan:** 0..1 assignee
- **Mobile start:** mereu `role=primary`
- **Available pool:** ascunde task dacă alt angajat are sesiune activă
- **Blueprint:** `active_workers`, `participants_count` — derivat

**Verdict:** infrastructură **PARTIAL** — produs **NOT_IMPLEMENTED**.

---

## WORKSTREAM 8 — Cerere de ajutor

**NOT_IMPLEMENTED.**

Există doar `TaskClarificationRequest` (clarificare plan preparer) — **nu** shop-floor help.

---

## WORKSTREAM 9 — Work sessions

| Întrebare | Răspuns |
|-----------|---------|
| Sesiuni / operație | 0..N |
| Active simultan | Da (teste) |
| Angajați diferiți | Da |
| Stop fără complete (mobile) | **NU** — doar complete/pause |
| Stop fără complete (operator API) | **DA** — `end-task` fără `completion_fields` |
| Complete închide operatie | Când **nu** mai există sesiuni active |

**T06:** policy `MOBILE_T06_COMPATIBIL_NUMAI_CU_EXECUTIE_INDIVIDUALA`.

---

## WORKSTREAM 10 — Progres

- **Per task boolean** — nu per angajat cantitativ
- **Blueprint `%`** = task-uri done/total — **nu** 17/40 litere
- **Complete** orice participant cu sesiune activă
- **Risc:** singurul activ care completează → task `done` (corect); cu helper activ → rămâne `in_progress` (testat)

---

## WORKSTREAM 11 — Număr oameni

Vezi `people_count_authority_matrix.json`.

**Product System nu trebuie să dețină** eligibili/disponibili/participanți — **confirmat**.

**`minimum_people` / `recommended_people`:** absente — model țintă **prematur** exceptând display recomandat.

---

## WORKSTREAM 12 — Exemplu 40 litere

Vezi `forty_letters_scenario.json`.

**Azi:** claim solo funcționează; 2+ oameni necesită `ExecutionRealityService.start_task` direct — **nu** flux mobile; progres 17/40 **imposibil**.

---

## WORKSTREAM 13 — Anti-hardcoding

| Count | Value |
|-------|-------|
| employee_id în Product System | **0** |
| Named employees runtime rules | **1** (Sandu dev fixture) |
| Seed explicit names | **12** operation groups |
| Fixed worker counts | **0** |

---

## WORKSTREAM 14 — UI reality

| Rută | Adevăr | Lipsește |
|------|--------|----------|
| `/employees` | LIVE registry | workload |
| `/execution/:id` | LIVE | help, quantity |
| `/employee-mobile-v2` | LIVE claim/start | help, join helper |
| `/shop-floor` | MOCK risk | tot fluxul real |
| `/tablet` | PARTIAL | claim parity |

---

## WORKSTREAM 15 — Contract minim

Vezi `simple_target_contract_assessment.json`.

**REQUIRED_NOW:** eligibili, sesiuni, cantitate/progres, participanți, help request, operator principal optional policy.

---

## D1–D24 decision package

Vezi `architectural_decision_package.json`.

**Contradicție dovedită azi:** **D6** — claim/active session blochează intrarea în available pool.

**Recomandare:** Owner confirmă D1–D24; **pause APP-AUTH-06G** până la contract general (Sandu rămâne sub observe-only).

---

## Risks (top)

1. **R9** — claim blochează participanți (HIGH)
2. **R1/R2** — assignment singular vs participare (HIGH)
3. **R15** — Shop Floor mock (HIGH)
4. **R13 target** — lipsă quantity progress (HIGH pentru litere)

---

## Gaps

- Help request
- Join-as-helper UX + API
- Quantity `progress_unit` / `completed_quantity`
- Stop-own-work distinct de Complete operation (mobile)
- Unassignment operator
- `collaboration_mode` / `parallelizable` în Product System output
- Workload / availability

---

## Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Nota audit vs roadmap | **8/10** |
| Poziție pas | Post MOBILE-T06 / APP-AUTH-06F — pre contract colaborare |
| Direcție stabilită | **~72%** — claim OK; colaborare/progres lipsesc |
| Dead pieces | Shop Floor mock ca „truth”; OWNER-DECISION-01 amânat 20/24 — superseded parțial de acest audit |
| Forbidden scope | **RESPECTAT** — zero code/DB |
| Deviație reală | **DA** — multi-session backend vs mobile individual policy |
| Sandu reconciliation pause? | **DA RECOMANDAT** — prioritate contract general OD-06 |

---

## Honest opinion

WorkOS **nu e blocat arhitectural** pentru flexibilitate operațională: Product System e curat, claim-ul e real, registry-ul poate lista N eligibili, Reality suportă sesiuni multiple. **Rigiditatea e în stratul produs:** un assignee pe plan, mobile forțat `primary`, pool available care respinge colegii cu sesiune activă, zero cantitate, zero help. Implementarea greșită a „ajutorului” ca **reassign** ar rupe T06 și frozen spine — de aceea auditul cere **OWNER-DECISION-06** înainte de ORICE motor de participare.

---

## Commands

```text
Read-only grep/read — no tests run (audit scope)
```

---

## Delivery footer

| Field | Value |
|-------|-------|
| Employee IDs in Product System | 0 |
| Named employees in runtime rules | 1 |
| Fixed worker counts | 0 |
| READY without assignment | PARTIAL |
| Eligibility returns multiple employees | YES |
| Employee self-claim | IMPLEMENTED |
| Manager manual assignment | IMPLEMENTED |
| Current assignment cardinality | 1 |
| Current participant cardinality | 0..N sessions (1 plan assignee) |
| Help request | NOT_IMPLEMENTED |
| Multiple employees per operation | PARTIAL |
| Multiple sessions per operation | YES |
| Stop own work separate | PARTIAL |
| Operation complete separate | PARTIAL |
| Quantity progress | NO |
| Product System owns | operations, skills, dependencies |
| Execution Plan owns | task graph, single assignee, readiness inputs |
| Runtime allocation owns | claim, assign, eligibility filter |
| Execution Reality owns | sessions, time, active_workers |
| Architectural decisions prepared | 24 |
| Code changed | NO |
| DB changed | NO |
| Commit | YES (pending) |
| Push | NO |
| PR | NO |
| Verdict | PROD_FLEX_INT_01_AUDIT_READY_FOR_OWNER_DECISIONS |
