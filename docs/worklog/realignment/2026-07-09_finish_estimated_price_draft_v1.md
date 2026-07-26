# FINISH_ESTIMATED_PRICE_DRAFT_V1

**Status:** PASS (readonly draft — no activation)  
**Mode:** READONLY ESTIMATED PRICE DRAFT — NO ACTIVATION  
**HEAD before:** `fc799ac`  
**HEAD after:** _(see commit)_  
**Date:** 2026-07-09

## Purpose

Prepare readonly estimated price draft for FINISH surface application variants, mirroring the FACE draft pattern, without activating pricing and without writing Product Truth / Pricing Registry.

## Files read

- `docs/worklog/owner-input/finish_component_truth_owner_decision_v1.md`
- `docs/worklog/owner-input/finish_component_truth_owner_inputs_pending.md`
- `docs/worklog/realignment/2026-07-09_finish_owner_answers_apply_v1.md`
- `docs/worklog/realignment/2026-07-09_finish_owner_decisions_visual_evidence_v1.md`
- `docs/qa/screenshots/2026-07-09_finish_owner_decisions_apply/`
- `frontend/src/features/product-system/componentFirstFinishTruthWorkshop.ts`
- `frontend/src/features/product-system/FinishTruthWorkshopPanel.tsx`
- `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.ts`
- `frontend/src/features/product-system/componentFirstFaceEstimatedPriceDraft.ts`
- `frontend/src/features/product-system/FaceEstimatedPriceDraftPanel.tsx`
- `docs/worklog/owner-input/face_price_registry_alignment_owner_decision_v1.md`

## Files changed

- `frontend/src/features/product-system/componentFirstFinishEstimatedPriceDraft.ts` (new)
- `frontend/src/features/product-system/FinishEstimatedPriceDraftPanel.tsx` (new)
- `frontend/src/features/product-system/FinishTruthWorkshopPanel.tsx` (wire panel)
- `frontend/src/features/product-system/componentFirstFinishEstimatedPriceDraft.test.ts` (new)
- `frontend/src/pages/ProductSystem.badges.test.tsx` (draft panel assertions)
- `frontend/scripts/capture-finish-estimated-price-draft-screenshots.mjs` (new)
- `docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md` (this file)
- `docs/worklog/owner-input/finish_estimated_price_draft_pending_values.md` (new)
- `docs/qa/screenshots/2026-07-09_finish_estimated_price_draft_v1/*.png`

## Draft rows created (10)

| Variant/group | Qty basis | Evidence refs | Draft value status | Activation |
|---------------|-----------|---------------|-------------------|------------|
| Face Oracal 641 | mp_face_area | MAT-ORACAL-641, FACE_VINYL_APPLICATION_LABOR | evidence_only | blocked |
| Face Oracal 651 | mp_face_area | MAT-ORACAL-651, FACE_VINYL_APPLICATION_LABOR | evidence_only | blocked |
| Face Oracal 8500 | mp_face_area | MAT-ORACAL-8500, FACE_VINYL_APPLICATION_LABOR | evidence_only | blocked |
| Face print+lam combined | mp_face_area | MAT-VINYL-PRINT-LAMINATED, FACE_VINYL_APPLICATION_LABOR | evidence_only | blocked |
| Face print+lam split | mp_face_area | MAT-VINYL-PRINT, LARGE_FORMAT_PRINT, LAMINATION, labor | evidence_only | blocked |
| Artwork Oracal 641 | mp_artwork_area | MAT-ORACAL-641, labor | evidence_only | blocked |
| Artwork print+lam | mp_artwork_area | MAT-VINYL-PRINT-LAMINATED, PRINT, LAMINATION | source_inventory_audit_required | blocked |
| Artwork print only | mp_artwork_area | MAT-VINYL-PRINT, LARGE_FORMAT_PRINT | source_inventory_audit_required | blocked |
| Artwork Oracal 8500 | mp_artwork_area | MAT-ORACAL-8500, labor | evidence_only | blocked |
| Artwork none/raw plexi | none | — | not_applicable | blocked |

Excluded: `RETURN_CANT_VINYL_APPLICATION_LABOR`, `MAT-ACP-FATA-LITERE`

## Values surfaced / missing

**Surfaced (evidence_only from seeds):** Oracal 641/651/8500, print/lam combined 10 EUR/mp, split components, FACE vinyl labor 5 EUR/mp.

**Missing / audit:** Artwork print/lam specific keys — `source_inventory_audit_required` on 2 rows.

## Authority flags

```txt
pricingActive: false
productTruthLiveWrite: false
pricingRegistryWrite: false
productDefinitionBridge: false
readyForPricing: false
estimatedPriceDraftOnly: true
```

## Boundary preserved

- No backend / seed / migration / DB changes
- No FACE pricing value changes
- No RETURN-CANT value changes
- No quote / order / execution integration
- No Save / Apply / Activate buttons
- Evidence refs remain evidence_only — not registry authority

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstFinishEstimatedPriceDraft.test.ts src/features/product-system/componentFirstFinishTruthWorkshop.test.ts src/pages/ProductSystem.badges.test.tsx src/features/product-system/componentFirstFaceTruthWorkshop.test.ts src/features/product-system/canonicalFinishEnumMap.test.ts
```

## Visual evidence

Route: `http://127.0.0.1:3000/product-system` → Component-first sets → candidate-set → Guards/Audit → FINISH Estimated Price Draft panel

Screenshots: `docs/qa/screenshots/2026-07-09_finish_estimated_price_draft_v1/`

## Scope check

Forbidden scope respected: **YES**

## Next recommended step

**FINISH_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1** — artwork print/lam keys inventory cross-ref before owner price values.

## Progress

Cat sunt in directia stabilita: **92/100%** (draft readonly complete; artwork inventory audit + owner prices remain before any activation path)
