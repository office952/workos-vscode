# WorkOS Profitability Actual Read Model V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Verdict | **PASS WITH WARNINGS** |
| Worktree | `C:\w\workos_profitability_actual_read_model_v1` |
| Branch | `feat/profitability-actual-read-model-v1` |
| Base | `c9ea5c0a` |
| DB | `backend/qa-dbs/profitability_rm_v1.db` (copy of sessions QA DB with 40 min actual) |

---

## 1. Status

**PASS WITH WARNINGS**

- Labor monetary cost unavailable (`employee_cost_policy_missing`) â€” correct, not invented.
- Actual margin unavailable â€” correct until materials + Owner labor policy + job closed.
- Task coverage incomplete on 973019 (1/18 tasks with sessions).
- Estimated margin shown only from frozen commercial âˆ’ frozen EIC.

## 2. Research answers (summary)

1. Revenue: frozen `order_snapshot_v2.accepted_commercial_total`
2. EIC: frozen on snapshot
3. Actuals: 40 minutes on LED for 973019
4. Material actual money: missing on fixture
5. Employee cost policy: **not approved**
6. Legacy rates: not used
7. Full real margin today: **no**
8. Factual: commercial, EIC, minutes, estimated margin when both exist
9. Unavailable: labor lei, actual total cost, actual margin
10. Mixing risks: CostEngine/`/price` â€” not called
11. No migration
12. Audience: admin/manager
13. Operator must not see salaries/margins (permission `execution.plan_generate`)
14. Job closed: needs full coverage + policy â€” reason codes emitted

## 3. Architecture

`GET /api/v1/profitability-actual/order/{id}` â†’ `ProfitabilityActualReadModelService` composing snapshot + ExecutionActuals RM. UI: `ProfitabilityActualReadPanel` on ExecutionDetail.

## 4. Fixture proof (973019)

| Field | Result |
|-------|--------|
| actual_duration | **40** minutes available |
| planned_minutes / variance | unavailable |
| labor_actual_cost | unavailable |
| actual_margin | unavailable |
| accepted commercial | 847.5 RON (frozen) |
| estimated margin | available (~66.33) |
| snap/tasks hashes | unchanged vs assignment baseline |
| mutated.* | all false |

## 5. Files

- `backend/services/profitability_actual_read_model_service.py`
- `backend/routers/profitability_actual_read_model.py`
- `backend/tests/test_profitability_actual_read_model.py`
- `frontend/src/api/profitabilityActualReadModel.ts`
- `frontend/src/components/execution/ProfitabilityActualReadPanel.tsx`
- `frontend/src/pages/ExecutionDetail.tsx` (panel mount only)
- QA + worklog

## 6. Tests

Run: `test_profitability_actual_read_model.py` + live isolated DB proof.
Not run: full suites.

## 7. Direction score

**CÃ¢t sunt Ã®n direcÈ›ia stabilitÄƒ: 72/100%** â€” honest RM skeleton; not Profitability Complete.

## 8. Next

Owner policy for employee actual cost and/or material actuals â†’ then Profitability Complete.
