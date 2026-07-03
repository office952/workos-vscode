# Archive snapshot — pre Smart Workspace implementation

**Date:** 2026-06-20  
**Git tag:** `archive/pre-smart-workspace-2026-06-20`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Purpose:** Backup before Faza 1 (SVG preview, import toggle, Inter/Mono fonts, progressive disclosure).

## What this snapshot includes

- Intake V3 three-step operator workspace (layers → review → confirm)
- Atoms parity layer color/font evidence (backend drawable summary + UI cards)
- SVG re-upload invalidation + structural change notices
- UX contract: `docs/qa/BUILD_INTAKE_V3_SMART_OPERATOR_WORKSPACE_UX.md`
- Visual reference: `docs/reference/intake-v3-operator-workspace-smart.html`

## What the next build adds (not in this archive)

- SVG preview panel dominant on Layers step
- Hidden dropzone until Replace
- Inter + JetBrains Mono on operator route
- Status bar, footer nav, derived-wrap collapsibles (phased)

## Restore

```powershell
git checkout archive/pre-smart-workspace-2026-06-20
```

Or create a branch from the tag:

```powershell
git checkout -b restore/pre-smart-workspace archive/pre-smart-workspace-2026-06-20
```
