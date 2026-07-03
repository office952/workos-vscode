# Step 9 — Materialization Audit-Only + Task Graph Safety Contract

**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**HEAD before:** `e9f8033` — `docs(step9): record fresh runtime persist verification`  
**Scope:** Audit-only materialization mapping; read-only GET audit; **no** execution_tasks; **no** sessions  
**Status:** **PASS_READ_ONLY_AUDIT_ENDPOINT**

---

## 1. Git preflight

| Item | Value |
|------|-------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD (start) | `e9f8033` |
| Remote sync | In sync at start |
| Tracked code changes at start | **None** |

---

## 2. Documents read

Realignment: README, 00, 01–06, 09–11, 16–20. Step 8/9 worklogs including HTTP fresh persist verification.

---

## 3. DB audit — `execution_plan.id=2` / order `88002`

| Field | Value |
|-------|-------|
| Plan id | **2** |
| order_id | **88002** |
| order_code | `ORD-IV6-V2-1782815703-1` |
| source_quote_snapshot_v2_id | **3** |
| source_snapshot_code | `QSN2-2026-0003` |
| plan_source | `order_snapshot_v2` |
| tasks_json | present (14430 bytes) |
| planned_tasks | **12** |
| planned_operations | **17** |
| operational_tasks in envelope | **0** |
| execution_tasks_created | **false** |
| Order snapshot_v2_json | present — commercial + internal |
| execution_tasks table | **absent** in dev.db |
| execution_reality | **0** |
| Duplicate plans for 88002 | **1** row only |

---

## 4. Code audit summary

| Zona | Fișier | Ce face | Activ? | Risc | Recomandare |
|------|--------|---------|--------|------|-------------|
| Preview | `execution_plan_v2_preview_service.py` | Read-only from `orders.snapshot_v2_json` | **Yes** | Low | Keep — Step 9 entry |
| Persist draft | `execution_plan_v2_persist_service.py` | One `execution_plan` row | **Yes** | Low | Validated |
| Materialize POST | `execution_plan_v2_materialize_service.py` | Writes `operational_tasks[]` into envelope | **Yes** | **High if used without GO** | **BLOCKED** until owner GO |
| Task parser | `execution_plan_task_parser.py` | Pure mapping planned→operational | **Yes** | Medium | Reuse for audit dry-run |
| Readiness gates | `execution_plan_operational_readiness_service.py` | Blocks assign/start if not materialized | **Yes** | Low | Step 11+ boundary |
| Legacy plan | `execution_plan_service.py` | V1 from snapshot_line_items | **Legacy** | Parallel path | Blocked for V2 orders |
| Assignment | `execution_task_assignment_service.py` | Mutates tasks_json assignments | **Yes** | Sessions-adjacent | Out of scope |
| Employee Mobile | (no direct wiring in Step 9 path) | N/A | N/A | Low | Final-final |

**Key finding:** WorkOS V2 does **not** use an `execution_tasks` SQL table in dev. Materialization means `operational_tasks[]` inside `execution_plan.tasks_json`, not separate ORM rows.

---

## 5. Materialization contract (audit-only)

### Source priority

1. **Primary:** `execution_plan.tasks_json` → `planned_tasks[]` (frozen at persist)
2. **Upstream provenance:** `orders.snapshot_v2_json` — audit compares READINESS_GATE exclusions only; **not** re-generated at materialize

### Materializable task (future)

Must have: `task_key`, label, `canonical_task_type`, optional `source_operation_code`, sequence, dependencies, workcenter via machine_requirement, `estimated_minutes` (planning-only, may be null with warning).

### Non-operational (never materialize)

READINESS_GATE, dossier checks, pricing review, owner approval, admin transitions, commercial pricing logic.

### Future POST materialize fields (envelope `operational_tasks[]`)

`task_id`, `source_task_key`, `process_type`, `process_id`, `operational_status=pending`, `execution_plan_id`, `order_id`, dependencies, `estimated_time_minutes`, provenance — see `execution_plan_task_parser.py`.

### Idempotency (future POST)

Unique on plan + `source_task_key`; `operational_tasks_already_materialized` if envelope already has tasks; activation hash over planned subset.

### Guards (future POST)

Plan exists; `plan_source=order_snapshot_v2`; no sessions; no CE/QO/price; no Employee Mobile.

**Actual POST materialize:** **BLOCKED / NEEDS OWNER GO**

---

## 6. Implementation — read-only audit

| File | Change |
|------|--------|
| `schemas/execution_plan_v2_materialization_audit.py` | **NEW** — audit response schema |
| `services/execution_plan_v2_materialization_audit_service.py` | **NEW** — dry-run audit service |
| `routers/execution_plan_v2.py` | **NEW** GET routes |
| `tests/test_step9_materialization_audit.py` | **NEW** — side-effect guards |
| `docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md` | Minimal audit section |

### Endpoints

| Route | Method |
|-------|--------|
| `/api/v1/execution/plan-v2/{execution_plan_id}/materialization-audit` | GET |
| `/api/v1/execution/plan-v2/from-order/{order_id}/materialization-audit` | GET |

---

## 7. HTTP runtime (fresh backend)

| Item | Value |
|------|-------|
| Backend | `.\scripts\dev-backend.ps1` (fresh restart) |
| Request | `GET .../plan-v2/2/materialization-audit` |
| HTTP | **200** |
| mode | `audit_only` |
| materialization_status | `blocked_needs_owner_go` |
| dry_run_status | `ready_with_warnings` |
| execution_plan_id | **2** |
| order_id | **88002** |
| source_quote_snapshot_v2_id | **3** |
| candidates | **12** |
| non_operational | **1** (READINESS_GATE) |
| guards.writes_database | **false** |

DB counts unchanged after HTTP call.

---

## 8. Tests

```powershell
cd backend
Remove-Item test_placeholder.db -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_v2_persist.py tests/test_execution_plan_v2_preview.py tests/test_step9_order_snapshot_to_execution_plan.py tests/test_step9_materialization_audit.py tests/test_order_snapshot_v2_convert.py tests/test_step8_snapshot_acceptability.py -q
```

**Result:** **113 passed**

---

## 9. UI

**Not changed** — no natural read-only surface without new navigation; Step 9B UI visibility remains separate pass.

---

## 10. No-side-effects confirmation

No execution_tasks rows, no sessions, no POST materialize, no CE/QO/price, no Employee Mobile, no migration, no Step 8 changes.

---

## 11. What remains blocked

| Item | Status |
|------|--------|
| POST `materialize-tasks` on live order | **NEEDS OWNER GO** |
| execution_tasks table (if ever introduced) | **Not in dev schema** |
| Sessions / ExecutionActuals | Step 11+ |
| Employee Mobile | Final-final |
| UI read-only panel | Optional Step 9B |

---

## 12. Next recommended step

**Step 9B read-only UI visibility** for execution plan draft + materialization audit badge (`Audit only`, `blocked_needs_owner_go`), **or** owner GO decision for controlled POST materialize on plan `id=2` with backup + tests.

---

## 13. Direction score

**Roadmap alignment note:** 9/10

**Cat sunt in directia stabilita: 96/100%**
