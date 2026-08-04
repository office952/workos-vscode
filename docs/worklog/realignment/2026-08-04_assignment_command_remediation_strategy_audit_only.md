# Assignment Command Remediation Strategy — Audit Only

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Status | **`ASSIGNMENT_REMEDIATION_STRATEGY_AUDIT = COMPLETE`** |
| Wave 5 | remains **`PARTIAL_BLOCKED`** |
| Wave 6 | **`NOT_AUTHORIZED`** |
| Mini decision | Strategy audit only — no assignment implementation/execution |
| Repo | `C:\Users\offic\workos_app_vs` (common git) |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `fa574d60` |
| Ancestry | `1e8d3344`, `6214ee7b`, `8386e3a6`, `9f236010`, `fa574d60` ⊂ HEAD (exit 0) |
| Preexisting tracked overlap | **none** |
| Untracked | `docs/qa/**` leftovers only — untouched |
| Production code changed | **NO** |
| FRONTEND_CHANGED | **NO** |
| BROWSER_PROOF | **NOT_APPLICABLE_TO_CODE_CHANGE** |

---

## Verdict block

```text
ASSIGNMENT_REMEDIATION_STRATEGY_AUDIT = COMPLETE
FINALIZATION_WAVE_5 = PARTIAL_BLOCKED
ASSIGNMENT_COMMAND_INVENTORY = VERIFIED
ASSIGNMENT_COMMAND_SAFETY = NOT_VERIFIED
AUTHORIZATION = PARTIAL_BLOCKED
IDEMPOTENCY = IDEMPOTENCY_PARTIAL
TRANSACTIONALITY = TRANSACTIONALITY_PARTIAL
CONCURRENCY_PROTECTION = CONCURRENCY_PARTIAL
SECURITY_BLOCKER = LEGACY_ASSIGNMENT_PATH_BYPASSES_CONTROLLED_REVALIDATION
ADDITIONAL_SECURITY_NOTE = DIRECT_SERVICE_ASSIGN_PATHS_BYPASS_DEC015_RM
PERSISTED_MUTATIONS = NONE
ASSIGNMENT_COMMAND_EXECUTED = NO
OWNER_DECISION_REQUIRED = YES
WAVE_6 = NOT_AUTHORIZED
SCHEMA_CHANGE_AUTHORIZED = FALSE (this task)
```

---

## Architecture readback

```text
Frozen truth     → ExecutionPlan V2 operational_tasks[]
Live reference   → employee/role/skill + machine/workcenter registries
Eligibility RO   → Wave 4 DEC-015 / F7C
Future command   → employee assignment (CLOSED)
Persisted result → assigned_employee_id embedded in tasks_json
Sessions / schedule / capacity / machine assign → separate / CLOSED / HOLD
```

Eligible ≠ selected ≠ assigned ≠ available ≠ scheduled ≠ authorized_to_start.  
Capable machine ≠ assigned/reserved machine.

---

## Command map

### A. Canonical HTTP path — ACTIVE_CANONICAL (code) / policy CLOSED

```text
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign
body: AssignPlanTaskRequest
  assigned_employee_id: int
  allow_reassign: bool = False
  controlled: bool = True          # injectable from client
→ get_current_user
→ require_permission("execution.task_assign")   # admin|manager|operator
→ if controlled:
     assign_operational_task_controlled
       → build_employee_eligibility_read_model (ops[] only)
       → match task_key
       → eligibility status gate
       → employee ∈ eligible_employees
       → reject active reality session
       → assign_plan_task(source=controlled_ops_graph_assign_v1)
→ else:   # controlled=false
     assign_plan_task(allow_reassign=True, source=manager_assign)
       # NO DEC-015 revalidation
```

Files: `backend/routers/execution.py`, `controlled_employee_assignment_service.py`, `execution_task_assignment_service.py`.

### B. Legacy HTTP bypass — ACTIVE_LEGACY / BYPASSABLE

| Aspect | Fact |
| ------ | ---- |
| Trigger | Request body `controlled: false` |
| Who can send | Any authenticated principal with `execution.task_assign` |
| FE production callers today | **None found** sending `controlled:false` (Ops-Graph uses `controlled:true`; Operator panel uses client default `true`) |
| Still reachable | **Yes** — HTTP/API/tests can inject the flag |
| Skips | DEC-015 RM, eligible list membership, controlled active-session check |
| Forces | `allow_reassign=True` (can overwrite other assignee) |
| Keeps | `is_assignable`, operational_tasks load, readiness mutation gate, FOR UPDATE, process lock |

Test caller: `backend/tests/test_execution_task_assignment.py` explicitly PATCH with `controlled: False`.

### C. Direct-service paths (bypass DEC-015 RM) — DEVIATED / BYPASSABLE relative to controlled contract

| Entry | File | Eligibility used | Class |
| ----- | ---- | ---------------- | ----- |
| `claim_my_task` → `assign_plan_task` | `employee_mobile_tasks_service.py` | `check_employee_operation_eligibility` (process/machine_type) | DEVIATED |
| `start_available_task` → `assign_plan_task` then session start | same | same matcher; rollback via `clear_plan_task_assignment` | DEVIATED |
| `dev_employee_mobile_sandu_fixture_service` | fixture helper | direct assign_plan_task | DEVIATED / test-dev |
| Unit/integration tests | `test_execution_operational_readiness_gates.py`, `test_execution_plan_task_parser_consumers.py`, etc. | direct service | test |

Employee Mobile is **FROZEN_FINAL_FINAL** for product rollout, but code paths remain inventoriable bypasses of DEC-015 RM.

### D. Frontend callers of mutate

| Caller | controlled | Class |
| ------ | ---------- | ----- |
| `MaterializedOpsGraph` assign picker | explicit `true` | ACTIVE_LEGACY UI (mutate surface outside ExecutionDetail RO) |
| `OperatorTaskAssignmentPanel` | default `true` (omit flag) | DEVIATED UX (full employee list; backend still revalidates if controlled) |
| `executionTaskAssignment.ts` | option defaults `true`; **can** pass `false` | COMPATIBILITY_BRIDGE API client |

### E. Persistence

- No separate assignment table.
- Write: `serialize_operational_tasks_to_plan_json` → replace `envelope.operational_tasks` → `plan.tasks_json` → `commit`.
- Entire operational_tasks list rewritten (envelope otherwise preserved).
- No assignment audit/event table write observed on success path.

---

## Authorization findings

| Control | Status |
| ------- | ------ |
| Authentication (`get_current_user`) | PROVEN (dependency present) |
| Global permission `execution.task_assign` | PROVEN — roles admin/manager/operator |
| Order-scoped authorization | **MISSING** |
| Plan-scoped authorization | **MISSING** (server picks latest plan by order_id) |
| Task-scoped authorization | PARTIAL — task must exist in ops; no ACL |
| Employee-scoped authorization (actor↔employee) | **MISSING** for manager assign; mobile uses self-user |
| Cross-order protection | **MISSING** → soft IDOR for any holder of permission |
| Cross-plan | N/A client plan_id (server chooses latest) |
| Arbitrary employee on controlled | PARTIAL — must be eligible |
| Arbitrary employee on `controlled=false` | **BYPASSABLE** — only `is_assignable` |
| Frontend-only guards | BYPASSABLE (must not trust) |
| Direct-service protection | **BYPASSABLE** — `assign_plan_task` callable without DEC-015 |
| Admin wildcard eligibility | not on controlled path; admin still has permission |

```text
AUTHORIZATION = PARTIAL_BLOCKED
SECURITY_BLOCKER = LEGACY_ASSIGNMENT_PATH_BYPASSES_CONTROLLED_REVALIDATION
ADDITIONAL_SECURITY_NOTE = DIRECT_SERVICE_ASSIGN_PATHS_BYPASS_DEC015_RM
IDOR = SOFT (permission-wide order access)
```

Answers (factual):

1. Who may assign? Roles mapped to `execution.task_assign` (admin/manager/operator).  
2. Org/tenant? No order-tenant binding proven on this route.  
3. Order belongs to context? **Not demonstrated** beyond path `order_id`.  
4. Plan belongs to order? Latest `ExecutionPlan` where `order_id=` — proven.  
5. Task belongs to plan? Must appear in `operational_tasks[]` — proven for persist path.  
6. Employee referable by actor? Manager path: any assignable employee id; mobile: self only.  
7. IDOR soft or hard? **Soft**.  
8. Task id from other order? If string collides across orders, lookup is order-scoped plan — mitigated.  
9. Employee from other context? **Yes**, if id exists and assignable (legacy) or eligible (controlled).  
10. Direct service without same protections? **Yes** (`assign_plan_task`).

---

## Idempotency findings

| Mechanism | Status |
| --------- | ------ |
| Unique constraint on assignee | MISSING |
| Idempotency key | MISSING |
| Request fingerprint store | MISSING |
| Task/plan version CAS from client | MISSING |
| Same-employee noop (`already_assigned`) | IMPLEMENTED_AND_PROVEN (code) |
| Other-employee conflict 409 | IMPLEMENTED_AND_PROVEN when `allow_reassign=false` |
| Legacy forces `allow_reassign=true` | BYPASSABLE — conflict protection weakened |
| DB row lock `SELECT FOR UPDATE` | IMPLEMENTED_NOT_PROVEN under multi-worker |
| Process `asyncio.Lock` | PARTIAL — single process only |
| Dedupe cache / event dedupe | MISSING |

### Duplicate / retry behavior (code-path analysis — not executed)

| Scenario | Current behavior | Risk |
| -------- | ---------------- | ---- |
| Double click same employee | Second returns `already_assigned` | Low |
| Double click two employees | One 409 if controlled; legacy may overwrite | High on legacy |
| Retry after timeout (commit unknown) | Client may retry; same employee → noop; other → conflict or overwrite (legacy) | Medium |
| Replay old request | No nonce; replay may reassign if allow_reassign | High on legacy |

```text
IDEMPOTENCY = IDEMPOTENCY_PARTIAL
```

### Strategy comparison (not implemented)

#### Strategy A — task-state compare-and-set (minimal schema)

```text
UPDATE ops task only if assigned_employee_id IS null
  OR (same employee) OR (allow_reassign AND expected_assignee matches)
optional: compare envelope plan_version / content hash
```

| | |
|--|--|
| Advantages | No new table; fits embedded JSON; closes lost silent overwrite if CAS fails closed |
| Risks | JSON CAS still whole-document rewrite; needs careful encoding of “expected state” |
| Schema | None or soft version field in envelope (Owner DEC) |
| Migration | None if pure read-modify-write under FOR UPDATE + null-check |
| Complexity | Low–medium |

#### Strategy B — idempotency key

```text
client/server key → persist request result → replay returns prior result
```

| | |
|--|--|
| Advantages | Clean timeout/retry semantics |
| Risks | New storage; TTL/cleanup; key scope (order+task+actor) |
| Schema | **Yes** (table or keyed store) |
| Migration | **Yes** if authorized later |
| Complexity | Medium–high |

#### Strategy C — uniqueness + transactional guard

```text
separate assignment row UNIQUE(plan_id, task_key) WHERE active
+ state validation in one DB transaction
```

| | |
|--|--|
| Advantages | DB-enforced single assignee; clearer concurrency |
| Risks | Dual-write with tasks_json; sync debt; large change |
| Schema | **Yes** |
| Migration | **Yes** |
| Complexity | High |

**Recommendation for Owner packet:** prefer **A + close bypass (Strategy Option 1 below)** before any schema. Add B only if timeout/retry SLA requires it. Defer C until embedding in `tasks_json` is proven insufficient.

---

## Transactionality findings

### Current boundary (controlled path)

```text
[no single TX wrapping eligibility]
build_employee_eligibility_read_model  → reads plan + registry (autocommit reads)
check ExecutionReality                 → read
assign_plan_task:
  begin implied by session
  lock plan FOR UPDATE
  assert_operational_mutation_allowed
  load tasks_json
  mutate one task dict
  serialize full operational_tasks into envelope
  commit
  refresh
response (no audit row write observed)
```

| Question | Answer |
| -------- | ------ |
| Eligibility + write atomic? | **No** |
| Employee active rechecked in write? | **Yes** (`is_assignable` inside `assign_plan_task`) |
| Role/skill rechecked in write? | **Only if controlled path re-ran RM before call** — not inside lock after RM |
| Task status / completed rechecked? | Reality `ended_at` checked inside lock |
| Plan version rechecked vs client? | **No** client version; FOR UPDATE serializes writers |
| Audit/event atomic with assign? | **No dedicated audit write** |
| Side effects after commit? | Response only |
| Entire tasks_json rewritten? | **operational_tasks array yes** (envelope otherwise preserved) |
| Lost update other tasks? | Mitigated by FOR UPDATE on plan row (single-writer); multi-worker depends on DB isolation |
| Retry after unknown commit? | No idempotency key |

```text
TRANSACTIONALITY = TRANSACTIONALITY_PARTIAL
```

---

## Concurrency / stale-state scenarios (10)

| # | Scenario | CURRENT_BEHAVIOR | RISK | EXISTING_PROTECTION | MISSING_PROTECTION | EXPECTED_TARGET |
| - | -------- | ---------------- | ---- | ------------------- | ------------------ | --------------- |
| 1 | Two different employees same task | One wins under FOR UPDATE; other 409 if controlled | Overwrite if legacy allow_reassign | FOR UPDATE, 409 | Cluster-safe lock; ban legacy overwrite | Exactly one assignee; loser 409 |
| 2 | Same employee twice | `already_assigned` noop | Low | Same-id short-circuit | Idempotency key for network ambiguity | Deterministic noop |
| 3 | Employee inactive between check and write | `is_assignable` in write path | Low–med | Lifecycle check in persist | None critical | 422 inactive |
| 4 | Role/skill lost between check and write | Controlled does not re-query RM inside lock | **Med** | Pre-write RM only | Revalidate eligibility inside lock | 422 not eligible |
| 5 | Task completed concurrently | 409 if reality.ended_at | Med | Reality check | Stronger status model | 409 completed |
| 6 | Plan version changes concurrently | Writers serialize on plan row | Med | FOR UPDATE | Client expected version | 409 version conflict |
| 7 | Other task in same JSON updated concurrently | Serialized by plan lock | Low if FOR UPDATE works | FOR UPDATE | Multi-worker proof | No silent clobber |
| 8 | Commit OK, client timeout, retry | Same emp → noop; other → conflict/overwrite | Med | already_assigned | Idempotency key / CAS | Safe replay |
| 9 | Legacy + canonical concurrent | Legacy can overwrite with allow_reassign=True | **High** | None between paths | Close or gate legacy | Single policy path |
| 10 | Assign OK, audit/event fails | No audit write today | Low now / future debt | N/A | Atomic audit if required | All-or-nothing |

```text
CONCURRENCY_PROTECTION = CONCURRENCY_PARTIAL
```

---

## Strategy options (for Owner)

### Option 1 — Minimal safe hardening (recommended first)

```text
scope: fail-closed controlled path only; no schema
```

Likely touch (future GO, not this task): `execution.py` (reject or permission-gate `controlled=false`), `controlled_employee_assignment_service.py` (revalidate eligibility inside/after lock), optional CAS null-check in `assign_plan_task`, docs/tests.

| Dimension | Assessment |
| --------- | ---------- |
| Schema / migration | None |
| Legacy compatibility | Breaks explicit `controlled=false` callers (tests + any external) — needs DEC-ASSIGN-01 |
| Auth model | Keep permission-wide **or** add order-scope later (DEC-ASSIGN-02) |
| Idempotency | CAS + same-employee noop |
| Transaction | Eligibility revalidate adjacent to write under FOR UPDATE |
| Audit/event | Unchanged unless DEC-ASSIGN-06 |
| Complexity | **Low** |
| Deploy risk | Low–medium (API contract change for legacy flag) |

### Option 2 — Canonical command consolidation

```text
scope: all assign mutations must call assign_operational_task_controlled (or shared pure validator)
```

Includes Option 1 plus wrapping mobile claim/start-from-available to DEC-015 RM (or Owner-accepted alternate policy), removing FE ability to send `controlled=false`, updating tests off legacy path.

| Dimension | Assessment |
| --------- | ---------- |
| Schema | None required |
| Legacy / Mobile | High touch; Mobile frozen — may stay blocked until Mobile GO |
| Complexity | **Medium** |
| Operational risk | Medium (many callers) |

### Option 3 — Strong transactional redesign

```text
scope: assignment entity + unique constraint + optional idempotency key + version
```

| Dimension | Assessment |
| --------- | ---------- |
| Schema / migration | **Required** — needs DEC-ASSIGN-04/05 |
| Dual-write vs tasks_json | Major risk |
| Complexity | **High** |
| Deploy risk | High |

**Cursor recommendation:** Owner should authorize **Option 1** decision packet first (close or hard-gate `controlled=false`, revalidate eligibility under lock, CAS). Defer Option 3 until Option 1 proven insufficient. Option 2 for Mobile/direct-service alignment when Employee Mobile unfreeze is considered — not now.

---

## Owner decisions required

```text
DEC-ASSIGN-01:
  Close controlled=false completely, or keep as gated compatibility bridge
  (e.g. admin-only + audit log)?  Recommendation: close for production paths; tests use controlled=true.

DEC-ASSIGN-02:
  Authorization order/plan/task scoped vs permission-wide?
  Recommendation: add order-scoped check before first real assign GO.

DEC-ASSIGN-03:
  Idempotency via task-state/version CAS, idempotency key, or both?
  Recommendation: CAS first (A); key (B) if timeout SLA demands.

DEC-ASSIGN-04:
  Is schema/constraint change authorized for concurrency?
  Recommendation: NOT yet — try Option 1 without schema.

DEC-ASSIGN-05:
  Keep assignment embedded in tasks_json vs separate model?
  Recommendation: keep embedded until Option 1 fails under load.

DEC-ASSIGN-06:
  Must audit/event be atomic with assignment?
  Recommendation: yes for production mutate GO; define minimal audit record.

DEC-ASSIGN-07:
  Official retry behavior after unknown result?
  Recommendation: clients retry safely only with same employee + CAS/idempotency; document 409 semantics.

DEC-ASSIGN-08:
  Compatibility for legacy consumers (tests, scripts, Ops-Graph, Mobile)?
  Recommendation: Ops-Graph stays controlled=true; Mobile remains frozen; tests migrate off controlled=false.
```

---

## Zero-mutation proof (fixture 880750)

| Metric | Before audit | After audit |
| ------ | ------------ | ----------- |
| DB path | `C:\w\psiso\backend\dev.db` (36163584 B) | same |
| plan_id | 23 | 23 |
| ops | 13 | 13 |
| execution_tasks_created | true | true |
| plan_version | `v2.preview_to_plan.1` | unchanged |
| tasks_json SHA-256 | `e120b0cb91ff500504a9beb62d8e7f6608f5a6a14df2ae1a743c5c111dbac0f2` | **identical** |
| updated_at | `2026-08-04 02:21:47.122899` | **identical** |
| assigned fields | 0 | 0 |
| reality rows | 0 | 0 |
| estimated_minutes null | 13/13 | 13/13 |
| PLANNING_MINUTES_SOURCE_REQUIRED | 13/13 | 13/13 |
| 880811 | 1847.5 | unchanged |
| 973019 | 847.5 | unchanged |
| 88002 | absent | unchanged |
| F7I | 15 / 1.5 / 35 / 20 EUR · 4/4 | unchanged (read from `commercial_rules_volumetric_v2.py`) |
| Scheduling | HOLD | HOLD |
| PATCH/assign executed | **NO** | **NO** |

---

## Tests and evidence

```text
NEW tests added this task: 0
Commands mutating assignment: 0
Static inspection: grep + source read of routes/services/FE/tests
RO sqlite: mode=ro URI
```

| Classification | Items |
| -------------- | ----- |
| SECURITY_BLOCKER | `controlled=false`; direct `assign_plan_task` without DEC-015 |
| INSUFFICIENT_EVIDENCE | Multi-worker FOR UPDATE under Postgres production; live concurrent race suites (forbidden here) |
| PRE_EXISTING | Legacy tests using `controlled=false`; Mobile claim paths |

No global green claim.

---

## Dead Pieces Check

| Piece | Class |
| ----- | ----- |
| PATCH controlled=true path | ACTIVE_CANONICAL (code) / policy CLOSED |
| PATCH controlled=false | ACTIVE_LEGACY / BYPASSABLE |
| Ops-Graph assign UI | ACTIVE_LEGACY |
| OperatorTaskAssignmentPanel | DEVIATED |
| Mobile claim/start assign | DEVIATED / FROZEN product |
| FE client optional controlled | COMPATIBILITY_BRIDGE |
| Wave 5 assignment-readiness GET | ACTIVE_CANONICAL RO audit |

```text
Dead pieces discovered: as table
Dead pieces touched: NONE
Dead pieces removed: NONE
Why removal was not authorized: LEGACY_PATH_REMOVAL_AUTHORIZED = FALSE
Future impact: Owner DEC-ASSIGN-01/08 decide retirement vs gated bridge
```

---

## Docs / files

| Action | Path |
| ------ | ---- |
| Created | this worklog |
| Updated | `21_WORKOS_IMPLEMENTATION_ROUTE.md` (next-step pointer only) |

Production command/schema/FE: **unchanged**.

---

## Scores

| Score | Value |
| ----- | ----- |
| Direction alignment | **86/100** |
| Operational completion | **30/100** |

Audit improved decision readiness; assignment remains closed and unsafe to authorize.

---

## Next recommended step

```text
OWNER DECISION ON ASSIGNMENT REMEDIATION STRATEGY
(DEC-ASSIGN-01 … DEC-ASSIGN-08)
```

Do **not** start Wave 6. Do **not** execute assignment. Do **not** remove legacy code until Owner decides.

---

## Method

1. Preflight clean at `fa574d60`.  
2. Grep all `controlled=false` / `assign_plan_task` / FE callers.  
3. Trace HTTP → controlled vs legacy → persist; inventory Mobile direct-service.  
4. Separate **inventory** (complete) from **safety** (not verified).  
5. Analyze 10 concurrency scenarios from code without writing DB.  
6. Compare Strategies A/B/C and Options 1/2/3; recommend Option 1 packet.  
7. Prove fixture hash unchanged via RO sqlite.

What could not be demonstrated without mutation: live multi-worker races, production Postgres isolation, real timeout/retry telemetry.
