# 2026-07-06 - Gradi Step 2 Logical List Read Model Contract V1

## Scope

Audit and contract only for Step 2 / Review logical-list read model on `gradi-curat.svg`.

No implementation, staging, commit, pricing mutation, schema change, Quote/Order handoff, inventory mutation, or execution behavior was performed.

## Git Gate

- Starting HEAD: `2a2abbf`.
- Branch state: `main...origin/main [ahead 19]`.
- No staged files were present at the gate.
- Existing worktree dirt was unrelated and intentionally left untouched.

## Sources Read

Architecture and prior decisions:

- `docs/architecture/product-system/INTAKE_V6_LAYER_ROLE_TAXONOMY_CONTRACT.md`
- `docs/worklog/realignment/2026-07-06_workos_realign_after_layer_role_taxonomy_commit_v1.md`
- `docs/architecture/product-system/GRADI_LOGICAL_LIST_TRACE_READ_MODEL_DRAFT.md`
- Product System / Form System / Product Truth / Material / Commercial / Formula contract docs read earlier in this task window.

Runtime/backend/frontend surfaces:

- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/lib/intakeV6/intakeV6LiveCalculationRowFilters.ts`
- `frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts`

## Runtime Read-Only Checks

Workspace:

- `IV6-0EFC6C31`
- `3c494f9f-4507-497a-912f-4f45fe709642`
- `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator`

Observed Step 2:

- Review was visible.
- Live sidebar showed internal cost `772.92 EUR`.
- Official priced dry-run showed gross `6,439.08 RON` and net `5,321.55 RON`.
- Owner-facing finish groups remained `Vector Litere` and `Vector Logo`.
- Review tabs remained `Finisaje`, `Iluminare`, `Montaj`.

Observed Step 3:

- Confirm was visible via stepper.
- Handoff was blocked.
- `Creeaza oferta pretuita` disabled.
- `Creeaza draft intern V6` disabled.
- Confirmations showed `1/2`.
- No write CTA was executed.

## Backend Audit Result

`logical-list-read-model` is implemented as a read-only Gradi reconciliation service.

Runtime result:

- `source: gradi_logical_list_read_model_v1`
- `core_row_count: 21`
- `target_core_row_count: 21`
- `core_rows_complete: true`
- `warnings: BACKING_AREA_FALLBACK_USED, ORACAL_ROLL_COLOR_SPLIT_MISSING`
- `blockers: []`
- validation flags true for duplicate tabs, excluded ambalare/montaj, categories, formula metadata.

Important backend facts:

- `ambalare` and `montaj` are excluded extra commercial lines, not core logical rows.
- `MATERIALE`, `SERVICII_OPERATII`, and `MANOPERA` are the core categories.
- `Finisaje`, `Iluminare`, and `Montaj` are UI/module concerns, not current logical-list categories.
- Formula metadata exists for every core row, but some rows are intentionally marked `legacy_unversioned` or gap-bearing.

## Frontend Audit Result

`IntakeV6ReviewStep` fetches `getIntakeV6LogicalListReadModel(workspaceId)` and stores `logicalListReadModel`.

The same component passes `logicalList={logicalListReadModel}` to `IntakeV6LiveCalculationSummary` in both mobile and right-panel placements.

However, `IntakeV6LiveCalculationSummary.tsx` does not consume `logicalList` in the component body. Its row source is still `buildIntakeV6LiveMaterialsUsedRows({ breakdown, ... })`, then local filtering through `filterLiveCalcRows`.

The current UI therefore displays a useful live calculation breakdown, but not the backend logical read-model contract as a first-class list.

Frontend type gap:

- `intakeV6Api.ts` imports and re-exports `IntakeV6LogicalListReadModelResponse` and `IntakeV6LogicalListLineTrace`.
- No matching definitions were found in `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts` or the rest of `frontend/src/lib/intakeV6` during this audit.

## Decision

Initial decision: `A. AUDIT-ONLY`.

This is not a tiny isolated runtime fix. The backend already produces the core read model; the remaining work is to formalize frontend types and wire a proper read-only UI surface.

Follow-up implementation in `GRADI_STEP2_LOGICAL_LIST_UI_WIRING_V1`: completed minimal UI wiring.

## UI Wiring Status

Implemented:

- `IntakeV6LiveCalculationSummary` now accepts and consumes `logicalList`.
- When `logicalList.rows` exists, the visible owner-facing line list is built from backend logical rows.
- Existing material-breakdown row construction remains as fallback only when logical rows are absent.
- Existing total displays continue to use internal cost / priced dry-run sources; no pricing is recalculated from logical rows.
- Logical rows show label, category grouping, quantity/unit, status, formula code/version, gaps/warnings/blockers, and child-row count.

Type work:

- Added `IntakeV6LogicalListLineTrace`.
- Added `IntakeV6LogicalListReadModelResponse`.
- Existing API exports are now backed by concrete frontend types.

## Validation After UI Wiring

Focused test:

```powershell
pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose
```

Result: `13 passed`.

`IntakeV6ReviewStep.test.tsx` does not exist in this workspace, so that requested companion command could not be run.

Diff checks:

```powershell
git diff --check
git diff --cached --check
```

Result: no output.

Runtime UI verification:

- Route: `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator`.
- Workspace: `IV6-0EFC6C31`.
- Step 2 showed `Lista logică read-model · 21/21 rânduri`.
- Categories visible: `Materiale · 14`, `Servicii / Operații · 6`, `Manoperă · 1`.
- Formula metadata count: `21`.
- Gap/warning samples visible: `BACKING_AREA_FALLBACK_USED`, `ORACAL_ROLL_COLOR_SPLIT_MISSING`, `FORMULA_TRACE_MISSING`, `COMMERCIAL_FORMULA_UNVERSIONED`.
- Step 1 remained unchanged: `Vector Litere`, `Vector Logo`, no `Vector Atipic`.
- Step 3 remained gated: `Creeaza oferta pretuita` disabled and `Creează draft intern V6` disabled.
- No quote/order write action was triggered.

## Files Added

- `docs/architecture/product-system/GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT.md`
- `docs/worklog/realignment/2026-07-06_gradi_step2_logical_list_read_model_contract_v1.md`
- `docs/qa/gradi-logical-list-trace/2026-07-06/GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1.md`

## Files Changed By UI Wiring

- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts`
- `docs/architecture/product-system/GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT.md`
- `docs/worklog/realignment/2026-07-06_gradi_step2_logical_list_read_model_contract_v1.md`
- `docs/qa/gradi-logical-list-trace/2026-07-06/GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1.md`

## Next Prompt

`IMPLEMENT_GRADI_STEP2_LOGICAL_LIST_UI_CONTRACT_V1`

Minimum acceptance:

- explicit frontend logical-list types;
- read-only rendering of backend `logicalList.rows`;
- formula/gap detail surface;
- existing live totals preserved;
- targeted Vitest coverage;
- no pricing, Product Truth, Quote/Order, inventory, CostEngine, or execution changes.