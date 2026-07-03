# ProductSystem Blueprint Studio — Full UI Implementation

## Design
- Extends existing ProductSystem page with a "Blueprint Dossier" tab
- Color palette: Same dark theme as existing ProductSystem
  - Background: #0F172A / #111827
  - Cards: #0D1321 with #1E293B borders
  - Accent purple: #A855F7 (dossier identity)
  - Status colors: draft=#6B7280, needs_review=#F59E0B, approved=#10B981, blocked=#EF4444, deprecated=#64748B
- Typography: Consistent with existing WorkOS UI — 10-13px labels, mono for codes
- Layout: Tab-based within ProductSystem — "Șabloane" (existing) + "Blueprint Dossier" (new)

## Architecture
- Dossier is a companion to product_template (1:1 via template_id)
- 13 JSON section fields, each editable via structured JSON editor
- Status lifecycle: draft → needs_review → approved (with version auto-increment)
- Completion state tracks per-section readiness
- API: /api/v1/entities/product-blueprint-dossiers (existing backend)

## Development Tasks
- [x] Create dossier API client in api/blueprintDossier.ts
- [x] Create BlueprintDossierStudio.tsx — main dossier management page
- [x] Integrate dossier tab into ProductSystem.tsx
- [x] Implement dossier list view with status badges and version display
- [x] Implement dossier detail/editor with section panels
- [x] Implement status transition controls with allowed-transition enforcement
- [x] Implement completion state visualization (per-section progress)
- [x] Run lint + build to verify