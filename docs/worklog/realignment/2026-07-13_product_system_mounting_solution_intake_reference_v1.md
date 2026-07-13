# Product System mounting solution Intake reference V1

**Task:** PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1  
**HEAD before:** 851c9fc  
**Date:** 2026-07-13

## Summary

Connected Intake V6 Pregătire pentru montaj to existing linked child `TPL-METAL-PREMOUNT-STRUCTURE_v1` via canonical `finish_setup.mounting_solution { template_code, configuration }`. Legacy `mounting_system` / `mounting_bar_profile` hydrate read paths and are stripped on canonical save (no permanent dual-write).

## Scope delivered

- Backend `mounting_solution_service.py` — normalize, hydrate, composition gates
- Schema `IntakeV4MountingSolution` on finish_setup
- Product Definition / BOM / quote handoff (`_build_linked_module_lines`) prefer solution reference when prep scope active
- Frontend selector: Fără soluție suplimentară | Structură metalică pentru premontaj
- Child config fields: bar_material, mounting_bar_profile, bar_count (PS-owned contract)
- Minimal execution sold-scope alias: `mounting_template_cnc_cut` → `finisaje`
- ACM: deferred note only — no template reference

## Out of scope (honored)

- ACM template seed/activation
- Pricing rates / fabrication labor invention
- MOUNTING sold module
- DB migrations

## Known gaps (unchanged)

- Premount fab labor still non-priced (`mounting_labor_not_priced`)
- No CPP lines for `structura_suport`
- Premount execution task still missing on parent task_rules (DEC-002)

## Verification

- `pytest tests/test_mounting_solution_intake_reference.py` — 12 passed
- `vitest run src/lib/intakeV6/mountingSolution.test.ts` — 5 passed
- Playwright: `frontend/e2e/intake-v6-mounting-solution-intake-reference-v1.spec.ts`

## Files (primary)

- `backend/services/mounting_solution_service.py`
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_finish_truth_service.py`
- `backend/services/intake_v4_commercial_quote_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/execution_sold_scope_reader_service.py`
- `frontend/src/lib/intakeV6/mountingSolution.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
