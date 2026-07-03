# ProductSystem Template Contract

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Pilot:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Related:** `PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md`

---

## 1. Rolul sistemului

ProductSystem Template definește **ce este posibil tehnologic** pentru o familie de produse: template-uri, componente posibile, module linked, reguli tehnologice, dependențe între module, material roles, operation roles, variante și constraints.

**Regulă:** ProductSystem Template = definește dependentele **posibile** și regulile tehnologice — **nu** alegerea concretă pentru o lucrare.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Template-uri** | Parent row, dossier, linked child modules |
| **Componente posibile** | comp_face_litere, comp_lateral_litere, etc. |
| **Module posibile** | TPL-VOLUM-ALUMINIU_v1, TPL-METAL-PREMOUNT-STRUCTURE_v1 |
| **Reguli tehnologice** | Ce operații/materials sunt permise |
| **Dependențe între module** | modelare_cant depinde de geometrie; LED depinde de iluminare |
| **Material roles** | MAT-SABLON-MONTAJ, profile materials, LED modules |
| **Operation roles** | face_cnc_cut, side_forming, led_install_letters |
| **Variante posibile** | Optional vs required modules |
| **Constraints** | Gates, formula_ids, workcenter mapping |
| **Dossier (documentație)** | sections_json, costengine_mapping, task_rules — **audit/reference** |

**Exemplu volumetric letters:**

| Dependență | Regulă template |
|------------|-----------------|
| modelare_cant | Depinde de geometrie + cant activ |
| LED | Depinde de iluminare activă |
| asamblare | Depinde de față + cant + spate + LED dacă există |
| structura_suport | Opțională — nu apare dacă ne-selectată |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Alegerea concretă pentru o lucrare (Intake V6) |
| Preț final comercial |
| Preț final intern |
| Taskuri reale runtime |
| Minute reale |
| Order runtime |
| ProfitabilityAnalysis |
| Compilarea produsului concret (ProductDefinition) |
| Snapshot quote/order |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Owner / admin | Template seed, dossier content, module links |
| Registry | inventory_materials codes referenced |
| Architecture docs | Mini-module contracts, shared edge rules |

**Citit de:** ProductDefinition builder, ProductAggregate expander, admin UI (`ProductSystem.tsx`).

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Template metadata | ProductDefinition, Aggregate |
| components_json / operations_json / materials | Aggregate expansion |
| Module link targets | ProductAggregate linked_modules |
| Dossier mapping | Audit, onboarding, future CE rules |
| Activation scope | Intake module visibility |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Ce este posibil tehnologic | **Registry / template truth** |
| Produs concret job | **NOT** — Intake + ProductDefinition |
| Prețuri | **NOT** — Pricing Registry separat |
| Parent row minimal vs dossier full | **KNOWN ISSUE** — aggregate resolves |

**Status audit:** Parent `TPL-VOLUMETRIC-LETTERS_v2` are `components_json=[]`; dossier are structură completă — **ProductAggregate** trebuie să unifice (Step 7A — GOOD foundation).

---

## 7. Conexiuni cu celelalte sisteme

```
ProductSystem Template (possible tech)
    ↑ read
Intake V6 (concrete choices)
    ↓
ProductDefinition (activates dependencies for this job)
    ↓
ProductAggregate (parent + dossier + modules merged)
    ↓
CommercialPriceProposal / EstimatedInternalCost (read aggregate + rules)
```

| Sistem | Relație |
|--------|---------|
| Intake V6 | Citește template_code; nu scrie template |
| ProductDefinition | Compilează din workspace + template |
| Cost Engine | Citește aggregate — **nu** decide structura produs |
| ExecutionPlan | Taskuri din ProductDefinition processes — **nu** din template alone |

---

## 8. Reguli owner obligatorii

1. Template = reguli tehnologice, **nu** markup comercial.
2. `TPL-VOLUMETRIC-LETTERS` = singurul template fully wired V2 (AGENTS.md).
3. `TPL-ACM-CASSETTED-PANEL` = future — fără activare parțială fără build dedicat.
4. Nu activa ACM în WorkIntake V2 / QuoteWizard fără GO.
5. Dossier explicit **audit-only** până la aggregate contract complet — nu presupune runtime authority.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Parent gol | components_json=[] → CE citește minimal | `DEAD_PIECE` |
| Dossier dead for CE | costengine_mapping nefolosit direct | `DEAD_PIECE` |
| comp_auto_1 UI | Sintetizat când parent empty | `MISLEADING_UI` |
| Duplicate lateral | Dossier vs TPL-VOLUM-ALUMINIU module | `NEEDS_OWNER_DECISION` |
| task_rules_json | Documentație, nu execution driver | `ANALYTICS_ONLY` / dead |
| 6+ parallel contracts | Form vs parent vs dossier vs modules | `HIGH_RISK_DEVIATED` |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Parent + dossier + modules | Consumate uniform via **ProductAggregate** |
| Mini-module registry | Form field → component → cost → task aligned |
| Template UI | Arată structură reală (post-aggregate), nu comp_auto_1 |
| Material/operation roles | Mapate explicit per template |
| Per-template inventory map | Materiale used / optional / legacy / unused (doc 13) |

**Endpoint/model țintă:**

- `GET /api/v1/product-system/templates/{code}` — parent metadata
- `GET /api/v1/product-system/aggregate/{code}` — **canonical read model**
- `GET /api/v1/product-system/product-definition/{code}` — compiled instance preview
- Admin: template CRUD — **registry**, nu runtime quote

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Template conține preț comercial client |
| Template generează taskuri fără ProductDefinition |
| Activare parțială ACM / template ne-scoped |
| Ștergere dossier/components fără owner decision |
| Template ca singură sursă fără Aggregate merge |
| RAL/Oracal registry → automatic Pricing/CostEngine rates |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Aggregate = single read model | Form, CE, Quote, Order, Tasks same graph |
| Dependencies documented | Volumetric example complete |
| Dead pieces tagged | Parent empty, dossier audit-only labeled |
| No commercial in template | Audit pass |
| Module links resolve | Child templates expand in aggregate |
