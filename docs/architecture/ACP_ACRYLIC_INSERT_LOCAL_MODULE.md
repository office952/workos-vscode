# ACP Acrylic Insert — Local Module

**Status:** ACTIVE_CONTRACT · OWNER_GATED_VALUES  
**Module code:** `ACP-LOCAL-MODULE-ACRYLIC-INSERT`  
**Host:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`  
**Treatment:** `FACE-TREATMENT-ACRYLIC-INSERT`  
**Geometry role:** `ACRYLIC_INSERT`

## Owner-confirmed truth

- Variant with ~10 mm plexiglas inserted into CNC pockets exists.
- Insert may form a luminous element.
- Can coexist with applied volumetric letters on the same ACP face.
- **Not** the same as plexiglas glued behind a routed cutout.

## Thickness policy

| Field | Value |
|-------|-------|
| `thickness_mm` default seed | `10` |
| `thickness_provenance` | `OWNER_CONFIRMED_VARIANT` |
| `thickness_status` | `OWNER_REVIEW_REQUIRED` |
| `sole_thickness_admitted` | `false` |

10 mm is **not** the only admitted thickness until owner confirms a closed catalog.

## Gated (not invented)

Clearance, protrusion, retention method, backing, LED/electrical details.

## Owner process truth (docs)

Constructie confirmată (placă suport + insert 10 mm + cianoacrilat), recomandări CNC/laser și diferența față de routed backlit:

→ `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §10  

Nu transforma aceste texte în defaults Aggregate fără GO.
