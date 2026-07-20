# External Artwork Analysis Boundary — allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `db64b4646625220c05a06b8e789880e91e494ef2` |
| Rule | Stage **only** paths below. Never reset/stash/clean/`git add .`. No push/PR. |

## Allowed paths

### Docs (commit 1)

- `docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md`
- `docs/architecture/artwork-understanding/2026-07-20_ARTWORK_UNDERSTANDING_OPERATOR_TEACHING_MODEL.md`
- `docs/architecture/product-system/WORKOS_SYSTEMS_ALIGNMENT_MAP.md`
- `AGENTS.md`

### Schemas + adapter (commit 2)

- `backend/schemas/artwork_analysis_contract_v1.py`
- `backend/services/artwork_analysis_intake_adapter.py`
- `backend/services/artwork_analysis_integration_readiness.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_artwork_analysis_contract_v1.py`
- `frontend/src/lib/artworkAnalysis/artworkAnalysisContractV1.ts`
- `frontend/src/lib/artworkAnalysis/artworkAnalysisContractV1.test.ts`

### UI + readiness surface (commit 3)

- `frontend/src/features/product-system/ArtworkAnalysisReviewPanel.tsx`
- `frontend/src/features/product-system/ArtworkAnalysisReviewPanel.test.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`

### Worklog / QA (commit 4)

- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/EXTERNAL_ARTWORK_ANALYSIS_BOUNDARY_ALLOWLIST.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/EXTERNAL_ARTWORK_ANALYSIS_BOUNDARY_REPORT.md`

## Forbidden

- Extending `frontend/src/lib/svgAnalyzer/**` analysis capability
- Extending `backend/services/svg_*` / `intake_v3_svg_*` / `acm_dxf_*` parsers
- Deleting legacy analyzers without owner GO
- Aluminiu activation, Build 2 teaching engines, transport implementation, push/PR
- Dirty-tree bulk stage
