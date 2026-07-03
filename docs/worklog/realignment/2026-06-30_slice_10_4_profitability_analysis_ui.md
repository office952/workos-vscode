# Slice 10.4 — Minimal ProfitabilityAnalysis UI — 2026-06-30

## Status

**PASS**

Read-only `ProfitabilityAnalysisPanel` on existing `ExecutionDetail` page. Binds `GET /api/v1/profitability-analysis/order/{order_id}`. No redesign, no new route, no charts.

## Scope

- API client: `frontend/src/api/profitabilityAnalysis.ts`
- Panel: `frontend/src/components/execution/ProfitabilityAnalysisPanel.tsx`
- Integration: `frontend/src/pages/ExecutionDetail.tsx`
- Vitest: `frontend/src/api/profitabilityAnalysis.test.ts`

## Architecture readback summary

Per docs 16, 17, 20: UI displays GET result only; no profit calculation; no write-back; actual margin null in MVP; `estimated_only` when no reality; misleading labels avoided.

## What changed

| File | Change |
|------|--------|
| `frontend/src/api/profitabilityAnalysis.ts` | Types + `fetchProfitabilityAnalysis` |
| `frontend/src/components/execution/ProfitabilityAnalysisPanel.tsx` | Read-only panel |
| `frontend/src/pages/ExecutionDetail.tsx` | Renders panel when order loaded |
| `frontend/src/api/profitabilityAnalysis.test.ts` | Label contract tests |

## What did not change

- Backend, pricing, `/price`, CostEngine, QuoteOrchestrator, sessions, mobile, navigation, DB

## Tests / validation

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/api/profitabilityAnalysis.test.ts
# 2 passed

npx --yes pnpm@8.10.0 run build
# PASS
```

API smoke (pre-UI): `GET /api/v1/profitability-analysis/order/88001` → 200, `estimated_only`, commercial 1500.

## Browser QA (order 88001)

- Panel visible: **Profitability analysis** / **Estimated only**
- Accepted revenue: **1500.00 RON**
- Estimated internal: **620.00 RON**
- Estimated margin: **880.00 RON / 58.67%**
- Actual cost: **not available**
- Actuals not recorded yet message present
- No reprice/save buttons
- `/reports/operational` — no profitability panel (smoke OK)

## UI location

`http://127.0.0.1:3000/execution/88001` — section **Profitability analysis** below Observabilitate/Alerte.

## Forbidden path confirmation

All confirmed not done: backend endpoint changes, mobile, pricing, sessions, redesign, new page, charts, push.

## Commit

`feat(profitability): show read-only analysis on execution detail`

## What remains

- Batch PUT guard — WATCH
- HR/inventory actual costing — OWNER_DECISION
- Docs sync marking 10.4 UI — optional follow-up
- 7G runtime — NOT STARTED

## Next recommended step

Docs sync after Slice 10.4 (mark UI IMPLEMENTED in doc 16/20) or batch PUT guard audit.

## Direction score

**Cat sunt in directia stabilita: 96/100%**
