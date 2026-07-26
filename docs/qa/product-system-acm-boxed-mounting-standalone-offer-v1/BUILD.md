# BUILD — PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_OFFER_FLOW_V1

**Purpose:** Complete standalone Product System offer path for `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` (3 mm only).

## Blocker resolved

| Class | Blocker | Fix |
|-------|---------|-----|
| B | PD root returned 404 — no Intake V6 form contract | Minimal standalone PD builder in `product_definition_builder_service.py` |
| C | CPP/EIC gated on linked-child `mounting_solution` payload | Extended `acm_quote_input_helpers` standalone root detection + module activation |
| A | Catalog showed ACM as internal module only | `product_template_availability_service` honors `root_offerable` policy |
| D | Quote snapshot V2 letters-only | Added ACM to `quote_snapshot_v2_service.SUPPORTED_TEMPLATES` |

## Files changed

- `backend/services/acm_quote_input_helpers.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/services/quote_snapshot_v2_service.py`
- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/data/internal_cost_rules_volumetric_v2.py`
- `backend/tests/test_acm_boxed_mounting_standalone_offer_v1.py`
- `frontend/src/features/product-system/buildUnifiedCatalogEntries.ts`
- `frontend/src/lib/acmQuoteInput.test.ts`
- `frontend/e2e/product-system-acm-boxed-mounting-standalone-offer-v1.spec.ts`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_boxed_mounting_standalone_offer_v1.py tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py -q
# 16 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/acmQuoteInput.test.ts src/lib/intakeV6/mountingSolution.test.ts
# 15 passed

$env:PW_SKIP_WEB_SERVER='1'
npx playwright test frontend/e2e/product-system-acm-boxed-mounting-standalone-offer-v1.spec.ts
```

## Boundary

- TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 only; 3 mm offerable, 4 mm blocked
- No Intake V6 standalone form contract; Product System + API quote path only
- Linked-child Intake path unchanged; metal premount unchanged
- No DB migration

## Verification contract

Standalone quote_input → PD → Aggregate → BOM → EIC → CPP → Quote snapshot: 6 `acm_*` CPP lines, assembly min 20 EUR, face+return materials.
