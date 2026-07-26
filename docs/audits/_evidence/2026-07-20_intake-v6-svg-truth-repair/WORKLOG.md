# Worklog — INTAKE_V6_SVG_TRUTH_CONTRACT_REPAIR_V1

**Date:** 2026-07-20  
**Mode:** implementation (forward-fix only)  
**Commit:** (see git after commit)

## Plan executed

R1–R5 owner decisions → analyzer provenance + refine + paint → logo_presence → Confirm All segmented path → P7 step intent → tests → runtime both fixtures → dry-run remediation → commit.

## Files modified (code)

- `frontend/src/lib/svgAnalyzer/analyzer/refineLayerRoleProposalsWithGeometry.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/artworkLogoCandidate.ts` (+ test)
- `frontend/src/lib/svgAnalyzer/analyzer/analyzePaint.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/analyzeLayers.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/buildAnalysisReport.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/types.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts`
- `frontend/src/lib/intakeV6/intakeV6LogoPresence.ts` (+ test)
- `frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts`
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts`
- `frontend/src/lib/intakeV6/intakeV6SupportPanelConfirmationPath.ts` (+ test)
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/lib/intakeV6/intakeV6Contracts.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.ts`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.p7.test.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`

## Contract final

- Support assembly = 1 component; panels[] = component-owned geometries
- `support_panel` high requires cumulative evidence; artwork/logo excluded from refine
- `logo_presence`: detected_confirmed | optional_absent | slot_available
- Confirm All = same path as manual support confirmation
- `operatorStepIntent` preserves Straturi reopen across LOAD_SUCCESS

## Runtime workspaces created

| Case | Code | ID |
|------|------|-----|
| ACM | IV6-379CEB03 | 646b746d-94c8-41e1-be27-baaeabd26457 |
| gradi | IV6-B6C01680 | 3f7d1c7a-a12b-488e-8f70-12df8de0795f |

## Tests

- goldenSvgFacts PASS
- logo presence / support path / P7 / ana-maria PASS
- runtime both fixtures PASS

## Dry-run remediation

`dry-run-remediation.json` — 2 historic audit WS flagged; **no data modified**.

## Remaining

- Owner-gated historic remediation
- Resume UI system audit after truth soak
- Expand SQL inventory of all suspect workspaces
