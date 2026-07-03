# Product System UI and Navigation Dual Audit

## 1. Context owner

Product System has recently moved through role classification, composition modules, scalable internal catalog views, compact cards, metadata popovers, and frontend-only template icons.

The current owner concern is split into two separate audits:

- Audit A: UI/UX density, card layout, compact/detailed behavior, scanability, and readiness for 50 products / 300 components.
- Audit B: navigation/state/back behavior after entering Products, opening a template editor, and returning.

This document is audit-only. No implementation was made.

## 2. Scope

In scope:

- runtime inspection of `http://127.0.0.1:3000/product-system`;
- runtime inspection of Product System internal views: Overview, Produse, Componente, Compozitii, Arhivate;
- runtime navigation/back scenarios for product template editor entry/return;
- code reading for Product System view state, editor state, and route definitions;
- recommendations for future micro-slices.

Out of scope and not modified:

- backend;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / Task Graph;
- Employee Mobile;
- git commit / push.

## 3. Audit A — UI/UX

### 3.1 Runtime observations

Runtime URL: `http://127.0.0.1:3000/product-system`.

Observed catalog views:

- Overview;
- Produse;
- Componente;
- Compozitii;
- Arhivate.

Current live data shape observed:

- Products view shows `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1` as primary product/candidate rows.
- Components view shows 12 component/module rows.
- Composition view shows 2 product compositions.
- Archived view is empty and has a clear empty state.

General UI observations:

- Header is acceptable after the recent density work; it is no longer the dominant problem.
- View switcher is clear and count-aware.
- Compact mode is default.
- Search appears in non-overview views.
- Products view filters are clear: all, offerable, candidate, owner GO.
- Components view filters are useful: all, internal, shared, parent product.
- Metadata clutter is mostly controlled: compact product cards hide secondary metadata in popover.
- Detailed mode restores audit/inspection information.
- There is still one interaction smell: product cards use `role="button"` at the card container level and also contain nested action buttons. This is usable in runtime, but semantically brittle for keyboard/screen-reader behavior.

### 3.2 Products view

What is good:

- Products view only shows offerable/candidate products as primary cards.
- Internal modules do not appear as product cards.
- Cards are compact and grid-based, suitable for more than the current two products.
- The specific `TPL-VOLUMETRIC-LETTERS_v2` icon is large enough to read as product identity.
- Fallback icon for `TPL-VOLUMETRIC-LOGO_v1` is coherent and not misleading.
- Secondary metadata is hidden in the info popover in compact mode.
- Detailed mode makes the full inspection data visible again.
- `TPL-VOLUMETRIC-LOGO_v1` is visually marked as `In pregatire`, so it does not look offerable.

Weak points:

- Icon-only collapse is accessible by aria-label, but discoverability depends on icon recognition. A tooltip or title would help later if operators miss it.
- Card-level `role="button"` plus inner buttons can create awkward focus semantics.
- Product card height is acceptable now, but the large icon increases row height; with 50 products this is still likely usable in a 3-4 column grid, but should be watched.
- Expanded composition inside a card is useful for the current two products, but for 50 products it should not become the main inspection surface.

Blocking before commit:

- No UI-density blocker found for the current slice.
- The nested interactive card semantics are a quality concern, not an immediate blocker, unless keyboard/screen-reader quality is part of the commit bar.

### 3.3 Components view

What is good:

- Components are table/list rows, not product cards.
- Rows are compact and scan-friendly at the current 12-row scale.
- `Folosit de` is visible.
- Internal/shared status is visible.
- Search exists.
- Component type filters and parent product filter exist.

Weak points for 300 components:

- No virtualization or pagination.
- Row height is compact, but 300 rows will still become long-scroll work.
- Filtering is useful but still basic; role/grouping and parent product filtering help, but there is no saved view or grouping-by-product mode.
- The table is dense, but not yet an industrial-scale component browser.

What would break first at 300 components:

1. Long-scroll scanning and browser render cost.
2. Lack of virtualization/pagination.
3. Limited grouping/sorting for operators looking by role/product family.
4. Parent filter discoverability when parent count grows.

### 3.4 Composition view

What is good:

- Product -> role -> component relation is understandable in compact summary form.
- Letters and Logo are clearly separated.
- Compact mode is concise.
- Detailed mode can show component template codes/status rows.

Weak points:

- Composition view has no drill-down controls today.
- For 50 products, a flat list will become too long.
- There is no collapse all / expand one model at the view level.
- There is no filter by component usage.
- Compact mode is readable for 2 products, but too summary-only for deep debugging.

Recommended future direction:

- Keep compact summary as default.
- Add search by product and component.
- Add collapse-all / expand-one product behavior.
- Consider both tree and table modes later: tree for operator comprehension, table for auditing relationships.

### 3.5 Compact vs Detailed

Observed:

- Default is compact.
- Detailed restores full inspection metadata.
- Detailed is useful for audit/inspection.
- Detailed expands layout but does not destroy it at the current scale.
- Switching compact/detailed preserves the current catalog view while the library remains mounted.
- Expanded product module state is local to each row and can be lost when the library is unmounted.

Important caveat:

- Compact/detailed state is local to `TemplateLibraryView`. It survives while staying in the library, but not when opening editor and returning.

### 3.6 UI/UX verdict

Verdict UI/UX: HEALTHY_WITH_MINOR_VISUAL_HIERARCHY_RISK.

The requested enum closest match is: HEALTHY.

Rationale:

- The current UI is much healthier than the earlier scroll catalog.
- Product vs component separation is real.
- Compact cards are scan-friendly enough for the next slice.
- Components view is acceptable now but will need virtualization/pagination/grouping before 300 components.
- The main remaining UX risk is not density; it is state/navigation continuity and nested interactive semantics.

### 3.7 UI recommendations

Recommended next UI micro-slice, only after navigation fix:

1. Replace product card `role="button"` container with a non-button card plus explicit open/edit button semantics, or make the whole card a link/button and move nested actions out of the interactive parent.
2. Add tooltip/title for icon-only composition collapse if operators find it ambiguous.
3. Defer component virtualization until component count or render cost makes it necessary.
4. Move deep composition inspection into selected product detail rather than expanding too much inside cards.

## 4. Audit B — Navigation / State / Back behavior

### 4.1 Runtime flows tested

Scenario 1: Products -> Letters template -> internal back

Steps:

1. Opened `/product-system`.
2. Clicked `Produse`.
3. Switched to `Detaliat`.
4. Expanded `TPL-VOLUMETRIC-LETTERS_v2` composition.
5. Clicked `TPL-VOLUMETRIC-LETTERS_v2` card.
6. Editor opened on same URL: `/product-system`.
7. Clicked internal `Înapoi la șabloane`.

Result:

- Returned to Product System library.
- Returned to `Overview`, not `Produse`.
- Density reset to `compact`, not the previous `detailed`.
- Expanded module state was lost.

Scenario 2: Products -> Logo template -> browser Back

Steps:

1. From library, clicked `Produse`.
2. Clicked `TPL-VOLUMETRIC-LOGO_v1`.
3. Editor opened on same URL: `/product-system`.
4. Used browser Back.

Result:

- Browser Back did not return to Products view.
- Because opening editor does not push a URL/history entry, browser Back left Product System and returned to previous browser history entry (`/intake` in this session).
- This behavior is not predictable from the operator's mental model.

Scenario 3: Components -> component -> back

Result:

- Components rows are not clickable drill-down targets today.
- Component row has no role, no tab index, and normal cursor.
- Scenario not applicable yet.

Scenario 4: Composition -> product/module -> back

Result:

- Composition view has no drill-down buttons today.
- Scenario not applicable yet.

Scenario 5: browser Back vs internal Back

Result:

- Internal Back returns to Product System library, but loses view context and returns to Overview.
- Browser Back is not synchronized with Product System editor state and may leave Product System entirely.
- Browser Back does not change internal catalog view because catalog view is not represented in URL/history.

### 4.2 Back behavior results

Confirmed problem: yes.

Observed wrong behavior:

```txt
Produse -> Template editor -> Înapoi la șabloane -> Overview
```

Expected safer behavior:

```txt
Produse -> Template editor -> Înapoi la șabloane -> Produse
```

Additional browser history problem:

```txt
Produse -> Template editor -> Browser Back -> previous route outside Product System
```

That happens because the editor is internal state on the same route, not a route/history entry.

### 4.3 Code path inspected

Inspected files:

- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/App.tsx`
- `frontend/src/features/product-system/productSystemNavigation.ts`

Relevant code facts:

- `TemplateLibraryView` owns `catalogView` locally:
  - `const [catalogView, setCatalogView] = useState<ProductSystemCatalogView>("overview");`
- `TemplateLibraryView` owns `density` locally:
  - `const [density, setDensity] = useState<CatalogDensity>("compact");`
- `TemplateLibraryView` owns product/component filters locally.
- `TemplateLibraryRow` owns `compositionOpen` locally.
- `ProductSystem.tsx` owns only higher-level screen state:
  - `const [screen, setScreen] = useState<ProductSystemScreen>(getInitialProductSystemScreen);`
- `handleOpenEditor` sets draft/selected template and `setScreen("editor")`.
- `handleBackToLibrary` sets `setScreen("library")`, clears draft/selected/new/picker, but has no return view.
- `App.tsx` has route `/product-system` only for this page.
- Product System view tabs are not represented in query params.
- Product System editor is not represented in route params.

### 4.4 Root cause

Root cause confirmed:

```txt
catalogView is local to TemplateLibraryView.
When a template is opened, ProductSystem switches screen from library to editor.
TemplateLibraryView unmounts.
When internal Back returns to library, TemplateLibraryView remounts.
Its local default catalogView is overview and density is compact.
Therefore the user returns to Overview instead of the previous Products context.
```

Secondary cause:

```txt
Editor open/close is internal React state only.
The URL remains /product-system.
No history entry is pushed for Products view or template editor.
Browser Back cannot know the desired return context.
```

### 4.5 Navigation verdict

Verdict navigation: NEEDS_STATE_PERSISTENCE.

Secondary longer-term verdict: NEEDS_QUERY_PARAM_ROUTING before Product System becomes a large workspace.

It does not need real routes immediately, but real routes are the cleanest end-state once the product/component detail model stabilizes.

### 4.6 Navigation recommendations

Immediate fix recommendation:

Micro-slice 1: Lift state into `ProductSystem.tsx`.

Move or control these from `ProductSystem.tsx`:

- `catalogView`
- `density`
- optionally `productFilter`, `componentFilter`, `parentFilter`
- optionally selected/expanded product composition state if preserving expand is required

Then pass them into `TemplateLibraryView` as controlled props.

Also add a simple `returnToView` model for editor open:

```txt
handleOpenEditor(template, { returnToView: catalogView })
handleBackToLibrary() -> screen = library, preserve returnToView/current view
```

Why this is the safest first fix:

- no new routes;
- small scope;
- fixes internal `Înapoi la șabloane` immediately;
- preserves current UI architecture;
- avoids route churn before detail pages are designed.

Second recommendation:

Micro-slice 2: Add query params for catalog view.

Example:

```txt
/product-system?view=products
/product-system?view=components
/product-system?view=composition
```

This improves refresh/share/back behavior for catalog views without adding full route hierarchy.

Third recommendation:

Micro-slice 3: Add real routes after UI stabilizes.

Possible future route model:

```txt
/product-system
/product-system/products
/product-system/components
/product-system/composition
/product-system/archived
/product-system/templates/:templateCode
```

This is cleaner for browser history and direct linking, but larger scope.

## 5. Recommended next micro-slices

Recommended order:

1. Navigation Micro-slice 1: lift `catalogView` and `density` to `ProductSystem.tsx`; preserve internal Back context from editor to previous view.
2. Navigation Micro-slice 2: add `?view=` query param sync for catalog views.
3. UI Micro-slice: clean product card interaction semantics so the card container is not a `role="button"` containing nested buttons.
4. Product Detail Micro-slice: introduce selected product detail surface, launched from product cards, with composition/validation details moved out of compact cards.
5. Component Scale Micro-slice: add virtualization/pagination/grouping when component count approaches hundreds.

## 6. Forbidden scope respected

Confirmed:

- no backend code changed;
- no DB changed;
- no seeds run;
- no migrations run;
- no Work Intake code changed;
- no Intake V6 changed;
- no SVG Analyzer changed;
- no Pricing / CostEngine changed;
- no Quote / Order changed;
- no ExecutionPlan changed;
- no Inventory changed;
- no ProductAggregate / Task Graph changed;
- no Employee Mobile changed;
- no commit;
- no push.

Only this audit worklog was created.

## 7. Tests/runtime used

Runtime used:

- `http://127.0.0.1:3000/product-system`
- existing frontend/backend stack already running; no server restart was needed.

Runtime scenarios used:

- Overview default load;
- Products view compact/detailed;
- Products -> Letters editor -> internal Back;
- Products -> Logo editor -> browser Back;
- Components view row click inspection;
- Composition view drill-down inspection;
- Archived empty state inspection.

Code inspected:

- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/App.tsx`
- `frontend/src/features/product-system/productSystemNavigation.ts`

No automated test suite was run because this was audit-only and no implementation was made.

## 8. Final verdict

Audit A verdict: HEALTHY, with minor visual hierarchy and interaction semantics risks.

Audit B verdict: NEEDS_STATE_PERSISTENCE now; NEEDS_QUERY_PARAM_ROUTING soon.

Commit readiness:

- UI density/card/layout: PARTIAL to DA, depending on whether nested interactive card semantics are considered blocking.
- Navigation/back behavior: NU. Back behavior should be fixed before considering the Product System navigation work complete.

## 9. Roadmap awareness checkpoint

Confirmed:

- Product System must scale to 50 products and 300 components.
- Compact UI remains default.
- Products and components remain separate views.
- Navigation/back behavior must preserve user context.
- Work Intake remains only `quote_offerable=true`.
- Logo remains candidate product until owner GO.
- UI must not invent roles or relationships.
- No quote/order/execution is created by this work.
- Pricing is not modified.
- ProductAggregate / Task Graph / ExecutionPlan remain out of scope.
- Employee Mobile remains final-final.

## Navigation Fix Slice — Preserve catalog view and density across editor back

### 1. Context

The dual audit confirmed a navigation defect:

```txt
Produse -> Template editor -> Înapoi la șabloane -> Overview
```

Root cause was local state ownership in `TemplateLibraryView`: `catalogView` and `density` reset when the library unmounted during editor mode and remounted after internal Back.

### 2. Implemented

Implemented frontend-only state persistence:

- exported `ProductSystemCatalogView` and `CatalogDensity` from `TemplateLibraryView`;
- lifted `catalogView` into `ProductSystem.tsx`;
- lifted `catalogDensity` into `ProductSystem.tsx`;
- made `TemplateLibraryView` receive `catalogView`, `onCatalogViewChange`, `density`, and `onDensityChange` as controlled props;
- preserved internal Back context automatically because the parent `ProductSystem` stays mounted while switching between library/editor screens;
- added test harness coverage for library unmount/remount around a simulated editor screen;
- verified Letters and Logo both return to Products view after internal Back.

No explicit `returnToView` state was needed for this micro-slice because parent-owned `catalogView` already preserves the last view.

### 3. Not implemented

Intentionally not implemented in this slice:

- query params;
- real routes;
- browser history fix for editor open;
- shareable URLs;
- product detail pages;
- component detail pages;
- persistence of expanded composition state across editor Back.

Browser Back remains a known limitation for a future query-param/route slice.

### 4. Tests run

Frontend Product System:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=dot
```

Result: `12 passed`.

Frontend typecheck:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Result: passed with no output.

Work Intake regression:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"; npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx --reporter=dot
```

Result: `7 passed`, with existing React `act(...)` warnings.

Backend availability sanity:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"; .\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py -q
```

Result: `9 passed, 20 warnings`.

### 5. Runtime verification

Runtime URL verified:

`http://127.0.0.1:3000/product-system`

Scenario A — Products -> Letters -> internal Back:

- opened Product System;
- clicked `Produse`;
- switched to `Detaliat`;
- opened `TPL-VOLUMETRIC-LETTERS_v2` editor;
- clicked `Înapoi la șabloane`;
- returned to Products view;
- Overview was not visible;
- density remained `detailed`;
- Letters remained visible.

Scenario B — Products -> Logo -> internal Back:

- opened `TPL-VOLUMETRIC-LOGO_v1` editor from Products;
- clicked `Înapoi la șabloane`;
- returned to Products view;
- Overview was not visible;
- Logo remained visible.

Scenario C — Components view persistence:

- switched to Components;
- switched density to Detailed;
- navigated Products -> Components;
- Components view was visible and density remained `detailed`.

Scenario D — Browser Back:

- browser Back from editor still left Product System in the current session;
- this remains expected/out of scope until query params or real routes are introduced.

Work Intake runtime sanity:

`http://127.0.0.1:3000/intake`

- page loaded;
- `Cerere Noua` opened;
- no Work Intake functional change was made.

### 6. Forbidden scope respected

Not modified:

- backend;
- DB;
- seed data;
- migrations;
- Work Intake functional code;
- Intake V6;
- SVG Analyzer;
- Pricing / CostEngine;
- Quote / Order;
- ExecutionPlan;
- Inventory;
- ProductAggregate / Task Graph;
- Employee Mobile.

No commit and no push were made.

### 7. Remaining risks

Remaining risks:

- Search/filter state is still split: global library search is parent-owned, but product/component filters remain local to `TemplateLibraryView` and can reset across editor Back if their view gets an editor entry in the future.
- Expanded composition state remains local to `TemplateLibraryRow` and is not preserved across editor Back.
- Browser Back remains unsolved until query params or real routes are implemented.

### 8. Next safe step

Next safe step: add `?view=products|components|composition|archived` query-param sync so browser Back, refresh, and shareable links preserve catalog view without introducing full route hierarchy yet.
