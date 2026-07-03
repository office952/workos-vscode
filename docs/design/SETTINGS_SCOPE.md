# WorkOS Settings — Scope & Information Architecture

**Status:** Governance document — **no Settings UI implementation**  
**Purpose:** Define what belongs in Settings vs operational modules  
**Related:** `UI_DO_NOT_BREAK.md`, `THEME_PHASE_PLAN.md`, `TypographyGuard.md`

---

## 1. Purpose

Settings exists today with real tabs (Societate, Plăți Repetitive, CostEngine, Integrări) but **no Appearance** section and **no strict admin boundary** in UI.

Settings must not become a catch-all for every WorkOS configuration. Operational registries (Pricing, ProductSystem, Inventory, HR) have their own modules, lifecycles, and permissions.

This document defines scope for **future** Settings IA only. It does not move tabs, add Appearance, or wire `ProtectedAdminRoute`.

---

## 2. Settings allowed sections (proposed IA)

Future Settings structure (logical grouping):

| Section | Purpose | Status today |
| ------- | ------- | ------------ |
| **Company & Commercial** | Legal/commercial profile, invoicing context | Partial — Societate (mock profile + real TVA/FX) |
| **TVA / FX** | Tax rate, EUR-RON | Real API |
| **Integrations** | SmartBill, future connectors | Real API — sensitive |
| **Appearance** | Theme, density (future) | **Not present** — see THEME_PHASE_PLAN |
| **Diagnostics** | Version, build, read-only health | Partial / scattered |
| **Permissions / Admin boundaries** | Role hints, links to security docs | **Not present** — `ProtectedAdminRoute` unused |
| **Links to operational registries** | Deep links only, not duplicate CRUD | Partial |

---

## 3. What belongs in Settings

| Setting type | Belongs in Settings? | Notes |
| ------------ | -------------------- | ----- |
| TVA rate | **Yes** | Commercial baseline |
| EUR-RON exchange | **Yes** | Commercial baseline |
| Company commercial profile | **Yes** (when real) | Today partially mock — banner OK |
| SmartBill integration | **Yes** | **Admin-only** — token write |
| Plăți repetitive (recurring payments) | **Yes** | Commercial/finance config |
| CostEngine configuration tab | **Yes, with admin guard** | Sensitive — real API writes |
| Appearance / theme preference | **Yes, after theme Phase 2+** | Read-only/disabled until ready |
| Typography / density preference | **Partial, future** | Global density is high risk; prefer module tokens first |
| Diagnostics / version / build | **Yes** | Read-only |
| Link → Pricing Registry | **Yes** | Navigation only |
| Link → Product System | **Yes** | Navigation only |
| Link → Inventory | **Yes** | Navigation only |
| Link → Sheet Quality / material policy docs | **Yes** | If documented elsewhere |

---

## 4. What does NOT belong in Settings

| Setting type | Belongs in Settings? | Belongs in module |
| ------------ | -------------------- | ----------------- |
| ProductSystem templates | **No** | `/product-system` |
| ProductDefinition / Form System | **No** | ProductSystem tab |
| Intake V6 flow / workspace config | **No** | Intake V6 standalone + operator routes |
| Material prices | **No** | `/inventory/pricing` (Pricing Registry) |
| Workcenter rates | **No** | Pricing Registry |
| Inventory stock / materials CRUD | **No** | `/inventory` |
| HR payroll rules | **No** | Employee payments / HR modules |
| Employee operational registry | **No** | `/employees`, `/employees-records` |
| Machine CRUD | **No** | `/utilaje` (when write exists) |
| Collaborators / externalization CRUD | **No** | `/colaboratori` |
| Quote / order / execution actions | **No** | Respective commercial/ops pages |
| Cost Engine **internals** (orchestration, reprice) | **No** | Backend services — not Settings UI |
| Blueprint / Dossier editing | **No** | ProductSystem sub-routes |
| Module Chain / Governance content | **No** | `/modules`, `/governance` |

**Rule:** If it is edited daily by commercial or production roles in context of a workflow, it stays in that workflow’s module — Settings links to it at most.

---

## 5. Admin boundary

### Sensitive today

| Area | Risk | Future guard |
| ---- | ---- | ------------ |
| **CostEngine tab** | Real config writes | Wrap with admin-only route or role check — dedicated task |
| **Integrations (SmartBill)** | Token storage | Admin-only |
| **TVA / FX** | Affects commercial calculations | Admin or commercial-manager role |

### Current state (audit)

- `ProtectedAdminRoute` **exists** in `frontend/src/components/ProtectedAdminRoute.tsx` but is **not used** on Settings or CostEngine tab.
- Any authenticated user who can open Settings can reach CostEngine edit UI.

### This document does NOT

- Implement `ProtectedAdminRoute` on Settings
- Change CostEngine tab behavior
- Add role matrix

Those require a dedicated **Admin boundary** task (listed in P1 roadmap).

---

## 6. Settings future IA (architecture only)

Proposed tab order (implementation later):

1. **Societate & Comercial** — profile (when real), TVA, FX, plăți repetitive  
2. **Integrări** — SmartBill, future APIs  
3. **Cost & Pricing** — **Link** to Pricing Registry + optional high-level CostEngine read-only summary; full CostEngine edit admin-only sub-section  
4. **Appearance** — disabled until theme Phase 2; “Light mode în pregătire”  
5. **Sistem** — diagnostics, version, links to Governance docs  

### Deep links (not duplicates)

```text
Settings → "Deschide Pricing Registry"     → /inventory/pricing
Settings → "Deschide Product System"       → /product-system
Settings → "Deschide Inventar"             → /inventory
Settings → "Documentație governance"       → /governance
```

### What stays out of Settings navigation entirely

- Intake V6 operator workspace
- Quote builder actions
- Execution plan generation
- Tablet queue

---

## 7. Relationship to theme plan

- **Appearance** tab content is defined in `THEME_PHASE_PLAN.md` Phase 2 (read-only/disabled first).
- Do not add functional theme toggle until Phase 3+ shell experiment and module regressions pass.

---

## 8. Checklist for future Settings tasks

```text
Settings Scope Check:
- New config is global vs operational: 
- Belongs in Settings per this doc: yes/no
- Duplicate of Pricing/ProductSystem/Inventory CRUD: yes/no
- Admin-only required: yes/no
- Link-only vs inline editor: 
- Cost Engine / QuoteOrchestrator touched: yes/no (should be no)
```
