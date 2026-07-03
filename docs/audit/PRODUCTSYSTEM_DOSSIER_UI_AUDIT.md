# ProductSystem / Blueprint Dossier — UI Audit (Pre-Refactor)

| Field | Value |
|-------|-------|
| **Application** | WorkOS |
| **Release reference** | `BUILD_25` (`release.json`) |
| **Audit date** | 2026-06-04 |
| **Scope** | ProductSystem, Blueprint Dossier UI, related display/readiness wiring |
| **Status** | Documentation-only — **no runtime changes in this step** |

---

## 1. Current architecture understanding

WorkOS follows a modular commercial → production chain. Each module owns one canonical truth; downstream modules consume snapshots or contracts—they do not rewrite upstream truth.

### Domain boundaries (canonical)

| Module | Responsibility | Must NOT |
|--------|----------------|----------|
| **ProductSystem** | Product definition at **design-time**: templates (`components_json`, `operations_json`, `required_materials_json`), families, linkage to blueprint dossier metadata | Calculate cost, set client price, freeze order snapshots, run production tasks |
| **Blueprint Dossier** | Structured **production dossier** per template: section JSON (`variants_json`, `task_rules_json`, `costengine_mapping_json`, etc.), dossier lifecycle status, `completion_state_json` | Replace product template structure; calculate CostEngine totals; create quotes/orders |
| **CostEngine** | Cost calculation from product definition + mappings | Modify product definition; own quote commercial rules |
| **Quotes** | Commercial document: margins, pricing rules, quote output composition | Contain cost formulas; mutate frozen product definition |
| **Orders** | **Frozen snapshot** from accepted quote; immutable commercial/technical baseline | Recalculate cost or product definition |
| **Execution / WorkOS** | Production execution (jobs, operations, reality, materials capture) | Become source of product or quote truth |

Backend contracts reinforce this in `backend/data_models/product_contracts.py` (REQUEST → PRODUCT DEFINITION → COST → OFFER → ORDER).

### UI role in this audit

- UI **displays and organizes** template and dossier data.
- UI **edits** only through existing API surfaces (CRUD entities, section JSON saves, status transitions allowed by backend).
- UI **must not** invent readiness, completion %, or gate outcomes that contradict backend services.

### Related routes (frontend)

| Route | Page file | Role |
|-------|-----------|------|
| `/product-system` | `frontend/src/pages/ProductSystem.tsx` | Template studio (list + editor) |
| `/product-system/blueprint-dossier` | `frontend/src/pages/BlueprintDossierStudio.tsx` | Dossier studio (list + section editors) |
| `/product-system/dossier-completion` | `frontend/src/pages/DossierCompletionDashboard.tsx` | Aggregate completion table (read-only intent) |
| `/product-system/output-blocks-preview` | `frontend/src/pages/OutputBlocksPreview.tsx` | Output blocks preview (adjacent; out of Phase 1) |

Legacy redirects: `/products`, `/templates` → `/product-system`.

---

## 2. ProductSystem / Dossier UI map

| Page / component | Main purpose | API / backend source | Entity / data source | Current risk |
|------------------|--------------|----------------------|----------------------|--------------|
| **ProductSystem** (`ProductSystem.tsx`, ~1978 lines) | Master-detail template CRUD: components, operations, materials; strict structural validation before save; links to dossier studio | `productTemplatesApi` → `/api/v1/entities/product_templates`; `productFamiliesApi`; `materialsApi` | `ProductTemplateEntity` (`components_json`, `operations_json`, `required_materials_json`, …) | Monolith page; mixed load/save/display; mock fallback in DEV can mask API failures |
| **ProductSystem — list panel** (inline in page) | Search/filter templates, select template, create/delete template | Same as above | `ProductTemplateEntity[]` | Duplicated “template list” pattern vs Blueprint Dossier Studio |
| **ProductSystem — editor** (inline subcomponents) | Edit component types, operations, materials; `validateTemplateComponentsStrict` blocks save | `productTemplatesApi` create/update | Draft mapped from entity | Business validation in UI (`validateTemplateComponentsStrict`) — must not weaken in display-only Phase 1 |
| **Blueprint Dossier Studio** (`BlueprintDossierStudio.tsx`, ~1906 lines) | Template list + dossier selection; per-section JSON editors; status transitions; readiness panel for selected dossier | `blueprintDossierApi` → `/api/v1/entities/product-blueprint-dossiers`; `productTemplatesApi`; `getProductReadiness` → `/api/v1/product-readiness/blueprints/{id}` | `BlueprintDossierEntity`; `ProductReadinessDto` | Second monolith; overlaps template list with ProductSystem; local `classifyError` duplicates API helper |
| **Dossier section editors** (`DossierSectionEditors.tsx`, ~1266 lines) | Section-specific forms (variants, task rules, cost mapping, QC, risks, completion state, validation summary) | Writes via `blueprintDossierApi` update | Section `*_json` fields on dossier | Large component file; editing + presentation coupled |
| **Dossier Completion Dashboard** (`DossierCompletionDashboard.tsx`, ~364 lines) | Read-only table: dossier status, section counts, missing sections, link to studio | `blueprintDossierApi.list` only | `BlueprintDossierEntity` | **Header claims no local readiness truth, but `computeDossierSummary` counts non-empty JSON locally** — diverges from backend readiness and from `getCompletionStates` |
| **Readiness display (Studio)** | Banner/sections for `ready_for_quote`, blockers, technical/costengine/document readiness | `getProductReadiness` (`frontend/src/api/productReadiness.ts`) | `ProductReadinessDto` (`policy.authority: "backend"`) | **Canonical when used**; not used on Completion Dashboard |
| **Readiness display (Completion Dashboard)** | Completion % and missing section labels | None for readiness | Derived locally in `computeDossierSummary` | **High risk**: UI becomes truth for “completare” |
| **Dossier API helpers** (`blueprintDossier.ts`) | `DOSSIER_SECTIONS` metadata; `countPopulatedSections`; `getCompletionStates`; CRUD | SDK `client.entities["product-blueprint-dossiers"]` | `BlueprintDossierEntity` | `countPopulatedSections` ≠ `completion_state_json` semantics; used for display counts |
| **Components / materials / operations UI** (inside ProductSystem) | Visual editing of template structure; workstation routing display | Template CRUD + `getRoutingForOperation` (local lib) | Parsed JSON arrays on template | Correct domain (product definition); keep save/validation behavior unchanged in Phase 1 |
| **Output Blocks Preview** (adjacent route) | Preview rendered output blocks for quotes/templates | `/api/v1/product-system/output-blocks/*` | Quote/template preview DTOs | Touching this in Phase 1 risks crossing into CostEngine/quote output — **exclude** |
| **Duplicated completion logic** | See §3 | — | — | **Three representations**: (1) `computeDossierSummary` non-empty JSON scan, (2) `countPopulatedSections`, (3) `getCompletionStates` / `completion_state_json`; readiness from `getProductReadiness` is separate and authoritative for gates |

### Backend endpoints (reference, not to change in Phase 1)

| Concern | Router / path |
|---------|----------------|
| Product templates | `backend/routers/product_templates.py` — `/api/v1/entities/product_templates` |
| Blueprint dossier | `backend/routers/product_blueprint_dossier.py` — `/api/v1/entities/product-blueprint-dossiers` |
| Product readiness | `backend/routers/product_readiness.py` — `/api/v1/product-readiness/blueprints/{blueprint_id}` and `/api/v1/product_system/readiness/{template_id}` (frontend uses blueprints path) |
| CostEngine | Separate routers/services — **forbidden in Phase 1** |

---

## 3. Canonical truth sources

| Truth | Owner | Canonical source | UI may |
|-------|--------|------------------|--------|
| **Product definition** | ProductSystem (design-time) | `product_templates` entity; validated on create/update (backend + `validateTemplateComponentsStrict` in UI before save) | Display, edit via existing CRUD; must not redefine component contracts |
| **Dossier section content** | Blueprint Dossier service | `product_blueprint_dossiers` `*_json` fields; server validation on write (`validate_json_fields`, `validate_completion_state_json`, status rules) | Display sections; edit via existing editors and API |
| **Dossier lifecycle status** | Backend | `status` on dossier entity; `ALLOWED_STATUS_TRANSITIONS` mirrored in `blueprintDossier.ts` for UI only | Show badges; submit transitions allowed by API |
| **Section completion state** | Backend (when populated) | `completion_state_json` on dossier | Display via `getCompletionStates`; must not invent new states |
| **Readiness / quote gates** | Backend | `ProductReadinessService` → `GET /api/v1/product-readiness/blueprints/{id}` | Display `ProductReadinessDto` only; **no local gate simulation** |
| **Cost** | CostEngine | CostEngine services and config routers | Display cost results only where already wired; **no CostEngine changes** |
| **Commercial quote** | Quotes module | Quote entities, output snapshots, documents | Out of Phase 1 scope |
| **Order snapshot** | Orders module | Frozen order/quote snapshot entities | Out of Phase 1 scope |
| **Execution** | WorkOS / Execution | Execution plans, reality, operator tasks | Out of Phase 1 scope |

### Display rules (audit constraints)

1. **Readiness** — When `getProductReadiness` is available, it is **canonical** for `ready_for_quote`, blockers, and readiness sections.
2. **Completion %** — Must not be computed only by “non-empty JSON string” heuristics if backend provides `completion_state_json` or readiness; align display layer in Phase 1 without changing backend rules.
3. **UI is not a source of truth** — Aggregates on Completion Dashboard should be refactored to **read** backend/state, not re-derive business meaning locally.

---

## 4. Known risks before refactor

| Risk | Description | Severity |
|------|-------------|----------|
| **Duplicated completion logic** | `computeDossierSummary` (Dashboard) vs `countPopulatedSections` / `getCompletionStates` (Studio/API helpers) measure different things | High |
| **Readiness not used on Dashboard** | Studio fetches `getProductReadiness`; Dashboard does not — inconsistent operator view | High |
| **Large page files** | `ProductSystem.tsx` (~1978), `BlueprintDossierStudio.tsx` (~1906), `DossierSectionEditors.tsx` (~1266) | Medium — refactor hazard if behavior mixed with layout |
| **Display vs business coupling** | Saving dossier sections, template strict validation, and status transitions live beside presentation | High if Phase 1 touches save paths |
| **Local UI calculations** | Empty-string checks (`null`, `[]`, `{}`) as “complete” proxy | High — can diverge from backend |
| **Accidental CostEngine / commercial chain edits** | Shared `frontend/src/api`, product-system output-blocks routes near dossier | Medium — scope discipline required |
| **Mock / DEV auth** | `isMockEnabled`, `VITE_ENABLE_DEV_AUTH` can show data without signaling production parity | Medium — document test conditions |
| **Deferred dossier sections in Studio** | `output_blocks_json`, `visual_prompt_blocks_json` excluded from `ACTIVE_SECTION_KEYS` | Low — intentional; document in Phase 1 UI copy |

---

## 5. Phase 1 recommended scope (UI / display only)

Phase 1 prepares a **display layer** without changing business behavior or contracts.

### In scope

- Add **`frontend/src/features/product-system/`** (or equivalent) with:
  - View-model mappers: template row, dossier row, section card, readiness banner
  - Hooks: `useBlueprintReadiness(templateId)`, `useDossierDisplay(dossier)` wrapping existing APIs
- **Consolidate presentation logic**:
  - Single module for section metadata (`DOSSIER_SECTIONS` already in `blueprintDossier.ts`)
  - Replace inline duplicate completion counting in Dashboard with shared display helpers that **prefer** `completion_state_json` and **optional** readiness fetch for badges
- **Split large UI sections** (presentational components only):
  - Template list panel, dossier list panel, readiness banner, section progress strip
- **Keep unchanged**:
  - All API URLs and request/response shapes
  - Backend services, routers, migrations
  - `validateTemplateComponentsStrict` behavior on save
  - Dossier save/update payloads and status transition rules
  - CostEngine, Quotes, Orders, Execution code paths
- **Testing**:
  - Existing vitest tests for `productReadiness`, `blueprintDossier` helpers must still pass
  - Manual smoke: `/product-system`, `/product-system/blueprint-dossier`, `/product-system/dossier-completion`

### Out of scope for Phase 1

- Unified hub layout / route merge (Phase 2)
- Figma/Code Connect (optional parallel track)
- Output blocks preview rework
- Backend new endpoints (unless separately approved)

### Safe rollback

- Work on branch `refactor/product-display-vm`
- Small commits per mapper/page wiring
- Revert branch if display regressions unacceptable

---

## 6. Phase 1 forbidden scope

The following are **explicitly forbidden** during Phase 1:

| Area | Forbidden actions |
|------|-------------------|
| **CostEngine** | Any router, service, formula, simulation, or config change |
| **Readiness rules** | Changes to `ProductReadinessService`, DTOs, gate logic, or new readiness semantics |
| **Product contracts** | `product_contracts.py`, template component contracts, linkage validators |
| **Quote / order snapshot** | Quote output, order snapshot, PDF, snapshot governance |
| **Inventory governance** | Admin inventory sheet remediation/quality, material registry |
| **Migrations** | Alembic versions, schema changes |
| **Auth** | OIDC, JWT, permissions, dev auth policy |
| **SmartBill / production config** | Integrations, staging/production env |
| **Backend dossier validation** | Status transitions, `validate_completion_state_json`, delete policy |
| **New business rules** | New gates, new required sections, new approval workflows |

---

## 7. PASS / FAIL checklist (this audit step)

| Criterion | Result |
|-----------|--------|
| Audit doc exists at `docs/audit/PRODUCTSYSTEM_DOSSIER_UI_AUDIT.md` | **PASS** |
| No runtime application code modified | **PASS** (documentation-only step) |
| No backend files modified | **PASS** |
| No migrations modified | **PASS** |
| No business logic modified | **PASS** |
| Phase 1 scope clearly documented | **PASS** |
| Risks clearly documented | **PASS** |

### Overall: **PASS**

This document satisfies the pre-refactor audit gate. Implementation of Phase 1 must be a **separate change set** with its own review against §5 and §6.

---

## Appendix A — File inventory (audit reference)

| Path | Approx. lines | Notes |
|------|---------------|-------|
| `frontend/src/pages/ProductSystem.tsx` | 1978 | Template studio monolith |
| `frontend/src/pages/BlueprintDossierStudio.tsx` | 1906 | Dossier studio monolith |
| `frontend/src/pages/DossierCompletionDashboard.tsx` | 364 | Local `computeDossierSummary` |
| `frontend/src/components/dossier/DossierSectionEditors.tsx` | 1266 | Section editors |
| `frontend/src/api/blueprintDossier.ts` | 397 | Section metadata + helpers + CRUD |
| `frontend/src/api/productReadiness.ts` | 58 | Canonical readiness client |
| `backend/routers/product_blueprint_dossier.py` | — | Dossier CRUD; no cost/quote/order |
| `backend/routers/product_readiness.py` | — | Readiness evaluation |
| `backend/data_models/product_contracts.py` | — | Cross-module DTO contracts |

## Appendix B — Duplicated completion / readiness (code anchors)

| Logic | Location | Mechanism |
|-------|----------|-----------|
| `computeDossierSummary` | `DossierCompletionDashboard.tsx` | Counts non-empty `*_json` fields (13 keys) |
| `countPopulatedSections` | `blueprintDossier.ts` | Counts non-empty strings for all `DOSSIER_SECTIONS` keys |
| `getCompletionStates` | `blueprintDossier.ts` | Parses `completion_state_json` |
| `getProductReadiness` | `productReadiness.ts` / Studio `useEffect` | Backend authority for gates |

**Recommendation for Phase 1:** One display module consumes `getCompletionStates` + optional `getProductReadiness`; deprecate ad-hoc non-empty JSON counting for user-facing “completare” labels.

---

*End of audit document.*
