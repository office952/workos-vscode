# PROD-FLEX-ARCH-02 — Participant Persistence Boundary

**Task:** PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY  
**Date:** 2026-07-15  
**Mode:** PLAN MODE  
**Compound command:** `/ce-plan`  
**Starting HEAD:** `eaa3025` (Phase A closure commit)

---

# PROD-FLEX-ARCH-02 — Final Report

## 1. Verdict

**`PROD_FLEX_ARCH_02_PARTICIPANT_PERSISTENCE_BOUNDARY_READY`**

Architecture decision package complete. Owner may decide persistence shape. **FLEX-02 implementation remains NOT AUTHORIZED** until P1–P11 sign-off.

---

## 2. Repository safety

- **Branch:** `feature/product-system-active-path-isolation-v1`
- **Phase A commit:** `eaa3025` — realignment closure only; unrelated dirty files untouched
- **Phase B scope:** docs-only ARCH-02 artifacts + minimal canonical update
- **No foreign files staged**

---

## 3. Starting HEAD

**`eaa3025`** — `docs(roadmap): close post-backup realignment checkpoint`

---

## 4. Cursor mode used

**PLAN MODE** (Phase B)

---

## 5. Compound plugin used

**`/ce-plan`** — read-only research + docs-only coordinator write

---

## 6. Multitasking execution

| Role | Workstream | Access |
|------|------------|--------|
| Subagent A | Identity and persistence model | Read-only |
| Subagent B | Session sufficiency and lifecycle gaps | Read-only |
| Subagent C | Concurrency and schema options A–E | Read-only |
| Subagent D | Roadmap dependency and product value | Read-only |
| Coordinator | Integration + artifact write | Docs-only |

**Integration method:** Coordinator waited for all four reports; synthesized options 1–5; assigned readiness classification; produced owner decision table P1–P12.

**Parallel write agents:** None.

---

## 7. Current truth reused

- OWNER-DECISION-06 D1–D24 collaboration contract
- OWNER-DECISION-07 G1–G10 (FLEX-01 only; FLEX-02 blocked; `participants_json` deferred)
- FLEX-01 read model (`execution_task_collaboration_read/v1`)
- FLEX-01A operation completion semantics
- WORKOS-ROADMAP-REALIGNMENT-01 verdict (FLEX-02 not next; runtime tooling closed)
- `participant_persistence_gate.json` four comparison options
- PROD-FLEX-ARCH-01 wave plan and contracts

---

## 8. Session sufficiency findings

**Sessions solve:** per-employee work time, multi-worker backend capture, FLEX-01A completion truth, historical session records per order, FLEX-01 read projection.

**Sessions do not solve:** help-request lifecycle, helper join mobile path (D6), split pools, join-before-session intent, quantity progress, normalized cross-task queries.

**Verdict:** Sessions remain **actual-work authority** (P6 YES). Insufficient alone for collaboration product path (OWNER-DECISION-07 G8).

---

## 9. Requirements beyond sessions

1. Help invitation/request lifecycle (OPEN/ACCEPT/CANCEL/CLOSE)
2. Helper participation before or without principal session blocking pool
3. Persistent PRINCIPAL/HELPER membership distinct from assignee hint
4. Duplicate-join prevention with idempotency
5. Leave membership distinct from session stop
6. Historical participation query separate from session rollup
7. Split principal-claim vs helper-join pools (D6 remediation)

---

## 10. Stable parent identity

**Recommended parent:** `(order_id, task_id)` on **materialized operational task**.

| Layer | Role |
|-------|------|
| `orders.id` | Aggregate root |
| `execution_plan.tasks_json.operational_tasks[]` | Plan + `assigned_employee_id` |
| `execution_reality.tasks_json` | Work sessions |
| `deterministic_task_key` / `frozen_task_identity/v1` | Semantic stable key |

**Not recommended:** execution_plan row alone; pre-materialization planned task; Product System graph node without order scope.

---

## 11. Options compared

| Option | Verdict |
|--------|---------|
| 1 — Sessions-only | **Reject** for collaboration writes |
| 2 — Normalized membership | **Adopt** (FLEX-02/03) |
| 3 — Help-request-first | **Adopt** as FLEX-04 companion |
| 4 — Defer all persistence | **Reject** |
| 5 — Hybrid normalized | **Recommended boundary** |

Full analysis: `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/plan.md`

---

## 12. Recommended boundary

**OPTION 5 — Hybrid normalized model:**

- `execution_task_participants` — normalized membership (FLEX-02/03)
- `execution_task_help_requests` — normalized help (FLEX-04)
- Sessions unchanged in `execution_reality.tasks_json`
- `assigned_employee_id` unchanged as optional principal
- Operational events as **audit supplement only**
- **No `participants_json`**

---

## 13. Authority model

| Truth | Owner |
|-------|-------|
| Principal hint | `assigned_employee_id` on plan operational task |
| Actual work/time | Work sessions in execution reality |
| Membership (future) | Normalized participant rows |
| Help (future) | Normalized help rows |
| Eligibility | Operational registry (unchanged) |
| Read projection (now) | FLEX-01 |

---

## 14. Concurrency model

- Unique active participant per `(task_id, employee_id)`
- Idempotent join → 200 already_joined
- Help accept only when OPEN
- Keep `_has_active_session_by_other` until FLEX-03 split pools
- Session-level `task_already_started` per employee preserved

---

## 15. Audit/history model

- Membership rows: `joined_at`, `left_at`, `joined_by`, `join_reason`, `source`
- Sessions: append-only work history
- Events: `PARTICIPANT_JOINED`, `HELP_ACCEPTED`, etc. — timeline supplement for FLEX-08

---

## 16. Migration implications

| When | What |
|------|------|
| ARCH-02 (now) | **No migration** |
| FLEX-02 (after GO) | Participants table — one Alembic revision |
| FLEX-04 (after GO) | Help table — one Alembic revision |
| Transition | Dual-read from sessions until join writes exist |

**P10:** Migration **NOT authorized** in this task.

---

## 17. Roadmap dependencies

```
ARCH-02 (complete) → Owner GO → FLEX-02 → FLEX-03 → FLEX-04 → FLEX-05 (first visible UI)
```

**FLEX-02 value before FLEX-05:** backend only — no owner-visible collaboration UI.

**Paused alternates:** APP-AUTH-06G, UI-TRUTH-01B.

---

## 18. Readiness classification

**`READY_FOR_OWNER_DECISION_NOW`**

Not blocked by operational task identity or materialization. Help lifecycle design exists in ARCH-01 but implementation correctly deferred to FLEX-04.

---

## 19. Owner decisions P1–P12

See `decision-log.md`. Summary:

- P1: YES — persistence needed for collaboration path
- P4: Hybrid normalized (recommended)
- P5/P6: YES — principal assignee + sessions unchanged
- P10/P11: NO — no migration or FLEX-02 in this task
- P12: FLEX-02 membership table + join/leave API (after GO)

**All twelve pending explicit owner sign-off.**

---

## 20. Forbidden scope confirmation

No code, DB, migration, seeds, UI, participant writes, FLEX-02 start, session/assignment/claim changes, Mobile/Operator changes, Product System/snapshot changes, runtime tooling changes, push, PR.

**Confirmed.**

---

## 21. Artifacts

| Artifact | Path |
|----------|------|
| Plan | `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/plan.md` |
| Decision log | `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/decision-log.md` |
| Risk register | `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/risk-register.md` |
| This worklog | `docs/worklog/realignment/2026-07-15_prod_flex_arch_02_participant_persistence_boundary.md` |

---

## 22. Canonical docs update

Minimal update: record PROD-FLEX-ARCH-02 plan **COMPLETE** and readiness `READY_FOR_OWNER_DECISION_NOW`. Does not advance FLEX-02 implementation status.

---

## 23. Commit

Docs-only commit for ARCH-02 artifacts + canonical sync (see delivery footer).

---

## 24. What remains

- Owner sign-off on P1–P12 (`decision-log.md`)
- FLEX-02 implementation (blocked)
- FLEX-03–09 waves (blocked)
- APP-AUTH-06G, UI-TRUTH-01B (paused)
- Runtime tooling (closed)

---

## 25. Next safe step

**Owner reviews `decision-log.md` and confirms P1–P4.**

If confirmed: authorize **FLEX-02 planning/build** as separate scoped task with migration gate — **not automatic**.

If owner wants visible product value first: unpause **UI-TRUTH-01B** or **APP-AUTH-06G** instead.

**Does not automatically authorize FLEX-02.**

---

## 26. Honest opinion

Sessions are doing more work than the product admits — backend already supports multi-worker sessions, but mobile and pools pretend individual-only. The right move is **not** to bolt `participants_json` onto `tasks_json` and hope concurrency works. The right move is **two small normalized tables** staged across FLEX-02 and FLEX-04, with sessions left alone.

ARCH-02 is correctly **plan-only**. FLEX-02 code before owner sign-off would repeat the FLEX detour mistake at a more expensive layer.

If the owner is fatigued by architecture: **UI-TRUTH-01B** delivers trust on every page faster than FLEX-02 ever will. But if collaboration is the strategic bet, sign the decision log and accept that **FLEX-05** is the first time anyone sees it on the floor.

---

## 27. Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Score (1–10) | **9** — clear boundary; owner sign-off is the only gap |
| Roadmap position | Post-realignment; at collaboration persistence **decision gate** |
| Paused lanes | Runtime tooling (CLOSED); FLEX-02–09; 06G; UI-TRUTH-01B–01E; PROD-ARCH-01; MOBILE-INT-02 |
| Dead pieces check | `participants_json` absent from code; help API absent; collaboration UI absent by design |
| Forbidden scope | Confirmed — no writes in this task |
| Cat sunt in directia stabilita | **82/100%** |

---

## DELIVERY FOOTER

```
Task: PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY
Starting HEAD: eaa3025
Cursor mode: PLAN MODE
Compound command: /ce-plan
Multitasking: ENABLED
Parallel read-only workstreams: 4
Write access: DOCS ONLY — ONE COORDINATOR
Implementation: NO
Participant persistence implemented: NO
participants_json: DEFERRED / NOT CANONICAL
DB migration: NO
Schema changes: NO
Participant writes: NO
UI changes: NO
Mobile changes: NO
Product System changes: NO
Snapshot changes: NO
Runtime tooling changes: NO
FLEX-02 started: NO
Readiness classification: READY_FOR_OWNER_DECISION_NOW
Recommended boundary: Hybrid normalized — execution_task_participants (FLEX-02) + execution_task_help_requests (FLEX-04) + sessions unchanged + audit events supplement
Owner decisions: 12 (P1–P12 pending sign-off)
Plan: .compound-engineering/prod-flex-arch-02-participant-persistence-boundary/plan.md
Decision log: .compound-engineering/prod-flex-arch-02-participant-persistence-boundary/decision-log.md
Worklog: docs/worklog/realignment/2026-07-15_prod_flex_arch_02_participant_persistence_boundary.md
Commit: YES (pending)
Commit hash: <see Phase B commit>
Push: NO
PR: NO
Verdict: PROD_FLEX_ARCH_02_PARTICIPANT_PERSISTENCE_BOUNDARY_READY
```
