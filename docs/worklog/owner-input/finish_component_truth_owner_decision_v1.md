# FINISH Component Truth — Owner Decision v1

> **Notă:** Decizie owner pentru contract FINISH component truth.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.

**Date:** 2026-07-10  
**HEAD la semnare:** `ee8e0c7` — Prepare FINISH owner inputs questions workshop  
**Owner:** Alex / P-Media  
**Decision source:** OwnerDecision block — `FINISH_OWNER_INPUTS_ANSWERS_WORKSHOP_V1` APPLY mode

---

## 1. Status

| Field | Value |
|---|---|
| Decision status | **OWNER_ACCEPTED** |
| Workshop mode | readonly owner-confirmed contract |
| `readyForPricing` | **false** |
| `pricingActive` | **false** |
| Product Truth live write | **false** |
| ProductDefinition bridge | **false** |
| Pricing Registry write | **false** |

---

## 2. Surface variants

All 9 variants **ACCEPT** as face/artwork surface application. `activationStatus` remains **blocked** (no pricing activation).

| Variant | Surface | Owner status | Quantity basis | Notes |
|---------|---------|--------------|----------------|-------|
| face_oracal_641 | face | owner_confirmed | mp_face_area | Simple visible mp — no roll optimization now |
| face_oracal_651 | face | owner_confirmed | mp_face_area | MAT-ORACAL-651 evidence only |
| face_oracal_8500 | face | owner_confirmed | mp_face_area | MAT-ORACAL-8500 evidence only |
| face_print_laminate | face | owner_confirmed | mp_face_area | Print+lam variant accepted; pricing inactive |
| artwork_print_laminate | artwork | owner_confirmed | mp_artwork_area | When artwork geometry exists |
| artwork_print_only | artwork | owner_confirmed | mp_artwork_area | When artwork geometry exists |
| artwork_cut_vinyl | artwork | owner_confirmed | mp_artwork_area | When artwork geometry exists |
| artwork_translucent_vinyl | artwork | owner_confirmed | mp_artwork_area | MAT-ORACAL-8500 evidence typical |
| artwork_none_raw_plexi | artwork | owner_confirmed | none | No extra finish application on artwork |

---

## 3. Quantity basis

| Rule | Owner decision |
|------|----------------|
| Face finish | **`mp_face_area`** — visible face/application basis |
| `face_material_usage_area_m2` | **Internal/evidence/reference only** — not FINISH owner-confirmed quantity basis |
| Artwork finish | **`mp_artwork_area`** / visible artwork area when geometry exists; blocked until artwork area source handoff |
| Oracal 641/651/8500 | **Simple visible mp** in workshop — no roll width×length optimization now |
| Print + laminare | **Conceptually separable** (print material/service + lamination material/service); `print_laminated` accepted as finish variant; pricing inactive |

---

## 4. Catalog/pricing refs (evidence only — not active authority)

| Key | Classification | Notes |
|-----|----------------|-------|
| MAT-ORACAL-641 | evidence_only | Face vinyl material cross-ref |
| MAT-ORACAL-651 | evidence_only | Face vinyl material cross-ref |
| MAT-ORACAL-8500 | evidence_only | Face/translucent vinyl cross-ref |
| MAT-VINYL-PRINT-LAMINATED | evidence_only | Combined print+lam face material evidence |
| FACE_VINYL_APPLICATION_LABOR | evidence_only | Face/artwork finish labor — not cant labor |
| LARGE_FORMAT_PRINT (PRINT) | evidence_only | Print service evidence |
| LAMINATION | evidence_only | Laminate service evidence |
| RETURN_CANT_VINYL_APPLICATION_LABOR | RETURN-CANT only | **Not FINISH** — outside FINISH ownership |

---

## 5. Boundary

**ACCEPTED — FINISH does NOT own:**

- RETURN-CANT cant finish (Stock / Oracal wrap / RAL paint)
- FACE base material / Plexiglas / acrylic selection (`MAT-ACP-FATA-LITERE`)
- RAL cant minimum 100 lei (RETURN-CANT commercial policy)
- Pricing Registry authority
- Product Truth live write
- Pricing activation
- ProductDefinition runtime bridge (this slice)

---

## 6. LOGO split

- **Artwork surface finish remains under FINISH for now.**
- FINISH owns finish/application decision on face/artwork area.
- Future **LOGO component** may own logo geometry, component logic, nesting, or execution identity — **not in this slice**.
- No migration of artwork finish to LOGO component now.

---

## 7. Still blocked

- Pricing activation
- Product Truth live write
- ProductDefinition handoff
- Runtime Intake V6 → FACE/FINISH handoff
- Pricing Registry write
- Quote/Order active pricing use
- Artwork geometry handoff until runtime source exists

---

## 8. Owner signature

| Field | Value |
|---|---|
| Owner decision | **ACCEPTED** |
| Date | 2026-07-10 |
| Owner | Alex / P-Media |
| Source | OwnerDecision block — FINISH_OWNER_INPUTS_ANSWERS_WORKSHOP_V1 APPLY |

---

## Related documents

- `docs/worklog/owner-input/finish_component_truth_owner_inputs_pending.md` — superseded by this doc
- `docs/worklog/owner-input/face_component_truth_owner_decision_v1.md` — FACE upstream boundary
- `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md` — canonical finish enum
