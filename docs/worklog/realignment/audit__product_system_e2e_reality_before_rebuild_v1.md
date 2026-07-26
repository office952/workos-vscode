# Audit — PRODUCT_SYSTEM_E2E_REALITY_AUDIT_AND_FIGMA_MAP_BEFORE_BLACK_REBUILD_V1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Type** | READ-ONLY E2E reality audit + FigJam ownership map |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **GO** | `PRODUCT_SYSTEM_E2E_REALITY_AUDIT_AND_FIGMA_MAP_BEFORE_BLACK_REBUILD_V1` |
| **Writes** | Acest raport + `audit_assets/25_product_system_e2e_figma_diagram.png` + FigJam board |
| **Forbidden (respected)** | UI implementare, commit, DB rename, API contracts, migrations, pricing/formula, PD/Aggregate behavior, Execution materialize, seed/reset, SVG/DWG parse |

---

## 1. Verdict

| Metric | Value |
|--------|-------|
| **Verdict rebuild UI/UX** | **GO_WITH_CONSTRAINTS** |
| **Cat suntem in directia stabilita** | **48/100%** |
| **Este sanatos rebuildul black?** | **DA** — dar ca rebuild de workspace Product System, nu ca polish pe UI-ul actual |
| **UI refresh anterior** | **NU acceptat** (owner) — scorul self-report 93% din build refresh este **respins** ca evidenta de acceptare |

### De ce GO_WITH_CONSTRAINTS

**GO** pentru rebuild UI Product System black, pentru ca:

- Ownership-ul canonic E2E este clar in cod + docs: Product System = biblioteca tehnica; Oferta = CPP/Snapshot; Execution = post-order.
- UI-ul actual confirma perceptia owner: refresh pe ramasite, prea multe niveluri de navigatie, Oferta/Cost vizibile in centrul Product System, taburi planned/placeholder, shell admin greu.
- Continuarea polish-ului pe acelasi stack vizual **nu** rezolva confuzia.

**CONSTRAINTS** (obligatorii pentru buildul urmator):

1. Doar UI/IA Product System (si legaturi de navigatie); **fara** schimbari PD/Aggregate/pricing/formula/API/DB.
2. Product System **nu** devine ecran de ofertare; Oferta/Cost/Execution = downstream channels / link-uri, nu flow principal.
3. Eliminare agresiva a taburilor/shell planned + orphan shells; diagnostic/admin separat.
4. Intake / Quotes / Pricing / Execution raman pe rutele lor — **nu** intra in rebuild Product System ca pagini principale.
5. Owner visual accept al noului black workspace inainte de orice „PASS” UI.

### Concluzie sincera Product System vs Oferta

**Product System** detine adevarul de **structura produs** (template, module produs, dossier, readiness).  
**Oferta** se formeaza in **Intake V6 + CommercialPriceProposal (7G) → Quote Snapshot V2**.  
Product System poate *mentiona* canalele Cost/Oferta/Execution, dar **nu** le detine si **nu** trebuie sa arate ca pagina de pret client.

---

## 2. Harta E2E (realitate actuala)

```text
Product Templates (Product System library)
        │
        ▼
Module produs (links + dossier + mini-modules)
        │
        ▼
Intake V6 workspace  ──► ProductDefinition / Product Compiler
        │                         │
        │                         ▼
        │                  ProductAggregate (technical graph + task_rules)
        │                         │
        ├─────────────────────────┼──► EstimatedInternalCost (7H)
        │                         └──► CommercialPriceProposal (7G)
        │                                   ▲
Pricing Registry (reference rates) ─────────┘
        │
        ▼
Oferta client (Intake dry-run/write + Quotes UI)
        │
        ▼
Quote Snapshot V2 (freeze 7G + 7H + PD + Aggregate)
        │
        ▼
Order Snapshot V2 (accepted freeze; no reprice)
        │
        ▼
ExecutionPlan V2 (preview / persist draft; materialize BLOCKED)
        │
        ▼
Execution Reality (sessions / actuals — later)

Registries interne (paralele, nu spine operator):
  Utilaje · HR/Pontaj · Inventory / Pricing Registry
```

### FigJam

| Item | Value |
|------|-------|
| **File name** | Product System E2E Reality Map + Target Black Workspace |
| **URL** | https://www.figma.com/board/PSqEHZNtrq5J0rjX7NQT5l |
| **Export PNG** | [`audit_assets/25_product_system_e2e_figma_diagram.png`](./audit_assets/25_product_system_e2e_figma_diagram.png) |
| **Sections** | 1 CURRENT · 2 OWNERSHIP · 3 MUST NOT COMBINE · 4 LEGACY · 5 TARGET · LEGEND |

---

## 3. Ownership boundaries (per sistem)

| Sistem | Owns | Does NOT own |
|--------|------|--------------|
| **Product System** | Template parent, Module produs links, dossier, task_rules source, readiness/publication lab gates, technical library UI | Pret client, ecran ofertare, Pricing hub, ExecutionPlan, Order |
| **ProductDefinition** | Compile: module active, canonical values, readiness/blockers | Pret, quote/order write, ExecutionPlan |
| **ProductAggregate** | Expanded graph: components/materials/ops + `task_contract.task_rules`; Cost BOM view | Oferta comerciala; scheduling |
| **Intake V6** | Product truth workspace, form answers, operator path to dry-run/write | Official freeze authority fara confirm; ExecutionPlan |
| **Pricing Registry** | Reference rates/rules (material / commercial / internal / capacity) | Instance CPP pe job; product structure |
| **EIC (7H)** | Cost intern estimativ pre-productie | Pret client |
| **CPP / Oferta (7G)** | Propunere comerciala client | Cost-plus intern ca oferta |
| **Quote Snapshot V2** | Freeze 7G+7H+PD+Aggregate | Live reprice din registry |
| **Order Snapshot V2** | Config + pret acceptat + estimate-at-accept | Recalc; create plan at convert |
| **ExecutionPlan** | planned_tasks din frozen Order Snapshot | Pricing; live Intake re-read |
| **Execution Reality** | Sessions / actuals (post-materialize) | Commercial formula |
| **Utilaje** | Capacity / machines | Pret client |
| **HR/Pontaj** | People / attendance / internal employee cost | Tarif client |
| **Governance** | GO / freeze / settings policy | Business compile / price calc |

### Raspunsuri obligatorii

| Intrebare | Raspuns |
|-----------|---------|
| Ce detine Product System? | Adevar tehnic produs: templates, module produs, dossier, readiness/publication lab |
| Ce NU detine? | Oferta, pret final, Pricing hub, Execution, Order freeze |
| Unde incepe Intake V6? | Capture workspace + form / product truth; rute `/intake-v6/.../operator` |
| Unde se termina ProductDefinition? | Dupa compile (structura + readiness); **inainte** de pret |
| Unde intra ProductAggregate? | Dupa/alongside PD: expand graph + task_rules pentru EIC / snapshot / plan |
| Unde se calculeaza cost intern? | EIC service (7H) + Cost BOM; consumat in Intake/lab; **nu** e oferta |
| Unde se formeaza Oferta client? | CPP 7G → Intake priced-quote → Quote Snapshot V2 → `/quotes` |
| Ce e doar downstream in PS? | Cost intern, Oferta client, ExecutionPlan / Reality, registries |
| Ce nu are voie UI principal in PS? | Ecran ofertare, Pricing editor, Execution board, QuoteWizard |
| Ce e legacy/dead/preview/admin/debug? | Vezi §5 |
| Ce meniuri/tabs de eliminat? | Vezi §6 |
| Ce rute istorice incurca? | Bare `/intake-v6`, planned shell tabs, orphan catalog shells, `/pricing` alias confusion |
| Ce ramane intern/diagnostic? | Diagnostic tabs, Laboratory Closure, Form System admin, runtime preview, orphan shells |

---

## 4. Ce NU trebuie combinat

1. **Product System ≠ Oferta** — chips CPP / „Ofertă client” in spine PS confunda ownership.
2. **Product System ≠ Pricing** — chip „Pricing (registry)” in header PS + tab „Prețuri template” = hub mixt.
3. **Product System ≠ Execution** — ExecutionPlan labels in compiler shell sunt downstream display, nu flow PS.
4. **Product System ≠ ecran de ofertare** — Laboratory Closure EIC+CPP pe overview este periculos operațional.
5. **Oferta foloseste PS downstream** — citește template/module/compile; **nu** detine Product System.
6. **EIC ≠ pret client**; **CPP ≠ cost intern**; **Snapshot ≠ live registry**.

---

## 5. Ramasite UI vechi / legacy / preview / admin / debug

### Confirmat din cod + screenshots `24_*` + runtime 200

| Remnant | Tip | Unde |
|---------|-----|------|
| App sidebar: Oferte / Pricing / Execution langa Product System | App nav (OK app-level; confuz daca PS se vinde ca hub) | `App.tsx` |
| PS shell tabs planned: Module produs, Resources, Operations, Dependencies, Validation, Advanced | Placeholder „În dezvoltare” | `productSystemShellConfig.ts` |
| Subtitle „Catalog admin → …” | Legacy mental model | `ProductSystemLayout` / catalog |
| Spine step 5 „Ofertă client / Cost intern” | Ownership blur in PS | `ProductSystemSpineBand.tsx` |
| `ProductSystemOfferCostChannels` pe empty + story | Downstream OK ca mention; prea central azi | Catalog + detail |
| Pricing registry chip in PS header | Cross-system chrome | Layout |
| 8 taburi primary detail + 4 diagnostic | Navigatie profunda | `ProductSystemTemplateDetailPanel.tsx` |
| Laboratory Closure / Reference Complete | Lab/admin pe overview | `ProductSystemReferenceCompletePanel.tsx` |
| Orphan `ProductSystemCatalogShell` + `TemplateLibraryView` | Dead/parallel UI code | features/product-system |
| Bare links `to="/intake-v6"` | Ruta confuza vs `/intake-v6/operator` | General tab, Finish/Mounting, tests |
| `/product-system/output-blocks-preview`, blueprint-dossier sibling | Admin/preview | `App.tsx` |
| QuoteWizard „+ Ofertă nouă” + CostEngine banner | Legacy offer path | `/quotes` (prior audit) |
| Unified catalog buckets `legacy-shared-modules` | Legacy vocabulary still in model | catalog entries |

### Screenshots existente (evidenta vizuala)

- `audit_assets/24_product_system_total_ui_ux_refresh_*` — refresh respins vizual
- `audit_assets/22_oferta_vs_cost_intern_*` — separare Oferta/Cost
- `audit_assets/23_adapter_display_admin_tables_*` — tabele tehnice
- `audit_assets/05/06/02/04` — PS / Intake / Quotes / Pricing (audit calcul)

---

## 6. Lista meniuri / tabs / sectiuni de eliminat (din UI principal PS)

**Elimina din primary chrome (muta admin/debug sau sterge din nav):**

1. Shell planned: Resources, Operations, Dependencies, Validation, Advanced  
2. Shell planned „Module produs” ca pagina separata placeholder (`/product-system/components`) — Module produs trebuie **in** Product Template, nu tab gol  
3. Detail tabs dominante: Contracte, Prețuri template, Publicare, Previzualizare runtime (admin/diagnostic)  
4. Laboratory Closure / Reference Complete pe overview  
5. Spine step care **incadreaza Oferta** ca pas 5 al Product System (inlocuieste cu „Downstream channels”)  
6. Pricing registry chip din header PS (ramane doar link secundar/admin)  
7. Orphan CatalogShell primary tabs (Dossiers / Guards placeholder) — nu mai expune  
8. Filter clutter „Pregătit pentru ofertă” ca daca PS ar fi oferta  

**Pastreaza ca centra paginii:**

- Product Template selectat  
- Module produs composition  
- Product Compiler compact  
- Readiness clar (fara lab closure money chips)

---

## 7. Ce muta in admin / debug / diagnostic

| Zona | Destinatie |
|------|------------|
| Diagnostic tabs (Componente, Relatii, Materiale, Guards) | Drawer `Diagnostic` |
| Prețuri template / Pricing Studio | Admin pricing recipe |
| Publicare / E2E lab panels | Admin readiness |
| Form System admin | Admin |
| Runtime preview | Debug |
| Laboratory Closure / Reference Complete | Lab-only |
| Blueprint dossier deep editor | Advanced admin route |
| Output blocks preview | Debug |
| Legacy replacement matrix | Admin migration |

---

## 8. Pagina principala Product System (target)

**O singura pagina-workspace black:**

1. **Centru:** Product Template + Module produs (composition grid)  
2. **Compact:** Product Compiler (PD + Aggregate ca un concept)  
3. **Readiness:** blockers/status fara bani  
4. **Downstream strip (secundar):** Cost intern · Oferta · Execution — link-uri, nu calculatoare  
5. **Registries:** Pricing / Utilaje / Pontaj — in afara PS (rute existente)  
6. **Admin/debug:** collapsed / permission-gated  

Nu: catalog legacy multi-bucket, nu hub mixt, nu ecran de oferta.

---

## 9. Propunere IA black workspace (arhitectura, nu pixel)

```text
/product-system/products[/:templateCode]   ← SINGURA ruta rebuild acum
  ├─ LEFT: lista Product Templates (minimal)
  ├─ CENTER: Module produs + Compiler + Readiness
  ├─ RIGHT/BOTTOM: Downstream channels (links)
  └─ ADVANCED drawer: diagnostic / publication / pricing recipe / dossier

OUT of rebuild now:
  /modules, /intake-v6*, /quotes*, /orders*, /execution*,
  /inventory/pricing, /utilaje, HR/Pontaj,
  /product-system/{components,resources,operations,dependencies,validation,advanced},
  /product-system/blueprint-dossier, output-blocks-preview
```

Visual direction (viitor build): complete black/dark; fara top-nav PS intern nefolosit; fara taburi legacy; fara tabele tehnice in centru; fara firmituri refresh-ului anterior.

---

## 10. Rute — in vs out of rebuild

### Intra in rebuild (UI Product System)

| Route | Rol |
|-------|-----|
| `/product-system` → products | Redirect |
| `/product-system/products` | Catalog minimal + workspace |
| `/product-system/products/:templateCode` | Detail black workspace |

### NU intra acum (mentionate ca downstream / separate)

| Route | Motiv |
|-------|-------|
| `/intake-v6/operator`, `/intake-v6/:id/operator` | Intake owns |
| `/quotes`, `/quotes/:id` | Oferta owns |
| `/orders`, `/orders/:id` | Order owns |
| `/execution`, `/execution/:order_id` | Execution owns |
| `/inventory/pricing`, `/pricing` | Pricing registry |
| `/utilaje` | Machines registry |
| `/modules` | System map (diagnostic L1) |
| Planned `/product-system/*` placeholders | Eliminate/hide, nu redesign |
| Blueprint dossier / output-blocks-preview | Admin later |

---

## 11. Runtime verification (2026-07-23)

| URL / call | Result |
|------------|--------|
| FE `:3000` | 200 |
| BE health | 200 |
| `/product-system/products` | 200 |
| `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | 200 |
| `/product-system/components` | 200 (planned placeholder) |
| `/modules` | 200 |
| `/intake-v6` | 200 (nu e ruta operator canonica) |
| `/intake-v6/operator` | 200 |
| `/inventory/pricing` | 200 |
| `/pricing` | 200 (redirect target) |
| `/utilaje` | 200 |
| `/quotes` | 200 |
| `/orders` | 200 |
| `/execution` | 200 |
| `GET …/product-definition/TPL-VOLUMETRIC-LETTERS_v2` | 200 |
| `GET …/aggregate/TPL-VOLUMETRIC-LETTERS_v2` | 200 |
| `POST …/entities/quotes/price` | **410** (retired) |

Note: dry-run / freeze **nu** au fost rulate (risc persistenta) — vezi audit calcul anterior pentru gap EIC/Snapshot preview.

---

## 12. Doc / code drift (marcaje)

| Topic | Drift |
|-------|-------|
| Doc 21 „7G IMPLEMENTED_PREVIEW_ONLY” | Runtime V6 foloseste CPP ca autoritate comerciala (audit calcul) |
| Doc 21 `/price` DEAD_LEGACY_RISK callable | Runtime **410** |
| Operating model § QuoteWizard Commercial Lock | Spine V2 CPP+Snapshot este canonicul actual |
| Build refresh 93% direction | Owner visual reject → scor audit **48%** pe directia black workspace |

---

## 13. Riscuri

| Risk | Severitate | Note |
|------|------------|------|
| Rebuild pe ramasite (refresh peste vechi) | **HIGH** | Owner deja a vazut asta |
| Spine care include Oferta ca pas PS | **HIGH** | Confunda ownership |
| Atins PD/Aggregate/pricing in „UI rebuild” | **CRITICAL** | Forbidden |
| Orphan shells lasate in tree | **MED** | Reapar in UI/tests |
| Bare `/intake-v6` links | **MED** | Operator land pe dashboard/`*` |
| `/modules` + PS vocab overlap | **LOW** | OK ca harta; nu ca authoring |
| Freeze repo / lab closed | **MED** | Rebuild UI necesita GO dedicat owner (acest audit il pregateste) |

---

## 14. Teste necesare pentru buildul urmator

1. Vitest: vocabulary / spine **fara** „Ofertă” ca pas Product System (downstream label).  
2. Vitest: shell nav — doar Products operational; planned tabs absente sau admin-gated.  
3. Vitest: detail primary tabs reduse (Template / Modules / Compiler / Readiness).  
4. Vitest: OfferCost channels = links only, nu calculatoare.  
5. Vitest: no bare `/intake-v6` — doar `/intake-v6/operator` (+ workspace).  
6. Smoke Playwright (optional): `/product-system/products` + Letters detail — black workspace landmarks.  
7. Regression: PD/Aggregate API responses neschimbate (contract snapshot).  
8. Negative: Pricing / Quotes / Execution pages **neschimbate** functional.

---

## 15. Screenshots necesare pentru buildul urmator

1. `/product-system/products` — empty / list black workspace  
2. `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` — center Modules + Compiler + Readiness  
3. Downstream channels strip (Cost / Oferta / Execution) — secondary  
4. Admin/debug drawer closed vs open  
5. Confirm **absenta** Laboratory Closure money chips pe overview  
6. Confirm **absenta** shell planned tabs din chrome principal  
7. Side-by-side before (`24_*`) vs after  

---

## 16. Acceptance criteria (rebuild black)

1. Owner visual accept: Product System arata ca **un** workspace black, nu catalog admin + firmituri.  
2. Centru = Product Template + Module produs; Compiler compact; Readiness clar.  
3. Oferta / Cost / Execution **doar** downstream mention/link.  
4. Zero taburi planned in primary chrome.  
5. Diagnostic/admin nu e flow principal.  
6. Fara schimbari API/DB/pricing/PD/Aggregate behavior.  
7. Fara commit in acest audit; rebuild = task separat cu GO.  
8. Direction score post-rebuild tinta: ≥ **85/100%** pe IA (nu pe polish pe vechi).

---

## 17. Cat suntem in directia stabilita: **48/100%**

| Layer | Score | Note |
|------:|------:|------|
| Ownership E2E documentat + cod | 88% | Spine clara; docs partial stale |
| UI Product System ca workspace coerent | 30% | Refresh respins; stacking vizibil |
| Separare PS vs Oferta in UI | 35% | Spine + channels inca amesteca perceptia |
| Eliminare leftovers / planned tabs | 25% | Shell planned inca navigabil |
| Downstream-only money/execution | 40% | Mentions exista; inca prea centrale |
| Black IA target agreed | 70% | Acest audit + FigJam |
| Ready to implement rebuild | 55% | Asteapta owner validate pe audit/FigJam |

---

## 18. Fisiere citite (principale)

**Architecture:**  
`docs/architecture/realignment/03_PRODUCT_DEFINITION_COMPILER.md`  
`docs/architecture/app-flows/05_PRODUCT_AGGREGATE_FLOW.md`  
`docs/architecture/realignment/08_PRICING_REGISTRY_SEPARATION.md`  
`docs/architecture/app-flows/08_EXECUTION_PLAN_FLOW.md`  
`docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md`  
`docs/architecture/realignment/12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md`  
`docs/architecture/realignment/14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`  
`docs/architecture/realignment/18_GOVERNANCE_SETTINGS_POLICY.md`  
`docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`  
`docs/architecture/realignment/09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md`  
`docs/architecture/app-flows/03_PRODUCT_SYSTEM_FLOW.md`  
`docs/architecture/WORKOS_INTAKE_TO_EXECUTION_OPERATING_MODEL.md`  
`docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` (via prior audit)  
`docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md` (via prior audit)

**Worklog:**  
`docs/worklog/realignment/audit__product_system_to_offer_calculation_simplification.md`  
`docs/worklog/realignment/plan__workos_product_system_simplification_pass.md`  
`docs/worklog/realignment/build__product_system_total_ui_ux_refresh_v1.md`  
`docs/worklog/realignment/audit_assets/24_*` (+ 20–23 family)

**Code:**  
`frontend/src/App.tsx`  
`frontend/src/features/product-system/productSystemShellConfig.ts`  
`frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`  
`frontend/src/features/product-system/ProductSystemSpineBand.tsx`  
`frontend/src/features/product-system/ProductSystemOfferCostChannels.tsx`  
`frontend/src/features/product-system/ProductSystemLayout.tsx`  
(+ inventory explore: CatalogShell orphan, ModuleChain, intake links)

---

## 19. Prompt recomandat pentru buildul urmator (fara implementare aici)

```text
GO pentru PRODUCT_SYSTEM_BLACK_WORKSPACE_REBUILD_V1.

Root: C:\w\psiso
Branch: feature/product-system-active-path-isolation-v1

Prerequisite validat:
docs/worklog/realignment/audit__product_system_e2e_reality_before_rebuild_v1.md
FigJam: https://www.figma.com/board/PSqEHZNtrq5J0rjX7NQT5l
PNG: docs/worklog/realignment/audit_assets/25_product_system_e2e_figma_diagram.png

DECIZIE:
Nu polish pe UI-ul actual.
Nu UI nou peste ramasite.
Rebuild complet al workspace-ului Product System (IA black), pe rutele:
  /product-system/products
  /product-system/products/:templateCode

Centru obligatoriu:
- Product Template
- Module produs
- Product Compiler compact
- Readiness clar

Downstream only (link/mention, nu calculatoare):
- Cost intern
- Oferta client
- Execution

Elimina din chrome principal:
- shell planned tabs (components/resources/operations/dependencies/validation/advanced)
- Laboratory Closure money pe overview
- spine care trateaza Oferta ca pas Product System
- Pricing chip ca element dominant in PS header
- taburi tehnice ca flow principal

Strict interzis:
- DB rename, API contracts, migrations
- pricing/formula changes
- ProductDefinition / ProductAggregate behavior changes
- Execution materialization
- seed/reset, SVG/DWG parse
- remodelarea paginilor Intake/Quotes/Pricing/Execution

Acceptance: owner visual PASS pe black workspace + teste Vitest din audit §14.
Documenteaza in docs/worklog/realignment/build__product_system_black_workspace_rebuild_v1.md
```

---

## 20. Confirmari finale

- **Nu s-a implementat UI** in acest task.  
- **Nu s-a facut commit.**  
- Livrabile: audit scris + FigJam + PNG `25_product_system_e2e_figma_diagram.png` + prompt rebuild.  
- Verdict: **GO_WITH_CONSTRAINTS** pentru rebuild black dupa validare owner pe acest audit/FigJam.
