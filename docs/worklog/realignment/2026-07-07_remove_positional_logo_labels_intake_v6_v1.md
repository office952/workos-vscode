## TASK

REMOVE_POSITIONAL_LOGO_LABELS_FROM_INTAKE_V6_V1

## HEAD before work

- `6527ac2`

## Safety state

- `git status -sb`: clean tracked worktree; repo already had unrelated historical untracked files
- `git diff --cached --name-only`: empty
- `git status --short --untracked-files=no`: empty

## Root cause

- Positional logo naming was produced in `assignRasterLogoLayers(...)` and `assignStrokeOnlyLogoLayers(...)` in [frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts).
- Existing operator-facing surfaces reused those positional names directly via:
  - [frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.ts)
  - [frontend/src/lib/intakeV6/intakeV6LayerDisplayLabel.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerDisplayLabel.ts)
  - [frontend/src/components/workos/intake-v6/layerColorDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/layerColorDisplay.ts)
  - [frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx)

## Fix summary

- Replaced positional operator-visible logo naming with deterministic neutral numbering:
  - first logo: `Logo 1`
  - second logo: `Logo 2`
  - third logo: `Logo 3`
- Kept role identity unchanged: `Vector Logo`
- Kept internal ids and payload keys unchanged where they still serve as stable technical identifiers
- Applied numbering by analyzer/order-of-appearance, not by left/right/center geometry wording

## Files changed

- [frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts)
- [frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.ts)
- [frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts)
- [frontend/src/lib/intakeV6/intakeV6LayerDisplayLabel.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerDisplayLabel.ts)
- [frontend/src/components/workos/intake-v6/layerColorDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/layerColorDisplay.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6ArtworkOnlyDecisionPanel.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ArtworkOnlyDecisionPanel.tsx)
- [frontend/src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.tsx)
- [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx)
- [frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx)
- [frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts)
- [frontend/src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx)
- [frontend/src/components/workos/intake-v6/layerColorDisplay.test.ts](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/layerColorDisplay.test.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx)
- [frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.test.tsx)

## Tests run

- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx --reporter=verbose`
  - PASS
- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.test.tsx -t "opens inspect dialog with layer legend from preview button|highlights preview geometry when hovering a layer legend row|highlights left and right logo layers independently" --reporter=verbose`
  - PASS
- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/components/workos/intake-v6/layerColorDisplay.test.ts src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx --reporter=verbose`
  - PASS
- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx src/components/workos/intake-v6/layerColorDisplay.test.ts src/lib/intakeV6/intakeV6OperatorUiDisplay.test.ts --reporter=verbose`
  - PASS
- `git diff --check`
  - PASS

## Visual verification

- Route checked: `http://127.0.0.1:3000/intake-v6/0cfafcb6-ea95-4ff5-9799-bbd88b24bf71/operator`
- Step checked: `Straturi`
- Verified visible surfaces:
  - `Decizii straturi`: `Grup detectat: Logo 1`
  - `Atenție analiză`: chip `Logo 1`
  - `Culori detectate`: `Logo 1`
  - `Compozitie produs propusa`: `Straturi: Logo 1`
- Verified role dropdown remains `Vector Logo`
- No mutating workflow action was triggered

## Forbidden scope confirmation

- No Pricing changes
- No Quote/Order changes
- No Execution changes
- No ProductAggregate / TaskGraph / ExecutionPlan changes
- No DB / seed / migration work
- No Logo offerability activation
- No component root / quote rule changes
- No analyzer geometry detection rewrite beyond label naming/display