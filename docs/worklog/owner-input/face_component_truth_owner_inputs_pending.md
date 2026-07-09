# FACE Component Truth — Owner Inputs Pending

**Date:** 2026-07-09  
**Status:** Superseded by signed owner decisions — see [face_component_truth_owner_decision_v1.md](./face_component_truth_owner_decision_v1.md)  
**Source decisions:** [canonical_finish_enum_map_owner_decision_v1.md](./canonical_finish_enum_map_owner_decision_v1.md)  
**Workshop contract:** `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.ts`

---

## 1. What FACE owns

FACE (`TPL-COMP-LETTER-FACE_v1`) owns **substrate and geometry** for the visible letter face:

- Face substrate / material family
- Face material thickness
- Face cut geometry reference (contour / cut path)
- Face visible area basis (`mp_face_area`)
- Face perimeter / contour length (downstream for RETURN-CANT)
- Source layer role: **Vector Litere** (not Vector Logo)
- Selected layer refs from Intake V6 SVG analysis

Truth path prefix: `product.components.face.*`

---

## 2. What FACE does not own

- Face vinyl application → **FINISH** (`product.components.finish.face.vinyl.*`)
- Face print/laminate → **FINISH** (`product.components.finish.face.print_lamination.*`)
- Artwork / Vector Logo finish → **FINISH** (`product.components.finish.artwork.instances[]`)
- Cant finish (Stock / Oracal / RAL) → **RETURN-CANT** (`product.components.return_cant.*`)
- Cant material, depth, RAL minimum 100 lei → **RETURN-CANT**
- Pricing rates, EUR literals → **Pricing Registry** (readonly cross-ref only)
- Product Truth live write, ProductDefinition bridge, Work Intake exposure → **blocked**

Generic FINISH paths are **retired conceptually** (not active truth):

- `product.components.finish.oracal_code`
- `product.components.finish.ral_code`
- `product.components.finish.stock_color`
- `product.components.finish.type`

---

## 3. Owner questions

### A. Face material families

What materials are allowed for letter face?

Examples to confirm — **not assumed**:

- Plexiglas / acrylic
- Forex
- ACM / Bond
- Other (specify)

**Evidence in repo (not accepted):** skeleton workshop mentions plexiglas 3/5/10 mm; Intake V6 uses `plexiglas_face` material key; legacy `TPL-VOLUMETRIC-FACE_v1` module exists.

### B. Thickness options

For each confirmed material family, what thicknesses are valid?

Do not assume 3 / 5 / 10 mm unless owner confirms per material.

### C. Geometry — area basis

Does FACE area use **exact vector area** or **bounding / out-of-box** for nesting/material calculation?

**Do not decide here without owner.**

Note existing global rule if relevant: nesting/material calculation usually uses bounding/out-of-box on pieces, not raw area — except LED atypical cases mentioned in workshop skeleton.

### D. Perimeter

Is face contour/perimeter the **authoritative source** for RETURN-CANT cant length?

Current partial confirmation: RETURN-CANT owner inputs state perimeter/contour real; Product System audit shows `components.face.confirmed_perimeter` as target upstream.

### E. Cut process

Which process per material/thickness?

- CNC router (`debitare_fata` / `face_cnc_cut` — legacy evidence)
- Laser
- Other

No operation/pricing creation until owner confirms.

### F. Face finish boundary

Confirm: **FACE does not own** vinyl / print / laminate application; **FINISH owns** application finish on face surfaces.

Accepted in canonical finish enum owner decision A.

### G. Artwork boundary

Confirm: **Vector Logo / artwork** remains outside FACE — handled by FINISH artwork instances or future Logo component.

Accepted in canonical finish enum owner decision B.

---

## Next step after owner answers

1. Update `componentFirstFaceTruthWorkshop.ts` field statuses from `owner_input_required` → `owner_confirmed` where applicable.
2. Optional: FACE source/inventory cross-reference audit for material pricing keys (readonly — no rate invention).
3. Only then: FINISH component workshop (face/artwork entries currently `blocked` in canonical finish enum map).
