# Intake V6 — LIGHTING / ELECTRICAL sold scope v1

**Date:** 2026-07-12  
**Task:** `INTAKE_V6_STEP2_SLICE_C_LIGHTING_ELECTRICAL_SCOPE_V1`  
**HEAD before:** `d1e675d`

## Summary

Split combined `sistem_led` / `comp_led_litere` into independently selectable canonical scopes **LIGHTING** and **ELECTRICAL**, filtered at material/operation ownership within one dossier component.

## Ownership

| Scope | Owns |
|-------|------|
| LIGHTING | `led_modules`, `adhesive_led_modules`, `led_install_letters` |
| ELECTRICAL | PSU variants, `MAT-CABLU-MYYUP*`, `electrical_letters`, wiring |

`LED_COUNT` / wattage remain calc-only for ELECTRICAL-only (resolver `derive_calc_modules`).

## Backend

- `offer_scope_led_subscope_service.py` — ownership map + `electrica_litere` runtime alias
- `offer_scope_canonical_map.py` — LIGHTING/ELECTRICAL active in slice 1
- Filters wired: live calc, aggregate BOM, EIC, CPP, execution reader

## Frontend

- Offer scope panel: LIGHTING + ELECTRICAL checkboxes
- Iluminare tab: **Iluminare** + **Electrica** subsections; PSU selector moved from Montaj

## Tests

`backend/tests/test_intake_v6_lighting_electrical_scope.py` — resolver, BOM, EIC/CPP, live calc, execution, persistence/snapshot.

## Boundary

No template/DB/composer changes. FACE/RETURN-CANT/BACK/FINISH/MOUNTING ownership untouched except PSU removed from Montaj.
