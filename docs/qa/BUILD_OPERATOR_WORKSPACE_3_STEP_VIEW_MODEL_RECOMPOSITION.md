# BUILD_OPERATOR_WORKSPACE_3_STEP_VIEW_MODEL_RECOMPOSITION

## Context

Branch: `local/integration-pr4-plus-svg-path`

Atoms v20 audit verdict: **IMPLEMENTABLE WITH ADAPTATION**.

Operator Workspace Intake V3 funcționează tehnic (SVG upload/drop, DOCTYPE sanitization, re-upload layer role rebuild, path geometry, lighting suggestion, PSU allocator, materials read-only, quote guarded), dar UI-ul actual cu **10 taburi** amestecă flow operator cu diagnostic tehnic.

Acest build recompune presentation layer-ul într-un flow **Layers → Review → Confirm**, alimentat de un **view-model/adaptor** nou — nu de formularul vechi rearanjat.

## De ce nu portăm Atoms direct

- HTML-ul Atoms v20 conține feature-uri respinse: voice, AI copilot, confetti, particles, sound, theme toggle, cost estimate mock.
- Valorile din prototype sunt inventate (module count, dimensiuni, materiale).
- Dropdown-uri generice (illumination mode, LED strip) contrazic contractul volumetric WorkOS.
- Copierea CSS/HTML nu produce adapter curat între API real și UI.

## De ce nu păstrăm formularul vechi ca UI principal

- 10 taburi + Technical route (25-step) creează state stale, duplicate calculations, operator confusion.
- Tab-urile actuale expun panouri dry-run, guard policy, raw metrics — utile diagnostic, toxice ca flow principal.
- Rearanjare vizuală a tab-urilor păstrează aceleași dependențe și aceleași riscuri de date stale.

## Boundary

### Permis (acest build)

- View-model/adaptor frontend
- Teste unitare Vitest
- QA doc
- Păstrare tab-uri existente până la Faza B (fără eliminare în Faza A)
- Păstrare Technical route ca diagnostic
- Reutilizare helpers/API existente

### Interzis

- Backend / API contract changes
- CostEngine, Inventory, StockMovement
- ExecutionTask / ExecutionPlan, PO / SupplierOrder
- Parser SVG / security change
- Lighting / PSU / reserve / allocator change
- Port HTML Atoms direct
- Voice / AI / confetti / particles / cost mock
- Eliminarea tab-urilor în Faza A

## Structura view-model

Fișier: `frontend/src/lib/intakeV3/operatorWorkspaceThreeStepViewModel.ts`

Funcții:

- `buildOperatorWorkspaceThreeStepViewModel(input)`
- `buildOperatorWorkspaceThreeStepViewModelFromState(state, options)`

Tip exportat: `OperatorWorkspaceThreeStepViewModel`

Secțiuni:

| Secțiune | Sursă date |
|----------|------------|
| `header` | `deriveOperatorHeaderInfo`, `rawSvgAnalysis`, path geometry notices |
| `progress` | layer pending count, readiness quote status, current step |
| `contextualBanner` | reguli operator (pending layers, upload missing, quote blocked) |
| `layersStep` | `layerRoleConfirmation`, upload helpers |
| `reviewStep.geometry` | `geometryMetrics`, `pathPerimeterClassification` |
| `reviewStep.lighting` | `lightingForm` (optional input), module count derivation, PSU calc |
| `reviewStep.materials` | `materialBreakdown` (read-only groups) |
| `reviewStep.readiness` | `buildResult.preview` readiness / blockers |
| `reviewStep.advancedCollapsed` | link Technical route only |
| `confirmStep` | summary rows, pending layers, quote guard |
| `navigation` | step gating (layers complete before next) |

### Reguli view-model

1. Layer name = evidence; confirmed role = production truth.
2. Fără valori inventate — `null` / `blocked` / `unknown` când lipsesc date.
3. Volumetric (`TPL-VOLUMETRIC-LETTERS`): frontlit + modules locked; puteri 0.72 / 1 / 1.44 W; pitch 100 mm; reserve 30% din form calc.
4. Materials always `readOnly: true`.
5. Technical route doar în `advancedCollapsed.technicalRouteHref`.

### Gap documentat (Faza A)

**Lighting form** nu este încă în `useIntakeV3OperatorWorkspace` — tab-ul Lighting îl încarcă via `fetchIntakeV3LightingPlan`. View-model acceptă `lightingForm` optional în input; Faza B va ridica sau injecta acest slice.

## Componente vechi — logică/helper (păstrate)

- `useIntakeV3OperatorWorkspace`
- `operatorWorkspaceHelpers`, `layerRoleConfirmationContracts`
- `operatorSvgUploadHelpers`, `pathGeometryUploadNotice`, `layerRoleReuploadNotice`
- `operatorLightingPlanForm`, `lightingModuleCountDerivation`
- `operatorWorkspaceLoadSections`, `operatorWorkspacePresentation`
- `blockerMessages`, `deriveOperatorHeaderInfo`

## Componente vechi — NU ca UI principal

- `IntakeV3OperatorWorkspaceTabs` + cele 10 tab panels ca shell principal
- `IntakeV3ProductionModelReviewPanel` în flow Layers (duplicare formular)
- `IntakeV3FlowStepper`, quote dry-run panels în flow operator
- `IntakeV3App` / Technical route ca navigare principală

## Faza A — livrables

| Fișier | Rol |
|--------|-----|
| `operatorWorkspaceThreeStepViewModel.ts` | Adapter |
| `operatorWorkspaceThreeStepViewModel.test.ts` | Teste pure |
| `docs/qa/BUILD_OPERATOR_WORKSPACE_3_STEP_VIEW_MODEL_RECOMPOSITION.md` | Acest doc |

### Teste Faza A

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/operatorWorkspaceThreeStepViewModel.test.ts
```

Scenarii minime:

1. Workspace fără SVG — upload available, quote blocked
2. SVG Corel parsed — layer keys reale, fără stale names
3. Layer roles incomplete — banner + blockers
4. Geometry + lighting — perimeter, module suggestion, volumetric lock
5. Confirm — materials read-only, quote guard
6. Technical route — doar advancedCollapsed
7. Fără câmpuri Atoms respinse

## Faza B — următorul pas

1. `IntakeV3OperatorThreeStepWorkspace.tsx` — shell (progress, banner, footer nav)
2. `OperatorWorkspaceLayersStep.tsx`
3. `OperatorWorkspaceReviewStep.tsx`
4. `OperatorWorkspaceConfirmStep.tsx`
5. Integrare în `IntakeV3OperatorWorkspaceApp` (feature flag sau switch)
6. Teste component smoke; păstrare tab-uri behind fallback până la acceptance

## PASS / FAIL — Faza A

### PASS

- View-model + teste verzi
- Fără modificări backend
- Fără modificări tab-uri existente
- QA doc complet
- Technical route doar ca href diagnostic în view-model

### FAIL

- Mock values hardcodate în producție view-model
- Modificări API/backend
- Eliminare tab-uri în Faza A
- Câmpuri voice/AI/cost mock în structură

## Faza A result

**PASS — 3-step view-model foundation ready**

- `vitest run src/lib/intakeV3/operatorWorkspaceThreeStepViewModel.test.ts` — **8 passed**
- Fișiere noi: view-model, teste, acest QA doc
- Fără modificări backend; tab-uri existente neschimbate
- Gap lighting form documentat — input optional până la Faza B

## Faza B — UI shell (Full UI)

### Implementat

| Componentă | Rol |
|------------|-----|
| `three-step/IntakeV3OperatorThreeStepWorkspace.tsx` | Shell principal: step state, view-model, footer nav |
| `OperatorWorkspaceProgressBar.tsx` | Progress Layers / Review / Confirm |
| `OperatorWorkspaceContextBanner.tsx` | Banner contextual rule-based |
| `OperatorWorkspaceLayersStep.tsx` | Upload, notices, layer chips, layer role setup |
| `OperatorWorkspaceReviewStep.tsx` | Geometry, lighting+PSU, materials RO, readiness |
| `OperatorWorkspaceConfirmStep.tsx` | Summary, quote guard, legacy tabs collapsed |
| `IntakeV3OperatorLegacyTabPanels.tsx` | Tab-uri vechi — diagnostic only |
| `useOperatorWorkspaceLightingForm.ts` | Lighting state shared Review step |

`IntakeV3OperatorWorkspaceApp.tsx` folosește shell 3-step ca UI principal.

### Tab-uri vechi

- **Nu** mai sunt navigarea principală.
- Rămân în cod în `IntakeV3OperatorLegacyTabPanels`, accesibile doar din `<details>` collapsed pe Confirm step (`intake-v3-operator-legacy-tabs`).
- Technical route: link diagnostic în header + Review advanced + Confirm legacy.

### Teste Faza B

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/operatorWorkspaceThreeStepViewModel.test.ts src/pages/IntakeV3OperatorWorkspaceApp.test.tsx src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorWorkspaceFileDrop.test.ts src/lib/intakeV3/layerRoleReuploadNotice.test.ts
```

Rezultat: **41 passed** (8 view-model + 29 app + 2 file-drop + 2 reupload notice).

### Runtime smoke

Recomandat manual pe `http://localhost:3000/intake-v3/e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf/operator` cu stack pornit.

### Limitări Faza B

- Finishes / production setup rămân în legacy tabs (nu în flow principal 3-step).
- Layer finish sub-groups — confirmare rol în Layers; finish detaliat în legacy Finishes tab.
- Visual acceptance owner — următor pas după commit.

## Faza B result

**PASS — 3-step Operator Workspace implemented**
