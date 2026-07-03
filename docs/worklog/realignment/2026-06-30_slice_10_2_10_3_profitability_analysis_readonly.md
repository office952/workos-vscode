# Slice 10.2 + 10.3 — ProfitabilityAnalysis Read-Only — 2026-06-30

## Status

**PASS**

Read-only `ProfitabilityAnalysisService`, Pydantic schema, and `GET /api/v1/profitability-analysis/order/{order_id}` implemented with contract tests. No UI, no write-back, no CostEngine/QuoteOrchestrator.

## Scope

- `ProfitabilityAnalysisService` — read-only analysis from Order Snapshot V2 + ExecutionReality
- `ProfitabilityAnalysisResponse` schema
- GET endpoint with auth
- Contract tests + immutability regression (Slice 10.1)

## Architecture readback summary

Per docs 09, 11, 16, 20:

- Accepted commercial from frozen `snapshot_v2_json.accepted_commercial_total`
- Estimated internal from `estimated_internal_total`
- Actual labor minutes from ExecutionReality when present
- Actual cost/margin **null** in MVP — HR/inventory costing not approved
- `retroactive_change_allowed=false`, `write_back_performed=false` always
- No `/price`, CostEngine, QuoteOrchestrator, session writes

## What changed

| File | Purpose |
|------|---------|
| `backend/schemas/profitability_analysis.py` | Response + variance models |
| `backend/services/profitability_analysis_service.py` | Read-only analysis logic |
| `backend/routers/profitability_analysis.py` | GET endpoint |
| `backend/tests/test_profitability_analysis.py` | Contract tests |

## What did not change

- UI, mobile, pricing, `/price`, CostEngine, QuoteOrchestrator
- ExecutionReality/session logic, Order/Quote mutation
- Batch PUT guard (WATCH unchanged)
- DB migrations, seeds, resets

## Endpoint behavior

| Case | HTTP |
|------|------|
| Valid order | 200 + `ProfitabilityAnalysisResponse` |
| Missing order | 404 `order_not_found` |
| Invalid id ≤ 0 | 422 `order_id_invalid` |

### Status values

| Status | When |
|--------|------|
| `estimated_only` | V2 snapshot, no ExecutionReality |
| `actuals_partial` | Reality exists, actual cost null (MVP) |
| `actuals_available` | Reserved — when actual_total_cost computable |
| `unsupported_legacy_order` | No V2, uses `total_amount` + warning |
| `missing_snapshot` | No V2 and no revenue |

### MVP null fields

`actual_total_cost`, `actual_materials_total`, `actual_margin_*`, `variance.cost_delta`, `actual_labor_minutes` (without reality), `estimated_margin_*` (without inputs)

## Tests / validation

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_profitability_analysis.py tests/test_orders_update_immutability.py -q
# 15 passed

.\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_v2_persist.py tests/test_execution_plan_v2_materialize.py -q
# optional regression
```

## Runtime verification

`GET http://127.0.0.1:8000/api/v1/profitability-analysis/order/88001`

```json
{
  "profitability_status": "estimated_only",
  "accepted_commercial_total": 1500.0,
  "estimated_internal_total": 620.0,
  "has_execution_reality": false,
  "retroactive_change_allowed": false,
  "write_back_performed": false
}
```

Backend `:8000` healthy (no restart required — reload picked up router).

## Owner verification

### API

- URL: `http://127.0.0.1:8000/api/v1/profitability-analysis/order/88001`
- Expected: `estimated_only`, commercial 1500, `retroactive_change_allowed=false`

### Tests

- `backend/tests/test_profitability_analysis.py`

### Browser smoke (no new UI)

- `http://127.0.0.1:3000/execution/88001` — readiness unchanged
- `http://127.0.0.1:3000/reports/operational` — plan metrics unchanged

**Nu există UI dedicat pentru Step 10 ProfitabilityAnalysis în Slice 10.2 + 10.3.**

## Commit

`feat(profitability): add read-only order analysis endpoint`

## What remains

- Slice 10.4 optional minimal UI — **OWNER_DECISION**
- HR/inventory costing for actual margin — **OWNER_DECISION**
- Batch PUT guard — **WATCH**
- 7G full runtime — **NOT STARTED**

## Next recommended step

Extended QA on profitability endpoint across fixture orders; or owner GO for Slice 10.4 minimal read-only UI panel.

## Direction score

**Cat sunt in directia stabilita: 93/100%**
