# Intake V6 Step 2 — live calc offer_scope propagation (Slice A)

**Date:** 2026-07-12  
**HEAD before:** `94b25cf`  
**Task:** `INTAKE_V6_STEP2_SLICE_A_LIVE_CALC_OFFER_SCOPE_V1`

## Problem

Workspace `payload.offer_scope` persisted correctly but V6 live paths built `quote_input` without it. BOM/EIC/CPP filtering already worked when `offer_scope` was present in `quote_input`; operator UI hid fields but priced full product.

## Change

- Added `intake_v6_offer_scope_live_calc_service.py` — merge helper, scope resolution, material/logical-list filters.
- `build_v6_pricing_input_preview` attaches workspace `offer_scope` to `quote_input_payload`.
- Material breakdown, priced dry-run, logical-list read model, commercial quote handoff use the shared merge/filter path.

## Tests

`backend/tests/test_intake_v6_live_calc_offer_scope.py` — 10 scenarios (merge, legacy full product, FACE/RETURN-CANT/BACK/union CPP, filters, reload, save-then-filter).

## Runtime (IR-MRI01769, BACK only)

Before: CPP listed face/cant/LED/finisaje; logical list 21 rows.  
After: CPP `debitare_spate` only; logical list 2 rows (`material.forex_backing`, `service.cnc_back`).

## Boundary

No Step 2 UI, per-layer backing, LIGHTING/ELECTRICAL split, BOM formula, or DB changes.
