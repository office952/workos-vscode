# WORKOS_REALIGN_AFTER_LAYER_ROLE_TAXONOMY_COMMIT_V1

Date: 2026-07-06
Mode: audit + realignment only
Taxonomy commit audited: `a1a1fef` (`fix(intake-v6): align owner layer role taxonomy`)

## Verdict

Pas 1 is now aligned enough to be treated as stabilized for the documented direction: owner-facing layer role decisions are `Vector Litere` and `Vector Logo`, while target templates remain separate internal/product-system concepts (`TPL-VOLUMETRIC-LETTERS_v2`, `TPL-VOLUMETRIC-LOGO_v1`).

Post-audit follow-up note: owner observed that the right-side `Atenție analiză` panel also needed explicit alignment with the same owner taxonomy. That panel alignment should be closed before starting the next Pas 2 slice.

The next natural micro-slice is:

`GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1`

This should be a backend/read-model contract slice for Pas 2, with focused UI verification in Review/Calcul live. It should not be a QuoteWizard migration, CostEngine rewrite, ProductAggregate/TaskGraph/ExecutionPlan build, or broad UI polish pass.

This recommendation remains valid after `Atenție analiză` alignment is complete.

## Scope

In scope:
- Read-only audit after the layer role taxonomy commit.
- Confirm current alignment with Analyzer-first, Product System, Form System, Product Truth, ProductDefinition, and Commercial Preview direction.
- Identify the next small, natural implementation slice.
- Preserve backlog items without implementing them.

Out of scope:
- Runtime code changes.
- Backend schema/migration changes.
- CostEngine changes.
- Quote/order creation changes.
- ProductAggregate, TaskGraph, ExecutionPlan, or production task dependency work.
- Staging or commit.

## Git Gate

Command run before audit:

```powershell
git status -sb; git rev-parse --short HEAD; git diff --cached --name-only; git diff --check; git status --short --untracked-files=all
```

Observed:
- Branch: `main...origin/main [ahead 18]`.
- HEAD: `a1a1fef`.
- No staged files from this audit at gate time.
- Dirty/untracked repository state exists and was not reverted.
- Known untracked report `WORKOS_STEP1_LAYER_ROLE_OWNER_TAXONOMY_2026-07-06.md` remains intentionally untracked.
- No code/runtime/backend mutation was made during this audit.

## Sources Read

Architecture and direction:
- `docs/architecture/product-system/INTAKE_V6_LAYER_ROLE_TAXONOMY_CONTRACT.md`
- `docs/worklog/realignment/2026-07-06_intake_v6_layer_role_taxonomy_logic_v1.md`
- Product System / Form System / Product Truth / Material / Commercial contract docs already present in the repository.
- Gradi owner decision docs and commercial settings persistence docs already present in `docs/qa/` and `docs/worklog/`.
- Repository memory note `/memories/repo/product_template_module_composition_roles.md`.

Code surfaces:
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel.tsx`
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6LiveCalculationRowFilters.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/services/intake_v6_pricing_preview_sync_service.py`
- `backend/services/letter_group_finish_readiness_service.py`
- `backend/services/linked_template_runtime_segment_extraction_service.py`

Missing requested docs / alternate evidence:
- `docs/export/chatgpt-sources-workos-implementation-2026-07-04/*.md` was not found.
- `GRADI_LOGICAL_LIST_TRACE_V1.md` was not found.
- `GRADI_STEP2_LOGICAL_LIST_GAP_CHECK_V1.md` was not found.
- Alternate export pack exists under `docs/export/workos_chatgpt_sources_pack_2026-07-04_1328` and was used as available context.

## UI Runtime Verification

Target workspace/context:
- Workspace: `IV6-0EFC6C31`
- Route: `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator`
- Fixture SVG: `fisiere-teste-svg/gradi-curat.svg`

Pas 1 evidence:
- Previous real UI verification after the taxonomy fix showed all six layer dropdowns constrained to exactly two owner-facing options: `Vector Litere`, `Vector Logo`.
- Layers 1-4 were selected as `Vector Litere`.
- Layers 5-6 were selected as `Vector Logo`.
- No optgroups/global fallback role list leaked into the current letters+logo context.
- No `Vector Atipic` or `Vector Atipic / logo` remained in the owner-facing dropdown.

Pas 2 evidence observed in current audit:
- Current browser tab was on Review.
- Review showed a `Vector Litere` group with four letter pseudo rows.
- Review showed a `Vector Logo` group with Logo 1 / Logo 2.
- Review showed Form System Backbone text similar to `TPL-VOLUMETRIC-LETTERS_v2 · 10 fields · 9 blockers · downstream safe`.
- Commercial-looking totals and `Probleme & atenționări (8)` were visible.

Pas 3 limitation:
- Playwright attempts to navigate via stepper/test ids/footer did not reach Pas 3 in the current tab; page remained on Review.
- No mutative CTA was clicked.
- This is recorded as a runtime interaction limitation, not as evidence of a functional Pas 3 failure.

## Current Truth After Commit

| Concept | Current state | Audit judgement |
| --- | --- | --- |
| Analyzer | Suggests layer roles and template candidates | Correct direction; not final owner truth |
| Owner layer role | `Vector Litere` / `Vector Logo` | Correct and stable for Pas 1 |
| Target template | `TPL-VOLUMETRIC-LETTERS_v2` / `TPL-VOLUMETRIC-LOGO_v1` | Correctly separate from owner labels |
| Form System | Review derives finish/artwork fields and preserves pending/confirmed state | Directionally aligned; blockers still expected |
| Product Truth | Must store confirmed operator truth | Not the next broad implementation target |
| ProductDefinition | Should consume Product Truth read-only | Not next; depends on clearer Pas 2 logical trace |
| Commercial Preview | Exists as guarded preview/dry-run | Should remain gated, not quote/order authority |
| Quote/Order | Should happen only after gates | Out of scope for the next slice |
| ProductAggregate/TaskGraph/ExecutionPlan | Downstream | Explicitly out of scope now |

## Systems Alignment

| System | Alignment after taxonomy | Remaining gap |
| --- | --- | --- |
| Analyzer-first | Good: analyzer suggests, operator confirms | Need stronger trace from analysis/payload to logical rows |
| Product System | Good: templates and component roles remain internal concepts | Pas 2 rows need a clearer component/module/formula contract |
| Form System | Partial: Review fields and finish payload exist | Need row-level source/state clarity for materials/services/labor |
| Product Truth | Partial: readiness services exist | Need logical list to name what confirmed truth will feed |
| ProductDefinition | Guarded/read-only direction | Should not be expanded before Pas 2 trace is stable |
| Commercial Preview | Present through material breakdown + priced dry-run | Needs formula provenance/gap clarity before quote/order |

## Pas 2 Logical List Audit

The strongest controlling backend surface is `backend/services/gradi_logical_list_read_model_service.py`.

Findings:
- Endpoint exists: `GET /api/v1/intake-v6/workspaces/{workspace_id}/logical-list-read-model`.
- It is read-only and builds from existing material breakdown, priced dry-run, and finish preferences.
- It returns `source: gradi_logical_list_read_model_v1`.
- It targets `core_row_count == 21` and `target_core_row_count == 21`.
- It limits core categories to `MATERIALE`, `SERVICII_OPERATII`, `MANOPERA`.
- It excludes extra commercial lines such as `ambalare` and `montaj` from core rows.
- It includes `formula_code_proposed` and `formula_version_proposed` on logical rows.
- It validates `categories_valid` and `formula_trace_metadata_present`.

Important current gaps already exposed by the read-model:
- `LOGO_PLEXI_STRUCTURAL_RUNTIME_ROW_MISSING`
- `FORMULA_TRACE_MISSING`
- `COMMERCIAL_FORMULA_UNVERSIONED`
- `PRINT_ROWS_AGGREGATED_FOR_LOGICAL_LIST`
- `LAMINATION_ROWS_AGGREGATED_FOR_LOGICAL_LIST`
- `APPLICATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST`
- `DRY_RUN_BACK_CNC_M2_DEV_BRIDGE`
- `BACKING_AREA_FALLBACK_USED` when triggered by runtime warnings

Frontend evidence:
- `IntakeV6ReviewStep.tsx` fetches material breakdown, pricing preview, priced quote dry-run, and logical list read-model independently.
- `IntakeV6LiveCalculationSummary.tsx` receives `logicalList={logicalListReadModel}` alongside breakdown/pricing inputs.
- `intakeV6LiveCalculationRowFilters.ts` already has filters for `Materiale`, `Servicii / Operații`, and `Manoperă`.
- The UI therefore has a natural place to verify the logical read-model without moving quote/order boundaries.

## Decision: Next Natural Slice

Recommended next slice:

`GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1`

Goal:
- Make Pas 2's logical list contract explicit and testable for `gradi-curat.svg` after Pas 1 has stabilized owner layer roles.

Smallest useful acceptance target:
- Backend read-model returns 21 core rows for the Gradi workspace/fixture.
- Rows are grouped only as materials, services/operations, and labor.
- Each row exposes stable `line_id`, `display_label`, `category`, `component_code`, `module_code`, `formula_code_proposed`, `formula_version_proposed`, `status`, `quantity`, `unit`, `subtotal`, `child_rows`, `gaps`, `warnings`, and `blockers`.
- Logo plexiglas, print, lamination, application, LED, commercial formula, and CNC bridge gaps remain visible instead of being hidden.
- Ambalare/montaj remain excluded from core logical rows and treated as later/optional commercial owner decisions.
- Frontend Review/Calcul live can show the contract without inventing pricing or mutating Product Truth.

Cheap falsifying check:
- A targeted backend test for `build_gradi_logical_list_read_model_from_runtime` or the endpoint fixture should fail if row count, categories, formula metadata, or known gaps drift.
- A targeted frontend test can verify that Review/Calcul live consumes the read-model and exposes category filters without mixing quote/order authority.

Why not the other candidates first:
- QuoteWizard legacy is not the direct V6 direction; V6 priced quote remains separate and gated.
- CostEngine/pricing changes would cross a protected area before the logical Product/Form/Truth trace is stable.
- ProductAggregate/TaskGraph/ExecutionPlan are downstream and would be premature.
- Pure UI polish would hide the real uncertainty: Pas 2 needs a contract for what rows exist, where they came from, and which gaps are intentional.

## Backlog Preserved

Preserved for later slices:
- Pas 2 logical list for `gradi-curat.svg`.
- Materials/services/labor/lighting separation.
- Oracal / print / laminare / aplicare clarity.
- Roll print/laminare widths 1050/1320/1500 and 20+20 retractions.
- Real nesting on plexiglas/forex 3000x2000.
- Roll nesting with widths/retractions.
- Missing `formula_code` / `formula_version` trace where runtime remains legacy/unversioned.
- Commercial settings persistence.
- Adaos/discount/TVA/manual adjustment ownership.
- Product System UI semantic simplification.
- Component/product dossier.
- Production task dependencies downstream.
- QuoteWizard legacy is not the direct V6 direction.
- V6 quote priced flow remains separate/gated.

## Negative Confirmations

This audit did not:
- Change runtime code.
- Change backend services or routers.
- Change database schemas or migrations.
- Change CostEngine.
- Create Quote/Order behavior.
- Activate ProductAggregate, TaskGraph, ExecutionPlan, or production task dependencies.
- Weaken tests.
- Stage files.
- Commit files.

## Roadmap Awareness

Natural climb after Pas 1:

1. Pas 2 logical list read-model contract for Gradi.
2. Close formula/source/gap trace for materials, services, labor, lighting, print/lamination/application, and logo plexiglas.
3. Feed confirmed Product Truth/ProductDefinition read-only once Pas 2 rows are stable.
4. Keep Commercial Preview gated and auditable.
5. Only then consider quote/order handoff and downstream production structures.
