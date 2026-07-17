# Worklog — Product System Modularity and Ownership E2E Audit

**Date:** 2026-07-17  
**Mode:** Audit only — no implementation  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `7960bcafb11630da4c5c80cc50907201604678f0`

---

## Owner concern

Intake V6 is multi-product; Letters is only a pilot. Lighting/finishing/mounting must not become permanent Intake concepts. Product templates, component templates, modules and capabilities may overlap. Settings ownership is distributed. Implementation paused until ownership truth is proven.

---

## Outcome

Full audit written:

`docs/audits/2026-07-17_product_system_modularity_and_ownership_audit.md`

```text
PRODUCT_SYSTEM_MODULARITY_OWNER_GATES_READY
IMPLEMENTATION = STOP
MODULARITY MODEL = REWORK
```

---

## Headline truths

1. **Product Family** — first-class DB grouping (14 families); does not own modules/settings/pricing.
2. **Product Template** — real root composer in `product_templates`, but same table also stores linked modules.
3. **Component Template** — **MIXED / no table**; word means BOM part, child TPL, ghost FACE_v1 codes, and inactive `TPL-COMP-*`.
4. **Mini-Module** — code registry, **Letters-only**; generic names are false-generic.
5. **Capability** — catalog usage label ≠ UI interaction type; PS must not name React components.
6. **Options/settings** — split across company settings, form contract, FE maps, workspace.
7. **Activation** — ProductDefinition owns final module activation; FE visibility is not authority.
8. **Money** — CPP 7G; measurements from Aggregate; minutes ≠ price.
9. **Multi-product** — Banner/vehicle cannot reuse Letters mini-modules as-is; vehicle family has no template.
10. **Control Center** — spine accurate; collapses Family/Component/Module/Capability into Catalog.

---

## Recommended next build

**Option A — Canonical concept model first** (docs + owner decisions + Control Center vocabulary).  
No renderer expansion, no 7I, no new templates until owner pack is signed.

---

## Owner decisions (approved 2026-07-17)

```text
PRODUCT FAMILY = FIRST-CLASS GROUPING
PRODUCT TEMPLATE = ROOT COMPOSER
COMPONENT TEMPLATE = PHYSICAL REUSABLE PART — CONCEPT NORMALIZATION REQUIRED
MINI-MODULE = OPERATIONAL PACKAGE WITH EXPLICIT SCOPE
CAPABILITY = UI INTERACTION TYPE
MODULE ACTIVATION = PRODUCT DEFINITION
COMMERCIAL MEASUREMENT = PRODUCT AGGREGATE
MONEY = CPP 7G
MODULARITY MODEL = REWORK
AUDIT COMMIT = YES
IMPLEMENTATION = GO — CONCEPT AND NAVIGATION NORMALIZATION ONLY
```

**Permanent product scope (stabilization only):** Litere volumetrice · Logo · Panouri ACM.  
**Forbidden:** banner, vehicle graphics, new families/templates, schema/migration/seed, renderer expansion, Pricing Registry 7I.

**Memorable rule:**

```text
NU MAI EXTINDEM.
STABILIZAM: LITERE + LOGO + ACM.
UN SINGUR PRODUCT SYSTEM. UN SINGUR DOSSIER.
UN SINGUR INVENTORY. UN SINGUR PRICING. UN SINGUR TRASEU E2E.
```

Follow-on build: `CANONICAL_PRODUCT_MODEL_AND_NAVIGATION_TRUTH` (concept/nav only).

---

## Commit — audit

`0fa9156` — `docs(product): approve canonical modularity model`

---

## Follow-on — Canonical product model and navigation truth

**Build:** concept + navigation normalization only (no schema/seed/templates/renderer/7I).

### Delivered

- Canonical dictionary: `frontend/src/lib/productSystemCanonicalModel.ts`
- Stabilization scope: Letters / Logo / ACM only (Logo+ACM marked PARTIAL)
- Component representation inventory (BOM / child TPL / GHOST FACE_* / inactive TPL-COMP-*)
- Mini-module scope rows (no false-generic)
- Capability = UI interaction types (do not activate modules)
- Settings ownership matrix + conflicts (dual markup, triple finishes)
- Canonical Dossier: `/product-system/blueprint-dossier`
- Legacy redirect: `/product-system/dossier-completion` → canonical
- Pricing redirect: `/pricing` → `/inventory/pricing`
- `/modules` vocabulary section + route links
- `/governance` ownership rows + settings matrix + owner gates

### Remaining owner gates

- `component_templates` table migration
- Option catalog unification
- Mini-module multi-template registry
- Renderer expansion / Pricing Registry 7I (still paused)
