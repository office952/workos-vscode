# Plan — ACP Internal Frame Resource Option Contract

| Field | Value |
|-------|-------|
| Status | Implementation contract (Registry V1 + guarded Step 2) |
| Date | 2026-07-18 |
| Parent | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Profiles | **DEFERRED** — empty accepted set until owner confirms sections |

---

## Principles

```text
Step 1 → marker only (internal_frame_enabled)
Step 2 → material + profile + dimensions + crossbars from Shared RO
PD → nested typed internal_frame (wins over bare boolean)
Aggregate → technical intent; quantity GUARDED until BOM detail GO
CPP → OWNER_GATE (not this build)
```

Cadru interior ≠ Metal Premount (no global XOR).

---

## Nested config (typed)

```json
{
  "internal_frame": {
    "enabled": true,
    "material_code": "MAT-STRUCT-STEEL",
    "profile_code": null,
    "panel_outer_width_mm": 2000,
    "panel_outer_height_mm": 700,
    "panel_material_thickness_mm": 3,
    "total_fit_allowance_mm": 2,
    "frame_outer_width_mm": 1992,
    "frame_outer_height_mm": 692,
    "crossbar_rule_code": "MATERIAL_SPACING_V1",
    "max_crossbar_spacing_mm": 1000,
    "crossbar_orientation": "VERTICAL",
    "suggested_crossbar_count": 1,
    "confirmed_crossbar_count": 1,
    "override_reason": null,
    "structural_review_required": false,
    "confirmation_status": "INCOMPLETE",
    "provenance": {
      "source": "INTAKE_STEP_2",
      "resource_registry_version": "structural_resource_options/v1"
    }
  }
}
```

Legacy: `internal_frame_enabled` derived from `enabled`.  
Legacy `frame_clearance_mm`: not authority; do not map fit allowance into it as editable clearance.

`confirmation_status`: `CONFIRMED` only when material + **profile** + dimensions + crossbar confirmation present. Without profiles in catalog → cannot be CONFIRMED.

---

## Dimension rule `FRAME_FROM_PANEL_OUTER_DIMENSIONS_V1`

OWNER_CONFIRMED — domain-owned; fold-independent.

---

## Crossbar rule `MATERIAL_SPACING_V1`

OWNER_CONFIRMED spacing; suggestion + confirm.

---

## Product System accepted options

```text
accepted_material_codes: [MAT-STRUCT-STEEL, MAT-STRUCT-ALUMINIUM]
accepted_profile_shapes: [SHS, RHS]
accepted_profile_codes: []   # until owner confirms
```
