# INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1 — Validation

**Phase:** VALIDATION COMPLETE  
**Accepted HEAD before:** bee9757

## Git checks

| Command | Result |
|---|---|
| `git diff -- frontend` | No backend-task changes in frontend (unrelated dirty files present) |
| `git diff -- backend` | Only adapter + tests (task scope) |
| ProductDefinition diff | None |
| PA composition diff | None |
| Pricing / Quote / Order diff | None |
| DB / migration / seed diff | None |

## Test commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_aggregate_cost_bom_adapter.py -q
# 46 passed, exit 0, ~5s

.\.venv\Scripts\python.exe -m pytest tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_aggregate_cost_bom_adapter.py tests/test_product_aggregate_workspace_linked_logo_composition.py tests/test_intake_v6_layer_binding_persistence.py -q
# 73 passed, exit 0, ~6s

.\.venv\Scripts\python.exe -m pytest tests/test_product_definition_gradi_composition.py tests/test_selected_layer_refs_derivation.py tests/test_return_cant_product_truth_bridge.py -q
# 26 passed, exit 0, ~3s
```

**Total targeted:** 99 passed, 0 failed.

## Runtime API verification

| # | Scenario | HTTP | bom_status | Logo rows | Warnings | Commercial price |
|---|---|---|---|---|---|---|
| 1 | No workspace_id | 200 | varies | none | — | NO |
| 2 | Letters-only workspace | 200 | — | none | — | NO |
| 3 | Two bound logos | 200 | — | stanga + dreapta | composition applied | NO |
| 4 | Partial logo finish | 200 | partial | components only | finish partial | NO |

Route: `GET /api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS_v2`

Writes: NONE

## Warnings

Pydantic deprecation warnings from test fixtures (pre-existing).
