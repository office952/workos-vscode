# Execution Plan Flow

**Current status:** VALIDATED_WITH_GUARDS

---

## 1. Purpose

Transform **frozen Order Snapshot V2** technical graph into **execution plan draft** (`planned_tasks[]`) — preview, persist, materialization audit. Operational shop runtime (materialize, sessions) **blocked** pending owner decisions.

---

## 2. Current status

**VALIDATED_WITH_GUARDS** — preview + persist draft validated; HTTP fresh persist **PASS** (`e9f8033`); materialization audit GET exists; POST materialize **BLOCKED_NEEDS_OWNER_GO**.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| `/execution` | `ExecutionDashboard` | Plan list/overview | execution APIs | — | PARTIAL | — |
| `/execution/:order_id` | `ExecutionDetail` | Order execution detail | plan, profitability panel | assignment if materialized | PARTIAL | Profitability MVP read-only |
| `/execution/reality-review` | `OperationalRealityReview` | Reality review | read models | — | IMPLEMENTED_PREVIEW_ONLY | — |

**Step 9B UI (Faza 1):** NOT_STARTED — planned read-only plan + gap badges.

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| POST | `/api/v1/execution/plan-v2/preview/{order_id}` | `execution_plan_v2.py` | Read-only preview | `orders.snapshot_v2_json` | — | VALIDATED | `no_write=true` |
| POST | `/api/v1/execution/plan-v2/from-order/{order_id}` | same | Persist draft | snapshot | `execution_plan.tasks_json` | VALIDATED_WITH_GUARDS | HTTP fresh PASS |
| GET | `/api/v1/execution/plan-v2/{plan_id}/materialization-audit` | same | Dry-run audit | plan envelope | — | IMPLEMENTED_PREVIEW_ONLY | — |
| GET | `/api/v1/execution/plan-v2/from-order/{order_id}/materialization-audit` | same | Audit by order | plan | — | IMPLEMENTED_PREVIEW_ONLY | — |
| POST | `/api/v1/execution/plan-v2/materialize-tasks/{order_id}` | same | Materialize ops | planned_tasks | operational_tasks | BLOCKED_NEEDS_OWNER_GO | DEC-009 |
| GET | `/api/v1/execution/plan/{order_id}` | `execution.py` | Legacy/V2 plan get | plan row | — | VALIDATED | — |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `execution_plan_v2_preview_service.py` | Build preview | order.snapshot_v2_json | `ExecutionPlanV2Preview` | VALIDATED | task_rules driver |
| `execution_plan_v2_persist_service.py` | Persist draft | preview | execution_plan row | VALIDATED_WITH_GUARDS | idempotent |
| `execution_plan_v2_materialization_audit_service.py` | Audit dry-run | tasks_json | audit report | IMPLEMENTED_PREVIEW_ONLY | GET only |
| `execution_plan_v2_materialize_service.py` | Materialize | planned_tasks | operational_tasks | BLOCKED_NEEDS_OWNER_GO | Not exercised live |
| `execution_plan_task_parser.py` | Parse envelope | tasks_json | planned vs operational | VALIDATED | no fallback to planned for ops |
| `models/execution_plan.py` | Persistence | — | tasks_json, source metadata | VALIDATED | plan `id=2` fixture |

---

## 6. Data contract

**`tasks_json` V2 envelope:**

| Key | Role |
| --- | ---- |
| `planned_tasks[]` | 12 tasks from task_rules; READINESS_GATE excluded |
| `planned_operations[]` | 17 aggregate ops (includes orphans) |
| `operational_tasks[]` | **empty** until materialize |
| `execution_tasks_created` | false |
| `plan_source` | `order_snapshot_v2` |
| `source_quote_snapshot_v2_id` | 3 (fixture) |

**Planned task fields:** `task_key`, `canonical_task_type`, `source_operation_code`, `estimated_minutes` (null), `machine_requirement.workcenter` (null on fixture), `depends_on_task_keys[]` (linear chain)

**Preview ignores:** commercial/internal pricing snapshots for task generation.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Order Snapshot V2 | frozen aggregate task_rules | ExecutionPlan preview | read snapshot | STRONG | WC/minutes null |
| ExecutionPlan persist | tasks_json | Materialization audit | dry-run | STRONG | — |
| ExecutionPlan | materialize (blocked) | operational_tasks | envelope | MISSING | DEC-009 |
| operational_tasks | assignment service | Employees | employee_id on task | MISSING | Not materialized |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Task list (draft) | **`execution_plan.tasks_json.planned_tasks[]`** after persist |
| Upstream structure | **Frozen** `product_aggregate_snapshot.task_contract.task_rules` |
| Operational tasks (future) | **`operational_tasks[]`** after materialize GO |
| Live Intake task preview | **NOT truth** |

---

## 9. What must not happen

- POST materialize before DEC-003/004/005/007/009 owner GO.
- Re-read live Intake or `/price` when building plan from order.
- Treat planned_tasks as running shop tasks (not materialized).
- Create sessions at persist/preview time.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| workcenter null (12/12) | CRITICAL | order 88002 | Assignment/scheduling | DEC-005 |
| estimated_minutes null | HIGH | PLANNING_MINUTES_SOURCE_REQUIRED | Capacity | DEC-006 |
| Linear dependencies | HIGH | `_build_dependencies` | Wrong shop order | DEC-007 |
| Duplicate lateral ops in aggregate | HIGH | 17 ops vs 12 tasks | Double materialize | DEC-003/004 |
| POST materialize blocked | CRITICAL | owner review | Shop runtime | DEC-009 |

---

## 11. Owner decisions

| Decision ID | Topic | Blocks materialize? | Status |
| ----------- | ----- | ------------------- | ------ |
| DEC-003 | RETURN canonical | Yes | PENDING_OWNER |
| DEC-004 | painting canonical | Yes | PENDING_OWNER |
| DEC-005 | workcenter source | Yes | PENDING_OWNER |
| DEC-006 | planning minutes | Scheduling GO | PENDING_OWNER |
| DEC-007 | dependency DAG | Yes (production) | PENDING_OWNER |
| DEC-009 | POST materialize | Yes | PENDING_OWNER (remain blocked) |

---

## 12. Verification checklist

```powershell
# HTTP fresh PASS evidence — worklog 2026-06-30_step9_http_fresh_persist_verification.md
POST /api/v1/execution/plan-v2/from-order/88002  -> already_exists, plan id=2
GET  /api/v1/execution/plan-v2/from-order/88002/materialization-audit
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_v2*.py -q
```

---

## 13. Next safe step

Owner DEC-003/004/005 first; Step 9B UI read-only with gap badges (DEC-008=A); no POST materialize.
