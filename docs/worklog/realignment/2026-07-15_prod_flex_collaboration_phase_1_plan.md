# PROD-FLEX-COLLABORATION-PHASE-1 — PLAN REPORT

**Task:** PROD-FLEX-COLLABORATION-PHASE-1-IMPLEMENTATION-PLAN  
**Date:** 2026-07-15  
**Mode:** PLAN MODE  
**Compound command:** `/ce-plan`  
**Starting HEAD:** `361b8f7`  
**Verdict:** `PROD_FLEX_COLLABORATION_PHASE_1_PLAN_READY`

---

## 1. Verdict

**`PROD_FLEX_COLLABORATION_PHASE_1_PLAN_READY`**

One coherent Phase 1 implementation plan is ready for owner review. Architecture is accepted (OWNER-DECISION-08); implementation remains **NOT AUTHORIZED** until owner grants Phase 1 GO (G1–G4).

---

## 2. Repository truth

| Field | Value |
|-------|-------|
| Worktree | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Starting HEAD | `361b8f7` — OWNER-DECISION-08 sign-off |
| Accepted architecture | OPTION 5 hybrid; HELPER-only; sessions unchanged |
| Implementation status | **BLOCKED** |
| FLEX-01 | **COMPLETE** — read projection shipped, no frontend consumer |
| Runtime tooling | **CLOSED** at `e92d135` |
| Gate fixture order | `23099` — 13 materialized V2 tasks |

---

## 3. Current runtime truth

- **Backend canonical port:** `:8001` (not `:8000`)
- **Identity:** `(order_id, task_id)` where `task_id` = V2 `deterministic_task_key`
- **Sessions:** append-only in `execution_reality.tasks_json`; multi-worker capable
- **Principal:** `assigned_employee_id` on plan operational task only
- **Claim pool:** `_has_active_session_by_other` blocks principal claim when another session active
- **Collaboration read:** `GET .../task-collaboration-read` → 13 tasks on 23099, contract v1
- **No participant table** exists today
- **No join/help write API** exists today
- **Mobile `can_assist`:** hardcoded `false` in blueprint service

---

## 4. Product outcome

At Phase 1 implementation end (after future GO), WorkOS will have:

- Durable **HELPER collaboration authorization** distinct from assignment and sessions
- **Join/leave membership API** with idempotent, concurrency-safe semantics
- **Membership history** preserved with reactivation support
- **Extended read model** surfacing `helper_memberships[]` alongside session-derived workers
- **Unchanged** individual claim/start/complete behavior
- **Verifiable** on order 23099 via API probes and pytest

No owner-visible UI until Phase 3. No help invitation flow until Phase 2.

---

## 5. Options considered

| Option | Verdict |
|--------|---------|
| A — Sessions-only extension | **Reject** |
| B — `participants_json` blob | **Reject** |
| C — Membership-only normalized table | **Recommend Phase 1** |
| D — Membership + help in one phase | **Defer help to Phase 2** |
| E — Membership + session start bundled | **Reject** (violates P8) |

Full analysis: `.compound-engineering/prod-flex-collaboration-phase-1/plan.md`

---

## 6. Recommended Phase 1 scope

**One backend phase — Collaboration Membership Foundation:**

1. Migration: `execution_task_participants` (HELPER-only)
2. Membership service: join, leave, query
3. Join/leave API (operator + employee-mobile)
4. Membership read API
5. Collaboration read v1.1 extension (`helper_memberships[]`)
6. Eligibility guards (materialized V2, operational registry)
7. Pytest matrix + claim regression bundle
8. Runtime verification on order 23099
9. BUILD doc + OpenAPI manifest update
10. Optional write flag: `FLEX_MEMBERSHIP_API_ENABLED`

---

## 7. Explicitly deferred scope

| Deferred | Target phase |
|----------|--------------|
| Help request table + CRUD | Phase 2 |
| Split pools / `_has_active_session_by_other` bypass | Phase 2 |
| Helper session start (work verb) | Phase 2 |
| LEAVE stops own session | Phase 2 (optional contract) |
| `can_assist` backend truth | Phase 2 |
| Operation progress | Phase 3+ |
| Operator/Mobile UI | Phase 3 |
| Audit event timeline | Phase 3 |
| Legacy T-001 orders | Out of scope |
| Product System / snapshots | Forbidden |

---

## 8. Persistence design

**Table:** `execution_task_participants`  
**Parent:** `(order_id, task_id)` on materialized V2 operational task  
**Unique:** `(order_id, task_id, employee_id)`  
**Role:** `helper` only (app-enforced)  
**Reactivation:** Same row; LEAVE → inactive; re-JOIN → active  
**Migration:** Single `s57` off `s56` head; no backfill  
**Provenance:** Optional `execution_plan_id` (not parent key)

---

## 9. Identity and lifecycle

```text
Order 23099
  └── execution_plan.tasks_json
        └── operational_tasks[].task_id
              = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep" (example)
                    │
                    ├── execution_reality sessions (work proof)
                    └── execution_task_participants (authorization intent)
```

Lifecycle: none → JOIN(active) → LEAVE(inactive) → JOIN(reactivate)

---

## 10. JOIN and LEAVE semantics

**JOIN (binding):**
- Creates/reactivates HELPER membership
- Idempotent if already active
- Must NOT: session, claim, assignee, progress, complete

**LEAVE (binding):**
- Closes actor's own membership
- Must NOT: stop sessions, change principal, complete operation

---

## 11. Concurrency and idempotency

- DB unique constraint on `(order_id, task_id, employee_id)`
- `IntegrityError` → already_joined response
- Task-scoped lock + `FOR UPDATE` on membership row
- MOBILE-T06 claim concurrency tests must remain green

---

## 12. Migration and rollback

| Aspect | Plan |
|--------|------|
| Migration GO | Required separately (G2) |
| Revision | `s57_create_execution_task_participants` |
| SQLite | Inline unique in create_table |
| Backfill | None |
| Rollback | Drop table; reads revert to session-only |
| Feature flag off | Join/leave 503; reads return empty memberships |

---

## 13. API and read model

**Write (after GO):**
- `POST .../collaboration/join`
- `POST .../collaboration/leave`

**Read:**
- `GET .../collaboration/memberships`
- Extended `task-collaboration-read` v1.1 with `helper_memberships[]`

**No frontend client required** for Phase 1 value delivery.

---

## 14. Compatibility with sessions, assignment and claim

| Surface | Phase 1 touch |
|---------|---------------|
| Sessions | **None** |
| `assigned_employee_id` | **None** |
| Claim/start/complete | **None** |
| `_has_active_session_by_other` | **None** |
| FLEX-01 v1 fields | **Additive only** |
| `list_my_tasks` | **None** (membership ≠ my tasks yet) |

---

## 15. Help and pool boundaries

**Help:** Not in Phase 1. Direct JOIN by eligible employee sufficient for authorization foundation. Help table + accept→join in Phase 2.

**Pools:** `_has_active_session_by_other` **unchanged**. Join endpoint must NOT use claim-pool guard. Split `ajutor_solicitat` pool deferred to Phase 2.

---

## 16. UI and Mobile boundary

**Not in Phase 1.** Backend API + read model + tests + runtime proof deliver value. First owner-visible collaboration UI planned Phase 3. Employee Mobile join UX requires Phase 2 pools + Phase 3 wiring.

---

## 17. Testing strategy

| Tier | Command |
|------|---------|
| P0 | `pytest tests/test_execution_task_collaboration_read.py -q` |
| P0 | `pytest tests/test_employee_mobile_claim_concurrency.py -q` |
| P0 | `pytest tests/test_execution_task_participants.py -q` (new) |
| P1 | Integration HTTP tests for join/leave |
| P2 | Live probes on order 23099 |

15 new scenarios M1–M15 defined in plan.

---

## 18. Runtime verification plan

| Item | Value |
|------|-------|
| Backend URL | `http://127.0.0.1:8001` |
| Frontend URL | `http://127.0.0.1:3000` (smoke only) |
| Order ID | `23099` |
| Order code | `ORD-W5INT02-GATE` |
| Sample task ID | `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep` |
| Auth | `Bearer __DEV_BYPASS_TOKEN__` |

**Baseline probe:**
```
GET /api/v1/operator/orders/23099/task-collaboration-read
→ 200, contract_version=v1, 13 tasks, helper_memberships=[]
```

**After test join + leave:**
- Membership row active then inactive in DB
- `helper_memberships` reflects state in v1.1 read
- `actual_workers` unchanged (session-derived)
- `assigned_employee_id` unchanged
- Claim on unassigned task still 200

**Non-regression:**
- Order `23150` blocked fixture untouched
- `dev.db` mtime stable on read-only probes

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/flex_collab_phase1_runtime_evidence.json`

---

## 19. Implementation workstreams

| WS | Owner | Deliverable |
|----|-------|-------------|
| 1 | Schema | Migration + model + flag |
| 2 | Service | Join/leave/query + locks |
| 3 | API | Routers + auth |
| 4 | Read | v1.1 projection |
| 5 | QA | Tests + runtime + BUILD |

Single implementation owner integrates sequentially; one phase GO covers all.

---

## 20. Commit strategy

**3 commits within one phase:**

1. Migration + model + flag tests
2. Service + API + integration tests
3. Read v1.1 + regression green + runtime evidence + BUILD doc

Not 9 micro-commits. Not one monolithic commit.

---

## 21. Risks and blockers

| Risk | Severity | Status |
|------|----------|--------|
| JOIN bundled with session | High | Mitigated by tests + review |
| Dual PRINCIPAL row | High | HELPER-only enforced |
| Plan read as auto-GO | High | decision-log gates |
| 23099 fixture reset | Medium | Isolated test orders for destructive cases |
| `list_my_tasks` gap | Medium | Documented; Phase 3 |
| Alembic drift | Medium | BUILD_MIGRATION_HYGIENE |

**Blockers:** None for planning. Implementation blocked on owner GO.

---

## 22. Owner decisions required

Phase-level only (see `decision-log.md` G1–G12):

- **G1–G4:** Grant Phase 1 implementation, migration, API, read extension
- **G5–G8:** Reject help, pools, session start, UI in Phase 1 (recommended)
- **G9–G12:** Direct join, reactivation model, V2-only scope, write flag

Not field-by-field schema approval.

---

## 23. Recommended GO boundary

```
Owner grants ONE Phase 1 GO:
  ✅ Migration (s57)
  ✅ HELPER membership writes
  ✅ Join/leave API (membership only)
  ✅ Read v1.1 extension
  ❌ Help table
  ❌ Pool changes
  ❌ Session/assignment/claim changes
  ❌ UI / Mobile
```

---

## 24. What remains blocked

- Phase 1 implementation (until G1 signed)
- Migration (until G2 signed)
- All participant writes
- Help persistence
- Pool remediation
- UI / Mobile collaboration
- FLEX old wave numbering as implementation mandate

---

## 25. Honest opinion

The old FLEX-02/03/04 wave split was useful for research but would over-fragment implementation. Membership, migration, API, and read extension are **tightly coupled** — shipping membership without read surfacing creates dead infrastructure; shipping API without migration is impossible. One phase is right.

Help and pools are **genuinely separable**: you can authorize collaboration (membership row) without invitation flow or mobile pool UX. That is the correct cut.

The biggest product gap after Phase 1 will be **"I joined but I still can't see the task in My Tasks"** — that's expected and honest. Phase 3 fixes visibility. Do not cheat by auto-adding membership to `list_my_tasks` in Phase 1; that blurs membership with assignment.

Order 23099 remains the right verification spine. Do not mutate it destructively during tests; use isolated orders for join/leave cycles.

---

## 26. Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Score (1–10) | **9** — clear phase boundary; owner GO is the only gap |
| Roadmap position | Post ARCH-02 acceptance; pre Phase 1 implementation |
| Paused lanes | UI-TRUTH-01B, APP-AUTH-06G, runtime tooling (closed) |
| Dead pieces check | `participants_json` absent; help API absent; join API absent by design |
| Forbidden scope | Confirmed — plan-only, no writes |
| Cat sunt in directia stabilita | **88/100%** |

---

## Multitasking execution

| Role | Workstream | Access |
|------|------------|--------|
| A | Runtime and execution identity | Read-only |
| B | Persistence and migration | Read-only |
| C | Session, assignment, claim boundaries | Read-only |
| D | API and product flow | Read-only |
| E | Testing and rollout | Read-only |
| Coordinator | Integration + artifact write | Docs-only |

**Parallel read-only workstreams:** 5  
**Write agents:** None

---

## Artifacts

| Artifact | Path |
|----------|------|
| Plan | `.compound-engineering/prod-flex-collaboration-phase-1/plan.md` |
| Decision log | `.compound-engineering/prod-flex-collaboration-phase-1/decision-log.md` |
| This worklog | `docs/worklog/realignment/2026-07-15_prod_flex_collaboration_phase_1_plan.md` |

---

## Forbidden scope confirmation

No migration, DB schema change, backend code, frontend code, participant writes, session changes, assignment changes, claim changes, pool changes, Product System changes, push, or PR in this task.

**Confirmed.**

---

## DELIVERY FOOTER

```
Task: PROD-FLEX-COLLABORATION-PHASE-1-IMPLEMENTATION-PLAN
Starting HEAD: 361b8f7
Cursor mode: PLAN MODE
Compound command: /ce-plan
Multitasking: ENABLED
Parallel read-only workstreams: 5
Write access: DOCS ONLY — ONE COORDINATOR
Implementation: NO
Migration: NO
Participant writes: NO
UI: NO
Mobile: NO
FLEX implementation started: NO
Recommended Phase 1: Collaboration Membership Foundation — table + join/leave API + read v1.1 + tests + runtime proof
Deferred: Help table, split pools, helper session start, UI/Mobile, operation progress
Owner GO required: YES (G1–G4)
Plan: .compound-engineering/prod-flex-collaboration-phase-1/plan.md
Decision log: .compound-engineering/prod-flex-collaboration-phase-1/decision-log.md
Worklog: docs/worklog/realignment/2026-07-15_prod_flex_collaboration_phase_1_plan.md
Commit: YES (pending)
Push: NO
PR: NO
Verdict: PROD_FLEX_COLLABORATION_PHASE_1_PLAN_READY
```
