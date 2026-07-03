# ProfitabilityAnalysis — Post-Job Learning

**Version:** 1.0.3  
**Status:** Slice **10.1 IMPLEMENTED**; Slice **10.2+10.3 IMPLEMENTED + VALIDATED** (read-only MVP GET only); Slice **10.4** minimal panel on ExecutionDetail — **no dedicated profitability route**  
**Step:** 10 — **PARTIAL** (read-only MVP endpoint validated; complete post-job truth deferred; actual margin $ deferred)  
**Commits:** `45255a1` (API); `378b42b` (minimal UI panel)

---

## 1. Rolul sistemului

ProfitabilityAnalysis compares the **accepted commercial baseline** and **estimated internal baseline** against **execution reality when actuals exist**. In MVP, it can also return **`estimated_only`** analysis **before** ExecutionReality exists — that is **not** complete post-job profitability truth.

**Regulă:** **Nu** schimbă retroactiv oferta. **Nu** decide singur prețul inițial. **Nu** rulează înainte de execuție ca truth complet.

**Rol (target):** Să învețe sistemul dacă prețurile pe mp/ml/buc/set/minim au fost bune — **recomandările comerciale sunt viitoare și owner-approved, nu automate.**

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Comparații** | Commercial vs estimated vs actual |
| **Marjă estimată vs reală** | Percent and absolute |
| **Material variance** | Estimated vs consumed |
| **Time variance** | Plan/estimate vs ExecutionActuals |
| **Per-unit effective price** | lei/m², lei/ml, lei/literă realized |
| **Employee involvement** | Who contributed — from actuals |
| **Abatere analysis** | Root cause tags |
| **Recomandări viitoare** | Tune commercial rules — **future / owner GO only**, not automatic |
| **Report snapshots** | Analytics records |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Modificare quote acceptat |
| Modificare order commercial frozen |
| CommercialPriceProposal at offer time |
| Client invoice generation (**UNKNOWN** if separate system) |
| Real-time pricing during production |
| HR payroll execution |
| Automatic registry overwrite without owner approval |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Quote/Order snapshot | commercial_price, estimated_internal_cost |
| ExecutionActuals | Real minutes, materials |
| ExecutionPlan | Planned duration baseline |
| HR (internal) | Labor cost for margin — **NEEDS_OWNER_DECISION** |
| Inventory | Actual material costs |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Profitability report | Owner, production lead, finance |
| Rule tuning recommendations | Future CommercialPriceProposal / Registry — **OWNER_DECISION**, not auto-applied |
| Dashboards | Analytics only |
| Learning loop closure | Continuous improvement |

**Not client-facing** unless owner explicitly exports.

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Read-only ProfitabilityAnalysis MVP endpoint | **IMPLEMENTED + VALIDATED** — `GET /api/v1/profitability-analysis/order/{order_id}` (Slice 10.2+10.3) |
| Complete post-job profitability truth | **PARTIAL / deferred** — until HR labor costing and inventory/material actual costing are approved and implemented |
| Commercial at offer | Order Snapshot V2 `accepted_commercial_total` — **read-only input** |
| Estimated internal | Order Snapshot V2 `estimated_internal_total` — **read-only input** |
| Actual economics (MVP) | **PARTIAL** — ExecutionReality, sessions, materials are **read-only inputs**; `actual_total_cost` and `actual_margin_*` remain **null** until HR/inventory costing (**OWNER_DECISION**) |
| Order financial stability | Slice **10.1 IMPLEMENTED + VALIDATED** — individual + batch PUT guard on locked/V2 (`90ba918`, `453932f`) |
| Pre-offer margin guess | CommercialPriceProposal + EstimatedInternalCost preview services |

---

## 7. Conexiuni cu celelalte sisteme

```
Quote Snapshot (commercial + estimated at offer time)
    ↓
Order → ExecutionPlan → ExecutionActuals
    ↓
ProfitabilityAnalysis (THIS)
    ↓
Recommendations → Commercial Price Rules (future cycles, owner approved)
    ✗ Retroactive quote change
```

| Sistem | Relație |
|--------|---------|
| CommercialPriceProposal | Baseline quoted |
| EstimatedInternalCost | Baseline estimated |
| ExecutionActuals | Baseline actual |
| Pricing Registry | May receive recommended updates — owner GO |
| Cost Engine | **NO** automatic feedback to past quotes |

---

## 8. Reguli owner obligatorii

1. **`estimated_only`** is valid **before** ExecutionReality exists — not a substitute for complete post-job analysis.
2. Complete analysis **after** execution — or defined minimum actuals threshold — **NEEDS_OWNER_DECISION** (and requires HR/inventory costing for actual margin $).
2. Verify mp/ml/buc/set rules were economically correct — core purpose.
3. Real minutes used here — **correct role** for time data.
4. Recommendations ≠ automatic price changes.
5. Missing ProfitabilityAnalysis must **not** block commercial offer pre-production.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Actual margin $ incomplete | MVP nulls `actual_total_cost`, `actual_margin_*` — HR/inventory costing **OWNER_DECISION** | Expected MVP gap |
| Cost-plus today | No learning loop from proper baselines | `HIGH_RISK_DEVIATED` |
| Could be misbuilt on CE total | Would perpetuate wrong model | Risk for Step 10 — **forbidden in plan** |
| Dual snapshot V2 | **VALIDATED_WITH_GUARDS** — Step 8 live accept/convert (order `88002`); Step 9 persist draft plan `id=2` — **no** execution_tasks/sessions | Dependency for 10.2+10.3 |
| PUT order financial mutation | Was WATCH (batch bypass after 10.1) | **MITIGATED** — individual Slice 10.1 (`90ba918`); batch **was WATCH**, closed `453932f` |
| Actual margin $ in MVP | HR/inventory costing missing | **OWNER_DECISION** — `actual_margin_*` may be **null** |

---

## 10. Target state (Step 10)

### Slice 10.1 — Order financial immutability (**IMPLEMENTED**)

See [09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md](./09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md) §13.

### Slice 10.2 + 10.3 — Read-only ProfitabilityAnalysis MVP endpoint (**IMPLEMENTED + VALIDATED**)

**Scope boundary:** Read-only GET only. Does **not** implement complete post-job profitability truth, automatic commercial recommendations, or actual margin $.

| Item | Detail |
|------|--------|
| Service | `backend/services/profitability_analysis_service.py` — **read-only**, no CostEngine, no QuoteOrchestrator |
| Schema | `backend/schemas/profitability_analysis.py` — `ProfitabilityAnalysisResponse` |
| Router | `backend/routers/profitability_analysis.py` |
| Endpoint | `GET /api/v1/profitability-analysis/order/{order_id}` |
| Tests | `backend/tests/test_profitability_analysis.py` — 15 targeted (+ 61 execution plan V2 regression) |
| Writes | **None** — `retroactive_change_allowed: false`, `write_back_performed: false` always |
| Forbidden | `/price`, sessions create/start/stop, quote/order mutation |

#### HTTP behavior

| Case | HTTP | Detail |
|------|------|--------|
| Valid order | **200** | `ProfitabilityAnalysisResponse` |
| Missing order | **404** | `order_not_found` (e.g. order `99999999`) |
| Invalid id ≤ 0 | **422** | `order_id_invalid` |

#### `profitability_status` values

| Status | When |
|--------|------|
| `estimated_only` | V2 snapshot present; **no ExecutionReality required** — estimated baseline only |
| `actuals_partial` | ExecutionReality exists; actual cost null (MVP) |
| `actuals_available` | Reserved — when `actual_total_cost` computable |
| `unsupported_legacy_order` | No V2; uses `order.total_amount` + warning |
| `missing_snapshot` | No V2 and no revenue |

#### MVP null fields

`actual_total_cost`, `actual_materials_total`, `actual_margin_amount`, `actual_margin_percent`, `variance_estimated_vs_actual.cost_delta`, `actual_labor_minutes` (without ExecutionReality), `estimated_margin_*` (when inputs missing).

#### QA validation examples (2026-06-30)

| Order | Expected |
|-------|----------|
| **88001** (V2 fixture) | **200** — `estimated_only`; commercial 1500; internal 620; `has_execution_reality: false`; guard flags false |
| **99999999** | **404** — `order_not_found` |
| **1** (legacy E2E) | **200** — `unsupported_legacy_order`; `revenue_source: order.total_amount`; commercial 1398.25; `estimated_internal_total: null` |

**Worklogs:** `2026-06-30_slice_10_2_10_3_profitability_analysis_readonly.md`, `2026-06-30_extended_qa_profitability_analysis_api.md`

| Metric | Comparison |
|--------|------------|
| Commercial total | `accepted_commercial_total` from Snapshot V2 (fallback `order.total_amount` + warning) |
| Estimated internal | `estimated_internal_total` from Snapshot V2 |
| Actual labor minutes | `execution_reality.total_actual_time_minutes` when present |
| Actual material cost | **null in MVP** — materials observational only |
| Actual total cost | **null in MVP** — until HR/inventory costing (**OWNER_DECISION**) |
| Estimated margin | `commercial - estimated_internal` when both present |
| Actual margin | **null in MVP** if `actual_total_cost` null |
| Minutes variance | plan vs reality minutes when reality exists |

**Response shape (MVP):**

```
GET /api/v1/profitability-analysis/order/{order_id}
Response: {
  order_id, order_code, snapshot_version, has_snapshot_v2,
  revenue_source, accepted_commercial_total, estimated_internal_total,
  has_execution_reality, actual_total_cost, actual_labor_minutes,
  actual_materials_total, estimated_margin_amount, estimated_margin_percent,
  actual_margin_amount, actual_margin_percent,
  variance_estimated_vs_actual, profitability_status, warnings[],
  retroactive_change_allowed: false,
  write_back_performed: false
}
```

**UI:** **No dedicated Step 10 route or dashboard.** Slice **10.4** adds a **minimal read-only panel** on existing `ExecutionDetail` (`378b42b`) — displays GET response only; not a separate profitability product surface.

**Implementation plan:** `docs/worklog/realignment/2026-06-30_step_10_profitability_implementation_plan.md`

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Auto-reprice closed quotes from analysis |
| Run as pre-quote blocker |
| Use as CommercialPriceProposal engine |
| Client hourly billing retroactive from actuals |
| Apply recommendations without owner GO |
| Build on single cost-plus total without dual snapshot |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Dual snapshot input | V2 convert **VALIDATED** |
| Order PUT guard | Slice 10.1 individual + batch — **16** contract tests pass |
| Actuals complete | Step 9 hardening — **PARTIAL** |
| Read-only MVP GET | No write-back; no CE/QO — **VALIDATED** 10.2+10.3 |
| Complete post-job truth | **NOT** claimed — actual margin $ **deferred** |
| `estimated_only` without reality | **VALIDATED** — clearly not final profit |
| Per-unit metrics | mp/ml/buc/set — future beyond MVP |
| Recommendations only | No retroactive mutation |
| Owner review gate | Registry changes require GO |
