# PROD-FLEX-COLLABORATION-PHASE-1 — Implementation Plan

**Task:** PROD-FLEX-COLLABORATION-PHASE-1-IMPLEMENTATION-PLAN  
**Date:** 2026-07-15  
**Starting HEAD:** `361b8f7`  
**Mode:** PLAN ONLY — no implementation authorized by this document  
**Upstream:** OWNER-DECISION-08 (`PROD-FLEX-ARCH-02` accepted with corrections)

---

## Executive Summary

**Recommended verdict:** `PROD_FLEX_COLLABORATION_PHASE_1_PLAN_READY`

Phase 1 is a **single coherent backend implementation phase** — not a chain of micro-approvals. It delivers the first honest collaboration foundation: **HELPER membership persistence**, **join/leave membership API**, and **read-model surfacing** — without help tables, pool changes, session changes, UI, or Mobile.

The old FLEX-02/03/04 wave labels informed research but **do not dictate** the final grouping. Product outcome drives scope.

| Phase | Name | Delivers |
|-------|------|----------|
| **Phase 1** (this plan) | Collaboration Membership Foundation | Table + migration + join/leave + read extension + tests + runtime proof |
| **Phase 2** | Pools, Help & Helper Work Verbs | Help table, split pools, helper session start, optional leave+stop |
| **Phase 3** | Operator/Mobile Visibility | UI consumers, timeline, first owner-visible floor experience |

---

## Problem Frame

WorkOS already supports multi-worker **sessions** in `execution_reality.tasks_json`, but has no durable **collaboration authorization** layer. Today:

- Principal hint lives in `assigned_employee_id` (optional, not participation proof)
- Actual work/time lives in sessions only
- FLEX-01 read projection derives workers from sessions; no membership intent
- Mobile blocks helper claim when another session is active (`_has_active_session_by_other`)
- `can_assist: false` is hardcoded in blueprint service

OWNER-DECISION-08 accepted OPTION 5 hybrid architecture but blocked implementation. This plan defines **what one owner GO should authorize** to create a meaningful, testable, reversible backend foundation.

---

## Options Considered

### Option A — Sessions-only extension (reject)

Extend `execution_reality.tasks_json` with membership metadata alongside sessions.

| Pro | Con |
|-----|-----|
| No migration | Conflates authorization with work proof; JSON drift; rejected at ARCH-02 |
| | Blocks normalized queries and idempotent join |

**Verdict:** Rejected — contradicts accepted architecture.

### Option B — `participants_json` blob on plan (reject)

Store participant list in `execution_plan.tasks_json`.

| Pro | Con |
|-----|-----|
| Fast to prototype | No DB uniqueness; rematerialize risk; OWNER-DECISION-07 G4 rejected |

**Verdict:** Rejected.

### Option C — Membership-only normalized table (recommended Phase 1)

`execution_task_participants` table; HELPER-only rows; join/leave API; read extension.

| Pro | Con |
|-----|-----|
| Matches OWNER-DECISION-08 P7/P8/P9 | No help lifecycle yet |
| Distinct from sessions and assignee | Mobile still blocks claim pool until Phase 2 |
| Idempotent DB constraints | Requires migration GO |
| E2E testable on order 23099 | No owner-visible UI until Phase 3 |

**Verdict:** **Recommended Phase 1 scope.**

### Option D — Membership + help in one phase (reject for Phase 1)

Add `execution_task_help_requests` alongside participants.

| Pro | Con |
|-----|-----|
| Complete invitation flow | Help lifecycle is a separate product verb chain |
| | Accept→join coupling adds scope without being required for direct join |
| | Two migrations, more owner risk in one GO |

**Verdict:** Defer to **Phase 2**. Direct JOIN (eligible employee, no invitation) is sufficient for Phase 1 product outcome.

### Option E — Membership + helper session start bundled (reject)

JOIN also starts a helper session.

| Pro | Con |
|-----|-----|
| One call for mobile | **Violates OWNER-DECISION-08 P8** |
| | Conflates authorization with work proof |

**Verdict:** Rejected. Session start remains a **separate verb** in Phase 2.

---

## Recommended Phase 1 Scope

### In scope (one implementation GO)

| # | Deliverable | Rationale |
|---|-------------|-----------|
| 1 | **Alembic migration** — `execution_task_participants` | Persistence foundation; single revision off `s56` head |
| 2 | **SQLAlchemy model** | Follow `task_clarification_request` / junction-table precedents |
| 3 | **Membership service** | Join (idempotent), leave (own only), query active/historical |
| 4 | **Join/leave API** | Operator + employee-mobile scoped write endpoints |
| 5 | **Membership read API** | List active/historical memberships per task |
| 6 | **Collaboration read extension** | Additive `helper_memberships[]` on FLEX-01 projection (`v1.1`) |
| 7 | **Eligibility guards** | Materialized V2 task exists; operational registry; order not terminal |
| 8 | **Pytest matrix** | Unit + integration + mobile/claim regression bundle |
| 9 | **Runtime verification** | Live probes on order 23099 at `:8001`; evidence JSON |
| 10 | **BUILD doc** | `docs/qa/BUILD_PROD_FLEX_COLLAB_PHASE_1.md` |
| 11 | **OpenAPI manifest** | Add new routes to `scripts/workos-canonical-openapi-paths.json` |

### Product outcome achieved at Phase 1 end

- Eligible employee can **authorize** collaboration via JOIN (membership row)
- Membership is **distinct** from `assigned_employee_id`, claim, and sessions
- Actual work still proven **only** through sessions (unchanged)
- Membership history preserved (`joined_at`, `left_at`, reactivation)
- Duplicate joins safe (DB unique + idempotent 200)
- LEAVE closes **actor's own** membership only
- No implicit operation completion
- Individual claim/start/complete flow **unchanged**
- Collaboration state visible via **API + extended read model**
- Verifiable on **order 23099** with 13 materialized tasks

### Explicitly deferred (Phase 2+)

| Item | Phase | Why deferred |
|------|-------|--------------|
| `execution_task_help_requests` table | 2 | Separate lifecycle; not required for direct join |
| Help CRUD + accept→join | 2 | Depends on help entity |
| Split pools (`ajutor_solicitat`) | 2 | Requires help or explicit pool contract |
| `_has_active_session_by_other` changes | 2 | OWNER-DECISION-08 P12: unchanged in Phase 1 |
| Helper session start API | 2 | Separate work verb; P8 forbids bundling with JOIN |
| LEAVE stops own session | 2 | P9: only if future endpoint contract includes it |
| `can_assist` backend truth | 2 | Depends on pools + help |
| Operation progress | 3+ | Unrelated to membership foundation |
| Operation-level complete policy | 3+ | FLEX-01A already read-correct |
| Audit event timeline (`PARTICIPANT_JOINED`) | 3 | Membership timestamps sufficient for Phase 1 |
| UI / Operator panels | 3 | No frontend consumer required for backend value |
| Employee Mobile join UX | 3 | Mobile explicitly deferred |
| Legacy T-001 task IDs | — | V2 materialized path only |
| Product System / snapshot changes | — | Forbidden |
| `participants_json` | — | Rejected permanently |

---

## Persistence Design

### Table: `execution_task_participants`

Anchor: **`(order_id, task_id)`** on materialized V2 operational task.  
`execution_plan_id` optional provenance only (not parent key).

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Autoincrement |
| `order_id` | Integer NOT NULL, indexed | Soft FK (execution-layer convention) |
| `task_id` | String(256) NOT NULL, indexed | V2 `deterministic_task_key` |
| `employee_id` | Integer NOT NULL, FK→`employees.id` CASCADE | Hard FK (HR entity) |
| `role` | String(16) NOT NULL, default `'helper'` | App-enforced HELPER-only at Phase 1 |
| `status` | String(16) NOT NULL | `active` \| `inactive` |
| `joined_at` | DateTime TZ NOT NULL | |
| `left_at` | DateTime TZ nullable | Set on LEAVE |
| `joined_by_employee_id` | Integer nullable | Actor who performed join (self or manager) |
| `join_source` | String(32) nullable | `self_join` \| `manager_add` \| `help_accept` (future) |
| `execution_plan_id` | Integer nullable | Provenance snapshot |
| `created_at` / `updated_at` | DateTime TZ | Standard pattern |

**Unique constraint:** `(order_id, task_id, employee_id)` — one row per employee per task.

**Reactivation model (recommended):** Same row reused. LEAVE sets `status=inactive`, `left_at=now`. Re-JOIN reactivates: `status=active`, `left_at=null`, update `joined_at` (or add `last_joined_at` if history granularity needed — prefer single `joined_at` refresh for Phase 1 simplicity; full history via `left_at` preserved on prior cycle if using new row — **decision: reactivate same row** to satisfy unique constraint; audit via `updated_at` + optional `join_count` deferred).

**Rejected alternative:** Append-only new row per join cycle — breaks simple unique constraint; requires partial unique on active only (no SQLite precedent in repo).

### Migration strategy

| Aspect | Recommendation |
|--------|----------------|
| Revision | Single `s57_create_execution_task_participants` off `s56` head |
| SQLite safety | Inline unique in `create_table`; idempotent `_table_exists` guard |
| Backfill | **None** in migration — empty table start |
| Dual-read | FLEX-01 continues session projection; v1.1 adds membership array |
| Rollback | `downgrade()` drops table; reads fall back to session-only |
| Dev drift | Follow `docs/qa/BUILD_MIGRATION_HYGIENE.md`; validate clean `alembic upgrade head` |

### Feature flag (writes only)

`FLEX_MEMBERSHIP_API_ENABLED` — default `true` in development, `false` in production until rollout. Pattern: mirror `backend/parity/flags.py` BaseSettings. When off: join/leave return 503; reads still work (empty memberships).

---

## Identity and Lifecycle

### Parent identity

```
orders.id
  └── execution_plan.tasks_json.operational_tasks[].task_id
        = deterministic_task_key
        = frozen_task_identity.deterministic_task_key
```

Join key for sessions, membership, and FLEX-01: **`(order_id, task_id)`**.

### Membership lifecycle

```text
[no row] ──JOIN──► active (HELPER)
                      │
                      ├──JOIN (idempotent)──► 200 already_joined
                      │
                      └──LEAVE (actor)──► inactive (left_at set)
                              │
                              └──JOIN (reactivate)──► active (left_at cleared)
```

### Preconditions for JOIN

1. Order exists and not in terminal status
2. V2 plan materialized (`execution_tasks_created=true`)
3. `task_id` exists in `operational_tasks[]`
4. Actor eligible per operational registry (same rules as mobile claim eligibility)
5. Actor not blocked by business rules (future: help OPEN — not Phase 1)
6. **Must NOT check** `_has_active_session_by_other` for join endpoint (membership ≠ claim pool)

### Preconditions for LEAVE

1. Active membership row exists for `(order_id, task_id, actor_employee_id)`
2. Actor is the membership owner (no manager-leave-other in Phase 1)

---

## JOIN and LEAVE Semantics (implementation binding)

Matches OWNER-DECISION-08 P8/P9.

### JOIN

- Creates or reactivates HELPER membership
- Idempotent: active membership → `200` with `already_joined: true`
- **Must NOT:** start session; claim task; modify `assigned_employee_id`; mark progress; complete operation; touch `execution_reality.tasks_json`

### LEAVE

- Sets own membership `inactive`, `left_at=now`
- **Must NOT:** stop any session (own or other); change principal; complete operation
- Idempotent: already inactive → `200` with `already_left: true`

---

## Concurrency and Idempotency

| Concern | Mechanism |
|---------|-----------|
| Duplicate join | `UNIQUE(order_id, task_id, employee_id)` + `IntegrityError` → fetch existing |
| Concurrent join+leave | `SELECT ... FOR UPDATE` on membership row; mirror `execution_task_assignment_service` task-scoped asyncio lock |
| Concurrent join+claim | Independent surfaces — claim uses assignment service; join uses membership service; no cross-lock required if boundaries respected |
| Race: two joins same employee | DB unique wins; second returns already_joined |

Regression preservation: `test_employee_mobile_claim_concurrency.py` must remain green unchanged.

---

## API and Read Model

### Write endpoints (recommended shape)

Operator prefix (manager/system actions):

| Method | Path | Action |
|--------|------|--------|
| POST | `/api/v1/operator/orders/{order_id}/tasks/{task_id}/collaboration/join` | Join as HELPER (actor from auth context) |
| POST | `/api/v1/operator/orders/{order_id}/tasks/{task_id}/collaboration/leave` | Leave own membership |

Employee mobile prefix (self actions):

| Method | Path | Action |
|--------|------|--------|
| POST | `/api/v1/employee-mobile/orders/{order_id}/tasks/{task_id}/collaboration/join` | Self join |
| POST | `/api/v1/employee-mobile/orders/{order_id}/tasks/{task_id}/collaboration/leave` | Self leave |

**Rejected alternatives:**
- Single `/participants` CRUD — too generic; hides verb semantics
- Join on claim route — violates P8
- GraphQL-style mutation — not repo convention

### Read endpoints

| Method | Path | Action |
|--------|------|--------|
| GET | `/api/v1/operator/orders/{order_id}/tasks/{task_id}/collaboration/memberships` | Active + recent inactive |
| GET | `/api/v1/operator/orders/{order_id}/task-collaboration-read` | Extended (existing + `helper_memberships[]`) |

### Read model extension

**Contract:** `execution_task_collaboration_read/v1.1` (additive)

New per-task field:

```python
class HelperMembershipRead(BaseModel):
    employee_id: int
    employee_name: str | None
    status: Literal["active", "inactive"]
    joined_at: str
    left_at: str | None
    join_source: str | None

# On TaskCollaborationRead:
helper_memberships: list[HelperMembershipRead] = []
authorized_helper_count: int = 0  # active only
```

**Compatibility:** v1 consumers ignore new fields. Tests assert v1 fields unchanged. New tests assert v1.1 membership projection.

**Dual-read rule:** If membership table empty, `helper_memberships=[]` — sessions remain sole worker proof. Never infer membership from sessions automatically (avoids drift).

---

## Compatibility Matrix

| Surface | Phase 1 change | Regression risk |
|---------|----------------|-----------------|
| `assigned_employee_id` | **None** | Low |
| `execution_reality` sessions | **None** | Low |
| `claim_my_task` | **None** | Medium — must run MOBILE-T06 |
| `_has_active_session_by_other` | **None** | Low |
| FLEX-01 v1 fields | **None** (additive v1.1) | Low |
| `list_my_tasks` | **None** | Medium — membership does not auto-add to my tasks |
| `list_available_tasks` | **None** | Low |
| Operation completion (FLEX-01A) | **None** | Low |
| Order 23099 fixture | Read/write membership only; do not reset plan | Medium |

---

## Testing Strategy

### P0 — Must pass before phase close

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_execution_task_collaboration_read.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_task_work_sessions.py tests/test_employee_mobile_claim_concurrency.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_execution_task_participants.py -q  # new
```

### New test file: `test_execution_task_participants.py`

| ID | Scenario |
|----|----------|
| M1 | Join creates active HELPER row |
| M2 | Join idempotent (already active) |
| M3 | Leave sets inactive + left_at |
| M4 | Leave idempotent |
| M5 | Reactivate after leave |
| M6 | Join does NOT create session |
| M7 | Join does NOT change assigned_employee_id |
| M8 | Leave does NOT end session |
| M9 | Leave does NOT complete operation |
| M10 | Non-member leave → 404 |
| M11 | Join on non-materialized order → 409 |
| M12 | Join on unknown task_id → 404 |
| M13 | Concurrent double join → one row |
| M14 | v1.1 read includes helper_memberships |
| M15 | Regression: claim still works after membership writes |

### P1 — Integration

- HTTP tests for all new endpoints
- Eligibility guard (ineligible employee → 403)
- V2 identity: `task_id` matches `deterministic_task_key`

### P2 — Live runtime (order 23099)

See Runtime Verification section in worklog.

---

## Runtime Verification Plan

| Item | Value |
|------|-------|
| Backend | `http://127.0.0.1:8001` |
| Frontend | `http://127.0.0.1:3000` (read-only smoke; no UI changes expected) |
| Auth | `Bearer __DEV_BYPASS_TOKEN__` |
| Order | `23099` (`ORD-W5INT02-GATE`) |
| Sample task | `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep` |

### Expected states after Phase 1 implementation

**Before any join (baseline):**
- `task-collaboration-read` → 13 tasks, `helper_memberships=[]`
- `assigned_employee_id` unchanged from baseline
- Sessions unchanged
- Claim/start/complete still work

**After test join (helper employee, disposable or revert leave):**
- `helper_memberships[0].status=active`
- `authorized_helper_count=1`
- `actual_workers` still session-derived (empty if no session)
- `operation_completed` unchanged
- No new session in `execution_reality`

**Non-regression:**
- `POST .../claim` on unassigned task → still 200
- `_has_active_session_by_other` behavior on available pool unchanged
- Order 23150 blocked fixture untouched

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/flex_collab_phase1_runtime_evidence.json`

---

## Implementation Workstreams (single owner integration)

```text
Workstream 1 — Schema (migration + model + flag)
    ↓
Workstream 2 — Membership service (join/leave/query + locks)
    ↓
Workstream 3 — API routers (operator + mobile + auth guards)
    ↓
Workstream 4 — Read extension (v1.1 projection)
    ↓
Workstream 5 — Tests + runtime proof + BUILD doc
```

**Integration owner** merges in order; each workstream is reviewable but not separately GO'd.

---

## Commit Strategy

**Recommended: 3 isolated commits within one phase** (not 9 micro-commits):

| Commit | Contents |
|--------|----------|
| 1 | `s57` migration + model + `FLEX_MEMBERSHIP_API_ENABLED` + model tests |
| 2 | Membership service + API routers + integration tests |
| 3 | Read v1.1 extension + regression bundle green + runtime evidence + BUILD doc |

**Rejected:** Single monolithic commit (hard to review migration separately); 9 wave-sized commits (over-fragmented per user request).

---

## Authorization Gates (this plan does NOT grant)

| Gate | Status after this plan |
|------|------------------------|
| Architecture (ARCH-02) | **ACCEPTED** |
| Phase 1 implementation | **NOT AUTHORIZED** — requires owner GO |
| Migration | **NOT AUTHORIZED** — requires owner GO |
| Participant writes | **NOT AUTHORIZED** |
| Join/leave API | **NOT AUTHORIZED** |
| UI | **NOT AUTHORIZED** |
| Mobile UX | **NOT AUTHORIZED** |
| Help persistence | **NOT AUTHORIZED** (Phase 2) |
| Pool changes | **NOT AUTHORIZED** (Phase 2) |

### Recommended single owner GO block

```
PHASE-1 IMPLEMENTATION GO:
- Migration: YES (s57 execution_task_participants)
- Membership writes: YES (HELPER-only)
- Join/leave API: YES (membership only)
- Read extension v1.1: YES
- UI: NO
- Mobile UX: NO
- Help table: NO
- Pool / _has_active_session_by_other changes: NO
- Session / assignment / claim changes: NO
```

---

## Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-P1-01 | JOIN bundled with session start | High | Code review gate; M6 test |
| R-P1-02 | Dual principal (PRINCIPAL row) | High | role=helper enforced; no PRINCIPAL insert path |
| R-P1-03 | Membership inferred from sessions | Medium | Explicit table only; no backfill auto-join |
| R-P1-04 | 23099 fixture reset orphans rows | Medium | Use leave cleanup; prefer isolated test order for destructive tests |
| R-P1-05 | Alembic/create_all drift | Medium | BUILD_MIGRATION_HYGIENE gate |
| R-P1-06 | list_my_tasks expectation gap | Medium | Document: membership ≠ my tasks until Phase 3 |
| R-P1-07 | Plan read as auto-GO | High | decision-log.md gates explicit |

---

## Definition of Done (implementation phase — future)

- [ ] Migration applied cleanly on fresh SQLite
- [ ] All P0 pytest green
- [ ] MOBILE-T06 claim concurrency green
- [ ] FLEX-01 v1 fields regression green
- [ ] Runtime evidence JSON for order 23099
- [ ] OpenAPI manifest updated
- [ ] BUILD doc complete
- [ ] No changes to sessions, assignment, claim, pools, Product System

---

## References

- `backend/services/execution_task_collaboration_read_service.py`
- `backend/services/execution_task_assignment_service.py`
- `backend/services/execution_reality_service.py`
- `backend/services/employee_mobile_tasks_service.py`
- `backend/models/task_clarification_request.py`
- `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/decision-log.md`
- `docs/qa/BUILD_MIGRATION_HYGIENE.md`
