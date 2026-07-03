# BUILD — Template Intake Workspace Modularization (Volumetric First)

## Problem addressed

The volumetric intake page was a monolithic `VolumetricLettersIntakePage` with duplicated status pills, persistent helper text, and field badge spam. The goal was a **reusable module architecture** with a **visually lighter** operator UI, without changing pricing, CostEngine, or `product_spec_json` contracts.

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| Base HEAD (start) | `9a03dcd` |
| Backend | `:8000` healthy |
| Frontend | `:3000` up |
| Counts before | intakes **11**, quotes **7**, orders **8** (UI/API) |

## Module inventory

### Reusable modules (`frontend/src/components/workos/templateIntakeWorkspace/`)

| Module | Role |
|--------|------|
| `InfoHint` | Tooltip-only secondary explanations |
| `RequestContextPanel` | Client / contact / assignee / delivery |
| `TemplateStatusPanel` | Compact readiness strip |
| `WorkspaceTabBar` | Spec \| Simulare tabs |
| `WorkspaceAlerts` | Conflict + error banners |
| `TemplateConfirmationPanel` | Confirm template CTA |
| `ProductSpecEditorSlot` | Editor mount point |
| `TerrainRequirementPanel` | Install terrain or N/A |
| `ReadinessGatePanel` | Mark ready + simulare + blockers |
| `TemplateWorkspaceRouter` | Routes by template code |

### Volumetric-specific

| Module | Role |
|--------|------|
| `VolumetricLettersWorkspace` | Composition root |
| `QuoteHandoffPanel` | Embedded `VolumetricLettersQuoteFlow` |
| `IntakePathwaySelector` | 3-card pathway (in editor) |
| `Product001IntakeSpecEditor` | Unchanged contract |

## Clutter removed

- Four bordered `StatusPill` components → single `TemplateStatusPanel` text strip
- Persistent blue info box in readiness footer → `InfoHint` on mark-ready
- Field tag badges (`affects_cost`, `optional`, etc.) → tooltip on label
- Section `purpose` paragraphs in editor → `InfoHint` on section title
- Pathway subtitle + hint paragraph → single `InfoHint` on selector title
- Checkbox inline badge stacks → `InfoHint` per option

## Tooltip strategy

- Radix `Tooltip` via shared `InfoHint` component
- `aria-label` on trigger for accessibility
- Blockers, errors, and primary CTAs remain visible (not tooltipped)

## Browser validation (WI-SMOKE-P001)

| Check | Result |
|-------|--------|
| Cleaner workspace layout | PASS — modular header + tabs |
| Primary actions visible | PASS — Salvează, Simulare, Gata pt. Ofertă |
| Info icons present | PASS — section/field hints |
| Product001IntakeSpecEditor works | PASS |
| Vector Studio reachable | PASS — section 9 |
| Terrain conditional | PASS — install audit section when delivery_install |
| Quote handoff | PASS — embedded tab, no `/quotes` hop |
| Values 4800/600/60/2.88/18/9 | PASS |
| Simulation 844.41 EUR | PASS |
| No quote/order created | PASS — commercial quote button disabled |

## Browser validation (/quotes)

| Check | Result |
|-------|--------|
| Ofertă nouă opens generic wizard | PASS |
| Cancel without creating quote | PASS |

## Tests / lint

- Vitest: `TemplateWorkspaceRouter`, `VolumetricLettersWorkspace`, `IntakeDetail.volumetricShell`, `IntakeDetail.visibility` — **PASS**
- ESLint: new `templateIntakeWorkspace/` — clean; `IntakeDetail.tsx` has pre-existing hook-deps warnings only

## Counts after

| Entity | Count |
|--------|-------|
| Intakes | 11 |
| Quotes | 7 |
| Orders | 8 (unchanged) |

## Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created
- No Reference Catalogs started
- Readiness policy unchanged
- `Product001IntakeSpecEditor` contract unchanged
- `VolumetricLettersQuoteFlow` preserved
- Generic/non-volumetric flow unaffected

## Documentation

- `docs/architecture/TEMPLATE_INTAKE_WORKSPACE_MODULES.md`
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_WORKSPACE_COMPOSITION.md`

## Result

**PASS**
