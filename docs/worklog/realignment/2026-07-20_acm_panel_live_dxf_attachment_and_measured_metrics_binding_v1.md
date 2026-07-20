# Worklog — AcmPanel live DXF attachment + measured metrics binding v1

**Build:** `WORKOS_ACM_PANEL_LIVE_DXF_ATTACHMENT_AND_MEASURED_METRICS_BINDING_V1`  
**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Prerequisite:** metrics PASS `69e0260` / docs `fd777a4`

## Audit references

- AcmPanel metrics binding audit (path-only measure gap; JSON-on-instance extension)
- File attachment flows audit (no V6 DXF API; work-file pattern reusable; Intake_requests not owner)

## Owner decisions (binding)

| Gate | Decision |
|------|----------|
| Attachment owner | AcmPanel component instance |
| Storage | Adapt work-file disk pattern under V6 workspace namespace |
| Persistence | JSON-on-instance `production_geometry` — no migration |
| Geometry role | Only `production_geometry` / `cut_v_paths` feed CUT/V |
| Multi-panel | One DXF per panel; explicit panel_id |
| Fixture | Never bind golden 2000×300 to IV6 2000×350 |

## Storage adaptation

- Root: `backend/storage/intake_v6_production_geometry/{workspace_id}/`
- API: `POST /api/v1/intake-v6/workspaces/{id}/acm-panel/production-geometry/dxf`
- Download: `GET .../production-geometry/{attachment_id}/download`
- Not Work Intake `work-file-upload`

## Attachment contract

`acm_panel_production_geometry_attachment_v1` inside bundle `acm_panel_production_geometry_bundle_v1` on `acm_panel_instance.production_geometry`.

## Fingerprint / stale

`compute_config_fingerprint` covers active W/H, L1/L2, construction, panels dims/positions, fold_sides, corner, cutouts, segmentation. Mismatch → `stale`; quantities not consumed; proxy only if eligible.

## Security

`.dxf` only; no ZIP; sanitize + path traversal block; 50 MB; signature check; entity-count / extreme-coord guards; workspace isolation on download.

## ACI

Central `acm_aci_semantic_mapping_v1`; unknown excluded; may yield `measured_with_warnings` / `semantic_mapping_required`.

## UI

Compact block in AcmPanel inspector Geometrie section — filename, panel, status, CUT/V summary, warnings, replace. No money. Pricing remains in live-calc.

## Tests

- `backend/tests/test_acm_production_geometry_attachment_v1.py` (+ prior metrics/commercial/pricing suites)
- FE: `productionGeometryApi.test.ts`

## Runtime

`docs/audits/_evidence/2026-07-20_acm-panel-live-dxf-attachment/runtime-proof.json`

## Screenshots

UI screenshots: see evidence `screenshots-status.md` — capture deferred if stack not live; testids ready for operator capture.

## Next

Operator attach matching DXF for a dedicated V6 QA workspace (not IV6 contamination); optional export-profile ACI UI later.
