# Contract — SVG closed-contour selection

| Field | Value |
|-------|-------|
| Status | Active (V1) |
| Schema | `closed_contour_candidates_v1` / `svg_support_selection_v1` |
| Authority | Operator confirms; Analyzer proposes only |

## Flow

```text
SVG input
→ geometry extraction (existing nest2 parser)
→ closed-contour candidates
→ operator selection + role confirmation
→ typed finish_setup.svg_support_selection
→ ProductDefinition canonical_values
→ Product System later compiles (out of scope here)
```

## Candidate fields

`contour_id` (geometry-hash based), `element_id`, `source_element_type`, `geometry_hash`, bbox, width/height/area/perimeter mm, contains_count, rectangularity_score, confidence, reasons[].

Identity must survive reanalysis of the same SVG. Color and DOM order are not authority.

## Roles

- `ALUCOBOND_CASED_PANEL` — opens casing configuration
- `FLAT_BACKGROUND` / `DECORATIVE_CONTOUR` / `GRAPHIC_ELEMENT` / `IGNORE` — zero casing leakage

## Invalidation

If `svg_source_hash` or `geometry_hash` no longer match → `status=reconfirm_required`. No silent remapping in V1.

## Boundaries

No CPP, tasking, DXF, CUT/FOLD generation, SVG rewrite, or auto-SVGO.
