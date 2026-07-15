# OWNER-DECISION-06 — Operational flexibility and collaboration contract v1

**Task:** `OWNER-DECISION-06` — `OPERATIONAL_FLEXIBILITY_AND_COLLABORATION_CONTRACT_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `02b5981`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `OWNER_OPERATIONAL_FLEXIBILITY_CONTRACT_CONFIRMED_READY_FOR_ARCH_PLAN`  
**Next:** `PROD-FLEX-ARCH-01-FLEXIBLE-TASK-CLAIM-PARTICIPATION-AND-PROGRESS-PLAN`

**Scope:** Owner decision / docs only. No code, DB, UI, Sandu, eligibility, assignment, or implementation changes.

**Upstream:** PROD-FLEX-INT-01 @ `02b5981` — `PROD_FLEX_INT_01_AUDIT_READY_FOR_OWNER_DECISIONS`

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/owner_decision_06/` (18 JSON artifacts)

---

## Executive summary

Owner confirmed the **operational flexibility contract** (D1–D24) on the basis of the accepted audit. Product System remains **clean** (0 employee IDs). Claim and manual assignment stay. Collaboration, help, and quantity progress are **contract targets**, not implemented. **D6** is confirmed as **target** with **current debt** documented (`_has_active_session_by_other`). **Sandu reconciliation (APP-AUTH-06G) remains PAUSED.**

**Complete authority:** B — principal operator **or** manager.  
**Quantity progress:** MIXED model.  
**Roles:** PRINCIPAL + HELPER only for now.

---

## Prior audit integrity check

### 1. Named employee finding (preserved explicitly)

Prior footer said `Named employees in runtime rules: 1` **without naming the person, file, or classification.** This gate corrects that.

| ID | Who | File | Classification | Affects production? |
|----|-----|------|----------------|-------------------|
| NE-01 | **Putaru Sandu** (name strings) | `backend/services/dev_employee_mobile_sandu_fixture_service.py` L38–41 | **DEV_FIXTURE_TEST_ONLY** | NO |
| NE-02 | **employee_id = 4** (Sandu DB convention) | `backend/services/parity_observe/sandu.py` L18–19 | **OBSERVE_ONLY_HELPER** (flags-gated) | NO |
| NE-03 | Putaru Sandu + others | `backend/seeds/seed_operational_workforce_registry.py` | **SEED_DATA** (12 operation name groups) | Only after seed |
| NE-04/05 | Putaru Sandu probe constant | `mobile_t01` / `mobile_int_01` gate scripts | **QA_SCRIPT_HELPER** | NO |

**Confirmed absent:** no `if employee == Sandu` in eligibility, claim, assignment, or readiness production services.

Detail: `named_employee_runtime_finding.json`

### 2. JSON deliverable count (21 vs 19)

| Metric | Value |
|--------|-------|
| Prompt required | **21** JSON |
| Prior report declared | **19** (footer error) |
| Actual on disk | **21** — all present |
| Gap | **NONE** — `REPORTING_ERROR_IN_PRIOR_FOOTER_ONLY` |

Detail: `prior_audit_deliverable_reconciliation.json`

---

## Architectural truth (owner accepted)

```text
Product System:     CURAT — 0 employee IDs, 0 headcount rigid
Eligibility:        POATE INTOARCE MAI MULTI ANGAJATI
Claim:              EXISTA
Assignment:         SINGULAR IN EXECUTION PLAN (principal coordinator)
Execution Reality:  SUPORTA MAI MULTE SESIUNI
Mobile:             INDIVIDUAL-ONLY (policy + UX)
Ajutor:             LIPSESTE (contract confirmed for later)
Progres cantitativ: LIPSESTE (contract MIXED confirmed)
Blocaj principal:   claim + active session ascunde taskul colegilor
```

**Separation confirmed:**

```text
coordonator / assignee principal
!= participanti efectivi
!= sesiuni individuale
!= progresul operatiei
```

---

## D1–D24 decisions

| ID | Status | Note |
|----|--------|------|
| D1 | CONFIRMED | READY without assignment |
| D2 | CONFIRMED | Eligibility → visibility |
| D3 | CONFIRMED | eligible ≠ assigned ≠ claimed ≠ participating |
| D4 | CONFIRMED | No auto-dispatch |
| D5 | CONFIRMED | Manual assignment remains |
| D6 | CONFIRMED_TARGET_CURRENT_DEBT | Claim must not block collaboration — fix in arch plan |
| D7 | CONFIRMED | Principal operator optional |
| D8 | CONFIRMED | Participants 0..N |
| D9 | CONFIRMED_CONTRACT_MINIM | Help adds participants |
| D10 | CONFIRMED | Help does not reassign |
| D11 | CONFIRMED | Own session per participant |
| D12 | CONFIRMED | Stop own work ≠ complete operation |
| D13 | CONFIRMED | Progress belongs to operation |
| D14 | CONFIRMED | PS forbids employee IDs |
| D15 | CONFIRMED_TARGET | PS may declare parallel/progress/collaboration — not impl now |
| D16 | CONFIRMED | recommended_people non-blocking |
| D17 | CONFIRMED | minimum_people only for real rules |
| D18 | CONFIRMED | Concrete count is runtime |
| D19 | CONFIRMED | Availability/workload runtime only |
| D20 | CONFIRMED | Entry/exit without plan recompile |
| D21 | CONFIRMED | Snapshot freezes requirement not team |
| D22 | CONFIRMED | Operation complete ≠ contribution |
| D23 | CONFIRMED | Classify nominal references — see NE-* |
| D24 | CONFIRMED | No dispatch before foundation |

**Supplemental:** Complete authority **B** · Quantity progress **MIXED** · Roles **PRINCIPAL_HELPER**

Detail: `owner_decision_package_d1_d24.json`

---

## Contract summaries

### READY

Task may be READY without assignee. Assignment is not a general readiness gate. Exceptions reserved for explicit locks.

### Eligibility

Multi-employee list; filter for visibility; not auto-dispatch. Final competence authority per OWNER-DECISION-05.

### Claim / assignment / participation

- **CLAIM** — eligible self-take (implemented)
- **ASSIGN** — manager principal designation (implemented)
- **PARTICIPATION** — effective work via session (partial)
- **SESSION** — individual interval (backend yes, mobile primary-only)

### Help

Minimal contract confirmed; **not** `TaskClarificationRequest`. Adds participant; does not reassign.

### Sessions / stop / complete

- Stop own work → session only
- Complete operation → principal **or** manager (B); helpers end contribution only

### Progress / quantity

MIXED: `quantity_total/completed/unit` when natural unit exists; else status/percent.

### Forty letters

CONFIRMED flexible scenario — no fixed 2/4/6/10 team requirement.

### Boundaries

| Layer | Owns |
|-------|------|
| Product System | operations, skills, machines, deps, declarative collaboration/progress hints |
| Execution Plan | task graph, single principal assignee, readiness inputs |
| Runtime allocation | claim, assign, eligibility filter |
| Execution Reality | sessions, participants, progress, help (target) |

### Sandu

**PAUSED.** General contract first. `SK_PRINT_OPERATOR` = test data. Welding/mounting = real competences; correction needs separate GO.

### Concurrency (principles)

- Prevent double principal claim
- Allow multiple participant sessions
- Do not reuse claim lock to block helper join
- No duplicate active session same employee same operation
- Help accept idempotent where reasonable

### Attendance

Attendance (prezență) ≠ work session (timp pe operație). No payroll/commercial costing from this contract.

---

## Blocked scope

Implementation, DB, UI, Sandu DB, auto-dispatch, parity enforcement, removal of current D6 guard — all blocked. See `blocked_scope.json`.

---

## Next step

**PROD-FLEX-ARCH-01-FLEXIBLE-TASK-CLAIM-PARTICIPATION-AND-PROGRESS-PLAN** — plan only, no code.

---

## Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Nota | **9/10** |
| Poziție | Post PROD-FLEX-INT-01 → contract confirmed → arch plan next |
| Direcție | **~78%** |
| Model simplu | YES — post/competente/utilaje/zone; PS fără persoane |
| Auto-dispatch evitat | YES |
| DB prematură evitată | YES |
| Dead pieces | Shop Floor mock; D6 debt; mobile individual-only |
| Forbidden scope | RESPECTAT |

---

## Honest opinion

Auditul era solid arhitectural; singurele slăbiciuni de integritate erau **footer-ul JSON (19 vs 21)** și **lipsa de explicitare Sandu**. Contractul nu cere rescriere Product System — cere **strat runtime** pentru participare, ajutor și progres, cu **assignee** reinterpretat ca **coordonator principal optional**, nu proprietar exclusiv. Următorul pas trebuie să fie plan, nu tabele.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Prior audit named employee finding | Putaru Sandu — dev fixture + observe helper id=4 (see NE-*) |
| Prior audit expected JSON | 21 |
| Prior audit actual JSON | 21 |
| Prior audit delivery gap | EXPLAINED (footer typo) |
| Decisions total | 24 |
| Decisions confirmed | 24 |
| Decisions requiring owner | 0 |
| READY independent of assignment | CONFIRMED |
| Eligible distinct from assigned | CONFIRMED |
| Default flow | READY_ELIGIBLE_CLAIM_OR_MANUAL_ASSIGN |
| Auto-dispatch | REJECTED_FOR_NOW |
| Principal operator | OPTIONAL |
| Participant cardinality | 0..N |
| Operational roles | PRINCIPAL_HELPER |
| Help adds participant | CONFIRMED |
| Help reassigns task | NO |
| Own session stop | SEPARATE |
| Operation completion | SEPARATE |
| Complete authority | B |
| Progress owner | OPERATION |
| Quantity progress | MIXED |
| Product System employee IDs | FORBIDDEN |
| Concrete people count owner | RUNTIME |
| Frozen snapshot contains concrete team | NO |
| Forty-letter flexible scenario | CONFIRMED |
| Sandu reconciliation | PAUSED |
| Code changed | NO |
| DB changed | NO |
| Next task | PROD-FLEX-ARCH-01-FLEXIBLE-TASK-CLAIM-PARTICIPATION-AND-PROGRESS-PLAN |
| Verdict | OWNER_OPERATIONAL_FLEXIBILITY_CONTRACT_CONFIRMED_READY_FOR_ARCH_PLAN |
