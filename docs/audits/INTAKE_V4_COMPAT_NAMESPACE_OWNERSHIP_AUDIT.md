# Intake V4 Compat Namespace Ownership Audit

## Verdict
BLOCKED_NEEDS_ARCHITECTURE_GO

## Current State
- Remaining V4 test count: `1`
- Remaining V4 test: `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`
- Compat namespace: `@/lib/intakeV4/*`
- Known reason: `src/lib/intakeV4` exists physically but is empty; `svgAnalyzer` still imports compat helpers through that namespace, while the actual helper implementations live under `src/lib/intakeV6`.

## Namespace Inventory
| File | Exports | Logic owner | Consumers | Classification | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `src/lib/intakeV4/` | none | none | none directly; all imports fail resolution | `BLOCKED_NEEDS_ARCHITECTURE_DECISION` | Keep namespace unresolved for now; decide whether to materialize or retire the compat namespace before any extraction work. |
| logical `@/lib/intakeV4/intakeV4LayerRoleBridge` | `confirmAllSuggestedLayerRoles` and bridge helpers are expected by consumers; actual implementations exist in `src/lib/intakeV6/intakeV4LayerRoleBridge.ts` and V6 equivalent exists in `src/lib/intakeV6/intakeV6LayerRoleBridge.ts` | `intakeV6` compat over `svgAnalyzer` confirmation types | `svgAnalyzer` tests import the missing compat path | `COMPAT_PUBLIC_SURFACE`; `SVG_ANALYZER_DEPENDENCY`; `BLOCKED_NEEDS_ARCHITECTURE_DECISION` | Do not extract in isolation; decide whether `svgAnalyzer` should depend on a compat namespace at all. |
| logical `@/lib/intakeV4/intakeV4QuoteGeometry` | `extractQuoteGeometryFromAnalyzer`, `resolveQuoteGeometryForWorkspace`, related quote geometry types; actual implementations exist in `src/lib/intakeV6/intakeV4QuoteGeometry.ts` and V6 wrapper exists in `src/lib/intakeV6/intakeV6QuoteGeometry.ts` | mixed: `intakeV6` compat surface over analyzer-derived geometry | `svgAnalyzer` tests and `anaMariaPerimeterDiagnostic.ts` import the missing compat path | `COMPAT_PUBLIC_SURFACE`; `SVG_ANALYZER_DEPENDENCY`; `BLOCKED_NEEDS_ARCHITECTURE_DECISION` | Keep unchanged; this is a deeper namespace coupling point than `LayerRoleDisplay`. |
| logical `@/lib/intakeV4/intakeV4LayerRoleDisplay` | `buildLayerRoleRowsForDisplay`, `countArtworkLayers`, `countProductionGeometryLayers`; actual implementations exist in `src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`, with V6 re-export in `src/lib/intakeV6/intakeV6LayerRoleDisplay.ts` | mixed: analyzer report helpers plus compat operator labels | `svgAnalyzer` tests and one remaining `intakeV6` V4 test | `SHARED_HELPER_CANDIDATE`; `BLOCKED_NEEDS_ARCHITECTURE_DECISION` | Do not move alone; resolve compat namespace ownership first. |

## Import Consumers
| Consumer | Zone | Import | Test/runtime | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts` | `svgAnalyzer` | `intakeV4LayerRoleBridge`, `intakeV4LayerRoleDisplay` | test | `FAIL_IMPORT_RESOLUTION` | Fails before execution on missing `@/lib/intakeV4/intakeV4LayerRoleBridge`. |
| `src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts` | `svgAnalyzer` | `intakeV4LayerRoleBridge`, `intakeV4QuoteGeometry`, `intakeV4LayerRoleDisplay` | test | `FAIL_IMPORT_RESOLUTION` | Couples analyzer regression tests to compat namespace. |
| `src/lib/svgAnalyzer/analyzer/anaMariaPerimeterDiagnostic.ts` | `svgAnalyzer` | `intakeV4QuoteGeometry` | runtime helper | `IMPORT_AT_RISK` | Non-test analyzer helper depends on compat quote geometry type and extractor. |
| `src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts` | `svgAnalyzer` | `intakeV4LayerRoleBridge`, `intakeV4QuoteGeometry` | test | `FAIL_IMPORT_RESOLUTION` | Same missing compat namespace failure mode. |
| `src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts` | `svgAnalyzer` | `intakeV4LayerRoleBridge`, `intakeV4LayerRoleDisplay`, `intakeV4QuoteGeometry` | test | `FAIL_IMPORT_RESOLUTION` | Highest-signal regression gate, but currently tied to broken compat imports. |

## Ownership Findings
- intakeV6 findings:
  - Actual implementations for the referenced compat helpers live under `src/lib/intakeV6`, not under `src/lib/intakeV4`.
  - `intakeV6LayerRoleBridge.ts` and `intakeV6QuoteGeometry.ts` provide explicit V6 surfaces, but `intakeV6LayerRoleDisplay.ts` is still only a re-export of the V4-named helper.
  - The remaining V4 test in `intakeV6` covers `LayerRoleDisplay` locally and passes, so the cleanup closeout state is stable.
- svgAnalyzer findings:
  - `svgAnalyzer` has direct consumers of the compat namespace in four tests plus one analyzer helper.
  - The imports are not cosmetic: they cover layer role confirmation, quote geometry extraction, and layer-role display rows/counts.
  - Because `anaMariaPerimeterDiagnostic.ts` is not a test, the coupling is broader than regression fixtures alone.
- shared/helper findings:
  - `countArtworkLayers` and `countProductionGeometryLayers` are pure analyzer-report helpers and look like future shared-helper candidates.
  - `buildLayerRoleRowsForDisplay` is less neutral because it formats operator labels via `INTAKE_V4_LAYER_ROLE_OPTIONS`.
  - Any future shared extraction should separate pure analyzer counting from operator-facing display labels instead of moving the current compat module intact.
- broken/import-risk findings:
  - TypeScript and Vite alias config only define `@/* -> ./src/*`; there is no dedicated alias for `@/lib/intakeV4/*`.
  - Since `src/lib/intakeV4` is empty, current compat imports are structurally broken and fail module resolution.
  - The failure is preexisting and architectural, not caused by the recent cleanup work.

## Test Results
- LayerRoleDisplay V4: `PASS` (`npm.cmd exec vitest run src/lib/intakeV6/intakeV4LayerRoleDisplay.test.ts`) — `1` file, `3` tests.
- svgAnalyzer compat import tests: `FAIL_PREEXISTING_IMPORT_RESOLUTION` for:
  - `src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts`
  - `src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts`
  - `src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts`
  - `src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts`
  - Failure mode: `Failed to resolve import "@/lib/intakeV4/intakeV4LayerRoleBridge"`.
- V6 active: `PASS` (`6` files, `26` tests).
- V6 compat contract: `PASS` (`3` files, `15` tests).
- build: `PASS` with known historical CSS/config/chunk warnings.
- tsc: `STATUS_ONLY_UNRELIABLE_FROM_TERMINAL`; shell did not produce a stable transcript, but no local diagnostics were reported on the touched audit scope.

## Decision Options
### Option A — Keep compat namespace accepted
Pros:
- No runtime risk.
- Preserves current cleanup closeout state.
- Avoids partial extraction of one helper while bridge/quote geometry remain unresolved.
Cons:
- Leaves broken compat imports in `svgAnalyzer` unaddressed.
- Keeps architecture ambiguity alive.
When to choose:
- When the immediate goal is stability and no dedicated architecture slot exists yet.

### Option B — Extract shared compatibility layer
Pros:
- Could separate pure analyzer helpers from operator-facing compat display logic.
- Reduces `svgAnalyzer` ↔ `intakeV6` coupling if done as a broader namespace plan.
Cons:
- Requires deliberate redesign of public ownership and naming.
- Cannot be done safely as a read-through move of the current compat files.
When to choose:
- When a follow-up task is allowed to redesign the whole compat namespace, not just one helper.

### Option C — Move selected helpers to svgAnalyzer
Pros:
- Natural fit for pure analyzer counts and analyzer regression tests.
- Could eventually localize analyzer-specific test dependencies.
Cons:
- `LayerRoleDisplay` currently mixes analyzer data with `intakeV4` operator labels.
- Would not solve `LayerRoleBridge` and `QuoteGeometry` compat imports still used by `svgAnalyzer`.
When to choose:
- Only after splitting pure analyzer helpers from operator-facing compat surfaces.

### Option D — Remove namespace after migration
Pros:
- Cleanest end-state.
- Eliminates compat import ambiguity completely.
Cons:
- Requires migrating all `svgAnalyzer` compat imports and possibly materializing equivalent non-compat APIs first.
- Larger architecture task than the current audit allows.
When to choose:
- After the ownership of bridge, quote geometry, and display helpers is explicitly redesigned and tested.

## Recommendation
BLOCKED_NEEDS_ARCHITECTURE_GO

## Next Task
Run a dedicated architecture decision task for the compat namespace `@/lib/intakeV4/*`, focused on whether `LayerRoleBridge`, `QuoteGeometry`, and `LayerRoleDisplay` should remain an accepted compat namespace, be split into shared helpers plus operator display surfaces, or be migrated behind explicit non-compat APIs before any import rewiring.

## Compat Namespace Bridge Restoration

- Verdict: `PASS`
- Purpose:
  - restore explicit `src/lib/intakeV4/*` compatibility shims
  - keep real implementation in `src/lib/intakeV6`
- Shims created:
  - `src/lib/intakeV4/intakeV4LayerRoleBridge.ts`
  - `src/lib/intakeV4/intakeV4QuoteGeometry.ts`
  - `src/lib/intakeV4/intakeV4LayerRoleDisplay.ts`
- Behavior change:
  - none
- Import resolution status:
  - restored for the currently known compat consumers of `@/lib/intakeV4/*`
- svgAnalyzer tests:
  - `PASS`
  - `npm.cmd exec vitest run src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts`
  - rezultat: `4` fisiere, `19` teste
- LayerRoleDisplay V4 test:
  - `PASS`
  - `1` fisier, `3` teste
- V6 compat contract tests:
  - `PASS`
  - `3` fisiere, `15` teste
- V6 active:
  - `PASS`
  - `6` fisiere, `26` teste
- build:
  - `PASS`
- tsc:
  - global: `NOT RELIABLE_FROM_TERMINAL`
  - filtered: `NOT RELIABLE_FROM_TERMINAL`
  - shell-ul curent nu a produs transcript stabil pentru `tsc.cmd`, dar shim-urile noi nu au erori locale in `get_errors`
- Remaining V4 test count:
  - `0 / 1 / 1`
- Next recommendation:
  - keep the restored compat namespace as explicit bridge infrastructure, then handle ownership redesign separately from naming cleanup
