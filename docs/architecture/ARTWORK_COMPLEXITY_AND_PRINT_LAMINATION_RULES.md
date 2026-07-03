# Artwork complexity and print lamination rules

Classification-only build for Intake V4 SVG artwork applied on volumetric letter faces.

## Raster over vector (Regula 1)

When a raster `<image>` overlaps closed vector production geometry:

- Vector remains **production_geometry** (volumetric letter body / face cut source).
- Raster becomes **face_artwork** / **print_overlay** / **vinyl_overlay** metadata.
- Raster does **not** generate child volumetric parts, CNC, cant, or LED perimeter rows.

Overlap detection uses bounding-box intersection (minimum 1% overlap ratio). Print area MVP uses **sum of overlapped vector areas** (`covered_vector_area_estimate`), not the image bounding box.

## Color complexity (Regula 2)

When artwork has more than **three** dominant flat colors, gradients, photographs, external PNG/JPG, complex transparency, clip paths, or masks, the default recommendation is:

**print_on_vinyl_laminated** (imprimare pe autocolant + laminare)

—not separate cut vinyl per color.

## Simple artwork (Regula 3)

**1–3 flat colors** without gradient/photo/complex effects may remain **vinyl_cut** (Oracal cut). Operator may override manually; overrides are stored in `finish_setup.artwork_complexity_decisions`.

## production_geometry vs face_artwork

| Role | Meaning |
|------|---------|
| `production_geometry` | Closed vector paths used for letter volume, nesting, perimeter, cant |
| `face_artwork` / `print_overlay` | Overlapping raster or complex graphics applied on the face only |

## Analyzer output

`svg_analysis_json.artworkComplexity` (schema **1.11.0**) contains `assessments[]` with `recommended_application`, `recommendation_reason`, `artwork_area_estimate_m2`, and `warnings`.

## MVP limitations

- No exact alpha-mask intersection; bbox overlap + vector area sum only.
- No automatic vectorization, OCR, or RIP/prepress.
- Material breakdown shows preview rows with `missing_rate` when registry prices are absent.
- No quote/order/task creation, ExecutionPlan, stock consumption, or CostEngine changes from this classification path.

## Pseudo layers for unlayered / flat Corel exports

When Corel exports a single generic layer (`Layer_x0020_1`, inner `_123…` groups, or one `maria` bucket) but vectors use multiple solid fills:

- Analyzer clusters solid-fill paths into **pseudo layers** (`pseudo:fill:*`) with `layerKind: pseudo` and auto-role **face**.
- Raster `<image>` logos split to **raster_artwork_left** / **raster_artwork_right** with auto-role **printed_artwork**.
- Named volumetric layers (`gradinita`, `ana`, `maria`, `soare`) win over policromie heuristics when no raster is present.

See `semanticAndPseudoLayerExpansion.ts`, `anaMariaLetterSemantics.ts`, and `BUILD_INTAKE_V4_GEOMETRIC_PSEUDO_LAYER_CLASSIFICATION_AND_6_LAYER_UI_TESTS.md`.
