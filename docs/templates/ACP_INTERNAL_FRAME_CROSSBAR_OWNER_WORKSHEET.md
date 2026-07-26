# Owner Worksheet — ACP Internal Frame Crossbars

| Field | Value |
|-------|-------|
| Status | **PARTIAL OWNER_CONFIRMED** |
| Version | 2026-07-18.3 |
| Owner truth source | `ACP_INTERNAL_FRAME_OWNER_RULES.md` |

---

## Confirmed spacing (OWNER_CONFIRMED)

| Material | Max spacing between stiffeners |
|----------|-------------------------------|
| Oțel (`MAT-STRUCT-STEEL`) | **1000 mm** |
| Aluminiu (`MAT-STRUCT-ALUMINIUM`) | **750 mm** |

| Mode | Status |
|------|--------|
| System suggestion | **OWNER_CONFIRMED** |
| Operator confirmation | **OWNER_CONFIRMED** required |
| Override with reason | **OWNER_CONFIRMED** |
| Automatic final structural authority | **NOT_APPLICABLE** |
| Certified structural calc | **NOT_APPLICABLE** |

---

## Suggestion formula (implementation — suggestion only)

For relevant length `L` and max spacing `S`:

```text
number_of_spans = ceil(L / S)
number_of_internal_crossbars = max(0, number_of_spans - 1)
```

Interpretation V1 (documented):

- `L` = clear span along the axis **perpendicular** to crossbar orientation  
  - VERTICAL crossbars → L ≈ `frame_outer_width_mm`  
  - HORIZONTAL crossbars → L ≈ `frame_outer_height_mm`
- Spacing is the maximum allowed gap between stiffening members (perimeter counts as ends).
- Profile thickness / joint detail **not** subtracted in V1 → quantities remain **GUARDED** for BOM.
- Operator must confirm; override requires `override_reason`.

---

## Orientation

| Option | V1 |
|--------|-----|
| VERTICAL | Allowed — operator chooses |
| HORIZONTAL | Allowed — operator chooses |
| BOTH | Manual; may set `structural_review_required` |

---

## Threshold matrix by panel size

**DEFERRED** — not required when spacing rule + operator confirm is enough for V1 suggestion.

Empty size-threshold cells remain `NOT_APPLICABLE` for automation (not invented).

---

## Sign-off

| Field | Value |
|-------|-------|
| Spacing rules | OWNER_CONFIRMED 2026-07-18 |
| Profile-dependent exceptions | DEFERRED |
