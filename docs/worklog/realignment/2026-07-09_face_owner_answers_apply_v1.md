# FACE Owner Answers Apply v1 — Worklog

**Date:** 2026-07-09  
**Task:** FACE owner answers apply (conversation)  
**HEAD before:** `a5a527d`  
**Owner source:** Alex / P-Media — answers in chat 2026-07-09

---

## Owner decisions recorded

- **A:** Plexiglas/acrylic YES; Forex/ACM/Bond NO for FACE standard (special case only)
- **B:** Plexiglas 3 mm default; 5/10 mm optional with pre-pricing owner confirm
- **C:** Nesting = bounding/out-of-box per piece; holes negative not separate pieces
- **D:** FACE perimeter authoritative for RETURN-CANT
- **E:** Cut matrix — Plexiglas 3/5/10 mm CNC router; Forex/ACM not FACE standard
- **F:** Output contract accepted (face_piece_boxes, face_material_usage_area_m2, face_perimeter_length_m, mp_face_area, Vector Litere)
- **G:** Does-not-own all ACCEPT

---

## Files changed

| File | Change |
|------|--------|
| `docs/worklog/owner-input/face_component_truth_owner_decision_v1.md` | Created — signed owner decisions |
| `docs/worklog/owner-input/face_component_truth_owner_inputs_pending.md` | Superseded pointer |
| `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.ts` | Owner answers encoded |
| `frontend/src/features/product-system/FaceTruthWorkshopPanel.tsx` | UI reflects decisions |
| `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.test.ts` | Updated assertions |

---

## Still blocked

- Runtime handoff, Product Truth write, ProductDefinition bridge, FACE pricing, FINISH workshop slice, Work Intake

---

## Next step

`FACE_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1` (Plexiglas 3 mm MAT-* readonly) or `FINISH_COMPONENT_TRUTH_WORKSHOP_V1`
