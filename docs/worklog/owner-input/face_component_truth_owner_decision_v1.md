# FACE Component Truth — Owner Decision v1

> **Notă:** Decizie owner pentru contract FACE component truth.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.

**Date:** 2026-07-09  
**HEAD la semnare:** `a5a527d` — Add FACE component truth workshop  
**Owner:** Alex / P-Media (răspunsuri în conversație)

---

## Context

Răspunsuri la workshop-ul FACE owner inputs (`FACE_OWNER_INPUTS_ANSWERS_WORKSHOP_V1`), după contractul readonly `componentFirstFaceTruthWorkshop.ts`.

---

## A. Material families

| Material family | Allowed FACE standard? | Notes |
|---|---|---|
| Plexiglas / acrylic | **YES** | Material față standard litere volumetrice |
| Forex | **NO** (momentan) | Doar dacă owner decide caz special; altfel BACK/suport |
| ACM / Bond / Dibond | **NO** (momentan) | Backing / suport / panouri — nu FACE standard |
| Other | **OWNER_INPUT_REQUIRED** | — |

---

## B. Thicknesses

| Material family | Allowed thicknesses | Default | Notes |
|---|---|---|---|
| Plexiglas / acrylic | 3 mm (standard); 5 mm / 10 mm (opțional) | **3 mm** | 5 / 10 mm = opțiuni speciale; confirmare owner înainte de pricing |
| Forex | — | — | Nu pentru FACE standard |
| ACM / Bond | — | — | Nu pentru FACE standard |

---

## C. FACE material / nesting basis

**ACCEPT:**

- bounding / out-of-box **per piece**
- **not** exact vector area for material nesting
- interior holes = negative holes, **not** separate nesting pieces
- exceptions only if owner confirms explicitly

---

## D. FACE perimeter for RETURN-CANT

**ACCEPT:**

- FACE contour/perimeter is **authoritative** for RETURN-CANT cant length
- RETURN-CANT **consumes** FACE perimeter
- RETURN-CANT **does not invent** perimeter

---

## E. Cutting matrix (FACE standard)

| Material | Thickness | Process | Notes |
|---|---|---|---|
| Plexiglas / acrylic | 3 mm | CNC router | Standard FACE debitare |
| Plexiglas / acrylic | 5 mm | CNC router | Opțional — confirmare owner înainte de pricing |
| Plexiglas / acrylic | 10 mm | CNC router | Opțional / caz special |
| Forex | 10 mm | CNC router | **Nu FACE standard** — BACK/suport; confirmare separată |
| ACM / Bond | 3 mm | CNC router | **Nu FACE standard** — panou/backing/suport; confirmare separată |

---

## F. Downstream output contract

**ACCEPT** proposed names:

| Output | Consumer | Notes |
|---|---|---|
| `face_piece_boxes` | FACE material / nesting | Bounding boxes per piece |
| `face_material_usage_area_m2` | FACE / pricing (future) | From boxes, not raw vector area |
| `face_perimeter_length_m` | RETURN-CANT | Authoritative cant length source |
| `mp_face_area` | FINISH | Vinyl / print-laminate quantity basis |
| `source_layer_role = Vector Litere` | FACE geometry | Not Vector Logo |

---

## G. Does-not-own confirmation

**ACCEPT all:**

- FACE does **not** own face vinyl, print/laminate, artwork finish
- FACE does **not** own cant finish, RAL minimum, pricing rates

---

## Still blocked after this decision

- Runtime geometry handoff Intake V6 → FACE truth
- Product Truth live write
- ProductDefinition bridge
- FACE pricing activation / MAT-* cross-reference (separate readonly audit)
- FINISH workshop (separate slice; FACE boundary now owner-confirmed for core)
- Work Intake exposure

---

## Next recommended slice

1. `FACE_OWNER_ANSWERS_APPLY_V1` — encode decisions in readonly workshop contract (if not already committed)
2. `FACE_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1` — readonly MAT-* lookup for Plexiglas 3 mm only
3. `FINISH_COMPONENT_TRUTH_WORKSHOP_V1` — after FACE apply accepted
