# PROD-FLEX-ARCH-02 — Participant Persistence Boundary Plan

**Task:** PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY  
**Mode:** PLAN MODE — architecture/decision only  
**Starting HEAD:** `eaa3025` (WORKOS-ROADMAP-REALIGNMENT-01 closure)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Created:** 2026-07-15  
**Artifact type:** Owner decision package (not implementation-ready code plan)

---

## Goal Capsule

Define whether WorkOS needs persistent participant/help representation beyond `assigned_employee_id` (optional principal) and execution-reality work sessions (actual work/time authority). Select the persistence boundary before any FLEX-02 implementation. Do not assume a participant table is required; do not assume sessions alone suffice for every future workflow.

---

## Owner-Confirmed Foundation (binding)

- Product System defines operations; **no employee IDs** in PS or frozen snapshots.
- `assigned_employee_id` is **optional principal** — assignment is not proof of work.
- Sessions are **evidence of actual work/time**; principal is not the participant list.
- Eligible ≠ assigned; claim ≠ participation; stop ≠ operation complete.
- `participants_json` is **deferred** and rejected as hidden canonical authority.
- FLEX-02–09 remain **blocked**; UI and Employee Mobile collaboration remain **blocked**.
- Migration **not authorized** in this task.

---

## Readiness Classification

**`READY_FOR_OWNER_DECISION_NOW`**

| Prerequisite | Status |
|--------------|--------|
| Operational tasks materialized | **Satisfied** — order `23099`, 13 tasks, W5/W7 proven |
| Frozen task identity | **Satisfied** — `frozen_task_identity/v1`, `(order_id, task_id)` join stable |
| FLEX-01 read model | **Satisfied** — Option B baseline |
| Help lifecycle design (ARCH-01) | **Specified** — contracts exist; implementation deferred to FLEX-04 |
| Participant write authorization | **Not satisfied** — intentionally blocked until this decision |

**Not blocked by:** materialization, task identity, or help-lifecycle design completeness.

---

## Current Persistence Truth (three-layer model)

```text
Order (orders.id)
├── ExecutionPlan.tasks_json
│   ├── planned_tasks[]        ← frozen identity at preview
│   └── operational_tasks[]    ← materialized; assigned_employee_id lives here
└── ExecutionReality.tasks_json (1 row per order)
    └── work sessions          ← actual work/time; may include procurement meta pseudo-task
```

**Stable join key:** `(order_id, task_id)` where V2 `task_id` = `deterministic_task_key` = `{graph_node_id}:{task_rule_code}`.

**No ORM task table.** Participant persistence, if authorized, must anchor on `(order_id, task_id)` with optional `execution_plan_id` provenance.

---

## Session Sufficiency

### Sessions already solve

- Per-employee work time capture (start/end/duration, pause/block).
- Multi-worker backend model (concurrent sessions, `role` primary/helper).
- FLEX-01A `operation_completed` semantics (explicit completion per session).
- FLEX-01 read projection (principal from assignee, workers from sessions).
- Historical session records within order scope.

### Sessions cannot solve

- Help-request lifecycle (OPEN/ACCEPT/CANCEL/CLOSE) before work starts.
- Helper join product path (mobile blocked by `_has_active_session_by_other`).
- Split pools (principal claim vs helper join — D6 debt).
- Invite/intent before first session.
- Contribution stop without operation complete at write API level.
- Quantity progress (40-letter scenario).
- Cross-order participant queries without normalization.

**Conclusion:** Sessions remain **actual-work authority** (P6 YES). Additional persistence is required for collaboration **membership and help lifecycle**, not for replacing sessions.

---

## Requirements Beyond Sessions

| Requirement | Sessions sufficient? | Persistence need |
|-------------|---------------------|------------------|
| Record who is actively working | Yes | No |
| Record historical work time per worker | Yes | No |
| Represent helper before first session | No | Membership or help-accept row |
| Help invitation/request lifecycle | No | Normalized help entity (FLEX-04) |
| Accepted/declined/cancelled help states | No | Help entity |
| Persistent PRINCIPAL/HELPER roles | Partial | Membership row with role |
| Prevent duplicate active joins | Partial | DB unique constraint + idempotent join |
| Query active helpers without session | No | Membership query |
| Split principal vs helper pools (D6) | No | Membership + pool semantics (FLEX-03) |
| Audit join/leave/help timeline | Weak in JSON | Events as supplement |

---

## Options Compared

### OPTION 1 — Sessions-only (no participant persistence)

| Dimension | Assessment |
|-----------|------------|
| Benefits | Zero migration; matches today |
| Costs | FLEX-02–05 blocked; D6 persists |
| Current necessity | **Insufficient** for authorized collaboration frontier |
| Recommendation | **Reject** as write authority |

### OPTION 2 — Minimal normalized membership

Conceptual fields (analysis only — not finalized): `order_id`, `task_id`, `employee_id`, `role`, `status`, `joined_at`, `left_at`, `source`, `created_by`.

| Dimension | Assessment |
|-----------|------------|
| Benefits | Unblocks FLEX-02/03/05; concurrency via unique active constraint |
| Costs | One Alembic revision; dual-read transition |
| Duplication risk | Low if sessions remain work proof |
| Recommendation | **Primary** for participant writes |

### OPTION 3 — Help-request-first model

Persist help request → acceptance creates HELPER membership.

| Dimension | Assessment |
|-----------|------------|
| Benefits | Matches G6; powers `ajutor_solicitat` pool |
| Costs | Second entity; insufficient alone for direct JOIN verb |
| Recommendation | **Required companion** at FLEX-04, not sole participant model |

### OPTION 4 — Defer all persistence

| Dimension | Assessment |
|-----------|------------|
| Benefits | Avoids premature schema |
| Costs | Perpetuates blocked FLEX-02–09; D6 debt |
| Recommendation | **Reject** — contradicts program position post-realignment |

### OPTION 5 — Hybrid normalized model (recommended boundary)

Separate:
- **Intended/authorized participant relationship** → normalized membership table (FLEX-02/03).
- **Actual work sessions** → unchanged `execution_reality.tasks_json`.
- **Optional principal** → unchanged `assigned_employee_id` on plan.
- **Help lifecycle** → normalized help table (FLEX-04).
- **Audit timeline** → append-only events (non-authoritative for queries).

No JSON blob authority. No `participants_json`.

| Dimension | Assessment |
|-----------|------------|
| Benefits | Matches owner principle; unblocks wave chain |
| Costs | Two focused tables across FLEX-02 and FLEX-04 waves |
| Recommendation | **Recommended boundary** |

---

## Recommended Boundary

**Adopt OPTION 5 (hybrid normalized model) pending owner P1–P12 confirmation.**

```text
FLEX-02/03: execution_task_participants (normalized membership on order_id + task_id)
FLEX-04:     execution_task_help_requests (normalized) → accept activates HELPER membership
Always:      sessions in execution_reality.tasks_json = work/time authority
Always:      assigned_employee_id on plan = optional principal hint only
Audit:       append operational events (PARTICIPANT_JOINED, HELP_ACCEPTED, etc.) — supplement only
Rollback:    feature flags; FLEX-01 read adapters remain fallback
```

**Explicitly reject:** `participants_json` as canonical write authority; sessions-only for collaboration writes; defer-all.

---

## Authority Model

| Truth | Authority |
|-------|-----------|
| Optional principal | `execution_plan.operational_tasks[].assigned_employee_id` |
| Actual work/time | `execution_reality` work sessions |
| Participation membership (future) | Normalized `execution_task_participants` |
| Help lifecycle (future) | Normalized `execution_task_help_requests` |
| Collaboration read (now) | FLEX-01 projection — no write authority |
| Eligibility | `operational_registry_service` — independent of participation |

**Parent identity for persistence:** **`(order_id, task_id)`** on operational materialized tasks — not execution plan row alone, not pre-materialization planned task alone.

---

## Concurrency Model

Required guards (from ARCH-01 concurrency matrix):

| Race | Guard |
|------|-------|
| double_helper_join | Unique active `(task_id, employee_id)` + idempotent join → 200 already_joined |
| duplicate_active_session | Existing `task_already_started` per employee |
| help_accept_after_closed | Status check OPEN → 409 if closed |
| leave_after_completion | Idempotent no-op |
| complete_with_active_sessions | Policy: all sessions must explicitly complete for operation_completed |

**Do not remove `_has_active_session_by_other`** until FLEX-03 split pools ship (FLEX-05).

---

## Audit / History Model

- **Membership/help rows:** `joined_at`, `left_at`, `joined_by`, `join_reason`, `source`.
- **Sessions:** remain append-only historical work record.
- **Events (supplement):** `PARTICIPANT_JOINED`, `PARTICIPANT_LEFT`, `HELP_OPENED`, `HELP_ACCEPTED` — timeline for FLEX-08, not sole query authority.

Historical participation queryable separately from sessions via membership table; session history remains per-worker work proof.

---

## Migration Implications

| Phase | Action |
|-------|--------|
| ARCH-02 (this task) | Decision only — **no migration** |
| FLEX-02 (after GO) | One Alembic revision: participants table |
| FLEX-04 (after GO) | One Alembic revision: help requests table |
| Transition | Dual-read: derive membership from sessions until explicit join writes exist |
| Backfill | Filter sessions via `split_reality_task_entries()`; do not rematerialize operational tasks on orders with active history |
| Rollback | Feature flags off → FLEX-01 session-only read |

**P10 Migration authorized:** NO (this task).

---

## Roadmap Dependencies

```text
PROD-FLEX-ARCH-02 (this plan) → Owner GO
  → FLEX-02 participant membership writes
  → FLEX-03 join/leave, split pools, stop≠complete exposure
  → FLEX-04 help CRUD + accept→join
  → FLEX-05 Mobile helper UI (first major owner-visible collaboration)
  → FLEX-08 Operator visibility
```

**FLEX-02 does not create owner-visible value before FLEX-05.** ARCH-02 is the correct bounded next step.

**Alternate lanes (paused):** APP-AUTH-06G, UI-TRUTH-01B — higher immediate trust/evidence value if owner redirects.

---

## Owner Decision Table (P1–P12)

See `decision-log.md` for compact owner-facing table with recommended defaults.

---

## Hard Constraints (preserved)

All future persistence must preserve owner-confirmed foundation in § Owner-Confirmed Foundation.

---

## Forbidden Scope (this task)

No code, DB, migration, seeds, UI, participant writes, FLEX-02 start, runtime tooling changes, canonical inflation beyond ARCH-02 plan completion.

---

## Definition of Done

- [x] Four read-only workstreams completed
- [x] Five options compared with recommendation
- [x] Readiness classification assigned
- [x] Owner decision table P1–P12 produced
- [x] Plan + decision-log + worklog written
- [ ] Owner GO on persistence shape (external to this artifact)
- [ ] FLEX-02 implementation (blocked until GO)
