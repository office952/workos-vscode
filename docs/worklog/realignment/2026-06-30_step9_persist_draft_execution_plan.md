# Step 9 — Persist Draft ExecutionPlan V2 from Order Snapshot

**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**Baseline HEAD (start):** `8dd67e9` — `feat(step9): preview execution plan from order snapshot`  
**Status:** **PASS_WITH_GUARDS**  
**Scope:** Persist one `execution_plan` draft row from Order snapshot V2 — **no** execution_tasks, **no** sessions

---

## 1. Owner GO

Owner GO received for Step 9 persist draft build on order `88002` / snapshot `3`.

---

## 2. Architecture readback

Docs read: realignment README, `00`, `09`, `10`, `11`, `16`, `17`, `20`.

| Rule | Verdict |
|------|---------|
| Step 9 draft persistence ≠ execution runtime | **YES** |
| Step 11+ for sessions/actuals | **YES** — not touched |
| Employee Mobile final-final | **YES** — not touched |
| Consume Order snapshot V2 | **YES** — preview → persist |
| No quote/pricing recalculation | **YES** |
| Task candidates in `tasks_json` only | **YES** — no `execution_tasks` table |

---

## 3. Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| Upstream | `origin/feature/step-7g-commercial-price-proposal` |
| HEAD (start) | `8dd67e9` |
| Tracked changes at start | **None** |

---

## 4. Persist path audit (pre-implementation)

| # | Question | Answer |
|---|----------|--------|
| 1 | Endpoint | `POST /api/v1/execution/plan-v2/from-order/{order_id}` |
| 2 | Calls preview first? | **YES** — `build_execution_plan_v2_preview()` |
| 3 | One `execution_plan` row? | **YES** |
| 4 | Creates execution_tasks? | **NO** |
| 5 | Creates sessions? | **NO** |
| 6 | `/price`, CE, QO? | **NO** — static + pytest guards |
| 7 | Existing schema only? | **YES** — no migration |
| 8 | Fields persisted | `order_id`, `order_code`, `snapshot_version`, `tasks_json` envelope, `plan_source`, `source_quote_snapshot_v2_id`, metadata hashes |
| 9 | Idempotency (before hardening) | **409 plan_already_exists** |
| 10 | Order 88002 at start | **No plan** (only plan id=1 for order 88001) |

**Verdict:** Safe persist path — not `BLOCKED_UNSAFE_PERSIST_PATH`.

---

## 5. DB baseline (read-only)

| Table | Count |
|-------|-------|
| orders | 3 |
| execution_plan | 1 (order 88001) |
| quote_snapshots_v2 | 3 |
| quotes | 4 |
| execution_tasks | table absent |

**Order 88002:** `quote_snapshot_v2_id=3`, dual snapshots present, no existing plan.

---

## 6. Implementation changes

| File | Change |
|------|--------|
| `backend/schemas/execution_plan_v2.py` | `already_exists` status; `persist_status`, `template_code`, `input_summary` on persist result |
| `backend/services/execution_plan_v2_persist_service.py` | Idempotent `already_exists` return; source snapshot mismatch 409; `template_code` in envelope |
| `backend/routers/execution_plan_v2.py` | HTTP 200 for `already_exists` |
| `backend/tests/test_execution_plan_v2_persist.py` | Updated idempotency expectations |
| `backend/tests/test_step9_order_snapshot_to_execution_plan.py` | Persist draft + idempotency tests |

**No** execution_tasks, sessions, UI, migration, CE, QO, `/price`.

---

## 7. Tests

```powershell
cd backend
Remove-Item test_placeholder.db -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_v2_persist.py tests/test_execution_plan_v2_preview.py tests/test_step9_order_snapshot_to_execution_plan.py tests/test_order_snapshot_v2_convert.py tests/test_step8_snapshot_acceptability.py -q
```

**Result:** **107 passed**

---

## 8. Runtime QA

| Item | Result |
|------|--------|
| Health | **200** — backend running |
| Backup | `backend/dev.backup-before-step9-plan-persist-20260630-140648.db` |
| HTTP POST `/plan-v2/from-order/88002` | **422 BLOCKED** — uvicorn served **stale code** (pre-READINESS_GATE skip from `8dd67e9`); error `blocked_unknown_task_type:vector_file_verification` |
| Service-level persist (current code, dev.db) | **PASS** |

### Service-level persist result (order 88002)

| Field | Value |
|-------|-------|
| status / persist_status | `persisted` |
| execution_plan_id | **2** |
| order_id | **88002** |
| source_quote_snapshot_v2_id | **3** |
| template_code | `TPL-VOLUMETRIC-LETTERS_v2` |
| planned_tasks in envelope | **12** |
| planned_operations | **17** |
| materials (aggregate) | **22** |
| execution_tasks_created | **false** |

### DB after persist

| Metric | Value |
|--------|-------|
| execution_plan count | 1 → **2** (+1) |
| Plans for 88002 | **[(2,)]** only |
| execution_tasks | unchanged (table absent) |
| Second persist call | `already_exists`, plan id **2**, count unchanged |

**Note:** Restart dev backend to pick up `8dd67e9`+ before HTTP runtime QA.

---

## 9. No-side-effects confirmation

Confirmed: no `/price`, CostEngine, QuoteOrchestrator, Pricing Registry, UI, migration, Alembic, seed, execution_tasks, sessions, Employee Mobile, Step 11, push, work in `C:\Users\offic\workos`.

---

## 10. What remains

| Item | Status |
|------|--------|
| Step 9 materialize operational_tasks | **BLOCKED** — separate build |
| Step 11 sessions/actuals | **NOT STARTED** |
| Planning minutes source | **OPEN** — `PLANNING_MINUTES_SOURCE_REQUIRED` |
| HTTP runtime on live backend | **Pending backend restart** |
| 7I / 10 / 11 | unchanged — NEEDS OWNER GO |

---

## 11. Next recommended step

**Docs sync** — update realignment roadmap/docs to mark Step 9 persist draft **VALIDATED_WITH_GUARDS** on order 88002; or **Step 9 preview UI read-only** if UI is next priority.

---

## 12. Direction score

**Cat sunt in directia stabilita: 95/100%**

Persist draft path validated on live order data; HTTP blocked only by stale running backend process.
