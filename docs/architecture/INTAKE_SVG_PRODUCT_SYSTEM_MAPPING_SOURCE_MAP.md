# Source map — Intake SVG roles ↔ Product System (after component-aware assignment)

Updated 2026-07-17.

## Authority chain (target / implemented)

```text
Product Template (TPL-VOLUMETRIC-LETTERS_v2)
 → GET template-availability.svg_bindable_components
 → Intake Step 1 Asocieri produs
 → geometry (layer / closed contour)
 → finish_setup.svg_component_bindings (+ synced svg_support_selection)
 → ProductDefinition.svg_component_instances
```

## Before → after

| Concern | Before | After |
|---------|--------|-------|
| Option source | Hardcoded FE Vector Litere/Logo | Product System bindables |
| ACP | Parallel closed-contour panel SoT | Nested under Contur suport; same bindings SoT |
| FinishSetup | Dropped `svg_support_selection` | Persists selection + bindings |
| Stale support | `TPL-BOND-CASETAT` pending | Blocked for new selection; ACM live |
| PD | Partial selection projection | + `svg_component_instances` |

## Key files

| Concern | Path |
|---------|------|
| Binding contract | `backend/data/product_system/svg_component_binding_contract.py` |
| Persistence | `backend/services/svg_component_binding_persistence.py` |
| Finish schema | `backend/schemas/intake_v4.py` |
| PD projection | `backend/services/product_definition_builder_service.py` |
| Assignment UI | `frontend/.../IntakeV6SvgComponentAssignmentPanel.tsx` |
| FE bindings | `frontend/src/lib/intakeV6/svgComponentBindings.ts` |
| Legacy adapter | `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts` |
