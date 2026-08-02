# OWNER DECISION DOSSIER â€” Actual Cost & Job Closure Gate V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Track | **F2 only** |
| Status | **OWNER_DECISION_REQUIRED** |
| Worktree | `C:\w\workos_actual_cost_policy_gate_v1` |
| Branch | `feat/actual-cost-job-closure-gate-v1` |
| Base SHA | `3669ec86` |
| Fixture | Order **973019** / ExecutionPlan **21** |
| Runtime writes | **NONE** (research + contract design only) |
| Financial formulas implemented | **NONE** |

---

## Verdict

```text
OWNER_DECISION_REQUIRED
```

Nu existÄƒ politicÄƒ Owner demonstratÄƒ pentru costul real al muncii, pentru valuarea actualelor de material la momentul consumului, sau pentru Ã®nchiderea canonicÄƒ a lucrÄƒrii. Profitability Actual Read Model V1 rÄƒmÃ¢ne corect incomplet. **Nu se implementeazÄƒ formule financiare Ã®n aceastÄƒ rundÄƒ.**

---

## 1. Current truth (accepted)

| Item | Value |
|------|-------|
| Accepted commercial revenue | **847.5 RON** (frozen Order Snapshot V2) |
| Estimated internal margin | ~66.33 from frozen EIC only |
| Execution actual | **40 minutes** (operational truth; isolated QA DB in prior round) |
| Labor actual cost | unavailable â€” `employee_cost_policy_missing` |
| Actual material cost | unavailable â€” `actual_material_cost_missing` |
| Actual margin | unavailable |
| Job closure | **not canonically demonstrated** |
| Canonical RM | `profitability_actual_read_model_service.py` |
| Forbidden fallbacks (already coded) | `workcenter.rate_per_hour`, `cost_lunar_firmaÃ·hours`, commercial tariffs |

---

## 2. Canonical sources

| Domain | Path / symbol | Role for F2 |
|--------|---------------|-------------|
| Operational minutes | `controlled_task_session_service` â†’ `execution_reality.tasks_json` | Canonical actual time |
| Profitability RM | `profitability_actual_read_model_service.ProfitabilityActualReadModelService.build` | Honest incomplete RM |
| Order lifecycle | `validators/status_lifecycle.py` (`createdâ†’â€¦â†’completed`) | Status machine â€” **not** job-cost closure |
| Task end vs complete | `execution_reality_service.end_task` + `completion_fields` | Session end â‰  completion |
| Inventory deduction | `inventory_deduction_service.deduct_materials` + `StockMovement` | Explicit consume; not auto on complete |
| Material catalog cost | `inventory_materials.unit_cost` + `inventory_material_price_history` | Valuation inputs â€” policy needed |
| Employee cost fields | `Employees.cost_lunar_firma`, `monthly_internal_pay_amount` | CostEngine estimate inputs â€” **not** actual job cost authority |
| RBAC profit | `permissions.reports.view_profit` (admin/manager); frontend `view:reports_profit` | Target access model |

---

## 3. Legacy / ambiguous sources (do not auto-promote)

| Source | Why ambiguous |
|--------|----------------|
| `workcenter_rates.rate_per_hour` | Planned/pricing configuration; RM forbids as labor actual |
| `CostEngineConfigService.average_labour_hour_cost` | Monthly aggregate for estimates |
| `profitability_analysis_service` | Legacy; values materials at **current** catalog unit cost at read; weaker auth (`get_current_user` only) |
| `post_job_truth_service` material valuation | Same catalog-at-read convention |
| Operator registry `employee_id` from browser | DEV/identity gate issue â€” not a cost source; STAGING/PROD must fail closed |

---

## 4. Policy options â€” A. Employee actual labor cost (max 3)

### Policy A1 â€” Effective internal cost per employee (period-dated)

| Aspect | Detail |
|--------|--------|
| Formula (conceptual) | `labor_actual = Î£ (session_minutes / 60) Ã— employee_internal_hourly_cost(as_of session_start)` |
| Source | New (or hardened) employee cost version table; **not** net/gross salary as silent fallback |
| Includes | Owner-defined internal burden (must be explicit: base internal + employer contributions? overhead?) |
| Effective dating | Required: `valid_from` / `valid_to` per employee cost row |
| Confidentiality | Nominal rates = HR/finance only; never operator UI |
| Auditability | High if versioned + session timestamps |
| Advantage | Closest to â€œcost real al angajatuluiâ€ |
| Risk | Sensitive data; incomplete history; migration of `cost_lunar_firma` semantics |
| Profitability impact | Unlocks `labor_actual_cost` when policy + dating present |
| HR impact | HR owns rate maintenance; ops only sees minutes |
| Migration | Likely: new table or versioned columns; backfill policy TBD by Owner |

### Policy A2 â€” Standardized internal cost per role / skill

| Aspect | Detail |
|--------|--------|
| Formula | `labor_actual = Î£ (session_minutes / 60) Ã— role_or_skill_standard_rate(as_of)` |
| Source | Role/skill rate card (new contract) |
| Includes | Blended standard; no nominal employee pay |
| Effective dating | Rate card versions |
| Confidentiality | Lower leakage than A1; still not for operators |
| Auditability | Mediumâ€“high |
| Advantage | Simpler privacy; stable planningâ†”actual comparison |
| Risk | Less â€œrealâ€ per person; role mapping gaps |
| Profitability impact | Unlocks labor money without exposing payroll |
| HR impact | HR/ops define role rates; less payroll coupling |
| Migration | Need roleâ†”employee mapping quality |

### Policy A3 â€” Standardized cost per workcenter / operation

| Aspect | Detail |
|--------|--------|
| Formula | `labor_actual = Î£ (session_minutes / 60) Ã— workcenter_or_operation_standard_rate(as_of)` |
| Source | Could reuse `workcenter_rates` **only if Owner re-scopes** it from commercial/planned pricing to internal actual â€” currently forbidden |
| Includes | Machine/op standard, not person |
| Effective dating | Missing today on workcenter rates |
| Confidentiality | Usually lower sensitivity |
| Auditability | Medium; conflates pricing with actual cost if same table |
| Advantage | Aligns with shop-floor ops language |
| Risk | Contaminates pricing registry; falsely treats WC rate as labor truth |
| Profitability impact | Unlocks labor money; weak employee attribution |
| HR impact | Minimal |
| Migration | Rate history + clear split pricing vs internal actual |

**Recommendation (non-binding):** Prefer **A2** as default Owner option if privacy and speed matter; prefer **A1** if finance requires employee-true job costing and accepts HR versioning. **Do not** silently pick A3 via existing `rate_per_hour`.

---

## 5. Material actuals contract (proposed)

Separate states â€” **reservation â‰  consumption**:

| State | Meaning | Inventory write? |
|-------|---------|------------------|
| Estimated | Frozen EIC / plan materials | No |
| Reserved | Soft hold (if/when implemented) | No stock out |
| Released | Released to floor | Policy-dependent |
| Consumed | Explicit deduction â†’ `StockMovement` | Yes (already permissioned) |
| Returned | Reverse movement | Yes |
| Lost / diverted | Deviation record + approval | Yes after approval |
| Effective cost | Monetary value of consumed (+ approved deviations) | Valuation policy |

**Valuation options for Owner (not implemented):**

1. **Transaction-time snapshot** on `StockMovement` (recommended for audit).
2. **As-of price history** resolve `inventory_material_price_history` at `performed_at`.
3. **Catalog-at-read** (legacy analysis today) â€” **reject for closure-grade actuals**.

Until Owner picks valuation + completeness rules, RM keeps `actual_material_cost_missing`.

---

## 6. Job closed contract (proposed â€” no auto-close)

A job is **closed** only when **all** of the following are true (server-owned timestamp + authorized actor):

1. All **mandatory** operational tasks are completed (completion identity present â€” not merely session ended).
2. **No active session** on the order.
3. Material actuals for the order are **finalized** per Owner policy (consumed/returned/deviations approved â€” or explicit waiver).
4. External costs (if any) recorded or explicitly marked N/A.
5. Authorized **close** action by role (manager/admin or Owner-defined) with server timestamp.
6. Optional: freeze a closure snapshot of commercial + operational + cost inputs (immutable).

**Out of scope this round:** auto-close, UI close button that mutates without Owner policy, tying `orders.status=completed` without the above.

Current RM heuristic (`coverage_ratio` + no open sessions) is **diagnostic only**, reason `job_not_closed` â€” not canonical closure.

---

## 7. Access / privacy matrix

| Role | Minutes / sessions | Material qty operational | Labor rate / salary | Actual margin / profit | Close job |
|------|--------------------|--------------------------|---------------------|------------------------|-----------|
| operator | Own / assigned task truth | Operational capture only | **No** | **No** | No |
| supervisor* | Floor operational | Operational | **No** (unless Owner maps to manager) | **No** | No (unless Owner) |
| manager | Yes | Yes | Policy-gated summary; no raw salary unless HR grant | Yes if `reports.view_profit` | Proposed yes |
| finance | Yes | Yes | Yes (need) | Yes | Proposed yes / co-sign |
| HR | Employee cost maintenance | No product margin | Yes | No product margin by default | No |
| admin | Yes | Yes | Yes | Yes | Yes |
| unknown | Fail closed | Fail closed | Fail closed | Fail closed | Fail closed |

\* â€œsupervisorâ€ is not a first-class backend role today â€” map to manager or operator per Owner.

**UI hiding â‰  authorization.** Legacy `profitability_analysis` route must be tightened to match `reports.view_profit` after Owner GO (separate implementation CP).

---

## 8. Completeness policy (for RM)

Actual margin becomes available only when:

1. Owner labor policy selected + rates resolvable for all sessions with actual minutes.
2. Material actual cost available per valuation policy (or explicit zero-consumption attestation).
3. Job closed per Â§6.
4. Commercial accepted revenue still frozen (no quote write-back).

Otherwise keep `unavailable` + reason codes â€” **never 0**.

---

## 9. Migration impact

| Area | If A1 | If A2 | If A3 |
|------|-------|-------|-------|
| HR schema | High | Medium | Low |
| Workcenter rates | Untouched | Untouched | High (split pricing vs actual) |
| Inventory movements | Snapshot/as-of cost column | Same | Same |
| Sessions / ExecutionActuals | Read-only consumers | Same | Same |
| Pricing / EIC / snapshot | **No write-back** | Same | Same |
| Legacy ProfitabilityAnalysis | Deprecate or gate | Same | Same |

---

## 10. Exact Owner questions

1. **Labor policy:** A1, A2, or A3? If A1, what exact burden components are in â€œinternal hourly costâ€?
2. **Salary fields:** May `cost_lunar_firma` / `monthly_internal_pay_amount` seed A1 under explicit mapping, or must a new rate table be authored from scratch?
3. **Material valuation:** snapshot-on-movement vs as-of history vs reject catalog-at-read?
4. **Job closed:** Confirm Â§6 checklist; who is authorized to close; is `orders.status=completed` coupled or separate?
5. **Deviations:** Must approved material deviations exist before close, or waivable?
6. **Access:** Confirm matrix Â§7; should legacy profitability route be fail-closed for non-manager immediately?
7. **Effective dating start:** From which date must historical sessions (e.g. 973019 LED 40 min) become monetizable?

---

## 11. What stays unavailable until decision

- `labor_actual_cost`
- `actual_material_cost` (closure-grade)
- `actual_total_cost`
- `actual_margin`
- â€œProfitability Completeâ€
- Any payroll / salary mutation
- Job auto-close

Operational minutes and commercial 847.5 RON remain valid.

---

## 12. Next plan after Owner decision

1. Implement chosen labor policy behind RM (no UI invention of rates).
2. Implement material valuation + completeness gates.
3. Implement authorized job-close command + snapshot freeze.
4. Tighten legacy analysis auth; demote/remove UI ambiguity.
5. Then â€” and only then â€” declare path to Profitability Complete.

---

## 13. Direction score (honest)

CÃ¢t sunt Ã®n direcÈ›ia stabilitÄƒ: **88/100%** pentru gate-ul de decizie (research + contract).
CÃ¢t sunt spre Profitability Complete: **0%** (blocked on Owner).
