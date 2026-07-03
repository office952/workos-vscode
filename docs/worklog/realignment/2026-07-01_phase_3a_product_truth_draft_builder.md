# Phase 3A Product Truth Draft Builder Worklog

**Date:** 2026-07-01  
**Status:** PASS  
**Scope:** frontend-only pure Product Truth canonical draft builder; no API, persistence, payload runtime, readiness unlock, backend, pricing, ProductDefinition, ProductAggregate, Task Graph, ExecutionPlan, materialization, quote/order/execution, or Employee Mobile.

## Sources read before coding

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_FULL_E2E_PRODUCT_TRUTH_TO_EXECUTION_ALIGNMENT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_full_e2e_product_truth_to_execution_alignment.md`
- `docs/worklog/realignment/2026-07-01_phase_2_support_mounting_contract_alignment.md`
- `docs/worklog/realignment/2026-07-01_phase_2_gap_closure_existing_form_ui_only.md`
- `docs/worklog/realignment/2026-07-01_phase_2_product_truth_candidate_visibility_ui_only.md`

## Pre-coding source map

| Source area | File/function/type | Data it exposes | Can be used for Product Truth draft? | Source status | Risk | Notes |
|---|---|---|---|---|---|---|
| Workspace identity | `frontend/src/lib/intakeV6/intakeV4Api.ts` / `IntakeV4WorkspaceResponse` | `id`, `workspace_code`, `template_code`, payload, readiness | yes | hydrated/system | importing runtime API functions can drag fetch code | Phase 3A builder uses local input types instead of API calls. |
| Existing Review finish form | `IntakeV4FinishSetup` / `IntakeV6FinishSetup` | face finish, roll width, return finish/depth, lighting, LED/PSU, backing, mounting, template, group/artwork finishes, `confirmed` | yes | hydrated/confirmed/fallback depending field | existing fields encode some missing canonical semantics | builder keeps source state per field and does not silently promote fallback/hydrated values to confirmed. |
| Review contract defaults | `intakeV6ReviewFormContract.ts` / `buildIntakeV6ReviewFormContract` | fallback defaults: return 60 mm, direct wall, template enabled, PSU 100 W, roll 1000 mm | yes | fallback | defaults can look quote-safe | builder marks owner/template defaults as `fallback` unless matching confirmed Review state. |
| Layer role confirmation | `svgAnalyzer/analyzer/layerRoleTypes.ts` and V4 API layer role setup | layer key/name, auto role, confirmed role, confirmation state, warnings | yes | suggested/confirmed/ignored | analyzer suggestions can be mistaken for final truth | builder keeps auto role as suggestion and confirmed role only when confirmation state is confirmed or ignored. |
| Quote geometry | `intakeV6QuoteGeometry.ts` / `IntakeV6QuoteGeometry` | dimensions, counts, area, perimeter, geometry source, confirmed | yes | suggested/confirmed/hydrated | geometry alone is not Product Truth | builder includes geometry as draft context and blocks when missing, but never unlocks quote. |
| Letter group finishes | `intakeV4LetterGroups.ts` / `letterGroupFinishesFromPayload` | per group face/cant finish, colors, roll width, confirmed | yes | hydrated/confirmed/manual | global fallback can hide per-group differences | builder emits per-group draft rows with field-level source refs. |
| Artwork finishes | `intakeV4ArtworkFinish.ts` / `artworkFinishesFromPayload` | artwork execution type, color mode, transparency, material, area, confirmed | yes | suggested/hydrated/confirmed | `printed_artwork` is not automatic print | builder separates `print_required` and `lamination_required` as draft booleans inferred from current encoded execution with warnings. |
| Module activation preview | `intakeV6ModuleActivationPreview.ts` | `structura_suport` bridge from `mounting_system` bar values | warning only | warning/bridge debt | collapses support into mounting | builder does not derive confirmed support truth from mounting; it only emits explicit warning/bridge suggestion. |
| Quote handoff readiness UI | `intakeV6QuoteHandoffReadiness.ts` | blocker labels and preview-only state | no runtime input | boundary reference | can accidentally mirror downstream unlock | builder has independent read-only readiness draft and does not call handoff preview. |
| Pricing/commercial docs | `WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` | commercial vs internal cost boundary | warning only | not Product Truth | pricing gaps could be blamed for truth gaps | builder emits pricing boundary as `not_applicable`/warning and never prices. |

## Initial local hypothesis

A pure builder can produce an in-memory canonical Product Truth draft from existing Intake V6 state if every value carries source state and source reference. The cheap falsifying check is a focused Vitest fixture where unconfirmed analyzer roles and fallback/default form values must remain non-final, support must not be confirmed from `mounting_system`, and downstream readiness flags must stay false.

## Implementation notes

Files added:

- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthReadiness.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthFixtures.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.test.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthReadiness.test.ts`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`

Builder design:

- accepts a local `ProductTruthDraftBuilderInput` instead of importing API functions;
- produces `ProductTruthDraft` in memory;
- attaches `ProductTruthSourceRef` to every field;
- keeps analyzer roles `suggested` until operator confirmation;
- keeps plexiglas opal 3 mm as `fallback` and quote/downstream blocker until canonical confirmation exists;
- splits encoded `print_laminate` into draft `printRequired` and `laminationRequired` fields with warning;
- preserves support/mounting separation and emits bridge warnings instead of confirmed support truth;
- keeps downstream readiness flags false with `PHASE_3A_PREVIEW_ONLY`.

UI preview added: NO.

Reason: this slice is builder/tests only to preserve no form, no payload, no gating, and no downstream changes.

## Validation

Focused Vitest:

```text
pnpm.cmd vitest run src/lib/intakeV6/productTruth/productTruthDraftBuilder.test.ts src/lib/intakeV6/productTruth/productTruthReadiness.test.ts
```

Result:

```text
Test Files  2 passed (2)
Tests       6 passed (6)
```

Editor diagnostics:

- `productTruthTypes.ts`: PASS
- `productTruthDraftBuilder.ts`: PASS
- `productTruthReadiness.ts`: PASS

Static boundary checks:

```text
Select-String -Path src\lib\intakeV6\productTruth\*.ts -Pattern "fetch\(|axios|localStorage|sessionStorage|createQuote|createOrder|ProductAggregate|ExecutionPlan|materialize|pricing mutation|readiness mutation|api/v1|requestIntake|saveIntake|persistIntake|CommercialPriceProposal|Quote Snapshot|Order Snapshot"
```

Result: PASS with expected mentions only for explicit downstream-disabled readiness/test fields and explanatory forbidden notes.

Strict mutation/API boundary check:

```text
Select-String -Path src\lib\intakeV6\productTruth\*.ts -Pattern "fetch\(|axios|localStorage|sessionStorage|createQuote|createOrder|materialize|pricing mutation|readiness mutation|api/v1|requestIntake|saveIntake|persistIntake"
```

Result: PASS, no output.

Runtime read-only check:

- URL: `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`
- current step: Review;
- `LIVE / DB` visible;
- workspace `IV6-BB8EE3F8` visible;
- Review accessible;
- Product Truth chips visible in Montaj tab;
- Support / Mounting split visible:
	- `mounting_system is Mounting, not Support truth`;
	- `metal_support_required means Support/Bare, not mounting method`;
	- `Support and mounting are separate decisions`;
- pricing boundary chips visible:
	- `Pricing Registry does not decide Product Truth`;
	- `CostEngine internal-only`;
- commercial preview says: `Propunere comerciala preview doar pentru revizuire interna. Oferta oficiala exista doar dupa Quote Snapshot V2.`;
- CTA read-only DOM check found `Continuă la Confirmare` enabled and no draft/order/materialization CTA visible in current Review step;
- no state-changing controls were clicked;
- no false Pricing Registry blame observed;
- no commercial hour/minute pricing observed in the checked surfaces.

## Limitations

- No runtime `product_truth` payload branch exists yet.
- No backend/schema/API contract exists yet.
- No UI preview was added.
- Face material/thickness remain fallback because current Review form has no first-class canonical confirmation fields.
- Mounting scope remains blocked because current Review form has no first-class commercial scope field.
- Support remains unknown or suggested because current Review form has no first-class support_required/support_type/support_source fields.
- ProductDefinition, ProductSystem, CommercialPriceProposal, snapshots, ProductAggregate, Task Graph, ExecutionPlan, and execution do not consume this draft.

## Forbidden scope confirmation

Confirmed for this slice:

- no new form;
- no duplicate controls;
- no wizard;
- no backend changes;
- no DB/schema/seeds;
- no API calls;
- no persistence;
- no saved payload shape changes;
- no Intake V6 runtime readiness/unlock changes;
- no analyzer runtime changes;
- no pricing behavior;
- no ProductDefinition/ProductSystem runtime consumption;
- no ProductAggregate;
- no Task Graph;
- no ExecutionPlan;
- no materialization;
- no quote/order/execution;
- no Employee Mobile.