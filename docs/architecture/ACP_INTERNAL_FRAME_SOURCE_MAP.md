# ACP Internal Frame — Source Map

| Field | Value |
|-------|-------|
| Status | Audit map (2026-07-17) |
| Related audit | `docs/audits/2026-07-17_acp_internal_frame_existing_contract_audit.md` |
| Product path | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / Contur suport / Panou Alucobond casetat |

## Authority order (truth)

1. Runtime FinishSetup (`svg_support_selection` + `mounting_solution.configuration`)
2. Active FE confirm mapper (`alucobondCasedPanelSelection.ts`)
3. Active BE persistence / PD builder
4. Product System SVG binding contract capabilities
5. ACM seed components / Aggregate projection
6. Tests
7. Canonical docs (`ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md`)
8. Worklogs / older audits
9. Archive / mock „Cadru metalic”

## End-to-end flow (as implemented)

```text
Step 1 SVG Analyzer
  IntakeV6AlucobondContourPanel checkbox "Cadru interior activ"
    → confirmAlucobondSelection(internal_frame_enabled)
    → svg_support_selection.internal_frame_enabled
    → binding.configuration.internal_frame_enabled  (when bindingFromSupportSelection used)
    → mounting_solution.configuration
         internal_frame_enabled
         frame_clearance_mm = enabled ? 5 : 0

Step 2 Review (ACM mounting fields)
  frame_clearance_mm  ("Luft / clearance cadru")  ← editable number
  (no steel/aluminium, no profile UI)

FinishSetup persist
  BE svg_component_binding_persistence + mounting_solution_service normalize

ProductDefinition
  canonical_values.internal_frame_enabled = bool(selection)
  (no nested frame material/profile structure)

ProductAggregate / CPP
  (no frame material/process lines today)
```

## Source files

| Layer | Path | Role |
|-------|------|------|
| Types | `frontend/src/lib/svgAnalyzer/closed-contour/closedContourTypes.ts` | `internal_frame_enabled: boolean` |
| Mapper | `frontend/src/lib/svgAnalyzer/closed-contour/alucobondCasedPanelSelection.ts` | confirm + clearance=5 mapping |
| UI Step 1 | `frontend/src/components/workos/intake-v6/IntakeV6AlucobondContourPanel.tsx` | checkbox |
| Early associate | `frontend/src/components/workos/intake-v6/IntakeV6SupportContourGeometryCard.tsx` | preserves existing flag (default false) |
| Binding sync | `frontend/src/lib/intakeV6/svgComponentBindings.ts` | copies flag into binding config |
| Mounting FE | `frontend/src/lib/intakeV6/mountingSolution.ts` | default `frame_clearance_mm: 0` |
| Quote fields | `frontend/src/lib/acmQuoteInput.ts` | clearance field label/helper |
| UI Step 2 | `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | renders clearance |
| Persist BE | `backend/services/svg_component_binding_persistence.py` | flag merge |
| Mounting BE | `backend/services/mounting_solution_service.py` | normalize flag + clearance |
| PD | `backend/services/product_definition_builder_service.py` | canonical boolean |
| Contract | `backend/data/product_system/svg_component_binding_contract.py` | capability `internal_frame` |
| Seed ACM | `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py` | default clearance 0; **no frame component** |
| ACM pack | `backend/scripts/seed_acm_template_pack.py` | quote key `frame_clearance_mm`; comps face/returns/fasteners |
| Doc | `docs/architecture/ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md` | enabled ↔ clearance |

## What is **not** a source for ACP internal frame

| Lookalike | Why excluded |
|-----------|--------------|
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | Premount structure — **independent** of ACP nested internal frame; composition XOR (if any) is mounting-support choice vs Alucobond *panel*, not vs frame |
| SVG role `metal_frame` / „Cadru metalic” | Letter geometry layer suggestion |
| Lightbox `frame_profile` | Different product family |
| Volumetric `mounting_bar_profile` `20x20x1.5` | Letter mounting bars, not ACP casing reinforcement |
| Mock `WELD_FRAME` / „Sudură cadru metalic” | Legacy mock product ops |

## Persistence keys

| Key | Location | Meaning today |
|-----|----------|---------------|
| `internal_frame_enabled` | selection / binding / mounting / PD | Operator marker |
| `frame_clearance_mm` | mounting / quote_input | Gap mm; hardcoded 5 when enabled |
| `geometry_requirements.internal_frame` | SVG binding contract | Capability claim |
| `capabilities[] = "internal_frame"` | SVG binding contract | Same claim |

## Consumers (real)

| Consumer | Uses flag? | Uses clearance? | Uses material? |
|----------|------------|-----------------|----------------|
| Step 2 ACM form | Indirect | Yes | No |
| PD canonical | Yes | No | No |
| Aggregate materials/ops | No | No | No |
| CPP / pricing | No dedicated | Passthrough key only | No |
| Lifecycle stage gate | Surfaces capability | No completeness rule | No |
| Tasking | No | No | No |

## Gaps (source-level)

1. No nested `internal_frame: { material, profile, … }` schema.
2. Binding early path may persist empty `configuration`.
3. Clearance label ≠ reinforcement BOM.
4. Contract capability without Aggregate consumer.
