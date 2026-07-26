# OWNER-DECISION-07 — Flexible execution implementation gate v1

**Task:** `OWNER-DECISION-07` — `FLEXIBLE_EXECUTION_IMPLEMENTATION_GATE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `39d24db`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `OWNER_FLEX_EXECUTION_GATE_CONFIRMED_FLEX_01_ONLY`  
**Next:** `FLEX-01-EXECUTION-COLLABORATION-READ-MODEL-FOUNDATION`

**Scope:** Owner decision / docs only. No code, DB, migrations, JSON fields, tables, or UI.

**Upstream:** PROD-FLEX-INT-01 · OWNER-DECISION-06 · PROD-FLEX-ARCH-01 @ `39d24db`

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/owner_decision_07/` (14 JSON artifacts)

---

## Executive summary

Owner confirms **FLEX-01 ONLY** — read models, terminology, projections derived from **existing** data. **No implementation** beyond read-only foundation is authorized.

**Critical owner amendment to arch plan:** `participants_json` is **DEFERRED**, not auto-accepted as persistence. Neither large schema now nor JSON blob authority for all runtime truth.

**FLEX-01 read model:** **Option B** — principal from `assigned_employee_id` + workers/helpers from sessions (read-only).

**FLEX-02+ blocked** until `PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY`.

---

## G1–G10 decisions

| ID | Decision | Status |
|----|----------|--------|
| G1 | FLEX-01 GO only | **CONFIRMED** |
| G2 | Reuse current registry, eligibility, sessions, claim | **CONFIRMED** |
| G3 | Participant read model Option B for FLEX-01 | **CONFIRMED** |
| G4 | `participants_json` → **DEFERRED** | **CONFIRMED** |
| G5 | FLEX-02 blocked pending persistence gate | **CONFIRMED** |
| G6 | Help → normalized when FLEX-04; none in FLEX-01 | **CONFIRMED** |
| G7 | Progress read-only FLEX-01; quantity blocked until FLEX-06 gate | **CONFIRMED** |
| G8 | Sessions authoritative for actual work/time | **CONFIRMED** |
| G9 | `assigned_employee_id` = optional principal | **CONFIRMED** |
| G10 | Authorize wave A — FLEX-01 only | **CONFIRMED** |

**10/10 confirmed.**

---

## Owner reserve on JSON-first

Owner rejects automatic acceptance of:

```text
sessions → participants_json → tables later
```

Concerns documented: concurrency on blob, lost join/leave updates, weak audit/query, help/progress mixed in JSON, session/participant contradiction.

Healthy path:

```text
FLEX-01: read models + adapters — no DB writes
Before FLEX-02: separate persistence decision
Help/progress: not auto-authorized in JSON
```

---

## FLEX-01 authorized scope

**Allowed:** terminology, read projections (principal, active/historical participants from sessions), additive API fields, focused tests.

**Forbidden:** writes, DB, migrations, JSON columns, claim/pool changes, help, progress, Mobile UI rollout.

**Visual behavior:** **UNCHANGED** (default).

Detail: `flex_01_authorized_scope.json`

---

## Persistence outlook (not schema)

| Capability | FLEX-01 | Later |
|------------|---------|-------|
| Principal | `assigned_employee_id` | unchanged |
| Active worker | sessions | existing |
| Participant before session | absent | ARCH-02 decision |
| Help | absent | normalized likely (FLEX-04) |
| Quantity progress | absent | concurrency-safe store (FLEX-06 gate) |

---

## Sandu

**PAUSED.** No registry correction. General foundation independent of Sandu fixes.

---

## Roadmap checkpoint

| Metric | Value |
|--------|-------|
| Nota | **9/10** |
| Direcție | **~85%** |
| Model simplu | YES |
| PS fără persoane | YES |
| Auto-dispatch evitat | YES |
| JSON blob rejected as canonical | YES |

---

## Honest opinion

Owner decision is the right brake: arch plan direction was sound but **persistence was underspecified**. FLEX-01 as pure read-model proves Option B projections against real sessions before any write representation. That avoids both premature migrations and a `participants_json` trap.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Decisions | 10 |
| Decisions confirmed | 10 |
| FLEX-01 | AUTHORIZED |
| FLEX-02 | BLOCKED |
| participants_json | DEFERRED |
| Participant writes | NOT_AUTHORIZED |
| Help persistence | NORMALIZED_WHEN_FLEX_04 |
| Quantity progress | BLOCKED_UNTIL_FLEX_06_GATE |
| DB migration | NOT_AUTHORIZED |
| UI changes | NOT_AUTHORIZED |
| Sandu | PAUSED |
| Next task | FLEX-01-EXECUTION-COLLABORATION-READ-MODEL-FOUNDATION |
| Code/DB changed | NO |
| Verdict | OWNER_FLEX_EXECUTION_GATE_CONFIRMED_FLEX_01_ONLY |
