# Product System scalable navigation information architecture audit - 2026-07-03

## 1. Context owner

Owner context: Product System must become a scalable product/component/composition workspace, not a long catalog page.

Current Product System improvements already exist:

- backend returns `product_system_role`, `display_group`, and `composition_modules`;
- UI separates offerable products, candidate products, internal modules, shared components, and archived/experimental records;
- product cards can expand to show composition modules;
- top chips are real buttons that scroll/focus sections.

This audit is proposal-only. No code, UI, backend, DB, seed, migration, Work Intake, Intake V6, SVG Analyzer, Product Truth, Pricing, Quote/Order, ExecutionPlan, Inventory, ProductAggregate/TaskGraph, or Employee Mobile changes were made.

## 2. Problema UI actuala

Runtime verified at `http://127.0.0.1:3000/product-system`:

- `Produse ofertabile (1)`
- `Produse in pregatire (1)`
- `Module interne (12)`
- `Componente comune (0)`
- `Arhivate / experimentale (0)`
- `Toate (14)`

The current UI is a logical catalog, but still a scroll page. With 12 modules it is usable because the list is short. With 300 modules it becomes operationally weak:

- chips only relocate the user inside the same long document;
- product, component, and relation concepts compete in the same reading flow;
- internal modules consume most vertical space;
- expanded product compositions help local understanding, but do not replace a component workspace;
- there is no dedicated product list, component list, composition map, product detail, or component detail view.

Current answers to the audit questions:

- 12 modules: readable, but already visibly list-heavy.
- 300 modules: not acceptable as cards on one page.
- Clicks to understand a product: currently 1 click to expand composition, plus scanning the same page; acceptable for 2 products, weak for 50.
- Search component quickly: partially, global search can find code/family/description/role text, but results are still mixed with products.
- See all components of a product: yes through product expand, but only inside product card.
- See where a component is used: partially via `Folosit de`, but not as a component detail view.
- Filter by role: only section grouping, not interactive filters.
- Filter by parent product: no dedicated filter.
- Filter by status: only section grouping, not independent filters.
- UI type: catalog/list page, not a scalable dashboard/workspace.

## 3. De ce scroll-page nu scaleaza

A scroll-page is fine for orientation and smoke validation. It fails as the main model for 50 products and 300 components because it makes navigation proportional to catalog size.

For 300 components, the operator needs task-specific surfaces:

- find product;
- inspect product composition;
- find component;
- inspect component usage;
- compare product-component relationships;
- separate offerability from internal construction logic.

Those tasks should not require scrolling through unrelated sections.

## 4. Propunere Information Architecture

Recommended target IA:

```txt
/product-system                      Overview / Dashboard
/product-system/products             Product list
/product-system/products/:code       Product detail
/product-system/components           Component/module list
/product-system/components/:code     Component detail
/product-system/composition          Product -> component relationship map
/product-system/archived             Archived / experimental
```

First implementation does not need real routes. Start with internal view state:

```txt
view = overview | products | components | composition | archived
selectedProduct = templateCode | null
selectedComponent = componentCode | null
```

This gives immediate UX separation without route churn. Later, the same view model can map to real routes.

## 5. Overview view

Overview must orient, not list everything.

Recommended content:

```txt
Product System Catalog

Produse                 2
Componente / Module    12
Compozitii             2
Arhivate               0

Produse importante:
- TPL-VOLUMETRIC-LETTERS_v2
- TPL-VOLUMETRIC-LOGO_v1

Actiuni:
- Vezi produse
- Vezi componente
- Vezi harta compozitii
```

For 50 products / 300 components, Overview should show counts, recent/important items, warnings, and entry points only.

Do not render all modules on Overview.

## 6. Products view

Products view contains only:

- `offerable_product`
- `candidate_product`

It must not show internal modules.

Recommended controls:

- search by template code, family, description, role label;
- filters: all products, offerable, in preparation, needs owner GO;
- compact product cards or dense rows;
- sort by role/rank, updated date, validation status.

Compact product row/card fields:

- template code;
- status label;
- appears in Work Intake: yes/no;
- module count;
- validation summary;
- owner decision required;
- action: open product.

For 50 products, card height should stay compact and composition should not be expanded inline by default. Product detail is the correct place for full composition.

## 7. Product detail view

Product detail is the central understanding surface for a product.

Example:

```txt
TPL-VOLUMETRIC-LETTERS_v2
Produs activ pentru ofertare
Apare in Work Intake: DA

Tabs:
1. Compozitie
2. Operatii
3. Materiale
4. Formular / Intake
5. Dossier
6. Validare

Compozitie:
- Fata litera
- Spate litera
- Cant / laterale
- LED / iluminare
- Finisaje
- Structura montaj
```

Composition can be open by default here. This is where module role, required/optional status, hints, and child template codes should be easy to inspect.

Product detail should also expose clear Work Intake status:

- offerable product: appears in Work Intake;
- candidate product: does not appear until owner GO;
- internal module: never directly offerable.

## 8. Components view

Components view must be separate from products.

For 300 components, use a compact table or virtualized list, not cards.

Recommended controls:

- search by role label, role key, template code, family, parent product;
- filters: role, parent product, status, shared vs single-parent, material/process if available later;
- columns: Role, Template code, Folosit de, Status, Shared, Action.

Example row:

```txt
Rol              Template code                  Folosit de                      Status              Shared
Fata litera      TPL-VOLUMETRIC-FACE_v1         TPL-VOLUMETRIC-LETTERS_v2       Modul intern activ  Nu
```

This view answers component discovery. It should not mix in product parent cards.

## 9. Component detail view

Component detail should answer:

- What is this component?
- In which products is it used?
- What role does it play in each product?
- What operations/materials does it use?
- Is it shared?
- Is it active?
- Is it directly offerable? No, unless explicitly modeled as a product.

Example:

```txt
TPL-VOLUMETRIC-FACE_v1
Componenta: Fata litera

Folosit de:
- TPL-VOLUMETRIC-LETTERS_v2

Rol:
- Fata litera

Operatii:
- debitare fata
- aplicare folie
```

The current availability API gives parent codes and product role, but component detail will need richer operations/material summaries or a join with template detail data.

## 10. Composition map view

Composition view should show product-to-component relationships. Do not start with a complex graph.

Recommended first version: dense matrix/table or tree view.

Table:

```txt
Produs                         Module
TPL-VOLUMETRIC-LETTERS_v2      Fata, Spate, Cant, LED, Finisaje, Montaj
TPL-VOLUMETRIC-LOGO_v1         Fata logo, Return, Spate, Iluminare, Finisaje, Montaj
```

Tree:

```txt
TPL-VOLUMETRIC-LETTERS_v2
  - Fata litera
  - Spate litera
  - Cant / laterale
  - LED / iluminare
  - Finisaje
  - Structura montaj
```

Start with table/tree. Add graph visualization only if operators need topology analysis beyond parent-child inspection.

## 11. Chips/tabs/navigation recommendation

Recommendation for first micro-slice: Variant B - internal Product System sidebar or segmented mini-nav.

Use internal navigation:

- Overview
- Produse
- Componente
- Compozitii
- Arhivate
- Dossier tools later, if needed

Why not scroll chips: they preserve the long-page model.

Why not only tabs: tabs can work for the first slice, but a sidebar/mini-nav scales better once product/component detail panels and dossier tools exist.

Pragmatic first implementation: mini-nav backed by internal view state. It can visually behave like tabs on desktop if simpler, but conceptually it must switch isolated views, not scroll sections.

## 12. Backend/API readiness

Current availability fields reviewed:

- `product_system_role`
- `display_group`
- `composition_modules`
- `parent_codes`
- `module_codes`
- `parent_product_codes`
- `child_module_codes`
- `shared_with_product_codes`
- `owner_decision_required`
- `quote_offerable`
- `runtime_module`
- `status` / `status_reason`

Answers:

1. Sufficient for Slice 1: yes. Overview, Products, Components, Composition, and Archived views can be derived from current availability response.
2. Missing for Component detail: detailed operations/materials summaries per component, component-level validation detail, richer role metadata source, and maybe usage rows with parent-specific relation metadata.
3. Missing for shared components: canonical shared component identity if similar components are modeled as separate templates; current shared detection only works when the same module template is linked to multiple parents.
4. New endpoint needed now: no, not for Slice 1.
5. Availability API enough for first slice: yes, with existing product template data already loaded in the page for counts/summaries.

Longer term, add dedicated read-only endpoints only when details become heavy:

- `GET /api/v1/product-system/products/:templateCode`
- `GET /api/v1/product-system/components/:componentCode`
- `GET /api/v1/product-system/composition-map`

## 13. Micro-slice implementation plan

### Slice 1 - Internal view state, no routes

- Replace scroll chips with Product System mini-nav.
- Add views: Overview, Products, Components, Composition, Archived.
- Keep using availability API.
- Products view shows only offerable/candidate products.
- Components view shows modules/components in a compact table.
- Composition view shows table/tree product -> modules.
- Work Intake remains unchanged and still uses `quote_offerable=true`.

### Slice 2 - Product detail panel/page

- Click product opens `selectedProduct` detail.
- Composition tab is visible by default.
- Show Work Intake eligibility, owner GO requirement, validation, operations/materials tabs.

### Slice 3 - Component detail panel/page

- Click component opens `selectedComponent` detail.
- Show used-by products, role per product, status, shared/single-parent, active/direct-offerable flags.

### Slice 4 - Real routes

- Map internal views to routes:
  - `/product-system/products`
  - `/product-system/products/:templateCode`
  - `/product-system/components`
  - `/product-system/components/:componentCode`
  - `/product-system/composition`
  - `/product-system/archived`

### Slice 5 - Virtualized components list

- Add virtualization only when component count or render cost requires it.
- For 300+ components, this likely becomes necessary.

What to do now: Slice 1.

What to leave for later: real routes, virtualization, graph visualization, heavy component detail endpoints, owner GO workflow.

## 14. Ce NU ai modificat

Not modified:

- code
- UI implementation
- backend implementation
- DB
- seed data
- migrations
- Work Intake
- Intake V6
- SVG Analyzer
- Product Truth
- Pricing / CostEngine
- Quote / Order
- ExecutionPlan
- Inventory
- ProductAggregate / TaskGraph
- Employee Mobile
- git commit / push

## 15. Next safe prompt

Recommended next prompt:

```txt
Implement Product System scalable navigation Slice 1 only.

Scope:
- frontend only;
- no backend changes;
- no DB/seed/migration;
- no Work Intake changes;
- no Intake V6/SVG Analyzer/Product Truth/Pricing/Quote/Order/ExecutionPlan/Inventory/ProductAggregate/TaskGraph/Employee Mobile;
- no commit/push.

Implement internal view state in Product System:
- Overview
- Products
- Components
- Composition
- Archived

Replace scroll chips with view navigation.
Overview shows counts/actions only, not full module list.
Products view shows only offerable/candidate products.
Components view shows compact table/list for modules/components.
Composition view shows product -> composition_modules table/tree.
Archived view shows archived/experimental records.

Use existing availability API and existing ProductTemplateEntity summaries.
Add focused frontend tests and runtime verification.
```

## Roadmap awareness checkpoint

Confirmed:

- Product System must scale to dozens of products and hundreds of components.
- Catalog must not remain a long scroll page.
- Products and components need separate views.
- Work Intake remains only `quote_offerable=true`.
- Logo remains a candidate product until owner GO.
- No quote/order/execution is created.
- Pricing is not modified.
- ProductAggregate / Task Graph / ExecutionPlan remain out of scope.
- Employee Mobile remains final-final.

Decision: do not keep repairing scroll. Change the navigation model first, then grow detail views behind it.

## Slice 1 Implementation - View-state scalable catalog

### 1. Context owner

Owner context: Product System navigation must scale to dozens of products and hundreds of components without becoming a long scroll catalog.

This slice implements the first navigation step only: frontend view-state views inside the existing `/product-system` page. No new routes were added.

### 2. Problema veche: scroll-page

The previous catalog model rendered all Product System groups one under another:

- active products;
- candidate products;
- internal modules;
- shared components;
- archived/experimental.

The top controls were real buttons, but they still only moved focus/scroll inside the same long page. That was acceptable for the current 14 records but not for 50 products and 300 components.

### 3. Ce s-a implementat

Implemented internal view-state navigation in `TemplateLibraryView`:

```txt
overview | products | components | composition | archived
```

Implemented views:

- `Overview`: default view; shows counts/cards/actions and important products, not the full module list.
- `Products`: shows only `offerable_product` and `candidate_product`; keeps product composition expand in card.
- `Components`: shows only `internal_module` and `shared_component`; uses compact table/list, search, status filters, and parent product filter.
- `Composition`: shows product -> role -> module rows from `composition_modules`.
- `Archived`: shows only `archived_experimental`; empty state when count is zero.

The view switcher now changes visible content. It is no longer scroll-only navigation.

### 4. Ce NU s-a implementat

Not implemented in this slice:

- real routes;
- full product detail page/panel;
- full component detail page/panel;
- virtualized list;
- graph visualization;
- owner GO workflow;
- Dossier/editor changes.

### 5. Date folosite din API

The UI uses existing availability/template data only:

- `product_system_role`
- `display_group`
- `quote_offerable`
- `runtime_module`
- `owner_decision_required`
- `ui_label`
- `ui_description`
- `readiness_reason`
- `parent_codes`
- `parent_product_codes`
- `shared_with_product_codes`
- `composition_modules`

The UI does not invent products, commercial statuses, formulas, totals, quote/order/execution flows, or composition relationships.

### 6. Teste rulate

Frontend Product System:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=dot
```

Result: `7 passed`.

Work Intake regression:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx --reporter=dot
```

Result: `7 passed`, with existing React `act(...)` warnings.

Frontend typecheck:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Result: passed with no output.

Backend sanity:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py -q
```

Result: `9 passed, 20 warnings`.

### 7. Runtime verification

Runtime URL verified:

`http://127.0.0.1:3000/product-system`

Verified behavior:

- page loads `Overview` by default;
- Overview shows counts/actions and important products;
- Overview does not render the long module/component list;
- `Produse` switches content to product rows only: `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1`;
- `Componente` switches content to compact module table with 12 modules;
- `Compozitii` switches content to product -> role -> module rows for letters and logo;
- `Arhivate` switches content to empty archived/experimental state;
- `TPL-VOLUMETRIC-LETTERS_v2` remains a product;
- `TPL-VOLUMETRIC-LOGO_v1` remains a candidate product;
- `TPL-VOLUM-ALUMINIU_v1` appears as a component/module, not a product row;
- old scroll-page section navigation is no longer the primary model.

Work Intake runtime sanity:

`http://127.0.0.1:3000/intake`

Verified:

- Work Intake page loads;
- `Cerere Noua` dialog opens;
- live `offerable_only=true` API returns only `TPL-VOLUMETRIC-LETTERS_v2`, not logo and not modules.

### 8. Ce NU ai modificat

Not modified:

- backend code;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Product Truth;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / TaskGraph;
- Employee Mobile;
- template active flags;
- template links.

No commit and no push were made.

### 9. Riscuri ramase

Remaining risks:

- Components view is compact but not virtualized yet; this is acceptable for Slice 1 but should be revisited around 300+ components.
- Product and component detail are still lightweight; deeper operator workflows need separate detail views in later slices.
- Shared components are still limited by backend data truth: current detection only confirms shared when the same module template is linked to multiple products.

### 10. Next safe step

Next safe step: implement Slice 2 product detail as internal selected-product panel/page, still frontend-only if possible, using existing availability and template data. Keep Work Intake and backend untouched unless a read-only detail contract is explicitly required.

## Slice 2 Implementation - Compact default UI density

### 1. Context owner

Owner context: after Slice 1, Product System had the correct scalable view model, but the default UI still felt too verbose for operational catalog use.

Runtime baseline showed:

- large Product System header and tab cards;
- Overview cards consuming too much vertical space;
- Products view using full-width cards;
- product cards repeating long Work Intake/owner/date copy by default;
- detailed composition text visible before the operator asks for it.

### 2. Problema rezolvata

The default catalog needed to become compact and scan-first:

- reduced header height;
- slim segmented navigation with counts;
- compact default density;
- optional detailed mode;
- multi-card Products grid on desktop;
- compact Components table;
- compact Composition summaries.

### 3. Ce s-a implementat

Implemented frontend-only density polish in `TemplateLibraryView`:

- added density state: `compact | detailed`;
- default density is `compact`;
- added `Compact` / `Detaliat` toggle;
- replaced large nav cards with slim segmented buttons and counts: `Produse 2`, `Componente 12`, `Compozitii 2`, `Arhivate 0`;
- reduced catalog header and view-section padding;
- made Overview cards compact by default;
- Products view now renders a responsive grid: 1 column mobile, 2 large, 3 XL, 4 2XL;
- product cards show compact chips for modules, validation, Work Intake yes/no, and GO owner;
- long Work Intake and owner copy, dates, and verbose metrics are hidden in compact mode;
- Detailed mode restores the richer product copy and dates;
- Components table has denser row/header spacing;
- Composition view is compact by default with role-label summaries, while Detailed mode shows module template codes/status rows.

### 4. Ce NU s-a modificat

Not modified:

- backend code;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Product Truth;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / TaskGraph;
- Employee Mobile;
- template active flags;
- template links;
- routes.

No commit and no push were made.

### 5. Teste rulate

Frontend Product System:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=dot
```

Result: `8 passed`.

Work Intake regression:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx --reporter=dot
```

Result: `7 passed`, with existing React `act(...)` warnings.

Frontend typecheck:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Result: passed with no output.

Backend availability sanity:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py -q
```

Result: `9 passed, 20 warnings`.

### 6. Runtime verification

Runtime URL verified:

`http://127.0.0.1:3000/product-system`

Verified behavior:

- Product System loads with `data-density="compact"`;
- navigation labels are slim and count-aware: `Overview`, `Produse 2`, `Componente 12`, `Compozitii 2`, `Arhivate 0`;
- compact mode does not render the long owner copy by default;
- Products view uses grid classes `grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4`;
- product cards show compact Work Intake chips;
- Detailed mode shows owner copy and update/create dates;
- Composition Detailed mode shows module template codes;
- Composition Compact mode shows role summaries.

Work Intake runtime sanity:

`http://127.0.0.1:3000/intake`

Verified:

- Work Intake page loads;
- `Cerere Noua` modal opens;
- live `offerable_only=true` API returns total `1` and code `TPL-VOLUMETRIC-LETTERS_v2` only.

### 7. Riscuri ramase

Remaining risks:

- Products grid is not virtualized; acceptable for current product counts and likely fine for 50 products, but component virtualization remains a later concern.
- Compact Composition hides module template codes until Detailed mode; this is intentional for density but should be revisited if operators need codes constantly visible.
- Detailed mode preserves old verbose copy; later product-detail work should move deep inspection out of the card.

### 8. Next safe step

Next safe step: implement a selected product detail panel/page inside the existing Product System route, using the compact catalog as the launcher and keeping backend/Work Intake unchanged unless a read-only detail contract is explicitly required.

## Slice 3 Implementation - Compact cards metadata popover and template icons

### 1. Context owner

Owner context: after Slice 2, Product System had compact density and a products grid, but compact cards still showed too many direct metadata chips. The owner request for this slice was frontend-only cleanup: reduce badge clutter, move secondary metadata into an info/hover popover, and use the SVG from the desktop icons folder for `TPL-VOLUMETRIC-LETTERS_v2`.

Runtime/source observations:

- the desktop icon source exists at `C:\Users\offic\Desktop\icons\tpl-letters.svg`;
- no existing SVGR pattern is configured in the frontend;
- Vite asset URL imports are available;
- `TemplateLibraryRow` controlled both compact badge clutter and the generic template icon.

### 2. Problema rezolvata

Compact product cards were visually noisy because they rendered secondary metadata directly:

- module count;
- validation count;
- Work Intake yes/no;
- GO owner;
- recommended/status badges.

They also reused the same generic package icon for every product, which does not scale once templates need product-specific visual identity.

### 3. Ce s-a implementat

Implemented frontend-only UI metadata and compact-card cleanup:

- copied the owner SVG into `frontend/src/assets/product-system/icons/tpl-letters.svg`;
- normalized the copied SVG fill to `currentColor`;
- added `productTemplateIconRegistry.tsx` as UI metadata only, not business truth;
- configured `TPL-VOLUMETRIC-LETTERS_v2` with the specific SVG icon and controlled color `#8B5CF6`;
- added fallback product/component icon configs using existing lucide icons;
- replaced the hardcoded generic card icon with a registry-driven renderer;
- rendered SVG URLs through CSS mask so the configured color controls the icon;
- removed direct compact chip clutter from product cards;
- added a compact metadata trigger and hover/focus/click popover;
- moved status, recommended, modules, validation, Work Intake, and GO owner metadata into the popover in compact mode;
- kept detailed mode as the richer direct-information view.

### 4. Ce NU s-a modificat

Not modified:

- backend code;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Product Truth;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / TaskGraph;
- Employee Mobile;
- template active flags;
- template links;
- routes.

No commit and no push were made.

### 5. Teste rulate

Frontend Product System:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=dot
```

Result: `10 passed`.

Work Intake regression:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx --reporter=dot
```

Result: `7 passed`, with existing React `act(...)` warnings.

Frontend typecheck:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Result: passed with no output.

Backend availability sanity:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py -q
```

Result: `9 passed, 20 warnings`.

### 6. Runtime verification

Runtime URL verified:

`http://127.0.0.1:3000/product-system`

Verified behavior:

- Product System loads and Products view keeps compact cards in a grid;
- compact cards no longer show direct secondary chip clutter for Work Intake, GO owner, or validation;
- compact cards keep essential product identity and status text;
- `TPL-VOLUMETRIC-LETTERS_v2` uses the specific SVG icon config with source `specific` and color `#8B5CF6`;
- `TPL-VOLUMETRIC-LOGO_v1` uses fallback product icon config with source `fallback`;
- the Letters metadata popover shows Status, Recomandat, Module, Validare, Work Intake, and GO owner;
- Detailed mode shows secondary info directly again;
- Components view remains separate and visible.

Work Intake runtime sanity:

`http://127.0.0.1:3000/intake`

Verified:

- Work Intake page loads;
- `Cerere Noua` modal opens;
- live `offerable_only=true` API returns code `TPL-VOLUMETRIC-LETTERS_v2` only.

### 7. Riscuri ramase

Remaining risks:

- Icon registry is intentionally frontend UI metadata; it must not be treated as template/product business truth.
- More template-specific icons can be added safely through the registry, but they should stay documented as presentation metadata.
- Compact popover is a card-level metadata reveal, not a substitute for the later product detail panel/page.

### 8. Next safe step

Next safe step: implement selected product detail inside the existing Product System route, launched from the compact card, with composition/validation details moved out of the card and no backend/Work Intake changes unless a read-only detail contract is explicitly requested.

## Slice 4 Implementation - Compact product card final polish

### 1. Context owner

Owner context: the compact Product System product card was close, but final visual polish was still needed before growing product-detail surfaces.

Visual observations from owner review:

- template icon was too small to act as product identity;
- info/edit actions were placed in the upper-right corner, making the compact card feel top-heavy;
- the composition collapse trigger still displayed `Module (6)` in compact mode;
- compact mode still needed a stricter separation between daily scanning and inspection metadata.

### 2. Ce s-a implementat

Implemented frontend-only compact card polish in `TemplateLibraryView`:

- enlarged the product template icon in compact mode to `h-16 w-16` and `xl:h-20 xl:w-20`;
- enlarged the internal SVG/masked icon to visually fill the icon container;
- kept color/source controlled by the existing frontend icon registry;
- moved compact info/edit actions into a bottom-right action row;
- added a testable bottom action container per template;
- changed the product composition trigger to icon-only in compact mode;
- removed direct `Module (6)` / `Module produs (6)` text from compact mode;
- added aria labels with module count: `Afiseaza modulele produsului, 6 module`;
- kept `aria-expanded` true/false behavior;
- kept detailed mode allowed to show `Module produs (6)` / `Module produs candidat (6)`;
- kept secondary metadata inside the compact info popover;
- kept detailed mode as the direct metadata/audit view.

### 3. Ce NU s-a modificat

Not modified:

- backend code;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Product Truth;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / TaskGraph;
- Employee Mobile;
- template active flags;
- template links;
- routes.

No commit and no push were made.

### 4. Teste rulate

Frontend Product System:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=dot
```

Result: `10 passed`.

Work Intake regression:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx --reporter=dot
```

Result: `7 passed`, with existing React `act(...)` warnings.

Frontend typecheck:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Result: passed with no output.

Backend availability sanity:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py -q
```

Result: `9 passed, 20 warnings`.

### 5. Runtime verification

Runtime URL verified:

`http://127.0.0.1:3000/product-system`

Verified behavior:

- Product System loads and Products view keeps compact grid layout;
- compact product icon for `TPL-VOLUMETRIC-LETTERS_v2` is marked `data-icon-size="large"` and uses classes `h-16 w-16 xl:h-20 xl:w-20`;
- icon source remains `specific` and color remains `#8B5CF6`;
- compact cards do not show direct `Module (6)` / `Module produs (6)` text;
- compact cards do not show direct Work Intake / GO owner / validation chip clutter;
- info/edit actions are in the bottom action row;
- collapse trigger has empty visible text, aria-label with `6 module`, and `aria-expanded=false` before opening;
- clicking collapse changes `aria-expanded=true` and shows module rows;
- Letters popover shows Status, Recomandat, Module, Validare, Work Intake, and GO owner with `6/6` and Work Intake `Da`;
- Logo popover shows candidate metadata with `2/6`, Work Intake `Nu`, and GO owner `Da`;
- Detailed mode shows full secondary information directly, including `Module produs (6)`, `Work Intake: DA`, and `GO owner`;
- Components view remains compact and does not render large product card icons for modules.

Work Intake runtime sanity:

`http://127.0.0.1:3000/intake`

Verified:

- Work Intake page loads;
- `Cerere Noua` modal opens;
- live `offerable_only=true` API returns code `TPL-VOLUMETRIC-LETTERS_v2` only.

### 6. Riscuri ramase

Remaining risks:

- The compact product card now gives icons stronger visual weight; future template-specific icons should be added through the registry to keep the system coherent.
- Popover metadata remains a compact-card aid; deeper composition/validation inspection still belongs in a selected product detail view.
- Component virtualization remains a later concern for the 300-component target.

### 7. Next safe step

Next safe step: implement selected product detail inside the existing Product System route, launched from the compact card, so composition and validation inspection moves out of compact cards while keeping Work Intake and backend unchanged.