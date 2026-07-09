# FACE Price Draft Align 3mm to Registry v1 — Worklog

**Date:** 2026-07-09  
**Task:** `FACE_PRICE_DRAFT_ALIGN_3MM_TO_REGISTRY_V1`  
**Mode:** READONLY DRAFT ALIGNMENT APPLY  
**HEAD before:** `df49462`

---

## Owner decision source

`docs/worklog/owner-input/face_price_registry_alignment_owner_decision_v1.md`

---

## What changed

| Item | Before | After |
|---|---:|---:|
| Plexiglas/acrylic 3 mm material draft | 15 EUR/mp | **16 EUR/mp** |
| Cross-reference note (MAT-ACP-FATA-LITERE) | mismatch note | aligned to registry authority |

**Unchanged:** Plexiglas 5 mm (25 EUR/mp), 10 mm (50 EUR/mp), CNC contour 1.00/1.50/2.50 EUR/ml, 50 lei minimum, `readyForPricing: false`, `pricingActive: false`.

---

## What was not changed

- No Pricing Registry write
- No `/inventory/pricing` write
- No pricing activation
- No backend/seed/migration/DB
- No Product Truth live write
- No ProductDefinition bridge
- No FINISH workshop
- No new MAT-* keys
- No Work Intake / Quote / Order / Execution changes

---

## Files changed

| File | Change |
|------|--------|
| `frontend/src/features/product-system/componentFirstFaceEstimatedPriceDraft.ts` | 3 mm material 15 → 16; alignment notes |
| `frontend/src/features/product-system/componentFirstFaceEstimatedPriceDraft.test.ts` | Assertions 16 EUR/mp |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | UI assertion 16.00 EUR/mp |
| `docs/worklog/owner-input/face_estimated_price_draft_v1.md` | Current value + historical note |
| `docs/worklog/realignment/2026-07-09_face_price_draft_align_3mm_to_registry_v1.md` | This worklog |

---

## Remaining blockers

- FACE pricing activation
- Pricing Registry write
- Product Truth live write
- ProductDefinition bridge
- FINISH workshop (separate slice)
- Plexiglas 5/10 mm registry keys absent
- Runtime Intake V6 → FACE handoff

---

## Next recommended slice

**`FINISH_COMPONENT_TRUTH_WORKSHOP_V1`** — FACE boundary and 3 mm alignment documented/applied; FINISH can proceed without 15 vs 16 ambiguity.

**Alternative:** `FACE_CNC_COMMERCIAL_POLICY_DRAFT_APPLY_V1` if owner wants CNC policy refined before FINISH.
