# Plan — ADAPTER_DISPLAY_ADMIN_TABLES (labels / IA only)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Type** | Audit + implementation plan (**docs only** — no production code in this pass) |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Base commit** | `7f14971afe7c0391d42c7aa7492e158d5b633ecf` — Clarify offer versus internal cost chrome |
| **Parent plans / builds** | [`plan__workos_product_system_simplification_pass.md`](./plan__workos_product_system_simplification_pass.md) · [`build__product_compiler_display_shell_v1.md`](./build__product_compiler_display_shell_v1.md) · [`build__oferta_vs_cost_intern_intake_chrome_v1.md`](./build__oferta_vs_cost_intern_intake_chrome_v1.md) |
| **Forbidden (this plan + next build)** | DB rename, API contract changes, real `module_template_*` rename, migrations, formulas/pricing, ProductDefinition/ProductAggregate **behavior**, Execution materialization, seed/reset, SVG/DWG parsing |

---

## Verdict

**GO_WITH_CONSTRAINTS**

Wire the existing display adapter (`displayModuleTemplateWireLabel` + small related vocabulary helpers) onto admin Product System tables/panels that still print raw wire field names or English “Shared module(s)” chrome. Keep `TPL-*` codes visible as identity (monospace secondary). Do **not** rename DB/API. Pricing Registry has **no** `module_template_*` column headers today — out of hot path for this build.

---

## Direction score

**88/100%** (honest)

| Layer | Score | Note |
|------:|------:|------|
| Product Template → Module produs vocabulary | 98% | Nivel 1–2B closed |
| Product Compiler shell | 86% | Prior build; preserved |
| Ofertă client vs Cost intern chrome | 90% | Prior build; warnings remain (see below) |
| Adapter helper exists | 55% | `displayModuleTemplateWireLabel` tested; **almost unused in UI** |
| Admin tables / ownership audit wire labels | 35% | Hot: return-cant truth field labels, Shared modules chrome, composition secondary codes |
| Intake technical disclosure of template codes | 45% | Codes under details / review binding — acceptable if labeled |
| Nivel 3 real rename | 0% | Intentionally deferred |

Prior baselines: Ofertă vs Cost intern **90%**; Product Compiler shell **86%**. This slice is still naming/display only — score rises on **admin wire-label hygiene**, not offer/cost or compiler engines.

---

## Existing adapter (do not reinvent)

| Artifact | Path | Status |
|----------|------|--------|
| Wire → display helper | `frontend/src/features/product-system/productTemplateModulesVocabulary.ts` → `displayModuleTemplateWireLabel()` | Maps `module_template_code`, `*_module_template_code`, `component_template_code` → **Module produs code**; other `module_template*` → **Module produs (wire)** |
| Source-type helper | same file → `displayModuleSourceTypeLabel()` | Already used in return-cant truth table for `sourceType` |
| Unit tests | `frontend/src/features/product-system/productTemplateModulesVocabulary.test.ts` | Adapter cases present; not yet call-site coverage |
| Related display | `frontend/src/features/product-system/productSystemAdminDisplay.ts` → `humanTemplateName()` | Humanizes **values** (`TPL-…`), not wire **keys** |

**Gap:** Compiler shell added the helper but left admin cells printing raw keys / “Shared module*” English. That is the explicit Nivel 3 remainder from `build__product_compiler_display_shell_v1.md`.

---

## Exact inventory — places wire / technical labels still appear

### A. In-scope hot (admin Product System — next build)

| # | File | UI context | Route(s) | What operator sees |
|---|------|------------|----------|--------------------|
| 1 | `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts` | Return-cant truth container **Field** column | `/product-system/products/:templateCode` (ownership / return-cant panel) | Primary label `component_template_code` (and other snake_case field labels) |
| 2 | `frontend/src/pages/ProductSystem.tsx` | Duplicate `RETURN_CANT_TRUTH_CONTAINER_FIELDS` + `ReturnCantTruthContainerPanel` render `{field.label}` | same | Same raw `component_template_code` as Field header text; `formSystemFields` includes `volum_aluminum_module_template_code` in ownership audit data |
| 3 | `frontend/src/pages/ProductSystem.tsx` | Shared component foundation cards | same (template editor / shared foundation) | Prefix **“Shared module:”** + `module_template_code` / `shared_module_template_code` / `reserved_module_template_code` values |
| 4 | `frontend/src/features/product-system/TemplateLibraryView.tsx` | Catalog overview card + compact foundation chips + composition grid | `/product-system/products` | Title/chips **“Shared modules”** / **“Shared modules: N/6”**; composition rows show raw `module.module_template_code` (value OK; column is unlabeled wire identity) |
| 5 | `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` | Template detail composition / relations lists | `/product-system/products/:templateCode` | Lists print `module.module_template_code` / `contract.module_template_code` as primary mono lines; “modul legacy partajat” OK |
| 6 | `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx` | Composition authoring (API: `product_template_module_links`) | template detail (embedded) | Human name primary; secondary mono = code (OK). File comment still says `product_template_module_links` (dev-facing only) |
| 7 | `frontend/src/features/product-system/ComponentContractUsedByPanel.tsx` | Contract “Copii / module” list + admin inputs | template / contract admin surfaces | Secondary `module_template_code`; labels `usage_mode`, `instance_schema_id` (admin wire — soft adapt) |

### B. Secondary / operator-adjacent (optional same build or follow-up)

| # | File | UI context | Route(s) | Note |
|---|------|------------|----------|------|
| 8 | `frontend/src/pages/BlueprintDossierStudio.tsx` | Module links cards | `/product-system/blueprint-dossier` | Primary line = `link.module_template_code` (prefer `humanTemplateName` primary + code secondary) |
| 9 | `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | Review binding / volum module | `/intake-v6/operator` | “Template modul” select shows codes; “Module active:” joins codes — label polish only |
| 10 | `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx` | Layer component “Detalii tehnice” | Intake V6 Straturi | `component_template_code` under `<details>` — keep as technical disclosure; optional caption via adapter |
| 11 | `frontend/src/components/workos/intake-v6/IntakeV6SupportContourGeometryCard.tsx` | Support contour card | Intake V6 | Mono `component_template_code` value |
| 12 | `frontend/src/components/workos/OperatorTaskIdentityPresentation.tsx` | Task identity “Șablon:” | Execution / operator task UI | Shows code value (OK); caption already RO |

### C. Clean / out of this build

| Surface | Finding |
|---------|---------|
| Pricing Registry (`frontend/src/components/pricing/PricingRegistrySpaciousView.tsx`, `/inventory/pricing`) | **No** `module_template_*` / `component_template_code` UI strings |
| `/modules` ModuleChain | No wire-key column labels found for this adapter |
| Shell nav `Module produs` → `/product-system/components` | Planned section; path id cosmetic (optional later) |
| API types (`frontend/src/api/productTemplateModuleLinks.ts`, `productTemplateComponentContracts.ts`, `lib/api.ts`) | Wire contracts — **must stay** |

---

## What can be fixed via display adapter

1. **Field / column labels** that equal wire keys (`component_template_code`, `module_template_code`, `volum_aluminum_module_template_code`, any `*_module_template_code`) → run through `displayModuleTemplateWireLabel` (or a thin table-label wrapper).
2. **Chrome strings** “Shared module” / “Shared modules” → vocabulary constants aligned with `MODULE_PRODUS_SHARED_LABEL` / “Module produs partajate”.
3. **Admin form labels** `usage_mode` / `instance_schema_id` → short RO/EN human labels (display only; patch payload keys unchanged).
4. **Optional:** caption above monospace `TPL-*` values (“Module produs code”) without hiding the code.
5. **Pattern for composition lists:** primary = `humanTemplateName(code)` (already often true); secondary = code; never promote wire key name as the only heading.

Extend adapter only if needed:

- `product_template_module_links` → display “Legături Module produs” (admin heading)
- `module_template_id` → “Module produs id” (if ever shown as a column header)

Do **not** map unrelated snake_case (`instance_id`, `layer_group_ids`) into Module produs language — those stay technical audit fields (optional soft humanization later, separate from this GO).

---

## What must stay internal

| Keep as-is | Why |
|------------|-----|
| TS/API fields `module_template_code`, `shared_module_template_code`, `reserved_module_template_code`, `component_template_code`, `module_template_id` | Contract honesty |
| DB / OpenAPI / Python services | Forbidden rename |
| Test fixtures using wire keys | Correct contract samples |
| Logs, data-testid keys, React keys using codes | Stability |
| `TPL-*` / `TPL-COMP-*` identity values in mono | Stable identity, not type labels |
| Guard copy mentioning ProductDefinition / ProductAggregate | Honesty |
| CPP / EIC / Snapshot wire names in parentheses | Offer/cost channel honesty from prior build |
| `targetPath` strings like `components.return_cant.instances[].component_template_code` | Path truth for auditors — keep; only adapt **Field** label column |

---

## What must NOT be renamed now

- Any DB column or JSON key `module_template_*`
- API routes / DTOs / Alembic
- Service class names ProductDefinition* / ProductAggregate*
- Template codes themselves
- Pricing rate IDs / formula keys
- Route path `/product-system/components` (optional cosmetic later only)
- Historical worklog / QA folder names

---

## Remaining warnings from Ofertă vs Cost intern build

From [`build__oferta_vs_cost_intern_intake_chrome_v1.md`](./build__oferta_vs_cost_intern_intake_chrome_v1.md) (`PASS_WITH_WARNINGS`):

1. Early Intake V6 steps (Straturi) still use scope copy like „Ofertă pentru produs complet” (composition scope, not price channel).
2. Quotes list KPI titles still say „VALOARE TOTALĂ” rather than „Ofertă client”.
3. Some non-offer-flow admin (e.g. ClientWorkspace) still says „comercial”.
4. Nivel 3 wire rename explicitly deferred; adapter still not on every admin cell — **this plan addresses #4 only**.

Do **not** mix offer/cost microcopy polish into the adapter-tables build unless owner expands scope.

---

## Estimated risk

| Risk | Level | Mitigation |
|------|-------|------------|
| Tests assert visible text `component_template_code` / `Shared modules` | Medium | Update targeted Vitest expectations when labels change |
| Over-adapting audit `targetPath` / technical disclosure | Medium | Adapt labels only; keep paths and `<details>` codes |
| Confusing operators by hiding `TPL-*` | Low–Med | Keep codes secondary mono |
| Accidental API/DTO rename | **High if done** | Forbidden; review diff for wire key renames |
| Scope creep into Intake commercial chrome | Medium | Stay on Product System admin tables first |
| Pricing Registry churn with no wire pain | Low | Skip unless new findings |

**Overall risk of next build (display adapter wiring):** **Low–Medium**.  
**Risk of real rename instead:** **High — do not**.

---

## Exact tasks for the next build (numbered, scoped)

**Suggested build name:** `ADAPTER_DISPLAY_ADMIN_TABLES_V1`

1. **Extend vocabulary (minimal)** in `productTemplateModulesVocabulary.ts`: shared-modules chrome constants; ensure `displayModuleTemplateWireLabel` covers `product_template_module_links` / `module_template_id` if used as headings; keep pass-through for unrelated keys.
2. **Return-cant truth Field labels:** set `label` via adapter in `returnCantReadonlyContainerModel.ts` and remove/sync duplicate `RETURN_CANT_TRUTH_CONTAINER_FIELDS` labels in `ProductSystem.tsx` so UI never shows raw `component_template_code` as the Field title (`targetPath` unchanged).
3. **Shared foundation / catalog chrome:** replace “Shared module(s)” strings in `ProductSystem.tsx` and `TemplateLibraryView.tsx` with Module produs shared vocabulary; keep code values.
4. **Template detail composition lists:** in `ProductSystemTemplateDetailPanel.tsx`, prefer human name primary + code secondary; add “Module produs code” caption where a bare mono code is the only line.
5. **Contract admin soft labels:** `ComponentContractUsedByPanel.tsx` (+ optional composition authoring diagnostic labels) — humanize `usage_mode` / `instance_schema_id` captions only.
6. **Optional stretch (same PR if small):** Blueprint dossier link cards primary = `humanTemplateName`; Intake review “Module active” → “Module produs active” without changing joined codes.
7. **Tests + screenshots** (below); worklog `build__adapter_display_admin_tables_v1.md`.
8. **Out:** Pricing Registry structural edits, offer/cost KPI polish, DB/API rename, PD/Aggregate behavior, Execution materialize.

---

## Necessary tests

```powershell
cd C:\w\psiso\frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/TemplateLibraryView.test.tsx `
  src/pages/ProductSystem.badges.test.tsx `
  src/features/product-system/TemplateCompositionAuthoringPanel.test.tsx
```

Add/adjust:

| Test | Expect |
|------|--------|
| Vocabulary | Existing adapter cases + any new chrome constants |
| `ProductSystem.badges.test.tsx` | Stop requiring visible `component_template_code` as Field label; assert adapted label / still show path or code value where intended |
| `TemplateLibraryView.test.tsx` | “Shared modules” → Module produs shared wording |
| Optional smoke | Template detail composition list still shows `TPL-*` codes |

Do **not** claim `validate:frontend` green (known TS debt).

---

## Routes for screenshots

| Route | Capture focus |
|-------|----------------|
| `/product-system/products` | Catalog “Shared modules” → Module produs partajate chrome |
| `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | Template detail composition + ownership return-cant Field column |
| `/product-system/products` → open template editor / shared foundation | “Shared module:” cards |
| `/product-system/blueprint-dossier` | Optional if stretch task included |
| `/inventory/pricing` | **Control only** — confirm still no wire-key columns (no redesign) |

Suggested asset prefix: `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_*`.

---

## Continuity notes

- Simplification plan §8 already recommended adapter-first; Compiler shell left adapter at ~40% wired.
- Ofertă vs Cost intern closed money-channel chrome; remaining warnings are **not** this build’s acceptance criteria.
- Active-path isolation / freeze: display-only reference correction under owner GO for this labels pass — no feature expansion.

---

## Summary for parent / implementer

| Item | Value |
|------|-------|
| Verdict | **GO_WITH_CONSTRAINTS** |
| Next build | Wire adapter + Shared-modules chrome on Product System admin tables |
| Hottest call sites | See top 5 below |
| Direction | **88/100%** after this plan is accepted; ~92% if V1 build lands cleanly |
| This pass changed | **This markdown file only** |
| Commit | **NO** |
