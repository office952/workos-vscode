# SVG Face Treatment Binding Contract

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Schema | `svg_component_bindings_v1` (additive fields) |
| Authority | `backend/data/product_system/svg_component_binding_contract.py` + persistence |

## Binding shape (conceptual)

```json
{
  "schema": "svg_component_bindings_v1",
  "binding_id": "bind_cutout_text_…",
  "local_zone_id": "zone_cutout_text_…",
  "geometry_role": "CUTOUT_TEXT",
  "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
  "face_treatment_code": "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT",
  "confirmation_status": "CONFIRMED",
  "status": "CONFIRMED",
  "local_configuration_status": "NOT_CONFIGURED",
  "selected_geometry": {
    "layer_ids": [],
    "group_ids": [],
    "element_ids": ["…"],
    "geometry_hashes": ["…"],
    "source_svg_hash": "…"
  },
  "provenance": {
    "source": "operator",
    "svg_hash": "…",
    "geometry_hash": "…"
  },
  "face_treatment_contract_version": "acp_face_treatment/v1"
}
```

## Geometry roles added

| Role | Purpose |
|------|---------|
| `CUTOUT_TEXT` | Routed/cut text geometry |
| `CUTOUT_LOGO` | Routed/cut logo geometry |
| `ACRYLIC_INSERT` | Insert geometry |

`ROUTED_FACE` is **not** introduced — treatment carries construction.

## Cardinality

| Binding | Cardinality |
|---------|-------------|
| `SUPPORT_CONTOUR` | MAX_ONE |
| Shell-local cutout/insert/decorative | MULTI |
| Letter/logo | MULTI (existing) |

## Backwards compatibility

Missing `face_treatment_code` → normalized to `NOT_APPLICABLE` for legacy roles. Does **not** invalidate the binding.

## Upsert identity

Frontend/backend identity is `binding_id` (+ role rules for letters/support). Never component_template_code alone (multiple ACM treatments share one template).
