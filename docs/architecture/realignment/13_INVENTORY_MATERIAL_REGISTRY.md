# Inventory & Material Registry

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)

---

## 1. Rolul sistemului

Inventory Material Registry deține **materiale, unități, coduri, prețuri de achiziție, stoc, alternative** — clasificate active/legacy/future/unused — ca **truth pentru cost materiale intern**, nu ca preț comercial client direct.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Materiale** | material_code, descriptions |
| **Unități** | buc, ml, m², kg, etc. |
| **Coduri canonice** | MAT-* naming |
| **Prețuri achiziție** | unit_cost — internal acquisition |
| **Stoc** | Quantities, locations |
| **Alternative** | Substitutable materials |
| **Clasificări** | active / legacy / future / unused |
| **Template linkage map** | Per template: used, optional, missing |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Balast materiale nefolosite fără tag |
| Sursă de costuri false pentru quote |
| Preț comercial mp/ml client (without Commercial Price Rule) |
| Reguli comerciale |
| Product structure |
| Automatic inclusion in cost for unused materials |
| RAL/Oracal color → automatic pricing (frontend registry separate) |

**Regulă:** Inventory **not** direct quote price source — feeds EstimatedInternalCost via explicit formulas.

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Admin / procurement | unit_cost updates, new materials |
| ProductSystem templates | Required material codes |
| Aggregate BOM adapter | Existence checks |
| Sheet exports / imports | **UNKNOWN** current process detail |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| unit_cost lookups | Cost Engine, EstimatedInternalCost |
| Material existence gates | Aggregate BOM blockers |
| Stock availability | Feasibility warnings — **not** commercial block by default |
| Consumption deductions | ExecutionActuals → inventory |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Material acquisition cost | **Source of truth** (`inventory_materials.unit_cost`) |
| Commercial client price per mp | **NOT** — Commercial Price Rules |
| Stock levels | **Operational truth** |
| Template-required materials | Cross-ref ProductSystem + aggregate |

**Per template (target map):**

| Class | Meaning |
|-------|---------|
| used_real | In aggregate for active config |
| optional | Conditional module materials |
| future | Planned not active |
| legacy | Deprecated but in DB |
| unused | Orphan — risk accidental inclusion |
| missing | Referenced but not in inventory — blocker |

---

## 7. Conexiuni cu celelalte sisteme

```
Inventory (material acquisition truth)
    ↓
EstimatedInternalCost / Cost Engine
    ✗ CommercialPriceProposal (direct unit_cost → client price forbidden)

ProductSystem / Aggregate
    → validates material codes exist

ExecutionActuals
    → stock deductions (operational)
```

| Sistem | Relație |
|--------|---------|
| Pricing Registry | Material Prices tab mirrors/admin — separated (7I) |
| ProductAggregate | Inventory alignment blockers |
| ProfitabilityAnalysis | Material estimate vs actual |

---

## 8. Reguli owner obligatorii

1. Do not use Inventory as direct quote price source (AGENTS.md protected).
2. unit_cost PATCH admin — internal only.
3. MAT-VOPSEA-RAL etc. — owner accepted overrides documented in costing audit.
4. Each template material must be classified — no silent orphans.
5. Color registry (RAL/Oracal) stays frontend config — not auto CE rates.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Unused materials in registry | Accidental formula reference | `DEAD_PIECE` |
| Parent template 2 mats only | Most materials via breakdown not CE | `DEAD_PIECE` |
| Duplicate material lists | Intake vs template vs inventory | `NEEDS_OWNER_DECISION` |
| Missing material blocks quote | May be correct for internal — reclassify commercial | Partial |
| EUR vs RON | Volumetric EUR base — conversion manual | Documented |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Template material map | Document per TPL-* |
| Unused tagged | Cannot enter aggregate accidentally |
| Separation | unit_cost ≠ commercial mp price |
| Aggregate gates | Missing → internal blocker explicit |
| Stock vs cost | Separate concerns |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Inventory unit_cost → client line without commercial rule |
| Unused materials in default BOM |
| Auto-wire RAL registry to pricing |
| Inventory as CommercialPriceProposal engine |
| Silent default unit_cost for missing material |
| Delete materials without zero-reference check |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric material map | used/optional/legacy listed |
| No orphan pricing | Unused tagged |
| CE reads inventory explicitly | Formula-linked only |
| Commercial separation | No direct inventory → client total |
| Missing material explicit | Blocker with code |
