# TPL-VOLUMETRIC-LETTERS — Workspace Composition

## Entry

- Route: `/intake/:id`
- Gate: `shouldUseVolumetricIntakePage(confirmedTemplateCode, productFamily)`
- Shell: `VolumetricLettersWorkspace` via `TemplateWorkspaceRouter`

## Layout

- Container: `w-full` (no `max-w-5xl` constraint)
- Grid: `TemplateWorkspaceLayout` — `minmax(0,1fr)` main + `280–320px` sticky side on `xl+`
- Mobile: single column, main first then side panel

## Module stack

| Region | Module | Notes |
|--------|--------|-------|
| Header | FlowBreadcrumb | Full width |
| Main | WorkspaceTabBar | Spec + Simulare tabs |
| Main | WorkspaceAlerts | Critical banners |
| Main | TemplateConfirmationPanel | When spec tab |
| Main | ProductSpecEditorSlot | Core form |
| Main | TerrainRequirementPanel | Install only |
| Main | QuoteHandoffPanel | Quote tab |
| Side | RequestContextPanel | `variant="compact"` |
| Side | TemplateStatusPanel | `variant="stacked"` |
| Side | ReadinessGatePanel | `layout="stack"` — Simulare + Gata pt. Ofertă |

## Template-specific (not extracted)

- `IntakePathwaySelector` inside `Product001IntakeSpecEditor`
- `VectorIntakeFastAskPanel` — vector-first entry assistant when pathway is `vector` (file picker with SVG MIME support, client-side SVG layer detection, fast questions → metadata attach → prefill → full editor)
- `VectorStudioPanel` inside editor section 9
- `VolumetricLettersQuoteFlow` simulation payload
- Pathway progressive disclosure (`volumetricIntakePathway.ts`)

## Reused from generic IntakeDetail

- `AuditTerenSection` passed as `installTerrainSection` ReactNode
- Readiness evaluation (`evaluateIntakeReadyPrerequisites`)
- Persistence handlers (`handleSaveProductSpec`, `handleMarkReadyForQuote`, etc.)

## Legacy overlap

- `VolumetricLettersIntakePage.tsx` is a thin re-export of `VolumetricLettersWorkspace` for import stability.
- Generic intake still renders full `IntakeDetail` legacy layout (identity, assist, action summary, etc.).

## Data unchanged

- `product_spec_json` contract unchanged
- `Product001IntakeSpecEditor` props contract unchanged
- No pricing / CostEngine / readiness policy changes
