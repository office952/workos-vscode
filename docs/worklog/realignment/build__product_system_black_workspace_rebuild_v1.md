# Build — PRODUCT_SYSTEM_BLACK_WORKSPACE_REBUILD_V1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Prerequisite** | [`audit__product_system_e2e_reality_before_rebuild_v1.md`](./audit__product_system_e2e_reality_before_rebuild_v1.md) |
| **FigJam** | https://www.figma.com/board/PSqEHZNtrq5J0rjX7NQT5l |
| **Meaning of BLACK / blank** | **Structural rebuild from zero (blank slate IA)** — **not** a dark-theme deliverable |
| **Forbidden (respected)** | DB rename, API contracts, migrations, pricing/formula, PD/Aggregate behavior, Execution materialize, seed/reset, SVG/DWG, Intake/Quotes/Pricing/Execution page remodel, commit |

---

## Verdict

**PASS_WITH_WARNINGS**

Structural blank workspace IA is in place on `/product-system/products` and `/product-system/products/:templateCode`:

- Shell primary chrome = **Workspace only** (planned tabs hidden; Pricing chip removed)
- Spine = **4 steps** (Template → Module produs → Compiler → Pregătire) — **Oferta is not a spine step**
- Detail primary tabs = **Product Template / Module produs / Product Compiler / Pregătire**
- Admin/debug/diagnostic drawer holds former primary tabs + lab closure
- Downstream Cost / Ofertă / Execution = **secondary collapsed links** (not calculators)
- Bare `/intake-v6` links retargeted to `/intake-v6/operator`
- Laboratory Closure money **not** on default overview (`lab_closure_visible_on_default_overview = 0` at capture)

**Why not full PASS:** catalog left pane still carries dense filter chips and advanced/admin list (now collapsed); app-level sidebar still shows Pricing/Oferte/Execution (out of scope). Visual theme was **not** the deliverable — WorkOS chrome remains the existing app skin.

---

## Cat suntem in directia stabilita

**78/100%**

| Layer | Score | Note |
|------:|------:|------|
| Spine fără Oferta ca pas PS | 95% | 4-step ownership spine |
| Shell fără planned tabs / Pricing chip | 95% | Runtime count 0 / 0 |
| Detail IA Template/Modules/Compiler/Readiness | 92% | Primary tabs reduced |
| Downstream-only Cost/Ofertă/Execution | 90% | Collapsed links |
| Lab Closure of overview | 95% | Moved under admin publication |
| Blank structure vs painted-old-UI | 75% | IA rebuilt; catalog filters still dense |
| Theme cosmetics as acceptance | N/A | Explicitly **not** scored |

Prior audit direction was 48%; this pass lifts structural clarity without claiming theme completion.

---

## Ce am reconstruit

1. **Vocabulary / spine** — `PRODUCT_SYSTEM_SPINE_STEPS` without `offer`; tagline marks Oferta/Cost/Execution as downstream.
2. **Downstream strip** — `ProductSystemOfferCostChannels` = Cost → Intake operator, Ofertă → `/quotes`, Execution → `/execution` (links only).
3. **Shell** — planned nav removed from chrome; Pricing registry chip removed; subtitle = blank workspace IA.
4. **Detail IA** — 4 primary tabs; admin drawer for contracts/pricing/dossier/publication/runtime/diagnostic tables; compiler section; lab closure under publication admin.
5. **Catalog** — empty-state teaches blank center; advanced catalog collapsed; filter “Pregătit pentru ofertă” → “Pregătit (structură)”.
6. **Intake links** — canonical `/intake-v6/operator`.

---

## Legacy eliminat din chrome principal

- Shell planned tabs (components/resources/operations/dependencies/validation/advanced)
- Pricing chip in PS header
- Spine step “Ofertă client / Cost intern”
- 8 primary detail tabs (contracts/pricing/dossier/publication/runtime as primary)
- Laboratory Closure / Reference Complete on overview
- Bare `/intake-v6` Link targets
- Offer language in ready filter label

---

## Mutat in admin/debug/diagnostic

- Contracte, Prețuri template, Dosar tehnic, Publicare, Previzualizare runtime
- Componente / Relatii / Materiale / Guards
- Laboratory Closure + Finish Line + modularity honesty (under Publicare admin details)

---

## Intentionat intern / neschimbat

- Wire fields `module_template_*`, API/PD/Aggregate/CPP/EIC behavior
- Planned routes still deep-linkable (hidden from chrome)
- App sidebar Comercial/Resurse (out of rebuild scope)
- `/modules`, `/quotes`, `/execution`, `/inventory/pricing` pages

---

## Teste rulate

```text
cd frontend
npx pnpm@8.10.0 exec vitest run \
  src/features/product-system/ProductSystemSpineBand.test.tsx \
  src/features/product-system/productSystemShellNavigation.test.ts \
  src/features/product-system/productSystemIntakeV6Links.test.ts \
  src/features/product-system/productSystemBlankWorkspaceIa.test.ts \
  src/features/product-system/productTemplateModulesVocabulary.test.ts
```

**Result:** 5 files, **20 passed**.

---

## Runtime URLs

| URL | Evidence |
|-----|----------|
| `/product-system/products` | Screenshot `26_*_products_workspace.png`; planned=0 pricing_chip=0 |
| `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | Center modules/compiler/readiness + 4 tabs |
| Capture script | `frontend/scripts/capture-product-system-blank-workspace-rebuild-v1-screenshots.mjs` |

---

## Screenshots

| File | Proves |
|------|--------|
| `audit_assets/26_product_system_blank_workspace_products_workspace.png` | Blank workspace chrome |
| `audit_assets/26_product_system_blank_workspace_chrome_no_planned_tabs.png` | No planned tabs |
| `audit_assets/26_product_system_blank_workspace_letters_center_modules_compiler_readiness.png` | Center IA |
| `audit_assets/26_product_system_blank_workspace_primary_tabs_four.png` | 4 primary tabs |
| `audit_assets/26_product_system_blank_workspace_downstream_collapsed.png` | Downstream secondary |
| `audit_assets/26_product_system_blank_workspace_downstream_open.png` | Downstream links |
| `audit_assets/26_product_system_blank_workspace_admin_drawer_closed.png` | Admin closed |
| `audit_assets/26_product_system_blank_workspace_admin_drawer_open.png` | Admin open |
| `audit_assets/26_product_system_blank_workspace_overview_no_lab_closure_money.png` | No lab money on overview |
| Before (rejected) | `audit_assets/24_product_system_total_ui_ux_refresh_*` |

---

## Opinie sincera UI

IA-ul principal este acum **lizibil ca workspace blank** (4 pași PS + drawer admin + downstream secundar). Nu este încă un “greenfield” vizual perfect: catalogul rămâne dens (filtre, badge-uri), iar sidebar-ul global încă amestecă Pricing/Oferte lângă Product System. Tema dark a app-ului **nu** este acceptarea — acceptarea e structura.

---

## Warnings ramase

1. Catalog filter density / badge noise still high.
2. App sidebar still lists Pricing / Oferte / Execution next to Product System (global chrome).
3. Studio editor tabs inside `ProductSystem.tsx` (outside catalog master-detail) not fully blank-rebuilt.
4. Orphan `ProductSystemCatalogShell` / `TemplateLibraryView` code still in tree (not wired as primary).

---

## Confirmari

- **Nu** s-au schimbat DB / API contracts / pricing formulas / ProductDefinition / ProductAggregate / Execution materialization.
- **Nu** s-a făcut commit.
- Dark theme cosmetics **nu** sunt deliverable-ul; livrabilul este blank structural IA.
