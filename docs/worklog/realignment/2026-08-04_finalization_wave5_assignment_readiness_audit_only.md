# Finalization Wave 5 — Assignment Readiness Audit-Only (CORRECTED)

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Correction | `WAVE_5_REPORT_CORRECTION_ONLY` after Owner `REJECT_AND_RETURN_TO_CURSOR` |
| Mini decision | `OWNER_GO = FINALIZATION_WAVE_5_AUDIT_ONLY` · `IMPLEMENT_REAL_ASSIGNMENT = NO` |
| Prior incorrect verdict | `PASS` (withdrawn) |
| Corrected verdict | **`FINALIZATION_WAVE_5 = PARTIAL_BLOCKED`** |
| Repo | `C:\Users\offic\workos_app_vs` (common git dir) |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Wave 4 checkpoint HEAD at Wave 5 start | `8386e3a6` |
| Wave 4 implementation | `6214ee7b` |
| Wave 3 materialize | `1e8d3344` |
| Wave 5 implementation | `9f236010` |
| Wave 5 worklog tip note | `e110b1da` (+1 line Final HEAD) |
| Correction tip (this update) | recorded at commit time |

---

## 1. Corrected status block (mandatory)

```text
FINALIZATION_WAVE_5 = PARTIAL_BLOCKED
ASSIGNMENT_READINESS_AUDIT_SURFACE = IMPLEMENTED
ASSIGNMENT_COMMAND_INVENTORY = VERIFIED
ASSIGNMENT_COMMAND_SAFETY = NOT_VERIFIED
CANDIDATE_SELECTION_VALIDATION = PARTIAL
AUTHORIZATION = PARTIAL_BLOCKED
BLOCKER = LEGACY_CONTROLLED_FALSE_ASSIGNMENT_PATH_IS_BYPASSABLE
SECURITY_BLOCKER = LEGACY_ASSIGNMENT_PATH_BYPASSES_CONTROLLED_REVALIDATION
IDEMPOTENCY = IDEMPOTENCY_PARTIAL
TRANSACTIONALITY = TRANSACTIONALITY_PARTIAL
CONCURRENCY = CONCURRENCY_PARTIAL
ASSIGNMENT_COMMAND_EXECUTED = NO
EMPLOYEE_ASSIGNMENTS = 0
TEAM_ASSIGNMENTS = 0
MACHINE_ASSIGNMENTS = 0
SESSIONS = 0
SCHEDULING = HOLD
CAPACITY_ALLOCATION = NOT_STARTED
PERSISTED_MUTATIONS = NONE
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
PRODUCTION_ROLLOUT = NOT_AUTHORIZED
```

Why not PASS: inventory of the mutatable command exists and was researched, but **command safety is not verified** while `controlled=false` remains callable and idempotency/transactionality remain partial.

---

## 2. Preflight (commands + results)

```text
Get-Location                         → C:/w/psiso
git rev-parse --show-toplevel        → C:/w/psiso
git rev-parse --git-common-dir       → C:/Users/offic/workos_app_vs/.git
git branch --show-current            → feat/f7i-owner-rate-activation
git rev-parse HEAD (at correction)   → e110b1da48c8735d43b3ba68d6748c395aab4fc1 (before correction commit)
git merge-base --is-ancestor 1e8d3344 HEAD → exit 0
git merge-base --is-ancestor 6214ee7b HEAD → exit 0
git merge-base --is-ancestor 8386e3a6 HEAD → exit 0
git merge-base --is-ancestor 9f236010 HEAD → exit 0
```

### Preexisting changes (not Wave 5; not committed)

Tracked modifications overlapping Wave 5 scope at Wave 5 start: **none**.

Untracked only (user leftovers under `docs/qa/**`, worklogs) — **left untouched**, not staged.

### Commit evidence

**`9f236010`** — `feat(execution): add assignment readiness audit` — 17 files, +3582/−7  
**`e110b1da`** — `docs(execution): record Wave 5 final HEAD in worklog` — 1 file, +1 line  

`git diff --name-status 8386e3a6..e110b1da` (exact list):

```text
M backend/routers/execution_plan_v2.py
A backend/services/assignment_readiness_audit_service.py
A backend/tests/test_finalization_wave5_assignment_readiness_audit.py
M docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md
M docs/architecture/realignment/12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md
M docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md
A docs/qa/workos-wave5-assignment-readiness-audit-v1/* (README, JSON dumps, screenshots/.gitignore)
A docs/worklog/realignment/2026-08-04_finalization_wave5_assignment_readiness_audit_only.md
M frontend/src/api/execution.ts
A frontend/src/components/execution-result/AssignmentReadinessPanel.tsx
A frontend/src/components/execution-result/assignmentReadinessDisplay.test.ts
M frontend/src/pages/ExecutionDetail.step9b.test.tsx
M frontend/src/pages/ExecutionDetail.tsx
```

No DB, screenshots PNG, logs, secrets, artwork, or dependency lockfiles in those commits.

---

## 3. Architecture justification (production code changes)

```text
IMPLEMENTATION_MODE = VERIFY_AND_HARDEN (with production surfaces)
PRODUCTION_CODE_CHANGES = YES (backend RO GET + FE panel)
```

| Change | Justification |
| ------ | ------------- |
| `GET …/assignment-readiness` | Option **B** from Owner Wave 5 alternatives: compose Wave 4 RMs + command inventory + hypothetical candidate eval without calling PATCH assign. Eligibility alone does not answer “already assigned / active session / command contract / authorized=false”. |
| `AssignmentReadinessPanel` | Owner-visible honesty on `/execution/:order_id` (UI is Owner reality). Display-only; no Assign button. |
| Why not docs-only (A) | Would leave Ops-Graph as the only surface that knows assignment exists — misleading. |
| Why not extend eligibility (C) | Would overload DEC-015 envelope with command-contract concerns. |
| Ownership | Read-only aggregation; **not** a second task registry. Task source remains `operational_tasks[]`. Mutating authority remains PATCH assign (CLOSED for Wave 5 GO). |
| Stale risk | Live registry + plan JSON at request time; no persistent cache; `side_effects=none`. |

**Honest admission:** introducing production UI/backend went beyond “docs-only audit”. It remains within Owner-allowed “scoped RO Assignment Readiness Audit” / VERIFY_AND_HARDEN, but must not be sold as PASS for command safety.

---

## 4. Environment / runtime identity

| Item | Evidence |
| ---- | -------- |
| APP_ENV | `development` (Wave 5 uvicorn start env) |
| PRODUCTION | FALSE |
| DB absolute path | `C:\w\psiso\backend\dev.db` |
| DB size | 36163584 bytes |
| BE Wave 5 code | `:8002` · PID listener **9032** · cmdline `uvicorn main:app --port 8002 --host 127.0.0.1` (venv python 27704 parent) |
| BE Wave 4 stale | `:8001` · PID **4584** · still listening; **does not** serve Wave 5 route (404 assignment-readiness) |
| FE Wave 5 | `:3001` · PID **9820** vite · started with `BACKEND_PORT=8002` |
| FE Wave 4 | `:3000` · proxies older BE; left running; not killed |
| Health | `GET :8002/health` → `{"status":"healthy"}` |

Non-production proof: development env vars + local sqlite path under worktree + Staging UI chrome; no production deploy.

---

## 5. Fixture identity (complete)

| Field | Value |
| ----- | ----- |
| order_id | 880750 / `ORD-WAVE2-QA-880750` |
| plan_id | 23 |
| operational_tasks | 13 |
| execution_tasks_created | **true** (envelope field) |
| algorithm | **SHA-256** over raw `execution_plan.tasks_json` bytes |
| tasks_json sha256 | `e120b0cb91ff500504a9beb62d8e7f6608f5a6a14df2ae1a743c5c111dbac0f2` |
| plan updated_at | `2026-08-04 02:21:47.122899` |
| assigned_employee_id count | **0** |
| execution_reality rows for 880750 | **0** |
| estimated_time_minutes | **null** on all 13 |
| warning | `PLANNING_MINUTES_SOURCE_REQUIRED` (+ `PLANNING_MINUTES_SOURCE_MISSING`) on all 13 |

### Task keys + frozen workcenters (`workcenter` field)

| task_id (suffix) | workcenter | depends_on (suffixes) |
| ---------------- | ---------- | --------------------- |
| vector_prep | WC_PREPRESS | [] |
| cnc_face_cut | WC_CNC_ROUTING | vector_prep |
| back_cut | WC_CNC_ROUTING | vector_prep |
| return_profile_forming | WC_LETTER_FORMING | [] |
| return_face_bonding | WC_METAL_FAB | cnc_face_cut, return_profile_forming |
| painting | WC_ASSEMBLY | return_face_bonding |
| led_install_letters | WC_LED_ASSEMBLY | back_cut |
| electrical_letters | WC_LED_ASSEMBLY | led_install_letters |
| assembly_letters | WC_ASSEMBLY | back_cut, electrical, led, painting, return_face_bonding |
| vinyl_application | WC_VINYL_APPLICATION | assembly_letters, return_face_bonding |
| mounting_template_cnc_cut | WC_CNC_ROUTING | vector_prep |
| qc_letters | WC_ASSEMBLY | assembly_letters, vinyl_application |
| packaging | WC_ASSEMBLY | qc_letters |

**Foil/vinyl finish-aware edge:** `vinyl_application` depends on `assembly_letters` **and** `return_face_bonding` (not CNC-only). Unchanged vs Wave 3 materialization.

### Zero-mutation after Wave 5 GET reads (before = after)

| Metric | Before reads | After reads |
| ------ | ------------ | ----------- |
| tasks_json sha256 | `e120b0cb91ff500504a9beb62d8e7f6608f5a6a14df2ae1a743c5c111dbac0f2` | identical |
| updated_at | `2026-08-04 02:21:47.122899` | identical |
| ops count | 13 | 13 |
| execution_tasks_created | true | true |
| assigned count | 0 | 0 |
| reality rows | 0 | 0 |
| 880811 total / ops / plan | 1847.5 / 5 / 22 | unchanged (`orders.updated_at` 2026-08-03 00:06:15.954195) |
| 973019 total / ops / plan | 847.5 / 18 / 21 | unchanged |
| 88002 | absent from this DB | unchanged |
| F7I | 15 / 1.5 / 35 / 20 EUR · 4/4 in `commercial_rules_volumetric_v2.py` | unchanged |

Assignment/team/machine/session/attendance/scheduling tables: no dedicated assignment table; state is JSON-embedded. Counts remain 0 for 880750.

---

## 6. Command inventory + call graph

### Canonical (controlled) path — ACTIVE_CANONICAL code / policy CLOSED

```text
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign
→ AssignPlanTaskRequest { assigned_employee_id:int, allow_reassign:bool=False, controlled:bool=True }
→ get_current_user + require_permission("execution.task_assign")
→ [controlled=true] assign_operational_task_controlled(...)
   → build_employee_eligibility_read_model(db, order_id)   # operational_tasks[] only
   → match task_key == path task_id
   → reject blocked_* / not_required / not ready|ready_with_warnings
   → require assigned_employee_id ∈ eligible_employees
   → reject active ExecutionReality session for task
   → assign_plan_task(...)
→ [controlled=false] assign_plan_task(..., allow_reassign=True, source=manager_assign)  # BYPASS
```

`assign_plan_task`:

```text
validate ids → Employees lookup + is_assignable
→ asyncio.Lock(order_id, task_id)          # process-local
→ latest ExecutionPlan by order_id DESC + SELECT FOR UPDATE
→ assert_operational_mutation_allowed
→ load operational tasks from tasks_json   # no planned_tasks fallback
→ reject if reality.ended_at
→ 409 if other assignee and not allow_reassign
→ same assignee → already_assigned (no rewrite)
→ else embed assigned_employee_id (+ assignment_updated_at, assignment_source)
→ db.commit + refresh
→ response; sessions_created=0 / actuals_created=0 on controlled enrich path
```

### Component classification

| Component | Status |
| --------- | ------ |
| HTTP route PATCH assign | IMPLEMENTED_AND_PROVEN |
| Request schema | IMPLEMENTED_AND_PROVEN |
| Auth: JWT + `execution.task_assign` | IMPLEMENTED_AND_PROVEN |
| Order→latest plan | IMPLEMENTED_AND_PROVEN |
| Task in operational_tasks[] | IMPLEMENTED_AND_PROVEN |
| Employee lookup + is_assignable | IMPLEMENTED_AND_PROVEN |
| DEC-015 eligibility revalidation (controlled) | IMPLEMENTED_AND_PROVEN |
| Frontend eligibility/roles/skills as truth | absent on controlled path |
| Active session guard | IMPLEMENTED (controlled only) |
| Persistence (tasks_json embed) | IMPLEMENTED_AND_PROVEN |
| Downstream sessions/capacity | IMPLEMENTED_AND_PROVEN as none |
| Order-owner scoped authz | MISSING (org permission only) → IDOR soft |
| Idempotency key / unique constraint / ETag | MISSING |
| Multi-worker lock | MISSING (process-local only) |
| Owner GO gate inside command | MISSING |
| **`controlled=false` bypass** | **BYPASSABLE / ACTIVE_LEGACY** |
| Mobile claim/start assign paths | DEVIATED (Employee Mobile frozen; out of Wave 5 mutate) |
| Machine assignment mutation | MISSING |
| Assignment readiness GET | IMPLEMENTED (Wave 5 RO surface) |

### Frontend callers of mutate

| Caller | Notes |
| ------ | ----- |
| `assignExecutionPlanTask` | `frontend/src/api/executionTaskAssignment.ts` |
| `MaterializedOpsGraph` | controlled:true picker — ACTIVE_LEGACY relative to ExecutionDetail RO |
| `OperatorTaskAssignmentPanel` | lists employees; still hits same PATCH |

Wave 5 UI on ExecutionDetail does **not** call assign.

---

## 7. Idempotency / transactionality / concurrency (explicit)

### IDEMPOTENCY_PARTIAL — what exists

- Same employee re-PATCH → `already_assigned: true`, no rewrite
- Different employee without `allow_reassign` → 409
- No Idempotency-Key header
- No DB unique constraint (JSON blob)
- No expected version / ETag from client

### IDEMPOTENCY_PARTIAL — what is missing / unknown under load

- Duplicate click across workers may race before FOR UPDATE
- Retry after timeout: client may not know if commit landed (no idempotency key)
- Two candidates concurrent: FOR UPDATE serializes per plan row in one DB; **not proven** across multi-worker without shared lock manager

### TRANSACTIONALITY_PARTIAL — what exists

- Single-entity write: one `ExecutionPlan.tasks_json` + one `commit`
- Exception before commit → prior state remains
- Controlled path: eligibility read then mutate — **not one atomic TX spanning registry drift**

### TRANSACTIONALITY_PARTIAL — gaps

- No multi-entity outbox; partial risk low for assign-alone
- `clear_plan_task_assignment` (session rollback helper) has **no** assign lock
- If employee becomes inactive between eligibility read and persist: controlled re-checks `is_assignable` inside `assign_plan_task` — **partial mitigation**
- If eligibility changes between read and write: second assign_plan_task does **not** re-run DEC-015 (controlled already ran it once; race window remains)

### CONCURRENCY_PARTIAL

- Protections: process `asyncio.Lock`, `SELECT FOR UPDATE`, 409 conflict
- Gaps: multi-worker, no plan/task version token, eligibility not revalidated inside DB lock

---

## 8. Authorization / IDOR / security

| Case | Result |
| ---- | ------ |
| Unauthenticated PATCH | denied by `get_current_user` (framework; not re-proven this wave) |
| Missing `execution.task_assign` | denied by `require_permission` |
| Cross-order with permission | **ALLOWED** — soft IDOR; no order-owner check |
| Cross-plan | plan_id not client-chosen; latest plan for order |
| Arbitrary task | 404 if not in ops / eligibility |
| Arbitrary employee controlled | 422 not eligible |
| Arbitrary employee `controlled=false` | **BYPASS** — only `is_assignable` |
| Frontend `eligible=true` | ignored (not in schema) |
| Admin wildcard eligibility | not used on controlled path |
| HR PII / rates on readiness GET | not exposed (id, display_name, provenance only) |
| Wave 5 GET mutation | proven none on fixture (sha/updated_at stable) |

```text
BLOCKER = LEGACY_CONTROLLED_FALSE_ASSIGNMENT_PATH_IS_BYPASSABLE
SECURITY_BLOCKER = LEGACY_ASSIGNMENT_PATH_BYPASSES_CONTROLLED_REVALIDATION
AUTHORIZATION = PARTIAL_BLOCKED
ASSIGNMENT_COMMAND_SAFETY = NOT_VERIFIED
```

Owner may schedule remediation in a later GO; existence of bypass **blocks** declaring the command contract safe.

---

## 9. Candidate validation matrix

| State | Covered how | Classification |
| ----- | ------------ | -------------- |
| NOT_ELIGIBLE (not in list) | pure unit test | PROVEN |
| VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT still authorized=false | pure unit + live hyp on CNC/emp7 | PROVEN |
| TASK_ALREADY_ASSIGNED | pure unit | PROVEN |
| forged eligible flag ignored | pure unit | PROVEN |
| CANDIDATE_NOT_FOUND | runtime hyp path / audit | PARTIAL |
| blocked_not_materialized / no planned fallback | integration test | PROVEN |
| zero mutation on audit GET | integration test | PROVEN |
| CANDIDATE_INACTIVE | code path exists (`is_assignable`) | IMPLEMENTED_NOT_PROVEN in Wave 5 suite |
| ELIGIBILITY_REQUIREMENTS_NOT_CONFIGURED | code path | IMPLEMENTED_NOT_PROVEN (dedicated case) |
| ORDER_PLAN_MISMATCH / TASK_PLAN_MISMATCH | not a client plan_id API | N/A path / INSUFFICIENT_EVIDENCE as negative HTTP suite |
| task completed / cancelled | assign_plan_task 409 ended_at | IMPLEMENTED_NOT_PROVEN in Wave 5 suite |
| duplicate same employee | assign_plan_task already_assigned | IMPLEMENTED_NOT_PROVEN in Wave 5 suite |
| cross-order HTTP deny | MISSING (current auth allows) | SECURITY_BLOCKER / gap |
| authorization false always on audit | live GET wave5_boundary | PROVEN |

```text
CANDIDATE_SELECTION_VALIDATION = PARTIAL
```

---

## 10. Tests (commands + counts)

```powershell
cd backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_finalization_wave5_assignment_readiness_audit.py `
  tests/test_controlled_employee_assignment.py --ignore=tests/manual
# → 11 passed

cd frontend
npx pnpm@8.10.0 exec vitest run `
  src/components/execution-result/assignmentReadinessDisplay.test.ts `
  src/pages/ExecutionDetail.step9b.test.tsx
# → 3 passed (2 files)
```

| Suite | Count | Notes |
| ----- | ----- | ----- |
| Wave 5 audit | 8 | zero mutation, pure eval, no planned fallback, stable GET |
| Controlled assign unit | 3 | reject / accept-mocked; **mutating path not executed on fixture** |
| FE display + Step9B mock | 3 | no browser e2e matrix |

Failure classification this correction: **none new**. Gaps above = **INSUFFICIENT_EVIDENCE** / **SECURITY_BLOCKER**, not greenwashed.

Full frontend lint/typecheck/build: **not claimed green** (subset only).

---

## 11. Runtime API proof

```text
GET http://127.0.0.1:8002/api/v1/execution/plan-v2/from-order/880750/assignment-readiness
Authorization: Bearer __DEV_BYPASS_TOKEN__
→ status=ok side_effects=none ops=13 assign=0 machine=0
→ wave5_boundary.assignment_authorized=false
→ command_contract.idempotency=IDEMPOTENCY_PARTIAL
→ command_contract.transactionality=TRANSACTIONALITY_PARTIAL
→ legacy_bypass=ACTIVE_LEGACY / BYPASSABLE
```

Hypothetical (no write): CNC face cut + employee 7 → `VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT` + `assignment_authorized=false`.

Dumps: `docs/qa/workos-wave5-assignment-readiness-audit-v1/*.json`

---

## 12. UI evidence (frontend touched)

| Item | Evidence |
| ---- | -------- |
| URL | `http://127.0.0.1:3001/execution/880750` |
| Section | Pregătire pentru atribuire |
| Expected badges | Assignment neautorizat; 13 taskuri; 13 neatribuite; Programare HOLD; Atribuiri 0 · Utilaje 0 |
| Minutes | null |
| Forbidden actions | Assign / Auto-assign / Materialize / Schedule / Start / Stop — absent on dangerous-button scan |
| Viewport 1920 light | local `screenshots/wave5-880750-1920-light.png` (not committed) |
| Viewport ~1366 light | local `screenshots/wave5-880750-1366-light.png` (not committed) |
| Dark | NOT_OFFICIALLY_SUPPORTED (secondary) |
| Loading/error/empty/partial UI states | **INSUFFICIENT_EVIDENCE** (panel code paths exist; not browser-matrix proven) |
| already-assigned / inactive candidate UI | **INSUFFICIENT_EVIDENCE** (fixture has 0 assignments) |

---

## 13. Dead pieces

| Piece | Class |
| ----- | ----- |
| `controlled=false` PATCH path | ACTIVE_LEGACY / BYPASSABLE — **blocker** |
| Ops-Graph Assign UI | ACTIVE_LEGACY |
| OperatorTaskAssignmentPanel | DEVIATED UX |
| Mobile claim/start | DEVIATED / FROZEN Employee Mobile |
| Finish/intake “assignment” services | OUT_OF_SCOPE domain |

Dead pieces removed: **NONE**.

---

## 14. Scores (corrected)

| Score | Value | Note |
| ----- | ----- | ---- |
| Direction alignment | **84/100** | operational_tasks source kept; no mutate; readiness RO |
| Operational completion | **28/100** | bypassable command; partial idempotency/TX; no sessions/scheduling; audit ≠ shop floor |

---

## 15. Exact next step

```text
DO NOT START WAVE 6.
DO NOT EXECUTE ASSIGNMENT.
WAVE_5 remains PARTIAL_BLOCKED until Owner decides remediation of:
  LEGACY_CONTROLLED_FALSE_ASSIGNMENT_PATH_IS_BYPASSABLE
  + idempotency/transactionality/concurrency strategy
```

Recommended unauthorized research only after Owner accepts this corrected report:

```text
Owner decision packet on legacy bypass + authz scope + idempotency/TX
(no mutation until explicit GO)
```

---

## 16. Honest opinion

Wave 5’s real value is the blocker discovery: a controlled path exists, but a legacy `controlled=false` bypass and only partial idempotency/transactionality mean the command is **not** ready. Calling that PASS was incorrect. `PARTIAL_BLOCKED` is the honest status.
