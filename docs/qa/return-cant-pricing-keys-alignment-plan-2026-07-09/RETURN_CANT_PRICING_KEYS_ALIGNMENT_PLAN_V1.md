# RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN_V1

## Verdict

```text
RETURN_CANT_PRICING_KEYS_ALIGNMENT_READY
```

## Scope checked

- docs-only
- no Pricing changes
- no UI changes
- no adapter changes
- no Product Truth writes
- no DB / seed / migration

## Accepted HEAD

- `d6b8d09`

## Decision summary

Planul de aliniere pentru Pricing keys este gata la nivel de contract:

1. profilele de cant pe latime exista deja si raman neschimbate;
2. `MAT-ORACAL-641` si `MAT-ORACAL-651` exista deja ca material rows valide pentru familia `vinyl_application`;
3. nu exista inca un labor row corect pentru aplicare folie pe cant `1 EUR/ml`;
4. nu exista inca material rows dedicate pentru `Vopsit RAL` pe latime `30/60/80/100 mm`;
5. nu exista inca un labor row dedicat pentru `Vopsit RAL` pe cant `1 EUR/ml`;
6. rows legacy `FACE_VINYL_APPLICATION_LABOR`, `VINYL_APPLICATION`, `PAINTING`, `MAT-VOPSEA-RAL` nu trebuie confundate cu targetul final `return_cant`.

## Evidence summary

### Exists now

- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`
- `PAINTING`
- `FACE_VINYL_APPLICATION_LABOR`
- `VINYL_APPLICATION` legacy
- `MAT-VOPSEA-RAL`

### Does not exist yet as exact target rows

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

## Naming recommendation

Recommended new rows:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

Naming reason:

1. material rows stay on the existing `MAT-*` inventory pattern;
2. labor rows stay on the existing uppercase underscore workcenter-rate pattern;
3. target rows do not overload `PAINTING` or `FACE_VINYL_APPLICATION_LABOR` with wrong scope or wrong unit.

## Mandatory matrix

| pricing_need | current_key | exists_now | proposed_key | unit | owner_value | width_dependent | used_by_variant | source_of_truth | blocker |
|---|---|---|---|---|---|---|---|---|---|
| profil cant 30 mm | `MAT-PROFIL-LATERAL-LITERE-30MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-30MM` | `ml` | `2 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing | none |
| profil cant 60 mm | `MAT-PROFIL-LATERAL-LITERE-60MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-60MM` | `ml` | `3 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing | none |
| profil cant 80 mm | `MAT-PROFIL-LATERAL-LITERE-80MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-80MM` | `ml` | `4 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing | none |
| profil cant 100 mm | `MAT-PROFIL-LATERAL-LITERE-100MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-100MM` | `ml` | `5 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing | none |
| Oracal 641 material | `MAT-ORACAL-641` | `yes` | `MAT-ORACAL-641` | `mp` | `6.5 EUR/mp` | `false` | `vinyl_application` | Pricing | runtime cant direct input still 651-only |
| Oracal 651 material | `MAT-ORACAL-651` | `yes` | `MAT-ORACAL-651` | `mp` | `9 EUR/mp` | `false` | `vinyl_application` | Pricing | none |
| aplicare folie pe cant | `FACE_VINYL_APPLICATION_LABOR` nearest row | `no` | `RETURN_CANT_VINYL_APPLICATION_LABOR` | `ml` | `1 EUR/ml` | `false` | `vinyl_application` | Pricing | nearest current row is face-only and `mp` |
| RAL material cant 30 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-30MM` | `ml` | `2 EUR/ml` | `true` | `paint_application` | Pricing | current row is tube-based |
| RAL material cant 60 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-60MM` | `ml` | `2.5 EUR/ml` | `true` | `paint_application` | Pricing | current row is tube-based |
| RAL material cant 80 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-80MM` | `ml` | `3 EUR/ml` | `true` | `paint_application` | Pricing | current row is tube-based |
| RAL material cant 100 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-100MM` | `ml` | `4 EUR/ml` | `true` | `paint_application` | Pricing | current row is tube-based |
| RAL labor | `PAINTING` nearest row | `no` | `RETURN_CANT_RAL_PAINT_LABOR` | `ml` | `1 EUR/ml` | `false` | `paint_application` | Pricing | `PAINTING` is generic and currently `4 EUR/ml` |

## Boundary confirmation

- componenta nu stocheaza valori EUR
- Product Truth nu stocheaza costuri
- adapterul emite doar pricing key references
- Pricing este singurul owner pentru valori
- catalogul este owner pentru cod / culoare / swatch, nu cost
- formula ramane declarativa

## Formula summary

`Culoare Stoc`

```text
material_profile_quantity_ml = confirmed_perimeter_m
extra_finish_cost = none
```

`Folie autocolanta`

```text
vinyl_material_quantity_mp = confirmed_perimeter_m x latime_cant_m
vinyl_application_labor_quantity_ml = confirmed_perimeter_m
```

`Vopsit RAL`

```text
ral_paint_material_key = width_selected_row
ral_paint_labor_quantity_ml = confirmed_perimeter_m
```

## Validation

- safety gate on accepted HEAD `d6b8d09`
- read-only code/doc audit
- no tests
- `git diff --check`

## Next prompt

```text
RETURN_CANT_PRICING_KEYS_CREATION_AND_REGISTRY_ALIGNMENT_V1
```