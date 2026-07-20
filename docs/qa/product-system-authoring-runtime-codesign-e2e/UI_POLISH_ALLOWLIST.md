# PRODUCT SYSTEM UI / FIGMA FINAL POLISH — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `2d4b3480687afba10da4abd3ae9fe6d7b8a30367` (**reconfirmed**) |
| Dirty tree | ~360 — **preserved**; allowlist-only staging |
| Owner GO | UI polish only — no architecture / Product Truth / schema |

## Kickoff confirmation

| # | Item | Status |
|---|------|--------|
| 1 | HEAD `2d4b348` on branch | **YES** |
| 2 | Prior authoring PASS_WITH_WARNINGS preserved | **YES** |
| 3 | Lifecycle/publication PASS preserved | **YES** |
| 4 | Readiness PASS_WITH_WARNINGS preserved | **YES** |
| 5 | Runtime preview PASS_WITH_WARNINGS preserved | **YES** |
| 6 | UI/Figma was NEEDS_POLISH | **YES** — this build |
| 7 | Aluminiu BLOCKED — no activation | **YES** |
| 8 | External Artwork Analysis Boundary | **YES** — untouched |
| 9 | No new Master Plan / general audit | **YES** |
| 10 | No CostEngine / Pricing / Snap / Execution | **YES** |
| 11 | No CT table / PI / CI / Build 2 | **YES** |
| 12 | No push / PR / git add -A | **YES** |

## Allowed paths (stage only these)

### Frontend

- `frontend/src/features/product-system/productSystemAdminDisplay.ts`
- `frontend/src/features/product-system/productSystemAdminDisplay.test.ts`
- `frontend/src/features/product-system/ProductSystemLayout.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/TemplateDualStatusChips.tsx`
- `frontend/src/features/product-system/TemplateDualStatusChips.test.tsx`
- `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx`
- `frontend/src/features/product-system/ComponentContractUsedByPanel.tsx`
- `frontend/src/features/product-system/ProductE2EReadinessPanel.tsx`
- `frontend/src/features/product-system/ProductE2EReadinessPanel.test.tsx`
- `frontend/src/features/product-system/ProductTemplatePublicationPanel.tsx`
- `frontend/src/features/product-system/ProductTemplatePublicationPanel.test.tsx`
- `frontend/src/features/product-system/TemplateRuntimePreviewPanel.tsx`
- `frontend/src/features/product-system/TemplateRuntimePreviewPanel.test.tsx`
- `frontend/src/pages/BlueprintDossierStudio.tsx` (sticky footer labels / a11y only)

### Docs / evidence

- `docs/qa/product-system-authoring-runtime-codesign-e2e/UI_POLISH_ALLOWLIST.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/UI_PAGE_AUDITS_FINAL_POLISH.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/UI_AUDIT_FINAL_POLISH.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/FIGMA_CLASSIFICATION_FINAL_POLISH.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/UI_FIGMA_FINAL_POLISH_REPORT.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/**` (polish_* + inventory updates)
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/capture_ui_final_polish.mjs`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/final_polish_ui_capture_evidence.json`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (§ PRODUCT SYSTEM UI / FIGMA FINAL POLISH)

## Forbidden (do not stage)

- Backend CostEngine / Pricing / Snapshot / Execution / migrations
- Artwork analysis / SVG / DWG / DXF parsers
- Aluminiu activation / ACM / Logo activation
- `ProductSystem.tsx` drive-by / foreign dirty files
- `git add -A`, reset, stash, clean, push, PR

## Commit groups (allowlist)

1. `fix(product-system-ui): clarify authoring shell and status hierarchy`
2. `fix(product-system-ui): simplify composition component contracts and dossier`
3. `fix(product-system-ui): refine readiness publication and runtime preview`
4. `test(product-system-ui): close interaction and state coverage`
5. `docs(qa): finalize Figma and screenshot acceptance`
