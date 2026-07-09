# Component-first RETURN-CANT — Owner Answers Workshop & Apply Plan v1

## HEAD before

`bc73b81` — Clarify RETURN-CANT owner input readiness

## Scope

Audit owner answer sources; apply only explicit answers; otherwise prepare apply plan and question pack. No runtime, no Product Truth write, no invented values.

## Owner answers audit

| Source | Result |
|--------|--------|
| `docs/worklog/owner-input/return_cant_owner_answers_pending.md` | **All 13 topics `pending`**, Owner answer column empty |
| Owner prompt (this task) | **No explicit answers** — questions only |

**answersFound: NO**

## Contract state (unchanged)

### Confirmed (5 owner inputs + workshop fields)

- `finish_type_variants` — Culoare Stock · Oracal · Vopsit RAL
- `stock_color_note_mode` — operator typed for atelier
- `ral_material_labor_separation` — model separate (not prices)
- `separate_calculation_component_truth` — component-owned path
- Workshop: `finish_type`, `stock_color_note`, `separate_calculation_allowed`

### owner_input_required (12 inputs)

- oracal_code_list, oracal_pricing_mode, ral_input_mode
- return_depths_standard, return_material, return_material_unit, return_labor_unit
- ral_material_price_rule, ral_labor_price_rule, minimum_price_rule
- stock_color_affects_price, perimeter_geometry_source, material_depth_compatibility

### blocked (1)

- `pricing_activation` — blocked_until_owner_decision

## Fields applied / not applied

| Action | Count |
|--------|-------|
| Applied from owner doc | **0** |
| Status changed to owner_confirmed | **0** |
| Values changed from null | **0** |

**Reason:** No explicit owner answers in allowed sources.

## Files changed

- `docs/worklog/owner-input/return_cant_owner_answers_pending.md` — restructured owner-friendly question pack (sections A–I)
- `frontend/src/features/product-system/componentFirstReturnCantOwnerApplyPlan.ts` — readonly apply plan helper
- `frontend/src/features/product-system/componentFirstReturnCantOwnerApplyPlan.test.ts`
- `docs/worklog/realignment/2026-07-09_component_first_return_cant_owner_answers_workshop_v1.md`

**Not changed:** `RETURN_CANT_OWNER_INPUTS` values/status, UI panel, backend, DB, pricing.

## What was not invented

No Oracal list · no RAL table · no prices · no units · no formulas · no Product Truth write

## Tests

```powershell
cd frontend
npm.cmd run test -- ... componentFirstReturnCantOwnerApplyPlan.test.ts ... (full gate)
```

Playwright: not run — no UI change (NOT NEEDED)

## Screenshots

NOT NEEDED — no UI change

## Final verdict

**PASS** — audit complete; question pack improved; apply plan ready; contract unchanged pending owner answers.

## Next required owner answers (priority)

1. Oracal selector + pricing mode
2. RAL input mode
3. Standard cant depths
4. Cant material (+ same/different per depth)
5. Material/labor units
6. RAL material/labor rules + minimum
7. Stock color pricing impact
8. Perimeter/geometry + material/depth compatibility

**Next slice:** `COMPONENT_FIRST_RETURN_CANT_OWNER_ANSWERS_APPLY_V2` — after owner fills `return_cant_owner_answers_pending.md` with Status=`answered`.
