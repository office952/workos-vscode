# ProductAggregate — Technical Graph Read Model

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Related:** Aggregate Cost BOM (Step 7A/7B), `aggregate_cost_bom_adapter.py`

---

## 1. Rolul sistemului

ProductAggregate este **graful tehnic complet** — read model care unește parent template, dossier și linked modules într-o structură expandată: componente reale, materiale agregate, operații agregate, provenance, dependențe tehnice, legătura module ↔ componente.

**Regulă:** ProductAggregate **expune graful tehnic complet** — nu prețul comercial.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Componente reale** | comp_face_litere, comp_lateral (from module), comp_led, etc. |
| **Materiale agregate** | Rolled-up material lines with formula refs |
| **Operații agregate** | All operation_keys from expanded graph |
| **Provenance** | parent vs dossier vs module source |
| **Dependențe tehnice** | Module activation graph |
| **Legătură module ↔ componente** | linked_modules[] expansion |
| **Aggregate Cost BOM view** | Readiness, blockers, inventory alignment (7B) |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial client |
| CommercialPriceProposal lines |
| Task scheduling final (ExecutionPlan owns order/assignments) |
| Minute reale |
| HR / employee cost |
| Quote final totals |
| ProfitabilityAnalysis |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| ProductDefinition | Active modules, workspace context |
| ProductSystem parent | components_json, operations_json, materials |
| Dossier | sections_json, costengine_mapping |
| Linked modules | Child template rows |
| Inventory registry | Material existence checks (BOM adapter) |
| workcenter_rates | Internal rate lookup — **not commercial truth** |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Expanded BOM structure | Cost Engine, EstimatedInternalCost |
| Aggregate Cost BOM preview | UI read-only truth (Step 7D labels) |
| Blockers / readiness | Quote gates — **reclassify** commercial vs internal |
| Geometry + structure keys | CommercialPriceProposal (7G) |

**Endpoint (existing):** `GET /api/v1/product-system/aggregate/{template_code}`

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Technical expanded BOM | **Read model truth** (post Intake + Definition) |
| Parent row alone | **NOT** sufficient — aggregate merges |
| Dossier alone | **NOT** runtime — merged in aggregate |
| Commercial price | **NOT** |

---

## 7. Conexiuni cu celelalte sisteme

```
ProductDefinition
    ↓
ProductAggregate (THIS)
    ├→ CommercialPriceProposal (geometry + active modules + commercial rules)
    ├→ EstimatedInternalCost (materials + internal op rules)
    ├→ Aggregate Cost BOM preview (read-only UI)
    └→ Quote snapshot embed (structure at freeze)
         ↓
    ExecutionPlan (processes from frozen product_definition — not re-aggregate)
```

**Regulă critică:** Taskurile vin din graful tehnic ProductDefinition/ProductAggregate. CostEngine **nu** decide taskurile. Ordinea operațională = ExecutionPlan.

---

## 8. Reguli owner obligatorii

1. Aggregate = single read model — rezolvă parent gol + dossier full.
2. Blockers `WC_*_rate_missing` → **reclassify**: internal cost confidence, **not** commercial offer block (Step 7F).
3. `pricing_source_required: workcenter_rates` → internal effort rules, **not** client hourly tariff.
4. Inventory alignment = material truth — nu preț comercial mp/ml.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| CE reads parent only | Repricing fails / sablon-only lines | `HIGH_RISK_DEVIATED` |
| WC rate missing blocks quote | NOT_READY reprice | `HIGH_RISK_WRONG_DIRECTION` |
| per_hour in aggregate path | Minutes → cost → quote | `HIGH_RISK_MINUTES_AS_PRICE` |
| Duplicate domain lateral | Dossier vs module | `NEEDS_OWNER_DECISION` |
| Blockers conflated | Commercial vs internal | `HIGH_RISK_DEVIATED` |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Uniform consumption | Form preview, CE, Quote, Order, Tasks — same aggregate |
| Blocker taxonomy | COMMERCIAL vs INTERNAL_CONFIDENCE |
| Non-hourly internal ops | ml/mp/buc/fix in expanded lines |
| Provenance visible | UI/admin shows parent/dossier/module source |
| Inventory gates | Missing material → explicit, not silent |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Aggregate sets commercial price |
| Aggregate generates ExecutionPlan assignments |
| Bypass aggregate → parent row for pricing |
| WC rate missing blocks CommercialPriceProposal |
| Aggregate mutates Intake workspace |
| Aggregate as unified Pricing Registry |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric full graph | 5 components + modules expanded |
| Same graph CE + 7G | Identical structure keys |
| Blockers reclassified | Documented + implemented (7H) |
| No commercial in aggregate output | Separation enforced |
| Provenance traceable | Audit can explain each line |
