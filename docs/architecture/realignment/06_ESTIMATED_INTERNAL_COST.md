# EstimatedInternalCost — Pre-Production Internal Estimate

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Step:** 7H (non-hourly realignment — NEEDS OWNER GO)

---

## 1. Rolul sistemului

EstimatedInternalCost estimează **costul intern înainte de producție** — materiale, consumabile, pierderi, operații estimate, overhead — pentru **decizie comercială și confidence marjă**, fără a dicta automat prețul client.

**Regulă:** EstimatedInternalCost **susține** decizia comercială — **nu o dictează**.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Materiale estimate** | From inventory unit_cost × quantities |
| **Consumabile** | Paint tubes, LED consumables, etc. |
| **Pierderi / scrap factors** | Formula-defined waste |
| **Operații estimate** | mp/ml/buc/fix internal rules — **target non-hourly** |
| **Overhead** | Configurable internal |
| **Sanity check timp** | Optional estimated minutes — **warning only** |
| **Confidence level** | completeness, missing rules |
| **Internal margin risk** | Warnings vs CommercialPriceProposal |
| **Blockers (internal)** | Missing inventory cost, missing internal op rule |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial final client |
| CommercialPriceProposal lines |
| Minute reale / ExecutionActuals |
| ProfitabilityAnalysis final (post-job) |
| Obligația ca internal total → client price |
| `per_hour` ca basis obligatoriu pre-quote (target) |
| HR payroll final |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| ProductAggregate | Expanded BOM, operation keys |
| Aggregate Cost BOM adapter | Readiness, inventory alignment |
| inventory_materials | unit_cost acquisition |
| Internal Cost Rules Registry | mp/ml/buc/fix op rates (Step 7I) |
| workcenter_rates | **Reclassified** — internal effort/capacity, not client tariff |
| Cost Engine v2 | Evolves from today — realigned path |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| estimated_material_cost | Quote snapshot.internal |
| estimated_operation_cost | Quote snapshot.internal |
| estimated_total | Margin preview vs commercial |
| warnings[], blockers[] | UI — internal confidence |
| completeness score | Governance |

**Today path (deviated):** Cost Engine → QuoteOrchestrator via `/price` — **FROZEN**.

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Internal pre-production estimate | **TARGET truth** in quote snapshot side B |
| Today | Mixed in `/price` + cost-plus commercial |
| Material unit cost | Inventory — **not** commercial mp price |
| Real cost post-job | ExecutionActuals + ProfitabilityAnalysis |

---

## 7. Conexiuni cu celelalte sisteme

```
ProductAggregate
    ↓
EstimatedInternalCost (THIS) ← Inventory + Internal Cost Rules
    ↓
Quote Snapshot.estimated_internal_cost (Step 8)
    ↓
ProfitabilityAnalysis compares vs ExecutionActuals
```

| Sistem | Relație |
|--------|---------|
| CommercialPriceProposal | Parallel — warnings only by default |
| Cost Engine | Calculator engine — **not** commercial generator |
| Pricing Registry | Internal Cost Rules tab — separated (7I) |
| ExecutionActuals | Replaces estimate with actuals post-job |

---

## 8. Reguli owner obligatorii

1. Internal cost **≠** client offer formula.
2. Missing `rate_per_hour` → affects **internal completeness**, **not** commercial offer ability.
3. Estimated minutes → **capacity warning**, not commercial price input.
4. Owner volumetric ops already **per ml/mp/buc** in costing audit — align CE runtime (7H).
5. QC / assembly generic — internal calibration, not quote-priced (owner decision documented).

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| per_hour default CE | minutes → hours × rate → total_cost | `HIGH_RISK_MINUTES_AS_PRICE` |
| WC rate missing blocks quote | WC_ASSEMBLY_rate_missing NOT_READY | `HIGH_RISK_WRONG_DIRECTION` |
| Mixed in /price | Single output | `FROZEN_UNTIL_REALIGNED` |
| cost-plus commercial | Orchestrator applies margin to internal total | `HIGH_RISK_WRONG_DIRECTION` |
| Time formulas mandatory | perimeter_based_time feeds cost path | Reclassify to optional sanity |

---

## 10. Target state (Step 7H)

| Aspect | Țintă |
|--------|-------|
| Non-hourly op basis | ml, mp, buc, fix for pre-quote |
| per_hour | Analytics/capacity only — post-quote or non-blocking |
| Separate API/preview | Distinct from CommercialPriceProposal |
| Blocker taxonomy | INTERNAL_INCOMPLETE vs COMMERCIAL_BLOCKED |
| Aggregate BOM preview | Relabeled „Cost intern estimativ” |

**Endpoint/model țintă:**

```
POST /api/v1/estimated-internal-cost/preview  (dry_run)
Response: {
  estimated_material_cost, estimated_operation_cost, estimated_total,
  completeness, warnings[], internal_blockers[]
}
```

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Internal total auto-becomes client price |
| per_hour as only op costing pre-quote |
| Block commercial offer on internal gap alone |
| Mix commercial transform in same endpoint |
| Retroactive rewrite from actuals into estimate snapshot |
| CE rewrite without 7H scope + GO |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric internal lines | ml/mp/buc aligned to owner audit |
| WC missing | Warning/confidence — not commercial block |
| Snapshot side B | Distinct field in Step 8 |
| No hourly in pre-quote path | Grep + behavior test |
| Time optional | Capacity warning without price impact |
