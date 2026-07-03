# BUILD: Desktop Preparation Ownership and Template Costing

## Purpose

Separate CNC preparation from order instrumentation in desktop/admin blueprint visibility, and model paper vs Forex mounting templates with registry-backed pricing.

## Context

Follows read-only audit `Desktop/Admin: Operational Preparation Ownership + Template Material Costing`. Employee Mobile v2 Work Room build (`78b3337`) is a separate boundary.

## Files changed

### Backend

- `backend/services/preparation_domain_service.py` — new
- `backend/services/order_production_blueprint_service.py` — preparation DTOs, prepared_by, template summary
- `backend/services/volumetric_quote_input_policy.py` — `mounting_template_material_type`
- `backend/services/quote_input_line_gate.py` — material type gate
- `backend/seeds/material_canonical_naming.py` — `MAT-SABLON-HARTIE`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py` — 5 EUR/mp paper template
- `backend/seeds/seed_build4_materials.py` — inventory row
- `backend/seeds/seed_build4_templates.py` — paper line, forex gate, CNC gate
- `backend/validators/intake_product_spec.py` — allowed quote_input key
- `backend/tests/test_preparation_domain_and_template_costing.py` — new
- `backend/tests/test_volumetric_finish_mounting_pricing.py` — paper template case

### Frontend (desktop/admin)

- `frontend/src/api/operatorProductionBlueprint.ts`
- `frontend/src/api/execution.ts`
- `frontend/src/components/workos/OperatorProductionBlueprintPanel.tsx`
- `frontend/src/pages/ExecutionDetail.tsx`

### Docs

- `docs/architecture/DESKTOP_PREPARATION_OWNERSHIP_AND_TEMPLATE_COSTING_DECISION.md`
- `docs/qa/BUILD_DESKTOP_PREPARATION_OWNERSHIP_AND_TEMPLATE_COSTING.md`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_operator_production_blueprint.py tests/test_execution_plan_prepared_by.py tests/test_volumetric_finish_mounting_pricing.py tests/test_preparation_domain_and_template_costing.py -q
```

**Result:** `47 passed` (2026-06-14)

## Verdict

**PASS**
