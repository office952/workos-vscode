# Component-first RETURN-CANT — Owner Input Apply v1

## HEAD before

`463a2e4` — Add component-first letters Product Truth owner workshop

## Scope

Read-only clarification of RETURN-CANT owner-confirmed vs pending inputs. No runtime, no Product Truth write, no pricing activation, no invented commercial values.

## Files changed

- `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.ts`
- `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts`
- `frontend/src/features/product-system/ReturnCantOwnerInputsPanel.tsx`
- `frontend/src/features/product-system/ComponentFirstProductTruthWorkshopPanel.tsx`
- `frontend/src/features/product-system/componentFirstLettersProductTruthWorkshop.ts` (export FINISH_TYPE_VALUES)
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/e2e/product-system-readonly-smoke.spec.ts`
- `frontend/scripts/capture-return-cant-owner-input-screenshots.mjs`
- `docs/worklog/owner-input/return_cant_owner_answers_pending.md`
- `docs/qa/component-first-return-cant-owner-input-apply-v1/screenshots/` (10 PNGs)

## Confirmed (owner / project memory)

- Finish variants: Culoare Stock · Oracal · Vopsit RAL
- Stock color: operator typed, atelier info, no price impact assumed
- RAL: material + labor separate (model only)
- Component-owned truth for separate cant calculation
- No activation paths

## Still owner_input_required

- Oracal list + pricing mode
- RAL input mode
- Standard depths, material, units
- RAL material/labor price rules + minimum
- Perimeter source + material/depth compatibility
- Stock color affects price? (explicit question)

## Not invented

- No Oracal codes, RAL table, prices, formulas, default depths/materials

## Tests

- Unit: 127/127 PASS (5 files)
- Playwright smoke: 1/1 PASS

## Screenshots

`docs/qa/component-first-return-cant-owner-input-apply-v1/screenshots/01`–`10_*.png`

## Final verdict

**PASS**

## Owner questions remaining (priority)

1. Oracal list + pricing mode
2. RAL mode (text vs selector)
3. Standard cant depths
4. Cant materials + depth pairing
5. Material/labor units
6. RAL material/labor rules + minimum
7. Stock color pricing impact
8. Perimeter geometry source
