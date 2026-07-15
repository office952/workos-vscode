# PROD-FLEX-ARCH-01 — Flexible task claim, participation and progress plan v1

**Task:** `PROD-FLEX-ARCH-01` — `FLEXIBLE_TASK_CLAIM_PARTICIPATION_AND_PROGRESS_PLAN_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `25e4233`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `PROD_FLEX_ARCH_01_PLAN_READY_REQUIRES_DB_DECISION`  
**Next:** `OWNER-DECISION-07-FLEXIBLE-EXECUTION-IMPLEMENTATION-GATE`

**Scope:** Architecture / docs only. No code, DB, UI, or implementation.

**Upstream:** PROD-FLEX-INT-01 @ `02b5981` · OWNER-DECISION-06 @ `25e4233`

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/prod_flex_arch_01/` (23 JSON artifacts)

---

## Executive summary

Planul arhitectural minimal pentru execuție flexibilă **nu rescrie Product System** și **nu elimină** `assigned_employee_id`. Păstrează **Option A**: assignee = coordonator principal optional, compatibilitate MOBILE-T06. Participarea, ajutorul, progresul și completarea operatiei trăiesc în **Execution Reality**, cu extensie JSON înainte de migrări normalizate.

**Separare centrală confirmată:**

```text
assigned_employee_id     → principal optional / legacy compat
participants           → cine lucrează efectiv (0..N)
work sessions          → timp individual per participant
operation progress     → progres comun (MIXED)
operation complete     → act separat (principal sau manager)
```

**Blocaj curent remediat în plan:** `_has_active_session_by_other` — **nu se elimină**; se separă pool principal claim vs pool helper join.

**9 valuri** FLEX-01 … FLEX-09. **0 migrări DB** pentru MVP; owner gate pentru JSON vs tabele înainte de FLEX-04+.

---

## Principiu general

```text
Product System     → ce operație + cerințe tehnologice
Execution Plan     → task + cerință înghețată + assignee optional
Eligibility        → cine poate executa
Claim/Assign       → coordonare inițială
Participation      → intrare efectivă în lucru
Work Session       → activitate individuală
Operation Progress → progres comun
Execution Reality  → adevăr runtime
```

---

## Workstream summaries

### 1 — Boundary map

Vezi `authority_boundary_map.json`. READY/eligibility/claim există; help/progress/complete operation lipsesc ca entități explicite.

### 2 — assigned_employee_id

**Recommendation: Option A** — păstrat ca principal optional. Nu array, nu deprecare imediată. Detaliu: `assigned_employee_compatibility_plan.json`.

### 3 — Participation model

**Recommendation: HYBRID** — Faza 1 sesiuni existente; Faza 2 `participants_json` pe Execution Reality; tabele DB opțional după owner gate. `participant_model_options.json`.

### 4 — Help request

Contract minim separat de `TaskClarificationRequest`. `help_request_contract.json`.

### 5 — Claim / assignment / join

CLAIM → PRINCIPAL; JOIN → HELPER fără reassign. Lock MOBILE-T06 păstrat. `claim_assignment_join_contract.json`.

### 6 — Available pools

Split:

- disponibile pentru **principal claim**
- **ajutor solicitat** pentru helper join

Nu ștergem guard-ul actual până la FLEX-05. `available_pool_plan.json`.

### 7 — Session semantics

Stop own work ≠ complete operation. Policy la complete: **A + C** (blocare sesiuni active + override manager). `session_semantics_plan.json`.

### 8 — Progress MIXED

Quantity pentru litere; status/percent altfel. `progress_model_plan.json`.

### 9–11 — PS / Plan / Reality contracts

PS declară posibilitatea, nu oamenii. Plan copiază cerința, nu echipa. Reality extinde envelope JSON. Fișiere `*_contract_plan.json`.

### 12 — 40 litere

Flux complet 12 pași în `forty_letters_flow.json` — claim → help → sesiuni → 17/40 → plecări → 40/40 → complete.

### 13–14 — UI și endpoints

Plan conceptual Mobile V2, Operator, Execution Detail. Endpoint-uri noi pentru join, stop, progress, help. `ui_plan.json`, `endpoint_plan.json`.

### 15 — Events

11 tipuri evenimente append-only pe reality. `event_contract.json`.

### 16–17 — Attendance și concurrency

Prezență ≠ sesiune. Matrice 10 curse. `attendance_boundary.json`, `concurrency_matrix.json`.

### 18 — Backward compatibility

**PASS_WITH_ADAPTERS** + feature flags. `backward_compatibility_plan.json`.

### 19 — Implementation waves

9 valuri FLEX-01 … FLEX-09. `implementation_waves.json`.

### 20 — DB decision

**0 migrări** pentru start; JSON extension pe `execution_reality`. Tabele amânate. Owner gate înainte de FLEX-04+. `db_change_decision.json`.

### 21 — Dead pieces

primary/helper parțial folosit; TaskClarificationRequest tentație semantică greșită; field_installation_teams domeniu paralel. `dead_pieces.json`.

---

## Sandu boundary

**PAUSED.** APP-AUTH-06G blocat. Modelul general se aplică ulterior fără excepții `if Sandu`.

---

## Risks (top)

1. Eliminare prematură `_has_active_session_by_other`
2. Confundare assignee cu participanți
3. Repurposing TaskClarificationRequest ca help

---

## Roadmap checkpoint

| Metric | Value |
|--------|-------|
| Nota | **9/10** |
| Poziție | Post OD-06 → arch plan → implementation gate |
| Direcție | **~82%** |
| Model simplu | YES |
| PS fără persoane | YES |
| assigned_employee_id compatibil | YES Option A |
| Auto-dispatch evitat | YES |
| Forbidden scope | RESPECTAT |

---

## Honest opinion

Cea mai sigură cale este **extinderea Execution Reality** fără a atinge snapshotul sau Product System. MOBILE-T06 rămâne fundație; lipsesc doar **pool-uri separate**, **help**, **stop vs complete**, și **progres cantitativ**. Nu începe implementarea fără **OWNER-DECISION-07** care confirmă JSON-first și ordinea valurilor.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Owner decisions accepted | 24/24 |
| assigned_employee_id target | OPTION_A_OPTIONAL_PRINCIPAL |
| Participant model | HYBRID_SESSION_THEN_PARTICIPANTS_JSON |
| Principal cardinality | 0..1 |
| Participant cardinality | 0..N |
| Help request | PLANNED |
| Own session stop | SEPARATE_PLANNED |
| Complete authority | PRINCIPAL_OR_MANAGER |
| Progress model | MIXED |
| Quantity progress scope | Pilot letter assembly + opt-in PS fields |
| Implementation waves | 9 |
| DB changes required (MVP) | 0 |
| DB changes deferred | 2 |
| Backward compatibility | PASS_WITH_ADAPTERS |
| Sandu | PAUSED |
| Code/DB changed | NO |
| Verdict | PROD_FLEX_ARCH_01_PLAN_READY_REQUIRES_DB_DECISION |
