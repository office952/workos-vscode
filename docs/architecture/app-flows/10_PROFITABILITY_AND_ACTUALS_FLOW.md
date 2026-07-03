# Profitability and Actuals Flow

**Current status:** PARTIAL

---

## 1. Purpose

**Post-job learning:** compare quoted commercial, estimated internal, and (future) actual cost/time — without retroactive quote changes. Sessions/ExecutionActuals collect real minutes (Step 11+).

---

## 2. Current status

**PARTIAL** — ProfitabilityAnalysis MVP GET + ExecutionDetail read-only panel **VALIDATED**; `actual_margin_*` and `actual_total_cost` **null**; sessions **FROZEN** on V2 not materialized orders.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| `/execution/:order_id` | `ExecutionDetail` | Profitability panel (10.4) | profitability GET | — | IMPLEMENTED_PREVIEW_ONLY | actuals null |
| `/reports`, `/reports/operational` | Reports | Ops summaries | report APIs | — | PARTIAL | — |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/profitability-analysis/order/{order_id}` | `profitability_analysis.py` | Read-only analysis | order snapshot_v2, quote | — | VALIDATED | MVP |
| POST | `/api/v1/execution/reality/start-task` | `execution.py` | Start session | operational task | execution_reality | FROZEN | Step 11+ |
| POST | `/api/v1/execution/reality/end-task` | same | End session | session | actual minutes | FROZEN | — |
| GET | `/api/v1/execution/reality/{order_id}` | same | Reality snapshot | sessions | — | FROZEN | 404 on 88002 |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `profitability_analysis_service.py` | MVP compare | order | quoted vs estimated; actual null | VALIDATED | no write-back |
| `execution_reality_service.py` | Sessions/actuals | materialized tasks | reality JSON | FROZEN | guards v2_not_materialized |
| `task_work_session_service` | Session rows | — | minutes | FROZEN | — |

---

## 6. Data contract

**Profitability MVP response (typical):**

| Field | Source | Status |
| ----- | ------ | ------ |
| `accepted_commercial_total` | order.snapshot_v2_json | populated |
| `estimated_internal_total` | snapshot | populated |
| `actual_total_cost` | HR/inventory actuals | **null** (deferred) |
| `actual_margin_*` | derived | **null** |
| `has_snapshot_v2` | bool | true on 88002 |
| `warnings[]` | legacy/missing actuals | present |

**Future actuals:** session minutes, material deviations — **must not** mutate accepted commercial price.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Order Snapshot V2 | commercial + internal totals | Profitability GET | read snapshot | STRONG | — |
| ExecutionPlan | planned minutes (null) | Future time compare | — | WEAK | DEC-006 |
| ExecutionActuals | sessions | Profitability actual side | — | MISSING | Step 11 |
| HR/pontaj | employee cost | actual_total_cost | — | MISSING | owner GO |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Quoted revenue (V2) | **Order Snapshot V2 `accepted_commercial_total`** |
| Estimated cost at accept | **snapshot `estimated_internal_total`** |
| Actual cost/time (future) | **ExecutionActuals / sessions** — not quote |
| Learning recommendations | **ProfitabilityAnalysis** — no quote rewrite |

---

## 9. What must not happen

- Retroactive quote/order price change from actuals.
- Profitability blocking pre-offer (read-only post-order).
- Starting sessions on `v2_not_materialized` plans.
- Using planning minutes as commercial price.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| actual margin null | HIGH | MVP by design | Full learning loop | Faza 7 + HR costing GO |
| No sessions on fixture 88002 | HIGH | operational_tasks empty | Actual minutes | Faza 3 then 6 |
| Planning minutes null | MEDIUM | plan preview | Estimated vs actual time | DEC-006 |
| Legacy orders without snapshot_v2 | MEDIUM | warning in service | Revenue source | Backfill policy |

---

## 11. Owner decisions

Owner GO required for HR/inventory actual costing formulas (Step 10 completion) — **PENDING_OWNER** at platform level.

---

## 12. Verification checklist

```powershell
GET /api/v1/profitability-analysis/order/88002
# Worklog: 2026-06-30_extended_qa_profitability_analysis_api.md
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_profitability*.py -q
```

---

## 13. Next safe step

Use profitability GET for quoted vs estimated on V2 orders only; defer actuals until Faza 6 GO.

**When sessions become safe:** After materialize GO + operational readiness `v2_operational_ready` (Doc 21 Faza 6).
