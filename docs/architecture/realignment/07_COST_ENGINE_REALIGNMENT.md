# Cost Engine — Realignment Target Role

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Service (read context):** `cost_engine_service.py`  
**Step:** 7H — NEEDS OWNER GO (no rewrite ad-hoc)

---

## 1. Rolul sistemului

Cost Engine devine **calculator de cost intern estimativ** — validator materiale, validator reguli interne, sanity check marjă/capacitate, suport pentru EstimatedInternalCost — **nu** generator universal de preț comercial.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Material cost calculation** | inventory unit_cost × formula quantities |
| **Internal operation costing** | mp/ml/buc/fix rules (target) |
| **Formula evaluation** | perimeter, area, module count, pass logic |
| **Validation / blockers** | Missing material, missing internal rule |
| **CostResult structure** | Lines, net, currency, provenance |
| **Dry-run preview** | Non-persist pricing preview |
| **Sanity time estimates** | Optional — non-blocking commercial |

---

## 3. Ce NU detine (target — today deviated)

| Exclus |
|--------|
| Generator universal preț comercial client |
| Formula `minute × rate_per_hour` ca basis comercial |
| Locul unde se decide oferta finală |
| Sursa taskurilor / ExecutionPlan |
| CommercialPriceProposal |
| Quote commercial transform (`_apply_commercial`) |
| ProfitabilityAnalysis |
| Modificare ProductDefinition / Intake |

**Today Cost Engine wrongly also feeds:** QuoteOrchestrator commercial path via total_cost.

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| ProductAggregate / ProductDefinition | BOM structure |
| quote_input | Geometry keys |
| inventory_materials | unit_cost |
| workcenter_rates | Internal rates — **reclassify from client tariff** |
| Formula registry | Quantity + optional time formulas |
| Settings | Labour/machine hourly fallback — **FROZEN for commercial** |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| CostResult | EstimatedInternalCost wrapper |
| Operation/material lines | Aggregate BOM preview |
| Blockers | Internal confidence — reclassified |
| Warnings | Capacity/time sanity |

**Today deviated output path:** `/price` → QuoteOrchestrator → grand_total — **FROZEN**.

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Internal cost calculation engine | **Partial truth today** — mixed hourly |
| Commercial price | **NOT** — CommercialPriceProposal |
| Material acquisition cost | Inventory — input to CE |
| Task list | ProductDefinition — **NOT** CE |

---

## 7. Conexiuni cu celelalte sisteme

```
ProductAggregate
    ↓
Cost Engine (THIS) → EstimatedInternalCost
    ✗ QuoteOrchestrator._apply_commercial (FROZEN — decouple)

CommercialPriceProposal ← separate rules engine (7G)
    ↓
Quote Snapshot merges both (Step 8)
```

| Sistem | Relație |
|--------|---------|
| QuoteOrchestrator | Today merges CE + commercial — **split** |
| Aggregate BOM adapter | Wraps CE for readiness UI |
| Pricing Registry | Supplies rates — separated tabs (7I) |
| ExecutionActuals | Actual cost replaces estimates post-job |

---

## 8. Reguli owner obligatorii

1. Owner volumetric ops: **per ml, per mp, per buc** — documented in costing audit.
2. `per_hour` column exists — **not** primary pre-quote commercial basis.
3. ASSEMBLY, generic LASER — not quote-priced for volumetric (owner).
4. QC — internal calibration only.
5. CE rewrite only in Step 7H with GO — not ad-hoc.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Default per_hour | estimated_minutes → hours × rate | `HIGH_RISK_MINUTES_AS_PRICE` |
| Settings hourly fallback | labour_rate_ron_per_hour 80, machine 40 | `FROZEN_UNTIL_REALIGNED` |
| CE → quote price | Single pipeline | `HIGH_RISK_WRONG_DIRECTION` |
| Parent BOM minimal | CE prices sablon only | `DEAD_PIECE` |
| Time formulas feed cost | Mandatory minute path | Reclassify |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Role | Internal estimator only |
| Op basis | ml/mp/buc/fix pre-quote |
| per_hour | Capacity/analytics — optional |
| API | `/estimated-internal-cost/preview` not `/price` mixed |
| Blockers | Internal completeness — not commercial |
| Keep v2_aggregate path | Engine path good — decouple commercial |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| CE outputs client grand_total directly |
| CE decides ExecutionPlan tasks |
| CE applies markup/VAT as commercial truth |
| Extend per_hour path for new products without owner review |
| Rewrite CE outside 7H boundary |
| Use CE as CommercialPriceProposal |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric simulate-cost | Matches owner audit unit bases |
| No commercial in CE output | Separate consumer |
| Hourly isolated | Not in pre-quote blocker path |
| Aggregate input only | Not parent-empty bypass |
| Frozen paths respected | No ad-hoc /price fixes |
