# Build — ADAPTER_DISPLAY_ADMIN_TABLES_WIRING_V1 (labels / IA only)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS_WITH_WARNINGS** |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Base** | `7f14971afe7c0391d42c7aa7492e158d5b633ecf` — Clarify offer versus internal cost chrome |
| **Plan** | [`plan__adapter_display_admin_tables.md`](./plan__adapter_display_admin_tables.md) |
| **Forbidden (respected)** | DB rename, API contracts, real `module_template_*` rename, migrations, formulas/pricing, ProductDefinition/ProductAggregate **behavior**, Execution materialization, seed/reset, SVG/DWG, commit |

---

## Verdict

**PASS_WITH_WARNINGS**

Display-adapter wiring only: `displayModuleTemplateWireLabel()` (+ shared Module produs chrome constants) is now used on the hot Product System admin tables/panels from the plan. Internal wire keys / `TPL-*` identity codes remain. Targeted Vitest green. Runtime screenshots under `audit_assets/23_adapter_display_admin_tables_*`. **No commit.**

**Warnings (honest):**

1. Primary `/product-system/products` catalog is `ProductSystemCanonicalCatalog` — `TemplateLibraryView` “Module produs partajate” overview chrome is wired + unit-tested but **not** the live products shell (CatalogShell unused by page).
2. Editor `SharedVolumetricFoundationPanel` (“Module produs partajat: …”) only renders when `shared_component_contracts.length > 0`; Letters runtime editor session had **0** contracts → panel absent (label wiring present in code).
3. Ofertă vs Cost intern prior warnings **unchanged** (out of this build): Intake Straturi scope copy, Quotes KPI „VALOARE TOTALĂ”, some admin „comercial”.
4. Unrelated audit snake_case Field labels (`instance_id`, `layer_group_ids`, …) intentionally left technical.

---

## Cat suntem in directia stabilita

**92/100%**

| Layer | Score | Note |
|------:|------:|------|
| Product Template → Module produs vocabulary | 98% | Nivel 1–2B closed |
| Product Compiler shell | 86% | Prior build; preserved |
| Ofertă client vs Cost intern chrome | 90% | Prior build; warnings remain |
| Adapter helper + admin table wiring | **88%** | Hot sites wired; CatalogShell / empty shared-contracts paths soft |
| Intake technical disclosure of codes | 50% | Soft stretch: “Module produs” / “Module produs active”; codes stay |
| Nivel 3 real rename | 0% | Intentionally deferred |

Prior plan baseline for this slice was **88/100%** (adapter ~55% unused). This build lifts **admin wire-label hygiene** without engines.

---

## Where the adapter is used

| Surface | File | Change |
|---------|------|--------|
| Vocabulary | `productTemplateModulesVocabulary.ts` | Shared chrome constants; adapter covers `component_template_code`, `*_module_template_code`, `module_template_id`, `product_template_module_links`, `usage_mode`, `instance_schema_id` |
| Return-cant Field column | `returnCantReadonlyContainerModel.ts` (+ duplicate sync in `ProductSystem.tsx`) | `component_template_code` → **Module produs code**; `targetPath` unchanged |
| Shared foundation cards | `ProductSystem.tsx` | “Shared module:” → **Module produs partajat:** |
| Catalog / foundation chips | `TemplateLibraryView.tsx` | “Shared modules” → **Module produs partajate**; composition rows human name + mono code |
| Template detail composition / components / relations | `ProductSystemTemplateDetailPanel.tsx` | Human primary + code secondary; column header via adapter; “Legături Module produs” via authoring panel |
| Contract admin | `ComponentContractUsedByPanel.tsx` | `usage_mode` / `instance_schema_id` → Mod utilizare / Schema instanță |
| Composition authoring | `TemplateCompositionAuthoringPanel.tsx` | Caption `Legături Module produs` |
| Blueprint dossier (stretch) | `BlueprintDossierStudio.tsx` | Human name primary + code secondary |
| Intake review (stretch) | `IntakeV6ReviewStep.tsx` | “Module produs” / “Module produs active” |

---

## Intentionally leftover wire labels

| Keep visible | Why |
|--------------|-----|
| `targetPath` like `components.return_cant.instances[].component_template_code` | Auditor path truth |
| Mono `TPL-*` / `TPL-COMP-*` values | Stable identity |
| Audit Field keys: `instance_id`, `layer_group_ids`, `confirmed_perimeter_m`, … | Not Module produs wire; plan: do not over-adapt |
| API/TS fields `module_template_code`, `shared_module_template_code`, … | Contract honesty |
| Intake `<details>` / technical binding codes | Optional disclosure; soft polish only |
| Pricing Registry | Control — still no `module_template_*` columns |

---

## Tests run

```powershell
cd C:\w\psiso\frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/TemplateLibraryView.test.tsx `
  src/pages/ProductSystem.badges.test.tsx `
  src/features/product-system/TemplateCompositionAuthoringPanel.test.tsx
```

**Result:** 4 files / **74 passed**

Do **not** claim `validate:frontend` green (known TS debt).

---

## Runtime

| Item | Value |
|------|--------|
| Frontend | http://127.0.0.1:3000 (HTTP 200) |
| Backend | http://127.0.0.1:8000 (HTTP 200) |
| Capture | `frontend/scripts/capture-adapter-display-admin-tables-screenshots.mjs` (+ focused Playwright one-offs for return-cant) |

### URLs verified

- `/product-system/products`
- `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` (detail + Compoziție + Editor → return-cant Field)
- `/product-system/components`
- `/modules`
- `/inventory/pricing` (control)

---

## Screenshots

- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_products_catalog.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_product_template_detail.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_composition_list.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_composition_links.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_return_cant_field_labels.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_return_cant_module_produs_code.png` (**Module produs code** Field + wire `targetPath`)
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_ownership_panel.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_components.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_modules_map.png`
- `docs/worklog/realignment/audit_assets/23_adapter_display_admin_tables_pricing_control.png`

---

## Remaining Ofertă vs Cost warnings (not acceptance for this build)

From [`build__oferta_vs_cost_intern_intake_chrome_v1.md`](./build__oferta_vs_cost_intern_intake_chrome_v1.md):

1. Intake V6 Straturi still uses „Ofertă pentru produs complet” (composition scope).
2. Quotes list KPI still „VALOARE TOTALĂ” vs „Ofertă client”.
3. Some non-offer admin still says „comercial”.
4. ~~Adapter not on every admin cell~~ — **this build addresses #4 for hot Product System tables**.

---

## Nivel 3 leftovers

1. Real DB/API `module_template_*` rename — **forbidden** until owner GO + dual-read.
2. Live products route still uses CanonicalCatalog (not TemplateLibraryView overview chrome).
3. Soft-humanize remaining audit snake_case Field labels (separate from Module produs adapter).
4. Optional route cosmetic `/product-system/components` path id.

---

## Honest UI opinion

The return-cant Field column now reads as an ownership audit in Module produs language without hiding the wire path — that is the highest-value win. Composition lists that lead with human name + mono `TPL-*` feel correct for operators. The Shared-modules English chrome is cleaned in the library component/tests, but the live products catalog no longer mounts that overview shell, so operators on `/product-system/products` will mainly notice detail/composition/editor changes, not overview cards. That mismatch is a shell-routing leftover, not an adapter failure.

---

## Files touched

- `frontend/src/features/product-system/productTemplateModulesVocabulary.ts` (+ test)
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/pages/ProductSystem.tsx` (+ badges test)
- `frontend/src/features/product-system/TemplateLibraryView.tsx` (+ test)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/ComponentContractUsedByPanel.tsx`
- `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx`
- `frontend/src/pages/BlueprintDossierStudio.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/scripts/capture-adapter-display-admin-tables-screenshots.mjs`
- This worklog + `audit_assets/23_adapter_display_admin_tables_*`

---

## Commit

**NO** — await separate user confirmation after PASS.
