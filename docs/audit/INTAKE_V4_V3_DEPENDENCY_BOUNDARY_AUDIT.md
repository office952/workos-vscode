# INTAKE V4 — V3 DEPENDENCY BOUNDARY AUDIT

**Date:** 2026-06-23  
**Mode:** Read-only audit — no code changes in this phase beyond this document  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Checkpoint reference:** `4557375` (nesting UI truth) + subsequent material-review finalization phases  

---

## 1. Verdict

Intake V4 is an **operator orchestration shell** with its own workspace persistence, client-side SVG analyzer (`lib/svgAnalyzer`), and V4-native material/nesting review truth. It **still depends on V3** for several **handoff adapters** (pricing input, production task dry-run, quote/order linkage, lighting plan sync, finish material flags) and for **shared SVG geometry utilities** on the server. None of these dependencies mutate commercial quote final pricing directly from the material-review phases audited here.

**Recommended extraction order (future builds, not this phase):**

1. Neutral `workos_svg_upload` + `workos_geometry_metrics` modules (currently `intake_v3_svg_analysis_service`, `intake_v3_geometry_*`).
2. Neutral `production_handoff_seed` module (currently `intake_v3_production_handoff_adapter`).
3. Neutral `pricing_input_candidate` module (currently `intake_v3_pricing_input_adapter`).
4. V4-native production task dry-run response schema (stop re-exporting `IntakeV3ProductionTaskDryRunResponse`).

---

## 2. Frontend — V3 components used in V4

| V4 consumer | V3 dependency | Category | Notes |
|-------------|---------------|----------|-------|
| `IntakeV4ReviewStep.tsx` | `IntakeV3ProductionTaskDryRunPanel` | **UI reuse (debug/preview)** | Dry-run panel embedded in Review; uses V3 contracts via `intakeV4Api` |
| `IntakeV4OperatorWorkspaceFileDrop.tsx` | `intakeV3SvgUploadFlow` (`isValidSvgFile`, `pickSvgFileFromFileList`) | **UI reuse** | File picker validation only |
| `IntakeV4OperatorWorkspaceApp.tsx` | `OperatorWorkspaceFontLoader` | **UI reuse** | Font loading for operator workspace |
| `IntakeV4OperatorWorkspaceApp.tsx` | Link to `/intake-v3/:id/operator` | **Navigation bridge** | Explicit legacy escape hatch |
| `useIntakeV4Workspace.ts` | `pickSvgFileFromFileList` | **UI reuse** | Upload flow helper |
| `intakeV4ClientSvgImport.ts` | `isValidSvgFile`, `sanitizeSvgPreview` | **UI reuse** | Client import + preview sanitization |
| `intakeV4Api.ts` | `IntakeV3ProductionTaskDryRunResponse` type | **Contract reuse** | Response shape shared with V3 dry-run endpoint |

**V4-native (no V3 import in component tree):** `intake-v4/*` panels for material breakdown, sheet quote review, nesting preview, geometry, finish, confirm — including owner review banner, footprint override, re-analyze preview warning, material review export.

---

## 3. Frontend — what is only UI reuse

These are **presentation / utility** dependencies. They do not define commercial truth:

- SVG file validation (`intakeV3SvgUploadFlow`)
- SVG preview sanitization (`sanitizeSvgPreview`)
- Operator workspace font loader
- Production task dry-run **panel** (display only; data from V4 API route)

**Safe to keep temporarily** if V3 modules remain stable. **Extract target:** `frontend/src/lib/workosSvg/` or `frontend/src/lib/operatorWorkspace/` neutral helpers.

---

## 4. Frontend — handoff adapters

| Path | Role |
|------|------|
| `intakeV4Api` → production task dry-run | V4 router delegates to V4 service that wraps V3 dry-run engine |
| `intakeV4QuoteHandoff*` | V4-native readiness; may reference quote wizard patterns from V2, not V3 UI |
| Legacy link V3 operator | Operator can jump to V3 workspace for side-by-side comparison |

---

## 5. Backend — V3 services used by V4

| V4 service | V3 dependency | Category |
|------------|---------------|----------|
| `intake_v4_workspace_service` | `intake_v3_svg_analysis_service`, `intake_v3_geometry_metrics_snapshot_service` | **Shared geometry engine (server)** |
| `intake_v4_layer_role_service` | `intake_v3_geometry_path_perimeter_classification_service` | **Geometry classification** |
| `intake_v4_finish_adapter` | `intake_v3_finish_material_service`, `intake_v3_lighting_plan_service`, `schemas.intake_v3` | **Handoff adapter** |
| `intake_v4_pricing_input_service` | `intake_v3_pricing_input_adapter` | **Handoff adapter** |
| `intake_v4_pricing_preview_sync_service` | `intake_v3_lighting_plan_service`, `schemas.intake_v3` | **Handoff adapter** |
| `intake_v4_production_preview_service` | `intake_v3_production_handoff_adapter` | **Handoff adapter** |
| `intake_v4_production_task_dry_run_service` | `intake_v3_production_task_dry_run_service`, material breakdown, handoff adapter | **Handoff adapter** |
| `intake_v4_cnc_operation_dry_run_service` | `schemas.intake_v3` candidate task types | **Contract reuse** |
| `intake_v4_quote_linkage_utils` | `intake_v3_quote_linkage_utils` | **Handoff adapter** |
| `intake_v4_quote_to_order_service` | `intake_v3_guarded_convert_to_order_service`, quote linkage | **Handoff adapter** |
| `intake_v4_order_bound_task_readiness_service` | same as quote/order | **Handoff adapter** |
| `intake_v4_workspaces` router | `IntakeV3ProductionTaskDryRunResponse` schema | **Contract reuse** |

**V4-native truth (no V3 import):** material breakdown aggregation, sheet quote candidate policy, footprint override, nesting material precision, re-analyze preview, commercial quote guards scoped to V4 tables, finish truth services under `intake_v4_*`.

---

## 6. Source of truth by concern

| Concern | Source of truth today | V3 role |
|---------|----------------------|---------|
| Workspace payload / steps | `intake_v4_workspaces` table + V4 schemas | None |
| Client SVG analysis / nesting layout | `frontend/src/lib/svgAnalyzer` (nest2 1.10.0) | Server parse only for legacy paths / metrics snapshot |
| Material sheet quote review | `intake_v4_sheet_quote_candidate_*`, `intake_v4_material_*` | None for selected quantity policy |
| Selected quote sheet area | V4 policy (`eligible_area_floor`, `is_applied_to_quote=false`) | None |
| Operator footprint override | `intake_v4_sheet_footprint_override_service` | None |
| Pricing preview input | V4 service → **V3 adapter** → quote_input shape | Adapter |
| Production task dry-run | V4 service → **V3 dry-run engine** | Adapter |
| Quote / order convert | V4 guarded services → **V3 linkage + convert** | Adapter |
| Finish + lighting sync | V4 finish adapter → **V3 lighting/finish services** | Adapter |
| CostEngine / final pricing | QuoteWizard / protected pricing path | Not intake-owned |

---

## 7. What should be extracted to neutral modules

| Current location | Proposed neutral module | Rationale |
|------------------|-------------------------|-----------|
| `intake_v3_svg_analysis_service` | `services/workos_svg_analysis.py` | Shared by V3 workspace attach and V4 server-side validation |
| `intake_v3_geometry_metrics_snapshot_service` | `services/workos_geometry_metrics.py` | Geometry summary not version-specific |
| `intake_v3_production_handoff_adapter` | `services/production_handoff_seed.py` | Template-agnostic task seed builder |
| `intake_v3_pricing_input_adapter` | `services/pricing_input_candidate.py` | quote_input builder used by V3/V4 |
| `intake_v3_production_task_dry_run_service` | `services/production_task_dry_run.py` | Dry-run engine behind V3/V4 routers |
| `intakeV3SvgUploadFlow` + `sanitizeSvgPreview` | `lib/workosSvg/` | Client utilities |
| `IntakeV3ProductionTaskDryRunResponse` | `schemas/production_task_dry_run.py` | Version-neutral API contract |

**Do not extract in haste:** quote linkage, guarded convert, CostEngine paths — protected areas per AGENTS.md.

---

## 8. Docs cross-reference

| Doc | Relevance |
|-----|-----------|
| `docs/audit/INTAKE_V4_ALIGNMENT_AUDIT.md` | Broader system map; recommends V4 orchestrator + V3 adapter chain |
| `docs/qa/BUILD_INTAKE_V4_REAL_FILE_MATERIAL_NESTING_TRUTH_AUDIT_AND_FIX.md` | Material/nesting truth boundary (closed at 4557375) |
| `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` | Template activation; ACM out of scope |

---

## 9. Boundary rules for next builds

1. **Material review UI** — extend only `intake-v4/*` + `intakeV4*` libs; do not wire selected sheet area into CostEngine without dedicated build.
2. **Re-analyze** — preview-only until owner-confirmed execution build; no silent workspace mutation.
3. **V3 panel embeds** — acceptable for dry-run; replace with V4 panel when response schema is neutralized.
4. **No new V3 imports** in V4 material/nesting truth services.
5. **Polygon nesting WorkOS integration** — out of scope (sandbox only).

---

## 10. Summary table

| Question | Answer |
|----------|--------|
| V3 components in V4 UI? | **4 touchpoints** — file drop, font loader, dry-run panel, legacy link |
| UI-only reuse? | **Yes** — upload validation, preview sanitize, fonts, dry-run display |
| Handoff adapters? | **Yes** — pricing input, production dry-run, quote/order, finish/lighting |
| V4-owned truth? | **Yes** — workspace, client analyzer, material breakdown, sheet quote review, footprint override |
| Must extract now? | **No** — document boundaries; extract incrementally per table §7 |
| Risk if unchanged? | Schema drift between V3/V4 dry-run types; dual server/client SVG metrics |

---

*End of audit — implementation changes not included in this phase.*
