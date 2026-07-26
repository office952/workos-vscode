# Build — PRODUCT_SYSTEM_V2_BLANK_WORKSPACE_FROM_ZERO_PLAN_AND_BUILD_V1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Prerequisite** | [`audit__product_system_e2e_reality_before_rebuild_v1.md`](./audit__product_system_e2e_reality_before_rebuild_v1.md) · [`build__product_system_black_workspace_rebuild_v1.md`](./build__product_system_black_workspace_rebuild_v1.md) |
| **Meaning of blank** | **IA / structure from zero** — not dark-theme cosmetics; not rearrange of old catalog |
| **Forbidden (respected)** | DB, API contracts, migrations, pricing/formula, PD/Aggregate behavior, Execution materialize, Intake/Quotes/Orders/Execution redesign, SVG/DWG, commit |

---

## Verdict

**PASS_WITH_WARNINGS**

Product System **V2** is now the primary experience on `/product-system/products` and `/product-system/products/:templateCode`: a dedicated blank workspace (rail + Template / Modules / Compiler / Readiness) that does **not** mount `ProductSystemCanonicalCatalog` filter chrome. Old catalog/studio is **isolated** behind `?ps_legacy=1` (not deleted).

**Why not full PASS:** app-level sidebar still shows Pricing / Oferte / Execution (out of scope). V2 still sits inside the global WorkOS shell. Owner visual review of `27_*` vs `24_*` / `26_*` remains the final bar.

Runtime capture: `canonical_filter_count_on_v2 = 0`.

---

## Cat suntem in directia stabilita

**86/100%**

| Layer | Score | Note |
|------:|------:|------|
| V2 as primary (not rearranged catalog) | 90% | New `ProductSystemV2Workspace` |
| No dense filter chips on primary | 95% | Capture count 0 |
| Template + Modules center | 92% | Modules grid is visual center |
| Compiler + Readiness clear | 90% | Side-by-side row |
| Downstream secondary only | 92% | Collapsed Cost / Ofertă / Execution links |
| Legacy isolated, not deleted | 95% | `?ps_legacy=1` |
| Global app chrome confusion | 55% | Out of scope sidebar |

Prior blank pass was 78%; V2 lifts “still feels like old catalog under new IA”.

---

## Ce am construit in V2

1. [`ProductSystemV2Workspace.tsx`](../../frontend/src/features/product-system/ProductSystemV2Workspace.tsx) — blank workspace primary UI  
2. [`productSystemV2WorkspaceModel.ts`](../../frontend/src/features/product-system/productSystemV2WorkspaceModel.ts) — list model + legacy query helpers  
3. Wire in [`ProductSystem.tsx`](../../frontend/src/pages/ProductSystem.tsx): V2 default; CanonicalCatalog only when `ps_legacy=1`  
4. Shell subtitle / nav label → Product System V2  
5. Downstream strip remains links only (Cost → Intake operator, Ofertă → `/quotes`, Execution → `/execution`)  
6. Admin/debug drawer on V2 (E2E readiness + link to legacy + optional editor)

**Center IA:** Product Template · Module produs · Product Compiler · Pregătire  
**Not center:** Oferta, Pricing, Execution, dense filters, Laboratory Closure money

---

## Ce am izolat din UI vechi

| Surface | Isolation |
|---------|-----------|
| `ProductSystemCanonicalCatalog` (filters, buckets, cards) | `?ps_legacy=1` only |
| Library header “Products” catalog chrome | Only on legacy path |
| Studio editor | Unchanged; reachable from V2 admin “Editor șablon (intern)” / More menu |
| Detail panel multi-tab story | Lives under legacy catalog selection |

---

## Ce NU am sters inca (si de ce)

- CanonicalCatalog + TemplateDetailPanel + TemplateEditor — needed for admin/diagnostic fallback and existing tests  
- Planned shell routes — still deep-linkable, hidden from primary chrome  
- App sidebar Comercial/Resurse — out of this GO  
- Blueprint dossier / output-blocks-preview routes — secondary/admin  

Owner rule: isolate, don’t brutal-delete.

---

## Screenshots

| File | Content |
|------|---------|
| [`audit_assets/27_product_system_v2_blank_products_workspace.png`](./audit_assets/27_product_system_v2_blank_products_workspace.png) | `/product-system/products` V2 |
| [`audit_assets/27_product_system_v2_blank_letters_center.png`](./audit_assets/27_product_system_v2_blank_letters_center.png) | Letters detail full |
| [`audit_assets/27_product_system_v2_blank_modules_compiler_readiness.png`](./audit_assets/27_product_system_v2_blank_modules_compiler_readiness.png) | Modules + Compiler + Readiness |
| [`audit_assets/27_product_system_v2_blank_admin_closed.png`](./audit_assets/27_product_system_v2_blank_admin_closed.png) | Admin closed |
| [`audit_assets/27_product_system_v2_blank_admin_open.png`](./audit_assets/27_product_system_v2_blank_admin_open.png) | Admin open |
| [`audit_assets/27_product_system_v2_blank_downstream_open.png`](./audit_assets/27_product_system_v2_blank_downstream_open.png) | Downstream open |
| [`audit_assets/27_product_system_v2_blank_legacy_isolated.png`](./audit_assets/27_product_system_v2_blank_legacy_isolated.png) | Legacy catalog badge path |

Compare visually to `24_*` (rejected refresh) and `26_*` (prior blank-on-catalog).

---

## Teste rulate

```text
cd frontend
npx pnpm@8.10.0 exec vitest run \
  src/features/product-system/productSystemV2Workspace.test.ts \
  src/features/product-system/productSystemBlankWorkspaceIa.test.ts \
  src/features/product-system/ProductSystemSpineBand.test.tsx \
  src/features/product-system/productSystemIntakeV6Links.test.ts \
  src/features/product-system/productSystemShellNavigation.test.ts \
  src/features/product-system/productTemplateModulesVocabulary.test.ts \
  src/pages/ProductSystem.badges.test.tsx
```

V2 + blank + spine + intake + shell + vocabulary: green.  
Badges suite: updated legacy default entry `?ps_legacy=1` + channel label expectations (run after fix).

Capture: `node scripts/capture-product-system-v2-blank-workspace-screenshots.mjs` → `canonical_filter_count_on_v2 0`.

---

## Opinie sincera vizuala

V2 **nu** mai arată ca filtrul dens CanonicalCatalog rearanjat: rail simplu + Module produs ca centru e o experiență diferită. Totuși rămâne în shell-ul WorkOS global (sidebar Pricing/Oferte), deci nu e “app blank” complet — doar Product System blank. Pentru PASS full ar trebui owner accept pe `27_*` și eventual un pass separat pe app nav (out of scope aici).

---

## Confirmari

- **Nu** DB / API / pricing / ProductDefinition / ProductAggregate / Execution changes  
- **Nu** commit  
- Atoms **nu** a fost sursa de adevăr UI  
- Blank ≠ dark theme deliverable  
