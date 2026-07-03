# Template Intake Workspace — Module System

Modular composition for template-specific Work Intake detail pages. First consumer: `TPL-VOLUMETRIC-LETTERS`.

## Router & layout

```
IntakeDetail
└─ TemplateWorkspaceRouter
   └─ VolumetricLettersWorkspace (w-full)
      └─ TemplateWorkspaceLayout (xl: 1fr + 320px)
         ├─ WorkspaceMainColumn
         │   ├─ WorkspaceTabBar
         │   ├─ WorkspaceAlerts
         │   ├─ [spec] TemplateConfirmationPanel, ProductSpecEditorSlot, TerrainRequirementPanel
         │   └─ [quote] QuoteHandoffPanel
         └─ WorkspaceSidePanel (sticky)
             ├─ RequestContextPanel (compact)
             ├─ TemplateStatusPanel (stacked)
             └─ StickyWorkspaceActions → ReadinessGatePanel (stack)
```

### Column placement rules

| Main column | Side panel |
|-------------|------------|
| Tab navigation | Request context (compact) |
| Form-related alerts | Template status (stacked) |
| Product spec editor | Readiness + primary CTAs |
| Terrain (when install) | — |
| Quote simulation flow | Sticky actions remain visible |

Generic/non-volumetric intakes remain on the legacy `IntakeDetail` path unchanged.

## Routing rules (intake detail)

| Condition | Shell |
|-----------|--------|
| `product_family` empty / whitespace | Generic **unresolved** (`IntakeDetail` + `UnresolvedWorkTypeSection`) |
| `confirmed_template_code === TPL-VOLUMETRIC-LETTERS` **or** `product_family` is litere volumetrice | **Volumetric modular** (`TemplateWorkspaceRouter` → `VolumetricLettersWorkspace`) |
| Any other `product_family` / template | Generic **legacy** (`IntakeDetail` mock assist or backend assist) |

`TemplateWorkspaceRouter` must never return a blank tree when `enabled=true`; unsupported modular templates show an explicit fallback panel.

Null/missing `dimensions` from the API must not crash detail hooks — normalize at load (`dataStore`) and parse defensively (`intakeDetailDimensions`).

---

## Module contracts

### InfoHint

| | |
|---|---|
| **Responsibility** | Accessible info icon; secondary explanations in tooltip only |
| **Inputs** | `label` (aria), `children` (tooltip body) |
| **Actions** | None |
| **Visibility** | Wherever explanatory text would clutter the UI |
| **Reuse** | All templates |
| **Default visible** | Icon only |
| **Tooltip** | Full explanation |
| **Forbidden clutter** | Inline paragraphs duplicating tooltip |

### RequestContextPanel

| | |
|---|---|
| **Responsibility** | Request identity: ID, status, client, contact, assignee, delivery |
| **Inputs** | `request`, `source`, `assignedTo`, `selectedDeliveryType`, handlers |
| **Actions** | Edit assignee, change delivery, navigate to list |
| **Visibility** | Always in template workspace header |
| **Reuse** | All templates with Work Intake context |
| **Default visible** | Compact grid of four fields |
| **Tooltip** | None (labels are self-explanatory) |
| **Forbidden clutter** | Duplicate client blocks, fiscal identity on volumetric path |

### TemplateStatusPanel

| | |
|---|---|
| **Responsibility** | Compact readiness strip (template / spec / terrain / intake) |
| **Inputs** | `actionSummary`, optional `readinessMissing` |
| **Actions** | None (read-only); blockers listed inline when present |
| **Visibility** | Always below request context |
| **Reuse** | Any template using `IntakeActionSummaryModel` |
| **Default visible** | Dot + label + value per dimension |
| **Tooltip** | InfoHint on aggregated “Lipsesc” line only |
| **Forbidden clutter** | Four separate bordered pills/badges |

### WorkspaceTabBar

| | |
|---|---|
| **Responsibility** | Primary navigation: Specificație \| Simulare ofertă |
| **Inputs** | `activeTab`, `onTabChange`, `actionSummary` |
| **Actions** | Switch tab; optional “Simulare” shortcut |
| **Visibility** | Always |
| **Reuse** | Templates with embedded quote/simulation tab |
| **Default visible** | Two tabs + handoff CTA when preliminary quote allowed |
| **Tooltip** | None |
| **Forbidden clutter** | Third duplicate quote entry points |

### WorkspaceAlerts

| | |
|---|---|
| **Responsibility** | Critical banners: status conflict, backend error, persist error |
| **Inputs** | `statusConflict`, `error`, `persistError`, `source` |
| **Visibility** | When any alert condition is true |
| **Reuse** | All template workspaces |
| **Default visible** | Full blocker text (not hidden in tooltip) |

### TemplateConfirmationPanel

| | |
|---|---|
| **Responsibility** | Confirm product template for the request |
| **Inputs** | `templateCode`, `confirmed`, `confirming`, `readOnly`, `onConfirm` |
| **Actions** | Confirm template CTA |
| **Visibility** | Spec tab; always (confirmed state is compact) |
| **Reuse** | Any template with `confirmed_template_code` gate |
| **Template-specific** | `templateCode` value per composition |

### ProductSpecEditorSlot

| | |
|---|---|
| **Responsibility** | Slot wrapper for template product specification editor |
| **Inputs** | `initialSpec`, `onSave`, `readOnly` |
| **Actions** | Delegates save to parent |
| **Visibility** | Spec tab after template confirmation area |
| **Reuse** | Swap editor component per template without changing router |
| **Template-specific** | Currently mounts `Product001IntakeSpecEditor` (contract unchanged) |

When `intake_input_pathway === "vector"`, the editor shows `VectorIntakeFastAskPanel` first (file picker, client-side SVG layer detection, fast production questions). Applying answers prefills `product_spec_json` via `mapVectorFastAskToProductSpec` (including `vector_detected_layers` metadata when SVG is analyzed) and unlocks the full section form. Manual and quick-estimate pathways are unchanged.

### TerrainRequirementPanel

| | |
|---|---|
| **Responsibility** | Site audit / terrain when install delivery; N/A otherwise |
| **Inputs** | `requiresInstallAudit`, `installTerrainSection` (ReactNode from IntakeDetail) |
| **Visibility** | Spec tab; N/A compact row for non-install |
| **Reuse** | Totem, ACM, any install-heavy template |
| **Tooltip** | N/A reason behind InfoHint |

### ReadinessGatePanel

| | |
|---|---|
| **Responsibility** | Mark ready + preliminary quote entry; list blockers |
| **Inputs** | `request`, `readiness`, `actionSummary`, loading/message, handlers |
| **Actions** | `onMarkReady`, `onOpenQuote` |
| **Visibility** | Spec tab footer |
| **Reuse** | All templates using shared readiness policy |
| **Default visible** | Primary CTAs; blocker list when not ready |
| **Tooltip** | InfoHint on mark-ready (secondary policy note) |
| **Forbidden clutter** | Temp ID badge, “pregătit pentru marcare” pill, blue info box |

### QuoteHandoffPanel

| | |
|---|---|
| **Responsibility** | Embedded preliminary quote (no `/quotes` navigation) |
| **Inputs** | `request`, `productSpec`, `intakeDbId`, `siteAuditJson`, labels |
| **Actions** | `onClose` → return to spec tab |
| **Visibility** | Quote tab only |
| **Reuse** | Pattern reusable; implementation volumetric-specific (`VolumetricLettersQuoteFlow`) |
| **Template-specific** | Quote flow component and template code |

---

## UX principles (enforced in this build)

1. Badges only for request status (single pill).
2. Field metadata tags in `Product001IntakeSpecEditor` moved to InfoHint tooltips.
3. Section purposes in editor behind InfoHint on section title.
4. Blockers and errors remain fully visible.
5. Primary CTAs: Save (in editor), Confirm template, Simulare, Gata pt. Ofertă.

---

## Adding a new template

1. Create `YourTemplateWorkspace.tsx` composing reusable modules.
2. Register in `TemplateWorkspaceRouter` by `confirmed_template_code`.
3. Pass `ProductSpecEditorSlot` with your editor or reuse existing slot.
4. Optionally add `QuoteHandoffPanel` variant or shared handoff interface.
5. Document composition in `TPL_*_WORKSPACE_COMPOSITION.md`.
