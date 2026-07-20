# Worklog — Intake V6 SVG Truth & Reinspection RCA

**Date:** 2026-07-20  
**Mode:** read-only root-cause  
**Report:** `docs/audits/2026-07-20_INTAKE_V6_SVG_TRUTH_AND_REINSPECTION_ROOT_CAUSE_AUDIT.md`

---

## Fișiere inspectate (cod)

### Analyzer

- `frontend/src/lib/svgAnalyzer/analyzer/analyzeSvg.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/parseSvg.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/pseudoLayerExpansionGuard.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/layerNameSemantics.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/guessLayerAutoRole.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/refineLayerRoleProposalsWithGeometry.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/analyzePaint.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/analyzeLayers.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/buildLayerRoleConfirmation.ts`

### Intake V6 FE

- `frontend/src/lib/intakeV6/intakeV6ClientSvgImport.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` (`confirmAllLayerRoles`, persist)
- `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.ts`
- `frontend/src/lib/intakeV6/intakeV6ServerUploadHydrationBridge.ts`
- `frontend/src/lib/intakeV6/segmentedBackground.ts`
- `frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts`
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts`
- `frontend/src/lib/intakeV6/goldenParity/goldenSvgFacts.test.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`

### Backend (composition / pricing / segmented)

- `backend/services/intake_v6_product_composition_recommendation_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/acm_segmented_background_service.py` (referenced)
- `backend/data/product_system/svg_component_binding_contract.py` (referenced)

### Docs / evidence

- `docs/audits/2026-07-20_INTAKE_V6_REAL_SVG_RUNTIME_AUDIT.md`
- `docs/audits/_evidence/2026-07-20_intake-v6-real-svg-runtime/**`
- `docs/architecture/product-system/INTAKE_V6_LAYER_ROLE_TAXONOMY_CONTRACT.md`

### Fixtures

- `C:\Users\offic\Desktop\fisiere-teste-svg\litere-cu-fundal-acm-segmentat.svg` (source read)
- `C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg` (via golden path / prior runtime)
- Workspaces compare: `IV6-87B98425`, `IV6-3A52D29C`

---

## Contracte inspectate

| Contract | Constatări |
|----------|------------|
| Layer role taxonomy | Vector Logo ↔ `printed_artwork`; nu definește absence |
| svg_component_binding | LETTER / LOGO / SUPPORT — fără logo_presence |
| segmented_background v1 | panels/joints/bindings; analyzer never auto-confirm |
| Product composition recommendation | logo_layers din roluri logo; support → ACM template |
| Finish artwork_finishes | dual path vs composition |
| Step readiness / hydrate | payload vs client dual authority |

---

## Cauze (confirmat)

| ID | Cauză |
|----|-------|
| P1 | (a) fill-cluster collapse 2 rect → 1 pseudo layer; (b) Confirm All skips segmented propose write-path |
| P2 | refine geometry overwrites printed_artwork on `layerKind:pseudo` logos → support_panel high |
| P3 | false policromie (fill+stroke) + `isArtworkLayer` ignores confirmed support_panel → Vector Logo finish row |
| P7 | LOAD_SUCCESS forces review when roles complete; layers UI selectors absent; not intentional block |
| P4 | CNC group names not in semantic preserve set; uniqueFills>1 blocks re-add |

---

## Ipoteze

| Ipoteză | Rezultat |
|---------|----------|
| Contururi lipsă ⇒ segmented null | **Respinsă** |
| Confirm All ocolește propose | **Confirmată** |
| support_panel din synonym „panel” pe nume logo | **Respinsă** |
| Refine pe pseudo logo | **Confirmată** |
| Vector Logo din template default | **Respinsă** |
| Vector Logo din finish derive + paint | **Confirmată** |
| Straturi intenționat blocat | **Respinsă** |
| API fără svg_analysis | **Respinsă** |
| Golden gradi încă verde | **Respinsă** — FAIL live `{ support_panel: 2 }` |

---

## Impact downstream

Documentat în raport §8: composition, aggregate, materials, pricing, order/execution, UI. Pricing safety **30/100**.

---

## Strategie recomandată

Domain contracts → analyzer refine/paint/provenance → Confirm-All write-path segmented → finish logo_presence → step/hydrate UI. Fără hardcode pe 2 SVG. Fără UI 21st.

---

## Teste necesare

Vezi raport §12. Prioritate: golden gradi verde; ACM zero artwork rows; Confirm All → segmented PROPOSED; reopen layers after LOAD_SUCCESS.

---

## Riscuri

Workspace-uri stale cu roles/composition greșite; oferte cu cost print/ACM inventat; regresie pe Ana Maria real semantic set.

---

## Next step

**STOP.** Owner R1–R5. Nu implementare. Nu redesign UI.
