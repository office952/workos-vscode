# ProductDefinition — Product Compiler

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Service (read context):** `product_definition_builder_service.py`

---

## 1. Rolul sistemului

ProductDefinition este **compilerul/orchestratorul produsului concret** — transformă Intake V6 workspace + ProductSystem template în structură tehnică canonică: module active/inactive, valori canonice, configurație selectată, readiness, câmpuri lipsă.

**Regulă:** ProductDefinition **activează dependentele** pentru produsul concret — nu decide prețul.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Module active/inactive** | debitare_fata, modelare_cant, sistem_led, etc. |
| **Canonical values** | Mapped quote_input → product structure |
| **Selected configuration** | Finishes, depths, backing, mounting flags |
| **Readiness** | Gates, blockers, missing fields |
| **Missing fields** | Explicit list — fail-closed |
| **Product-specific technical definition** | layers[], processes[], materials[] per policy |
| **Validation state** | NOT_READY / READY semantics |

**Exemplu (Intake spune → ProductDefinition activează):**

| Intake V6 input | ProductDefinition output |
|-----------------|--------------------------|
| 19 litere, LED, cant aluminiu, montaj direct, șablon | activează debitare_fata, modelare_cant, debitare_spate, sistem_led, sablon_montaj |
| Fără structură suport | **nu** activează structura_suport |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț final comercial |
| Preț final intern |
| CostEngine commercial logic |
| Task scheduling final / ExecutionPlan |
| Minute reale |
| HR / pontaj |
| Quote snapshot write |
| Order creation |
| ProfitabilityAnalysis |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Intake V6 workspace | payload_json, finish_setup, quote_geometry |
| quote_input adapter | ~70 keys at draft create |
| ProductSystem template | Parent + module activation rules |
| Template dossier / modules | Dependency resolution (via builder) |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| ProductDefinition JSON | ProductAggregate expander |
| Readiness / blockers | Quote pricing gates, UI panels |
| processes[] per layer | ExecutionPlan (post-order) |
| Validation errors | Intake gates, orchestrator 422 |

**Endpoint (existing context):** `GET /api/v1/product-system/product-definition/{template_code}` (with workspace/quote context).

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Structură tehnică produs concret | **Derived from Intake + Template** — truth la moment compile |
| Intake workspace | **Upstream truth** pentru input |
| Template | **Upstream truth** pentru ce e posibil |
| Preț | **NOT** |

**Status audit:** **GOOD** — direcție corectă; trebuie consumat uniform (nu parent row gol alone).

---

## 7. Conexiuni cu celelalte sisteme

```
Intake V6 → ProductDefinition builder
    ↓
ProductAggregate (expand parent + dossier + modules)
    ↓
EstimatedInternalCost / CommercialPriceProposal (read structure, not compile)
    ↓
Quote priced snapshot embeds product_definition at order convert
    ↓
ExecutionPlan reads order snapshot processes — NOT parallel catalog
```

| Sistem | Relație |
|--------|---------|
| ProductAggregate | Downstream expand |
| Cost Engine | Citește aggregate — nu rescrie definition |
| QuoteOrchestrator | Build definition at /price — **frozen path** |
| Task preview (V3 catalog) | **DEVIATED** — trebuie aliniat la definition |

---

## 8. Reguli owner obligatorii

1. ProductDefinition = activare dependențe — **nu** ore × tarif.
2. Fail-closed: missing critical data → blocked, nu silent defaults.
3. Taskurile **nu** vin din catalog paralel — vin din processes ProductDefinition/Aggregate.
4. CostEngine **nu** decide taskurile.
5. Protected foundation — nu redesign fără GO (audit acceptance §2).

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| /price builds from parent row | Minimal BOM dacă aggregate bypass | `HIGH_RISK_DEVIATED` |
| Draft quote fără product_definition | Notes au quote_input only | Partial |
| Task preview ≠ definition | V3 operation catalog parallel | `DEAD_PIECE` |
| produce_order fallback | ExecutionPlan când processes empty | `HIGH_RISK_DEVIATED` |
| Layer-1 only processes | Collapse multi-layer | `NEEDS_OWNER_DECISION` |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Single builder path | Intake → Definition → Aggregate → all consumers |
| Module activation | Explicit, traceable provenance |
| Readiness split | Commercial blockers vs internal cost confidence (separate) |
| Embedded at order | product_definition frozen in order snapshot |
| No parallel task source | Deprecate V3 catalog for production path |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| ProductDefinition calculează preț comercial |
| ProductDefinition scrie quote/order direct |
| Silent fallback când module lipsesc |
| Task generation from catalog bypassing definition |
| Modificare definition post-order freeze |
| Rewrite builder fără scoped step + GO |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric activation rules | Documented + tested (target) |
| Same definition for CE + EP | Single graph |
| Readiness explicit | No silent defaults |
| Intake → Definition contract | quote_input keys mapped |
| Blockers classified | Commercial vs internal (Step 7G/7H) |
