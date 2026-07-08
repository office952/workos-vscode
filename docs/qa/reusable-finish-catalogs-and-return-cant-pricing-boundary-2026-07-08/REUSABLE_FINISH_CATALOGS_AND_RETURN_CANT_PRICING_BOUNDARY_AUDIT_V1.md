# REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY_AUDIT_V1

## Verdict

```text
REUSABLE_FINISH_CATALOGS_BOUNDARY_READY
```

## Scope checked

- docs-only
- no code changes
- no UI changes
- no Pricing changes
- no Product Truth writes

## HEAD

- accepted HEAD: `570bd22`
- after write: pending at write time

## Decision summary

Boundary-ul reutilizabil pentru finisaje este gata la nivel de contract:

1. `Culoare Stoc` ramane familie operationala fara extra finish cost.
2. `Folie autocolanta` devine family universala user-facing pentru `Oracal 641` si `Oracal 651`.
3. `Vopsit RAL` devine family universala user-facing pentru paint application.
4. cataloagele tin identitate si swatch UI, nu costuri.
5. Pricing tine cost material si cost manopera.

## Mandatory matrix

| ui_label | technical_variant | catalog_reference | required_ui_control | pricing_material_basis | pricing_labor_basis | width_affects_material | width_affects_labor | component_truth_fields | blockers |
|---|---|---|---|---|---|---|---|---|---|
| `Culoare Stoc` | `stock_color` | `stock_color_catalog` | list/typeahead with workshop-visible color label | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING` | `true` | `false` | `finish_variant.type`, `stock_color_label`, `pricing_keys.material_profile_width` | canonical catalog boundary not yet runtime-modeled |
| `Folie autocolanta — Oracal 641` | `vinyl_application` | `vinyl_color_catalog(series=641)` | selector with code + visible color | `MAT-ORACAL-641` at `mp`, qty = `perimetru_ml x latime_cant_m` | dedicated cant vinyl labor target `1 EUR/ml` | `true` | `false` | `finish_variant.vinyl.*`, `pricing_keys.vinyl_material`, `pricing_keys.vinyl_application_labor` | current return_cant UI/adapter only models 651 |
| `Folie autocolanta — Oracal 651` | `vinyl_application` | `vinyl_color_catalog(series=651)` | selector with code + visible color | `MAT-ORACAL-651` at `mp`, qty = `perimetru_ml x latime_cant_m` | dedicated cant vinyl labor target `1 EUR/ml` | `true` | `false` | `finish_variant.vinyl.*`, `pricing_keys.vinyl_material`, `pricing_keys.vinyl_application_labor` | current cant labor alignment still incomplete |
| `Vopsit RAL` | `paint_application` | `paint_color_catalog(system=RAL)` | selector with RAL code + visible color | width-based material target rows | dedicated paint labor target `1 EUR/ml` | `true` | `false` | `finish_variant.paint.*`, `pricing_keys.ral_paint_material_by_width`, `pricing_keys.ral_paint_labor` | current runtime remains tube-based and lacks paint-target truth |

## Catalog boundary confirmation

Catalog keeps:

- code
- name
- visible color / swatch
- series / system
- active status
- technical metadata

Catalog does not keep:

- price
- material cost
- labor cost
- final tariff

## Pricing boundary confirmation

Profile by width:

- `30 mm` -> `MAT-PROFIL-LATERAL-LITERE-30MM` -> `2 EUR/ml`
- `60 mm` -> `MAT-PROFIL-LATERAL-LITERE-60MM` -> `3 EUR/ml`
- `80 mm` -> `MAT-PROFIL-LATERAL-LITERE-80MM` -> `4 EUR/ml`
- `100 mm` -> `MAT-PROFIL-LATERAL-LITERE-100MM` -> `5 EUR/ml`

Return operations stay in Pricing:

- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`

Vinyl target:

- `MAT-ORACAL-641` and `MAT-ORACAL-651` as material rows in Pricing
- quantity = `perimetru_ml x latime_cant_m`
- vinyl application labor target = `1 EUR/ml`
- width affects material only

RAL target:

- material by width: `2 / 2.5 / 3 / 4 EUR/ml`
- paint labor target = `1 EUR/ml`
- width affects material only

Current live/runtime gap explicitly retained:

- dedicated cant vinyl labor row is not yet cleanly proven live
- width-aware RAL material rows are not yet represented cleanly in current runtime
- current legacy `MAT-VOPSEA-RAL` is tube-based, not final return_cant width-based paint material semantics

## Product Truth target proposal

```text
components.return_cant.instances.<instance_key>.finish_variant.type =
  stock_color | vinyl_application | paint_application

components.return_cant.instances.<instance_key>.finish_variant.stock_color_label
components.return_cant.instances.<instance_key>.finish_variant.vinyl.material_family
components.return_cant.instances.<instance_key>.finish_variant.vinyl.series
components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code
components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference
components.return_cant.instances.<instance_key>.finish_variant.paint.system
components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference
components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor
```

## UI preservation rules

- UI must say `Culoare Stoc`
- stock color stays operator-facing and workshop-readable
- Oracal selector must show code + visible color
- RAL selector must show code + visible color
- visible colors are mandatory
- Oracal/RAL selectors must not degrade to plain text

## Adapter impact

Current adapter status:

```text
valid as first pass
```

Next update needed:

- move semantic terms from `oracal` / `ral_paint` to `vinyl_application` / `paint_application`
- add `Oracal 641` readiness in reusable finish terms
- preserve `stock_color`
- keep adapter read-only

No critical discrepancy requiring STOP was found in this task.

## Forbidden scope confirmation

- no code changes
- no UI changes
- no Pricing changes
- no DB / seed / migration
- no Quote / Order / Execution
- no ProductAggregate / TaskGraph / ExecutionPlan

## Validation

- `git diff --check`
- docs-only diff
- no build
- no tests

## Next prompt

```text
RETURN_CANT_READONLY_ADAPTER_UNIVERSAL_FINISH_TERMS_UPDATE_V1
```