# PRODUCT SYSTEM UI/UX AUDIT

## Context

- Screenshot reviewed from owner on `http://127.0.0.1:3001/product-system`
- Current UI already includes:
  - separate tabs for `Template-uri produs` and `Componente / module reutilizabile`
  - workflow editor moved into dedicated side panel
  - no inline child-module cards under product templates
  - compact workflow summary and actions in product cards
- No backend / DB / persistence changes were made for this audit.

## Verdict

Page is functional and directionally correct, but still needs a coherent UI hierarchy pass.

Main conclusion:

- behavior is now acceptable;
- information architecture is still mixed between product-owner actions, technical/system actions, and catalog-browsing actions;
- the next step should be phased UI cleanup, not another wide behavior refactor.

## Header audit

Observed in screenshot:

- page title: `ProductSystem / Sablone`
- subtitle under title
- right-side actions:
  - `Live DB`
  - `Info`
  - `Blueprint Dossier`
  - `Reincarca`
  - `Sablon Nou`

Assessment:

- too many actions are visually promoted at once;
- `Sablon Nou` is the only clear primary action;
- `Reincarca` is secondary but still reads as a peer to product creation;
- `Live DB`, `Info`, and `Blueprint Dossier` feel technical/system-level rather than catalog-browsing actions;
- header works for internal users, but not yet with clean action hierarchy.

Recommendation:

- keep `Sablon Nou` as the only strong primary action;
- keep `Reincarca` as secondary;
- move `Info`, `Blueprint Dossier`, and truth/system diagnostics under a compact `Sistem` or `Verificari` menu;
- keep `Live DB` as badge/status, not as equal-weight action button.

## Truth boundary audit

Observed in screenshot:

- trust/truth boundary panel is visible near top of page;
- contains explanatory copy plus quick links;
- visually occupies a large block before the catalog itself starts.

Assessment:

- content is useful for governance and internal debugging;
- it is not primary for catalog browsing;
- it pushes the actual working area too far down, especially on laptop-height screens;
- repeated visits will likely not need the full explanation visible each time.

Recommendation:

- collapsed by default for routine usage;
- header line remains visible:
  - source-of-truth label
  - environment status
  - one-line summary
- expand on demand for governance/debug context.

## Families / filters / search audit

Observed in screenshot:

- families occupy a full horizontal block with counts
- status filters occupy a second row
- search sits alone on another row
- surface tabs occupy another row

Assessment:

- each control is individually understandable;
- together they create too many stacked control rows before the first result card;
- this is manageable with 10-15 templates, but not efficient for 30+ templates;
- search is visually isolated and slightly detached from the other filters.

Recommendation:

- family chips remain first because they are the strongest content partition;
- search, status filter, and surface tabs should be regrouped into a compact filter bar;
- counts should stay, but be visually lighter;
- if possible later, make the compact filter row sticky.

## Tabs audit

Observed:

- `Template-uri produs`
- `Componente / module reutilizabile`

Assessment:

- the split is correct and materially improves mental separation;
- the labels are understandable;
- tab visibility is acceptable, but still subordinate to the stacked filter rows above.

Recommendation:

- keep the current split;
- visually bring tabs closer to content and integrate them with the compact filter/search row in a future pass.

## Template card audit

Code anchor:

- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- compact card surface is currently driven by `TemplateLibraryRow` plus `WorkflowSummaryCard`

Observed:

- current product card is much better than earlier iterations;
- no more inline child-module list;
- chips are compact;
- workflow entry is separated;
- still, each card carries many visible elements:
  - title + badges
  - family line
  - metrics line
  - component chips
  - workflow summary block
  - actions
  - trailing technical icons / editor icon cluster

Assessment:

- card is now acceptable, but still not final-form slim;
- strongest remaining density issue is action hierarchy and icon noise;
- metrics line is informative but visually busy;
- workflow block is still a mini-panel rather than a pure meta row;
- the purple edit icon / right chevron cluster reads as implementation detail rather than user-priority action.

Recommendation:

- keep title + badges;
- compress metrics into one lighter metadata line;
- keep chips on one row where possible;
- turn workflow block into a tighter meta row in a later pass;
- make explicit action hierarchy:
  - primary in-card action: `Workflow`
  - secondary: `Componente`
  - tertiary/technical: `Detalii` or overflow;
- reduce decorative icon prominence.

## Component card audit

Observed from code and current split:

- component cards already differ behaviorally from product cards;
- they surface usage kind (`Shared`, `Specific`, `Orphan`) plus `Used by`, material roles, and operation roles.

Assessment:

- this is the correct direction;
- however, visual language can be even more distinct from product cards so users do not interpret technical modules as sellable templates.

Recommendation:

- component cards should emphasize:
  - component code
  - friendly label
  - usage badge
  - `Used by`
  - role counts
- they do not need the same product-level visual weight as product template cards.

## Workflow entry audit

Observed:

- workflow no longer expands inline;
- workflow draft is isolated per template code;
- entry point is clear enough through `Configureaza workflow`.

Assessment:

- behavior is correct;
- wording can be simplified for density and clarity.

Recommendation:

- rename `Configureaza workflow` to `Workflow` in a safe cleanup pass;
- rename `Vezi componente` to `Componente` in the same pass;
- preserve the dedicated side panel behavior.

## Scalability audit

With 30+ templates, current risks are:

1. top-of-page control stack consumes too much vertical space before results start;
2. each card remains slightly taller than necessary because workflow summary is boxed rather than line-based;
3. repeated icon clusters and badge groups become visually noisy;
4. technical actions compete with user-primary actions.

What will become tiring first:

- scanning card actions;
- repeated metadata density;
- extra vertical distance before the first meaningful row of results.

## Problem table

| Zona | Problema | Impact | Severitate | Recomandare |
|---|---|---|---|---|
| Header | Prea multe actiuni cu aceeasi greutate vizuala | Userul nu vede rapid actiunea principala | Medium | Pastreaza `Sablon Nou` primar, `Reincarca` secundar, muta actiunile tehnice in overflow |
| Truth boundary | Bloc mare deasupra continutului principal | Impinge catalogul real in jos | Medium | Collapsed by default, cu sumar vizibil |
| Families / filters | Prea multe randuri de control separate | Creste timpul de orientare si reduce densitatea utila | Medium | Unifica search + status + tabs intr-o bara compacta |
| Search | Sta izolat fata de celelalte controale | Pare deconectat de filtrare | Low | Mutare in filter bar compact |
| Tabs | Corecte conceptual, dar putin ingropate | Separarea modurilor e mai putin evidenta decat ar trebui | Low | Apropie tabs de continut si de filter bar |
| Template card | Inca are multa informatie si multe iconuri | Scanezi mai greu 30+ carduri | High | Mai putine iconuri, meta row mai compact, actiuni mai clare |
| Workflow summary | Inca seamana cu un mini-panel in card | Mareste inaltimea cardului | Medium | In faza urmatoare, transforma in meta row compact |
| Card actions | Actiunile utile si cele tehnice sunt amestecate | Prioritatea interactiunilor nu e limpede | High | `Workflow`, `Componente`, apoi overflow / detalii |
| Component card | Nu este inca suficient de distinct vizual de product card | Risc de confuzie intre template produs si modul tehnic | Medium | Stil si ierarhie dedicate pentru component cards |

## Recommended final layout

### Header

Left:

- `Product System`
- subtitle scurt

Right:

- primary: `Sablon nou`
- secondary: `Reincarca`
- status badge: `Live DB`
- overflow `Sistem` / `Verificari`:
  - `Info`
  - `Blueprint Dossier`
  - truth boundary links

### Filters

Row 1:

- Family chips

Row 2 compact:

- Search
- Status filter
- Tabs: `Template-uri produs` / `Componente`

Preferred for 30+ templates:

- this compact 2-row layout is better than the current 4-row stack;
- later it can become sticky.

### Template card

Recommended target:

Header:

- `TPL-VOLUMETRIC-LOGO_v1` `Recomandat` `Activ`
- `Litere volumetrice`
- light metrics line: `Aggregate 6/22/20 · Validare 2/6`

Meta row:

- `Componente: Face · Finish · Return · Back · Lighting · Mounting`

Workflow row:

- `Workflow: 13 pasi · Recomandat · Valid`

Actions:

- `Workflow`
- `Componente`
- `Detalii`
- `...`

### Component card

Recommended target:

- component code
- friendly label
- `Shared` / `Specific` / `Orphan`
- `Used by: ...`
- material roles count
- operation roles count
- actions:
  - `Details`
  - `Used by`
  - `Validate`

## Phased implementation plan

### Phase A — UI cleanup without behavior change

- header action hierarchy
- truth boundary collapsed by default
- compact card spacing
- rename buttons:
  - `Configureaza workflow` -> `Workflow`
  - `Vezi componente` -> `Componente`
- move technical icons/actions toward overflow

### Phase B — Better filter bar

- compact filter layout
- search + status + tabs regrouped
- clearer count labels
- optional sticky filter row

### Phase C — Card redesign

- final slim template card
- component card with distinct visual language
- reduce icon noise and repeated badge weight

### Phase D — Advanced UX

- saved views
- density toggle: `Compact / Comfortable`
- keyboard search shortcut
- quick actions / command palette integration

## What was implemented in this audit

- No UI refactor was applied as part of this audit.
- Existing current state was reviewed and mapped to a phased plan.
- Latest already-existing card/workflow corrections remain unchanged.

## What remains

- explicit owner approval for Phase A cleanup
- then a narrow implementation pass with minimal behavior change

## Phase A cleanup implemented

- Header action hierarchy was tightened without changing page behavior:
  - `Sablon Nou` remains the strong primary CTA
  - `Reincarca` remains secondary
  - `Live DB` remains visible through the existing source/status badge instead of reading like a peer CTA
  - `Info` and `Blueprint Dossier` were visually reduced to technical secondary controls; no overflow grouping was introduced in this phase
- Truth boundary was compacted and is now collapsed by default:
  - one-line summary remains visible
  - live/source and upstream context remain visible
  - details and downstream truth links are available via expand/collapse
- Product template cards were slimmed with a light spacing pass only:
  - reduced card padding and top-level action spacing
  - workflow summary compressed into a tighter inline summary row
  - technical meta icons were visually softened
- Actions were renamed for calmer card density:
  - `Configureaza workflow` -> `Workflow`
  - `Vezi componente` -> `Componente`
- Not touched in Phase A:
  - tabs model
  - filtering logic
  - workflow panel behavior
  - component tab behavior
  - state management
  - persistence / backend / DB
- Validation:
  - focused page and library tests updated for compact truth boundary and renamed actions
  - frontend vitest slice and frontend build to be run after the patch
