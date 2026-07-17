# Source map — Intake SVG roles ↔ Product System

Status: audit truth (2026-07-17). No implementation.

## Authority chain (actual)

```text
SVG file
 → FE nest2 analyzeSvgString (frontend/src/lib/svgAnalyzer)
 → report.layers[] + closedContourCandidates
 → Operator Step 1 (IntakeV6SvgAnalyzerStep)
     ├─ Layer roles → layer_role_setup → analysis-bundle
     │    → selected_layer_refs (vector_litere / vector_logo)
     │    → composition recommendation (TPL-VOLUMETRIC-LETTERS_v2 / LOGO_v1)
     └─ Closed-contour → finish_setup (FE)
          → mounting_solution (persists)
          → svg_support_selection (DROPPED by IntakeV4FinishSetup)
 → ProductDefinition builder (partial projection)
 → Process adapter / resolver (support_type / mounting_solution)
```

## Key files

| Concern | Path |
|---------|------|
| Step 1 route | `frontend/src/App.tsx` (`/intake-v6/.../operator`) |
| Step shell | `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkspace.tsx` |
| Step UI | `…/steps/IntakeV6SvgAnalyzerStep.tsx` |
| Owner role options | `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts` |
| Full latent roles | `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.ts` |
| Role table | `…/IntakeV6LayersRoleTable.tsx` |
| Target badge | `frontend/src/lib/intakeV6/intakeV6LayerTargetTemplate.ts` |
| Contour panel | `…/IntakeV6AlucobondContourPanel.tsx` |
| Contour detect | `frontend/src/lib/svgAnalyzer/closed-contour/*` |
| Persist FE | `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` |
| analysis-bundle BE | `backend/services/intake_v6_workspace_service.py` |
| selected_layer_refs | `backend/services/intake_v4_layer_role_service.py` |
| Composition rec | `backend/services/intake_v6_product_composition_recommendation_service.py` |
| Finish schema | `backend/schemas/intake_v4.py` (`IntakeV4FinishSetup`) |
| Mounting ACM | `backend/services/mounting_solution_service.py` |
| PD projection | `backend/services/product_definition_builder_service.py` |
| Process components | `backend/data/product_process/volumetric_letters_v1.py` |
| ACM PS seed | `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py` |
| Letters root | `backend/seeds/seed_tpl_volumetric_letters_v2.py` |

## Persistence sinks

| Sink | Contents | Survives reload? |
|------|----------|------------------|
| `payload.layer_role_setup` | Layer roles | Yes |
| `payload.svg_runtime.selected_layer_refs` | vector_litere / vector_logo | Yes (derived) |
| `payload.finish_setup.mounting_solution` | ACM template + config | Yes |
| `payload.finish_setup.svg_support_selection` | Typed contour selection | **No** (schema drop) |
| `payload.product_composition` | Recommended/confirmed items | Separate confirm |

## Identity keys

| Key | Stable? | Used by |
|-----|---------|---------|
| `layer.id` / `layer.name` | If SVG has ids/names | Layer roles |
| `el-N` | Parse order — fragile | Contour secondary |
| `cc_<geometry_hash>` | Geometry-stable | Closed-contour primary |
| Template codes `TPL-*` | Registry | Composition / mounting |
