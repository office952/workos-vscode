# Phase 3A.1 Product Truth Draft Builder Hardening Worklog

**Date:** 2026-07-01  
**Status:** IMPLEMENTED_AND_VALIDATED  
**Scope:** frontend/lib pure TypeScript hardening, fixtures, tests, docs, docs-only sample payload, and static/read-only validation. No API, no persistence, no runtime payload save, no Intake V6 flow/gating changes, no backend, no ProductDefinition runtime, no downstream materialization.

## Sources read before coding

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_FULL_E2E_PRODUCT_TRUTH_TO_EXECUTION_ALIGNMENT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `docs/worklog/realignment/2026-07-01_phase_3a_product_truth_draft_builder.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_full_e2e_product_truth_to_execution_alignment.md`
- `docs/worklog/realignment/2026-07-01_phase_2_support_mounting_contract_alignment.md`
- `docs/worklog/realignment/2026-07-01_phase_2_gap_closure_existing_form_ui_only.md`

## Current builder package coverage map before changes

| File | Responsibility | Current behavior | Existing test coverage | Missing coverage | Risk | Planned change |
|---|---|---|---|---|---|---|
| `productTruthTypes.ts` | Defines draft, field, state, source, issue, readiness, and builder input types. | Covers state enum, component branches, field refs, blockers/warnings as codes. Source refs are stringly typed; issues lack affected field/source type and quote/order/execution booleans. | Indirect compile coverage only. States exercised indirectly: `suggested`, `confirmed`, `fallback`, `hydrated`, `blocked`, `not_applicable`, `unknown`. | `manual` and `warning` states not directly covered; source model not typed; issue metadata lacks `affected_component`, `affected_field`, `source`, `quote_blocker`, `order_blocker`, `execution_blocker`. | Canonical contract can drift because blockers are only gate arrays and strings. | Add conservative typed source model and expanded issue metadata without backend/API schema. |
| `productTruthDraftBuilder.ts` | Builds pure in-memory Product Truth draft from local Intake V6-like input. | Maps metadata, SVG, geometry, layers, face fallback, back, return/cant, finish, artwork print/lamination from execution type, lighting/electrical defaults, support/mounting warning bridge, pricing boundary. | 5 builder tests: suggestions block, face defaults fallback, print/lamination split from `print_laminate`, bar mounting not confirmed support, downstream readiness disabled. | Missing fixtures/tests for confirmed role truth, ignored artwork, artwork-only, print without laminate, laminate without print, finish target missing, missing cant depth, sanfren selected, direct_wall mounting only, SVG support role, cable defaults order/execution, no commercial price, CostEngine boundary, immutability/determinism. | Builder may silently overclaim canonical readiness or miss source-state distinctions in untested branches. | Harden mapping for explicit artwork decisions, finish target, issue metadata, electrical order/execution, support evidence, deterministic behavior. |
| `productTruthReadiness.ts` | Produces local read-only readiness preview from draft blockers/warnings. | Review/internal draft derive from gate blockers. Commercial/snapshot/order/aggregate/execution are forced false with `PHASE_3A_PREVIEW_ONLY`. | 1 readiness test for review true with confirmed fixture and downstream false. | Does not expose full blocker objects; no issue metadata; no tests for commercial blockers caused by artwork, finish target, support bridge, or unconfirmed roles. | Readiness preview could become too coarse to enforce canonical contract before persistence. | Return explicit issue summaries with severity/message/component/field/source and flags while still not wiring into UI gating. |
| `productTruthFixtures.ts` | Provides deterministic gradi-curat inputs. | Two fixtures: unconfirmed suggestions and confirmed roles with steel bars. | Used by all 6 tests. | Required fixtures A-J missing; no ignored/artwork-only, print no laminate, laminate without print, missing finish target, execution-only electrical, direct wall complete-review-like, support SVG role. | Contract coverage remains too small for canonical payload confidence. | Add deterministic fixture matrix with aliases requested by task and variants for edge cases. |
| `productTruthDraftBuilder.test.ts` | Builder behavior tests. | 5 tests. Covers state separation for analyzer roles, owner default fallback, print/lamination split for encoded value, support/mounting split, downstream disabled. | Missing 25+ required behaviors, issue metadata, no mutation, deterministic timestamp. | Regression risk high as builder grows. | Expand to at least 20 business-named tests, targeting all requested behaviors. |
| `productTruthReadiness.test.ts` | Readiness evaluator tests. | 1 test. Covers summary blockers and Phase 3A preview-only downstream false. | Missing commercial false for suggestions/artwork/finish/support; missing quote/order/aggregate/execution invariants across fixtures; no blocker metadata tests. | Readiness preview may diverge from Product Truth readiness boundary docs. | Expand focused readiness tests and assert issue summaries. |

## Explicit coverage gaps identified

| Area | Current coverage | Gap | Planned hardening |
|---|---|---|---|
| States tested | `suggested`, `confirmed`, `fallback`, `hydrated`, `blocked`, `not_applicable`, `unknown` | `manual`, `warning`; explicit ignored/artwork-only source state | add fixtures and tests for ignored/manual/operator decisions and warning fields. |
| Components tested | face, artwork, support, mounting, readiness | back, return_cant, finish target, lighting, electrical, pricing_boundary not directly asserted | add component assertions for all branches. |
| Blockers/warnings tested | `LAYER_ROLES_INCOMPLETE`, face fallback blockers, support bridge warning, print/lamination encoded warning, `PHASE_3A_PREVIEW_ONLY` | missing finish target, missing cant depth, artwork decision, laminate-without-print, support SVG role, order/execution-only electrical | add issue codes and tests. |
| Support/mounting split | bar mounting not confirmed support | direct_wall and SVG support roles not covered; bridge blocker/warning semantics coarse | test direct_wall, steel/aluminum bridge, SVG support evidence. |
| Print/lamination | `print_laminate` splits both true | print without laminate, laminate without print not covered | add explicit input booleans and execution types. |
| Artwork decision | printed artwork suggestion only indirectly | ignored and artwork-only decisions missing | add explicit `operator_decision` input and mapping. |
| Downstream readiness false | covered for bar mounting fixture | not covered across complete-review-like fixture and sample payload | add readiness tests across fixtures. |
| Mutation/determinism | not covered | builder could mutate nested input or vary timestamp | add deep clone/freeze style tests and timestamp override assertions. |

## Initial local hypothesis

The builder can be hardened without touching runtime if canonical issue metadata and deterministic fixture inputs are added locally. The cheap falsifying check is an expanded focused Vitest suite: at least 20 tests must pass while static boundary grep shows no API, persistence, pricing, ProductDefinition, aggregate, or execution terms beyond forbidden/readiness labels.

## Implementation notes

Implemented in the frontend-only Product Truth package:

- `productTruthTypes.ts`
	- Added typed `ProductTruthSourceKind`.
	- Required `sourceKind` on source refs.
	- Added issue metadata: `affectedComponent`, `affectedField`, `source`, `quoteBlocker`, `orderBlocker`, `executionBlocker`.
	- Added explicit fields for `artworkDecision`, `finishTarget`, `extraCableOrSiteDetails`, and readiness `blockerIssues` / `warningIssues`.
	- Expanded builder inputs for face material/thickness confirmation, artwork decisions, print/lamination booleans, finish target, mounting scope, support truth, PSU placement, and extra cable/site quote scope.
- `productTruthDraftBuilder.ts`
	- Emits typed source refs and richer issue metadata.
	- Keeps analyzer-only roles suggested and operator decisions confirmed/manual.
	- Preserves plexiglas opal 3 mm as fallback unless explicitly confirmed.
	- Preserves Forex 10 no-sanfren default and manual sanfren selection.
	- Adds blockers for missing finish target and missing active return/cant depth.
	- Separates artwork decisions from printed artwork suggestions.
	- Separates print and lamination booleans and warns for lamination without print.
	- Keeps support and mounting split; bar mounting remains suggestion/bridge only.
	- Preserves cable defaults and marks PSU/site/extra cable as order/execution-only unless quote scoped.
	- Keeps pricing boundary preview-only with no commercial price/CostEngine data.
- `productTruthReadiness.ts`
	- Keeps downstream flags false with `PHASE_3A_PREVIEW_ONLY`.
	- Adds full blocker/warning issue arrays to readiness flags.
- `productTruthFixtures.ts`
	- Added deterministic fixture matrix A-J:
		`gradiCuratUnconfirmedFixture`, `gradiCuratConfirmedRolesFixture`, `gradiCuratCompleteReviewLikeFixture`, `gradiCuratSupportMountingMismatchFixture`, `gradiCuratArtworkIgnoredFixture`, `gradiCuratArtworkOnlyFixture`, `gradiCuratPrintNoLaminateFixture`, `gradiCuratLaminateWithoutPrintWarningFixture`, `gradiCuratMissingFinishTargetFixture`, `gradiCuratExecutionOnlyElectricalFixture`.
	- Preserved legacy aliases for existing tests/imports.
- `productTruthDraftBuilder.test.ts`
	- Expanded to 26 focused builder behavior tests.
- `productTruthReadiness.test.ts`
	- Expanded to 6 readiness contract tests.
- `docs/architecture/product-system/samples/gradi_curat_product_truth_draft.sample.json`
	- Added docs-only sample with `SAMPLE_ONLY_NOT_RUNTIME_PAYLOAD` marker.
- `VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`
	- Added Phase 3A.1 fixture matrix, hardening rules, readiness issue-array notes, and sample path.

## Validation

Passed:

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend; pnpm.cmd vitest run src/lib/intakeV6/productTruth/productTruthDraftBuilder.test.ts src/lib/intakeV6/productTruth/productTruthReadiness.test.ts
```

Result: 2 test files passed, 32 tests passed.

Diagnostics were clean on the changed Product Truth TypeScript files after hardening.

Static forbidden boundary scan:

```powershell
Set-Location C:\Users\offic\workos_app_vs; Select-String -Path frontend\src\lib\intakeV6\productTruth\*.ts -Pattern 'fetch\(|axios|localStorage|sessionStorage|createQuote|createOrder|materialize|persist|save|api/v1|CommercialPriceProposal|ProductDefinition|ProductAggregate|ExecutionPlan|CostEngine' -CaseSensitive:$false
```

Result: no runtime API/storage/persistence/downstream calls. Hits were limited to negative test assertions, readiness flag/type names, and explanatory boundary strings.

Runtime read-only check on `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`:

- page remained on Review;
- Product Truth candidate chips were visible;
- support/mounting split text was visible;
- commercial preview remained internal/preview-only;
- no `product_truth`, `ProductTruthDraft`, or sample marker token appeared in page markup;
- no product-truth/quote/order localStorage or sessionStorage keys were present.

## Forbidden scope confirmation

Confirmed for this slice:

- no new form;
- no duplicate controls;
- no new wizard;
- no backend changes;
- no DB/schema/seeds;
- no API changes;
- no ProductTruth backend persistence;
- no runtime payload save;
- no readiness/gating changes;
- no analyzer runtime changes;
- no pricing runtime changes;
- no ProductDefinition runtime consumption;
- no ProductSystem runtime changes;
- no CommercialPriceProposal runtime changes;
- no Quote Snapshot;
- no Order Snapshot;
- no ProductAggregate;
- no Task Graph;
- no ExecutionPlan;
- no materialization;
- no quote/order/execution creation;
- no forced confirmations;
- no Employee Mobile.