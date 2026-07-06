# Worklog: WorkOS Realign After Layer Role Taxonomy Commit V1

Date: 2026-07-06
Mode: audit + realignment only
Commit audited: `a1a1fef` (`fix(intake-v6): align owner layer role taxonomy`)

## Scope

Audit the state after the Intake V6 layer-role owner taxonomy commit and answer what should happen next so Intake V6 climbs naturally toward the documented WorkOS direction.

No implementation, staging, commit, backend mutation, runtime mutation, CostEngine work, quote/order work, or downstream production graph work was in scope.

## Git Gate

Ran:

```powershell
git status -sb; git rev-parse --short HEAD; git diff --cached --name-only; git diff --check; git status --short --untracked-files=all
```

Observed:
- HEAD is `a1a1fef`.
- Branch is ahead of origin with existing dirty/untracked state.
- No staged files at audit start.
- Existing unrelated/untracked files were preserved.

## Sources Read

Read or inspected:
- Layer role taxonomy contract and taxonomy worklog.
- Product System / Form System / Product Truth / Material / Commercial direction docs available in the repo.
- Gradi owner decision and commercial settings persistence docs available in the repo.
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
- `backend/services/letter_group_finish_readiness_service.py`
- `backend/services/linked_template_runtime_segment_extraction_service.py`

Requested but not found:
- `docs/export/chatgpt-sources-workos-implementation-2026-07-04/*.md`
- `GRADI_LOGICAL_LIST_TRACE_V1.md`
- `GRADI_STEP2_LOGICAL_LIST_GAP_CHECK_V1.md`

## UI Verification

Pas 1 remains supported by prior real UI evidence after the commit:
- Owner-facing dropdown options are exactly `Vector Litere` and `Vector Logo` in the current Letters+Logo context.
- Layers 1-4 map to `Vector Litere`; layers 5-6 map to `Vector Logo`.
- Global fallback roles and `Vector Atipic` labels do not leak into the owner dropdown.

Current runtime read-only check:
- Browser was on Review.
- Review showed `Vector Litere` and `Vector Logo` groupings.
- Review showed Form System Backbone and blocker count.
- Commercial-looking totals and warnings were visible.
- Navigation attempts to Pas 1/Pas 3 in the current tab did not reliably move the page; no mutative CTA was used.

## Audit Finding

Pas 1 is now a stable owner-taxonomy foundation. The next uncertainty is not naming, and not QuoteWizard. The next uncertainty is Pas 2: the logical list/read-model that explains what the operator is reviewing and what future Product Truth/ProductDefinition/Commercial Preview should consume.

The backend already has a read-only Gradi logical list service. It builds from material breakdown, priced dry-run, and finish preferences. It targets 21 core rows, categories rows as materials/services/labor, excludes ambalare/montaj from core rows, and carries proposed formula metadata.

The service also exposes the real gaps that should guide the next slice:
- logo plexiglas structural runtime row missing;
- formula trace missing or legacy/unversioned for selected rows;
- print, lamination, and application rows aggregated for logical list;
- CNC back service dry-run bridge mismatch;
- backing fallback when runtime data requires it.

## Recommendation

Next prompt / build should be:

`GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1`

Post-audit sequencing update: close the `Atenție analiză` owner-taxonomy alignment first. After that, this Pas 2 recommendation remains the next natural slice.

Recommended boundary:
- Backend/read-model contract first.
- Focused Review/Calcul live UI verification second.
- No CostEngine, no quote/order write, no ProductAggregate/TaskGraph/ExecutionPlan.

Recommended first acceptance checks:
- Targeted backend test proves 21 core rows, valid categories, formula metadata presence, ambalare/montaj exclusion, and expected gap codes for Gradi runtime/fixture.
- Targeted frontend test proves Review/Calcul live consumes the logical list and preserves materials/services/labor semantics without becoming pricing authority.

## Negative Confirmations

This audit did not:
- Implement code.
- Modify runtime behavior.
- Modify backend services.
- Modify schemas/migrations.
- Touch CostEngine.
- Trigger quote/order creation.
- Stage or commit.
