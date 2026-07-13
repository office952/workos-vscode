# BUILD — ACM Boxed Mounting Owner Rates V1

**Purpose:** Close owner-rate and CPP/EIC wiring gaps for `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.

**Date:** 2026-07-13  
**Boundary:** No CostEngine core / markup policy; metal premount unchanged.

## Owner rates (locked)

| Code | Rate |
|------|------|
| MAT-ACM-BOND-3MM | 15 EUR/mp |
| MAT-SURUBURI-GEN | 5 EUR/set |
| ACM_PANEL_CUTTING | 1.5 EUR/lm |
| ACM_V_GROOVE | 3 EUR/lm |
| ACM_BOXED_ASSEMBLY | 15 EUR/mp, min 20 EUR/product |

4 mm: **deferred** — not exposed in boxed intake/resolver.

## Files changed

- `backend/seeds/seed_acm_boxed_mounting_owner_rates.py` (new)
- `backend/seeds/seed_acm_owner_confirmed_prices.py`
- `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py`
- `backend/services/pricing_registry_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/acm_bond_material_rate_resolver.py`
- `backend/services/mounting_solution_service.py`
- `backend/services/acm_quote_input_helpers.py`
- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/data/internal_cost_rules_volumetric_v2.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/scripts/seed_sync_all.py`
- `backend/tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py` (new)
- `frontend/src/lib/acmQuoteInput.ts`
- `frontend/src/lib/intakeV6/mountingSolution.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_acm_boxed_mounting_template_v1.py tests/test_mounting_solution_intake_reference.py -q
```

## Results (closeout 2026-07-13)

- `pytest tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py -q` → **7 passed**
- `pytest tests/test_acm_boxed_mounting_template_v1.py tests/test_mounting_solution_intake_reference.py -k "not test_api_save and not test_seed_creates" -q` → **20 passed**
- `vitest run src/lib/intakeV6/mountingSolution.test.ts src/lib/acmQuoteInput.test.ts` → **13 passed**
- Check 9: 4 mm preserved in normalization (explicit resolver block; no silent coerce to 3 mm)
- Runtime UI (IR-MRI01769): 3 mm only, preparation_only + ACM casetat, panel 400×300 mm, reload preserved
- Runtime CPP HTTP: **6 `acm_*` lines**, `acm_boxed_assembly` subtotal **20 EUR** (min charge at 400×300) — **PASS**

## Evidence

- `docs/qa/product-system-acm-boxed-mounting-owner-rates-cpp-v1/evidence_report.json`
- Screenshots: `01_acm_3mm_configuration.png`, `02_acm_cpp_owner_rates.png`, `03_acm_reload_preserved.png`
