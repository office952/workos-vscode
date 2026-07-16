# PROD-FLEX-COLLABORATION-PHASE-2-CORRECTION — Implementation Plan

**Task:** PROD-FLEX-COLLABORATION-PHASE-2-CORRECTION  
**Date:** 2026-07-16  
**Mode:** PLAN ONLY — implementation **NOT AUTHORIZED** until owner GO  
**Upstream closure:** `docs/worklog/realignment/2026-07-16_prod_flex_collaboration_phase_2_closure.md`  
**Starting HEAD (closure):** `17af5f6`  
**Verdict:** `PROD_FLEX_COLLABORATION_PHASE_2_CORRECTION_PLAN_READY`

---

## Why this phase exists

Phase 2 shipped a coherent collaboration capability, but closure audit found **blocking** gaps in:

1. **Cancel authorization** — any route-eligible employee can cancel any OPEN help.  
2. **Multiprocess session / close races** — helper start and completion→help-close lack cross-process integrity.  
3. **Completion→help reliability** — separate commits + mobile already-completed skip; runtime never proved real completion.

Phase 3 UI is **blocked** until this correction ships and re-closes.

---

## Product outcome (after correction)

1. Only the help requester (or an explicitly defined operator override, if GO chooses one) may cancel OPEN help.  
2. Completing an operation always closes remaining OPEN help for that task, even on idempotent complete retries.  
3. A helper cannot obtain two active sessions on the same task across workers.  
4. OPEN uniqueness holds on both migrated DBs and `create_all` / local fixtures.  
5. Runtime proof on order 23099 demonstrates **real** principal completion → help CLOSED, memberships preserved, `operation_completed` honest.  
6. Phase 3 UI planning may resume.

---

## Binding rules (unchanged)

Membership ≠ work; LEAVE ≠ STOP; STOP ≠ complete; claim principal-only; no PRINCIPAL membership; no auto assign/claim/complete; sessions = work/time; help accept ≠ session start.

---

## Locked correction decisions

| ID | Decision |
|----|----------|
| C1 | **Cancel = requester-only** on Operator and Employee Mobile (same rule). Targeted “no” remains **decline**. |
| C2 | Optional **operator override cancel** is **out of this correction** unless owner GO adds it as a separate explicit permission check — default is requester-only only. |
| C3 | Memberships remain **preserved** on cancel/close/completion. |
| C4 | `close_open_help_for_task` must be **idempotent** and invoked on **every** successful complete path, including mobile `already_completed` retries. |
| C5 | Prefer **same DB transaction** for complete + help close when feasible; if not feasible in current RealityService shape, use **ordered commits + mandatory retry-safe closer** and document residual split-commit risk as non-blocking only if closer cannot fail after successful complete without a compensating retry path. |
| C6 | Helper session start must load reality with **`for_update`** (or equivalent serialization) before duplicate-active check + append. |
| C7 | Declare OPEN partial unique on the **ORM model** (mirror s58) so `create_all` and tests match migrated DBs. No new Alembic revision unless ORM-only is insufficient for an already-migrated environment. |
| C8 | `close_open_help_for_task` must use task-scoped lock + `FOR UPDATE` (or single UPDATE … WHERE status='OPEN') to coordinate with accept. |
| C9 | **No UI.** Backend + tests + runtime proof only. |
| C10 | One coherent implementation GO — not three micro-fixes as separate owner loops. |

---

## Scope

### Authorized

- Cancel actor authorization in help service + negative tests  
- Complete-path help close reliability (mobile + operator)  
- Reality `start_task` row locking for employee-scoped starts (helper path at minimum; prefer all employee_id starts)  
- ORM index alignment for OPEN uniqueness  
- Lock/serialize `close_open_help_for_task`  
- Focused concurrency / auth / completion tests  
- Runtime proof: real completion on order 23099 (safe local data)  
- BUILD + worklog + STATUS updates after PASS  
- Isolated commits; no push/PR

### Not authorized

- Phase 3 UI  
- Operator override cancel (unless added to C2 by GO)  
- Leave+stop combo, quotas, acceptance child table  
- Orphan s50 Alembic repair  
- Product System / snapshots / pricing  
- Broad RealityService rewrite beyond locking needed for helper integrity

---

## Implementation units (suggested)

| Unit | Work |
|------|------|
| U1 | Requester-only cancel in `_close_like` when `action=cancel`; 403 `help_cancel_forbidden` |
| U2 | Mobile complete: call closer even on `already_completed`; operator path already always calls — add regression |
| U3 | Transaction or retry-safe pairing of `end_task` + `close_open_help_for_task` |
| U4 | `start_task` / helper start: `for_update` before active-session check |
| U5 | ORM `__table_args__` partial unique for OPEN help; verify create_all + s58 coexistence |
| U6 | Lock `close_open_help_for_task` |
| U7 | Tests: cancel auth negatives; complete closes help; already_completed still closes; concurrent helper start (best-effort under SQLite) |
| U8 | Runtime: principal completes task with OPEN broadcast help → CLOSED; memberships remain; collab read honest |

Cursor owns technical details within C1–C10.

---

## Test matrix (minimum)

- Non-requester cancel → 403 (Operator + Mobile service-level)  
- Requester cancel → CANCELLED; memberships intact  
- Complete with OPEN help → CLOSED  
- Complete already_done with leftover OPEN → closer still runs / help CLOSED  
- Helper start duplicate active rejected under serial and best-effort concurrent  
- Phase 1 membership + claim regressions green  
- Explicit upgrade path still s58 (no bare head)

---

## Runtime proof (correction)

Canonical `:8001`, order `23099`, one OPEN broadcast, then **actual** principal/operator **complete** (or controlled complete path that sets operation completion truth), then assert:

- help CLOSED  
- memberships still active  
- `operation_completed` / session completion honest  
- Do not only call `close_open_help_for_task` in isolation

---

## Commit strategy

1. Auth + close reliability  
2. Session lock + ORM unique + closer lock  
3. Tests + runtime + docs  

Or fewer if atomic correctness requires bundling.

---

## Owner GO (phase-level)

| Gate | Question | Default recommendation |
|------|----------|------------------------|
| G1 | Authorize this correction phase? | YES |
| G2 | Requester-only cancel (no override)? | YES |
| G3 | Allow operator override cancel with blueprint permission? | NO (defer) |
| G4 | Require reality `for_update` on helper/employee starts? | YES |
| G5 | Block Phase 3 until correction re-closes? | YES |

---

## What remains after correction

- Phase 3 Operator + Employee Mobile collaboration UX (separate plan)  
- Optional operator override cancel  
- Orphan Alembic multi-head merge  
- Stronger multiprocess test harness if needed

---

## Honest opinion

Phase 2 core model (broadcast OPEN, membership-as-acceptance, helper sessions, capability split) remains the right architecture. Correction is **authorization + integrity hardening**, not a redesign. Shipping UI on top of open cancel and unlocked session starts would bake bad floor behavior into screens.
