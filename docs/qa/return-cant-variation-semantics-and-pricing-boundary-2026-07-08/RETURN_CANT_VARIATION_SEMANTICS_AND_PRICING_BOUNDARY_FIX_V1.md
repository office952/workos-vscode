# RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY_FIX_V1

## Verdict

```text
RETURN_CANT_VARIATION_SEMANTICS_READY_FOR_ADAPTER
```

## Scope checked

- docs-only
- no code changes
- no UI changes
- no Pricing changes
- no adapter implementation

## HEAD

- accepted HEAD: `baa9541`
- after write: pending at write time

## Problem corrected

Auditul precedent folosea prea generic notiunea de `stock finish` pentru `Alb`, `Negru`, `Auriu`, `Argintiu`.

Corectia owner este:

- acestea sunt `stock_color`, nu `extra finish cost`;
- costul vine din profilul de material si din latimea cantului;
- Oracal si RAL raman singurele variatii de extra finish cost semantic.

## Mandatory matrix

| current_ui_option | corrected_semantic_variant | stock_color_label | extra_finish_cost | pricing_source | width_affects_cost | product_truth_target | adapter_rule | blocker |
|---|---|---|---|---|---|---|---|---|
| `Alb` | `stock_color` | `Alb` | `false` | `material_profile_width` | `true` | `finish_variant.type=stock_color`, `stock_color_label=Alb` | no separate finish pricing key | runtime writer missing |
| `Negru` | `stock_color` | `Negru` | `false` | `material_profile_width` | `true` | `finish_variant.type=stock_color`, `stock_color_label=Negru` | no separate finish pricing key | runtime writer missing |
| `Auriu` | `stock_color` | `Auriu` | `false` | `material_profile_width` | `true` | `finish_variant.type=stock_color`, `stock_color_label=Auriu` | no separate finish pricing key | runtime writer missing |
| `Argintiu` | `stock_color` | `Argintiu` | `false` | `material_profile_width` | `true` | `finish_variant.type=stock_color`, `stock_color_label=Argintiu` | no separate finish pricing key; normalize legacy silver aliases | alias normalization needed |
| `Oracal 651` | `oracal` | n/a | `true` | `/inventory/pricing` | `true` | `finish_variant.type=oracal`, `oracal_code`, `pricing_keys.finish_extra` when real | preserve Oracal code + color selector; emit key or blocker only | pricing alignment gap remains |
| `Vopsit RAL` | `ral_paint` | n/a | `true` | `/inventory/pricing` | `maybe/confirm from Pricing` | `finish_variant.type=ral_paint`, `ral_code`, optional `paint_target`, `pricing_keys.finish_extra` when real | preserve RAL code + color selector; emit key or blocker only | width-to-price and paint_target gap |

## Product Truth semantic target

```text
components.return_cant.instances.<instance_key>.finish_variant.type =
  stock_color | oracal | ral_paint

components.return_cant.instances.<instance_key>.finish_variant.stock_color_label
components.return_cant.instances.<instance_key>.finish_variant.oracal_code
components.return_cant.instances.<instance_key>.finish_variant.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint_target
components.return_cant.instances.<instance_key>.depth_mm
components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.finish_extra
```

Notes:

- `pricing_keys.*` are references only
- component still stores no cost or price values

## Pricing boundary confirmation

- stock color nu are cost suplimentar de finish
- latimea cantului afecteaza costul material
- Oracal are cost separat in Pricing
- RAL / vopsire are cost separat in Pricing
- componenta nu stocheaza cost sau pret

## UI preservation confirmation

- selectorul Oracal cod + culoare se pastreaza
- selectorul RAL cod + culoare se pastreaza
- nu se inlocuiesc cu text simplu

## Adapter rule summary

Must transform:

- `Alb/Negru/Auriu/Argintiu` -> `stock_color`
- `Oracal 651` -> `oracal`
- `Vopsit RAL` -> `ral_paint`

Must not transform:

- `stock_color` into extra finish pricing key
- missing Oracal/RAL pricing key into invented estimate
- Oracal/RAL selectors into plain text

## Decision basis

READY for adapter because:

1. UI taxonomy is already stable
2. material width pricing exists live
3. semantic correction is now explicit
4. adapter can map rows without inventing cost semantics

## Forbidden scope confirmation

- no code changes
- no UI changes
- no Pricing changes
- no component root
- no component quote
- no Quote / Order / Execution changes
- no DB / seed / migration

## Validation

- `git diff --check`
- docs-only diff only
- no build
- no tests

## Next prompt

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```