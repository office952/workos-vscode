# BUILD-WORKOS-FORM-FLOW-AUDIT-AND-PROPOSAL

**Date:** 2026-06-07  
**Build status:** **PASS**  
**Type:** Audit + proposal only — **no runtime code changes**  
**This build commit:** not committed (per user rule)  
**Pre-flight:** Working tree clean @ `1c626ff` (Finalization Pack committed)

## Summary

Read-only audit of WorkOS commercial/product intake forms with a single coherent **staged operator workflow** proposal for TPL-VOLUMETRIC-LETTERS. Identifies why intake feels dead (SVG/layer/geometry/save/readiness gaps) despite stabilized commercial spine downstream.

## Files inspected (representative)

| Area | Paths |
|------|-------|
| Intake pages | `frontend/src/pages/WorkIntake.tsx`, `IntakeDetail.tsx` |
| Template workspace | `frontend/src/components/workos/templateIntakeWorkspace/*` |
| Spec / vector forms | `Product001IntakeSpecEditor.tsx`, `VectorIntakeFastAskPanel.tsx`, `SvgLayerAnalysisPanel.tsx` |
| Quote surfaces | `QuoteWizard.tsx`, `VolumetricLettersQuoteFlow.tsx`, `Quotes.tsx` |
| Registry / admin | `ProductSystem.tsx`, `Pricing.tsx`, `Inventory.tsx`, `Clients.tsx`, `ClientWorkspace.tsx` |
| Lib / readiness | `svgGeometryParser.ts`, `mapSvgGeometryToSpec.ts`, `volumetricQuoteFlowState.ts`, `volumetricQuoteReady.ts`, `intakeReadiness.ts`, `intakeReadinessStages.ts`, `volumetricIntakeFormPrep.ts` |
| Backend contracts | `backend/validators/intake_product_spec.py`, `routers/intake_requests.py`, `quotes.py`, `vector_assets.py`, `schemas/product_readiness.py`, `schemas/vector_assets.py` |
| Prior art | `docs/architecture/INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md`, `TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md` |

## Files created

| File | Purpose |
|------|---------|
| `docs/audits/WORKOS_FORM_FLOW_AUDIT_AND_FLUID_PROPOSAL.md` | Full audit + staged architecture proposal + roadmap |
| `docs/qa/BUILD_WORKOS_FORM_FLOW_AUDIT_AND_PROPOSAL.md` | This QA note |

## Runtime changes

**None.** No frontend, backend, test, or config modifications.

## Main problems (top 5)

1. Fast-ask **Apply does not persist** — readiness stale until manual Save.
2. **SVG geometry MVP** does not supply area/perimeter — operator must manual entry with weak guidance.
3. **Layer mapping** lacks single confirm + repair CTA tied to readiness.
4. **Three+ readiness vocabularies** — list page, legacy gate, staged gates, quote_gate disagree.
5. **Duplicate vector/quote surfaces** — intake fast-ask vs Vector Studio vs QuoteWizard SvgLayerAnalysisPanel.

## Proposed architecture (one sentence)

**Staged operator workflow:** Context → Vector → Geometry → Production → Simulate → Quote handoff, with repair panel mapping every blocker to a field + CTA, autosave on vector boundaries, and typed QuoteWizard handoff from saved `product_spec_json`.

## Recommended next substantial build

**Build 1: SVG Intake Upload + Layer Mapping + Geometry Persistence** — make vector stage feel alive (parse banner, mapping persist, Apply autosaves) without CostEngine or quote_gate policy changes.

## Confidence score

**High (0.85)** for problem diagnosis — grounded in code inspection and prior intake automation audit.  
**Medium (0.70)** for staged UX proposal — needs owner answers on auto-confirm template, parser v2 investment, and pricing controls in embedded quote tab.

## FigJam

**Skipped** — no Figma boards/diagrams per build constraints; reference board `SQ1OvAy2AKV71WJhCaKzJV` unchanged.

## Hard constraints verified

- [x] No CostEngine / pricing formula changes
- [x] No readiness policy / quote / order / execution spine changes
- [x] No unsupported template activation
- [x] No UI implementation in this build
