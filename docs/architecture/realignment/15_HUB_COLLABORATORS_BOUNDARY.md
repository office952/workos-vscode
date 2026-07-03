# HUB / Collaborators — External Boundary

**Version:** 1.0.0  
**Status:** Target architecture (documentation only) — **FUTURE_RESERVED**

---

## 1. Rolul sistemului

**WorkOS** = sistem intern P-Media. **HUB** = externalizare, colaboratori, reseller, parteneri — **boundary viitor**, **neimplementat** în WorkOS activ.

Acest document marchează **limita** — ce WorkOS NU face acum și ce HUB va detine în viitor.

---

## 2. Ce detine (WorkOS today — boundary marker only)

| Categorie | Conținut |
|-----------|----------|
| **Future markers** | UI/docs references to external routing |
| **Boundary decisions** | What stays internal |
| **Integration hooks (future)** | **UNKNOWN** — not implemented |

**WorkOS NU implementează acum:**

- Furnizori externi activi
- Comenzi externe routing
- Taskuri externalizate runtime
- Routing colaboratori
- Reseller products active
- Marketplace

---

## 3. Ce NU detine (WorkOS — explicit)

| Exclus from WorkOS now |
|------------------------|
| Collaborator marketplace |
| Supplier order management |
| External task assignment production |
| Partner capacity registry (live) |
| Reseller commercial pricing engine |
| HUB authentication / SSO for partners |

---

## 4. Inputuri (future HUB)

| Sursă | Date |
|-------|------|
| External partners | Capacity, pricing, status |
| WorkOS orders | Externalizable work packages |
| Owner routing rules | What goes external |

**Today:** None operational in workos-active.

---

## 5. Outputuri (future HUB)

| Output | Consumator |
|--------|------------|
| External work orders | Partners |
| Supplier price + markup | **Future** commercial rules — separate from internal CE |
| Status trimis/primit/verificat | WorkOS read-only sync |
| Partner capacity | Routing decisions |

---

## 6. Source of truth

| Domain | Owner |
|--------|-------|
| Internal production truth | **WorkOS** |
| External partner truth | **HUB (future)** |
| Client commercial offer | **WorkOS** CommercialPriceProposal — external costs as input lines **NEEDS_OWNER_DECISION** |
| ExecutionActuals internal | **WorkOS** |
| External execution | **HUB (future)** → sync to WorkOS actuals |

---

## 7. Conexiuni cu celelalte sisteme

```
WorkOS canonical flow (internal)
    Intake → ... → ExecutionActuals → ProfitabilityAnalysis

HUB (future — external boundary)
    Collaborators, suppliers, outsourced tasks
    ↔ WorkOS Order (external package markers only today: NONE active)

Montaj external / subcontract hooks in costing audit metadata — **NEEDS_OWNER_DECISION**
```

| WorkOS system | HUB relation (future) |
|---------------|----------------------|
| CommercialPriceProposal | May include external service line with supplier cost + adaos |
| EstimatedInternalCost | Subcontract estimate hook (metadata today partial) |
| ExecutionPlan | Internal tasks only now |
| Inventory | Not HUB supplier catalog |

---

## 8. Reguli owner obligatorii

1. Do not implement HUB features in WorkOS without dedicated build + GO.
2. WorkOS internal flow remains canonical for P-Media production.
3. External montaj pricing = fix/manual/separat — owner examples — not auto hourly.
4. HUB pricing ≠ internal employee hourly ≠ client hourly.
5. Boundary docs only — no runtime in this task.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Scope creep | External features in WorkOS prematurely | `FUTURE_RESERVED` |
| Subcontract metadata partial | Finishing external hook unclear | `NEEDS_OWNER_DECISION` |
| No HUB repo in scope | C:\Users\offic\workos not touched | OK |

---

## 10. Target state (future HUB)

| HUB will own | WorkOS will consume |
|--------------|---------------------|
| Colaboratori, furnizori | Status sync read-only |
| Servicii externalizate | Package markers on order |
| Produse revândute | Catalog reference |
| Routing | Decision support |
| Preț furnizor + adaos | Input to CommercialPriceProposal line |
| Capacitate parteneri | Feasibility warning |

---

## 11. Forbidden behavior (WorkOS now)

| Interzis |
|----------|
| Build HUB marketplace in WorkOS without scoped build |
| Route production tasks externally without owner GO |
| Mix HUB supplier price with CE hourly path silently |
| Implement reseller catalog as ProductSystem without template build |
| Touch C:\Users\offic\workos from this documentation task |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Boundary documented | WorkOS vs HUB clear |
| No active HUB runtime claimed | Honest status |
| External montaj decision | Owner marks policy |
| Future hooks labeled | FUTURE_RESERVED in UI (Step 11) |
| Canonical flow internal | Unbroken for P-Media production |
