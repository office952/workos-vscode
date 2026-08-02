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

**Planned task fields:** `task_key`, `canonical_task_type`, `source_operation_code`, `estimated_minutes` (null + `PLANNING_MINUTES_SOURCE_REQUIRED`), `machine_requirement.workcenter` (from frozen Aggregate ops; registry-canonical codes required — see F7A/F7A.1), `depends_on_task_keys[]` (finish/process-aware DAG; no universal linear invent on EP V2 path)

**Historical fixture note (88002):** WC null + linear deps were true for that older Snapshot V2 and remain readable for regression. **Current controlled fixture (F7A/F7A.1):** parent WC stamped with registry codes (`WC_CNC_ROUTING`, `WC_LETTER_FORMING`, `WC_METAL_FAB`, `WC_ASSEMBLY`); DAG bond←face+side; aliases collapsed.

**Preview ignores:** commercial/internal pricing snapshots for task generation.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Order Snapshot V2 | frozen aggregate task_rules | ExecutionPlan preview | read snapshot | STRONG | Minutes still null (DEC-006); WC resolved on F7A.1 fixture |
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
| workcenter null (historical 88002) | CRITICAL (historical) | order 88002 | Assignment/scheduling | Use new F7A.1 fixture; do not rewrite 88002 |
| estimated_minutes null | HIGH | PLANNING_MINUTES_SOURCE_REQUIRED | Capacity / scheduling | DEC-006 remains open |
| Linear deps (historical / unresolved families) | MEDIUM | legacy frozen-graph preview only | Wrong shop order if wrong path | EP V2 uses process DAG; DEC-007 implemented on V2 |
| Duplicate lateral ops | CLOSED on F7A path | alias collapse DEC-003/004 | — | Keep collapse owner in bridge |
| Premount false task | CLOSED on F7A.1 | BOM-only hard ban DEC-002=A | — | No activation signal → no task |
| POST materialize blocked | CRITICAL | DEC-009=A | Shop runtime | Owner GO only after F7A.1 review |

---

## 11. Owner decisions

| Decision ID | Topic | Blocks materialize? | Status |
| ----------- | ----- | ------------------- | ------ |
| DEC-002 | premount BOM-only | Soft for materialize | **A** — hard synthesis ban (F7A.1) |
| DEC-003 | RETURN canonical | Soft | **A** — parent canonical; alias provenance (F7A) |
| DEC-004 | painting canonical | Soft | **A** — parent canonical; alias provenance (F7A) |
| DEC-005 | workcenter source | Soft | **A** — upstream Aggregate → freeze → plan; registry codes (F7A.1) |
| DEC-006 | planning minutes | Scheduling GO | PENDING — null + warning acceptable for draft |
| DEC-007 | dependency DAG | Soft | **B** — finish/process-aware on EP V2 (F7A) |
| DEC-009 | POST materialize | Yes | **A** — remain blocked until Owner sets B |

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

F7A/F7A.1 closed upstream alias/WC/premount/DAG gaps on the controlled fixture. Next: Owner DEC-009 decision only; no POST materialize until DEC-009=B.
