# Product System — Blueprint Authority Map

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_AUDIT_HISTORICAL_PRODUCT_SYSTEM_BLUEPRINT_UI` |
| Related audit | `docs/audits/2026-07-18_product_system_blueprint_historical_ui_audit.md` |

---

## Purpose

Separate overloaded meanings of “Blueprint” and define what each surface may own.

---

## Vocabulary (canonical)

| Name | What it is | Route / artifact | Authority class |
|------|------------|------------------|-----------------|
| **Blueprint Dossier** | Template-level technical documentation entity (1:1 template) | Table `product_blueprint_dossier`; UI `/product-system/blueprint-dossier` | **Documentation / declared contracts** — not BOM SoT, not task runtime |
| **Blueprint Dossier Studio** | Admin UI for dossier JSON sections | `BlueprintDossierStudio.tsx` | Surface over dossier entity |
| **Product System** | Catalog + template/component editor | `/product-system/products` | **Technical product configuration** (templates, links, form contracts) |
| **IA “Dossiers” tab** (historical) | Navigation bucket in `3be9c72` shell | Removed in unified catalog | Navigation only (historical) |
| **Docs “blueprint”** (`0416248`) | Design contract for inactive letters set | Worklog only | Design — no runtime |
| **Operator production blueprint** | Order/task production view | Operator panels / APIs | **Execution domain** — not Product System admin |
| **Employee Mobile order blueprint** | Mobile order view | Employee Mobile | **Mobile domain** — final-final, out of this GO |
| **Visual canvas Blueprint** | React Flow builder | — | **Does not exist** in this repo |

---

## Authority layering (required)

```text
Blueprint / Dossier UI
  = administration + visualization surface

Product System contracts
  (templates, components, roles, resource options, formulas)
  = technical authority

ProductDefinition
  = typed product truth for a job

ProductAggregate
  = compilation (materials / ops / task_rules from resolver)

CPP
  = owner-gated pricing

Snapshot
  = freeze

Existing mature tasking
  = operational materialization

Execution
  = shop floor
```

---

## Dossier section authority (current Studio groups)

| Group | Sections | Allowed | Forbidden |
|-------|----------|---------|-----------|
| Contract Ofertare | variants, costengine_mapping, quote_readiness | Declare option contracts; audit mapping | Own live price; replace Readiness Authority |
| Contract Producție | task_rules, qc, production_notes | Human guidance | Create tasks; move stock; schedule |
| Documentație Tehnică | sections, layers, time, risks | Human docs | Material/ops/price SoT |
| Avansat / Output | output/visual blocks, completion | Preview / editorial | Decide commercial readiness |

Source: `frontend/src/pages/BlueprintDossierStudio.tsx` (`DOSSIER_SECTION_GROUPS`).

---

## Conflict zones

| Conflict | Risk | Mitigation |
|----------|------|------------|
| Dossier `task_rules_json` vs Aggregate task_rules | Parallel task authority | Keep dossier as guidance; runtime from modular process → Aggregate |
| Dossier costengine_mapping vs Pricing Registry / CPP | Fake pricing path | Mapping = audit only |
| “Blueprint Studio” label on Product System | Navigation confusion | Prefer “Product System” vs “Blueprint Dossier” |
| Operator blueprint vs Product System Blueprint | Domain mix | Keep separate |

---

## What Blueprint UI may become (allowed)

- Clearer admin / overview of contracts already owned elsewhere.
- Sectioned visualization of variants, declared readiness policy, production guidance.
- Cross-links into Products, Modules, Governance, Pricing Registry.

## What Blueprint UI must not become

- Parallel database of product truth
- Workflow / task scheduler
- Pricing engine
- Execution engine
- Mega-schema
- React Flow product canvas invented without GO

---

## Related code

| Layer | Path |
|-------|------|
| Model | `backend/models/product_blueprint_dossier.py` |
| Service | `backend/services/product_blueprint_dossier_service.py` |
| Router | `backend/routers/product_blueprint_dossier.py` |
| FE API | `frontend/src/api/blueprintDossier.ts` |
| FE UI | `frontend/src/pages/BlueprintDossierStudio.tsx` |
| Canonical route helper | `frontend/src/lib/productSystemCanonicalModel.ts` (`CANONICAL_ROUTES.dossier`) |
