# Contract — Product System SVG component binding

| Field | Value |
|-------|-------|
| Status | Active (V1) |
| Authority | Product System (code-owned contract) |
| Schema | `product_system_svg_component_binding_contract_v1` |
| Date | 2026-07-17 |

## Separation

```text
SVG geometry role     = intentie geometrica (nu material)
Component Template    = componenta tehnica reutilizabila
Product Template      = declara ce componente SVG-bindable sunt disponibile
Intake (later)        = asociaza geometria cu componentele expuse
ProductDefinition     = salveaza component instances
```

## Canonical geometry roles

| Code | Owner label |
|------|-------------|
| `LETTER_VECTOR_SET` | Vector litere |
| `LOGO_VECTOR_SET` | Vector logo |
| `SUPPORT_CONTOUR` | Contur suport |
| `DECORATIVE_VECTOR` | Element decorativ |
| `IGNORE` | Ignoră |

**Forbidden as geometry roles:** `Vector ACP`, material names, Product Template codes.

## Source of truth

- Data: `backend/data/product_system/svg_component_binding_contract.py`
- Projector: `backend/services/svg_component_binding_service.py`
- Read model: `GET /api/v1/product-system/template-availability` → `svg_bindable_components[]`

## Letters root (`TPL-VOLUMETRIC-LETTERS_v2`)

| Component | Geometry role | Selection | Cardinality | Required | Active by default |
|-----------|---------------|-----------|-------------|----------|-------------------|
| `TPL-VOLUMETRIC-FACE_v1` | `LETTER_VECTOR_SET` | `LAYER_OR_GROUP` | `MULTI` | yes | yes |
| `TPL-VOLUMETRIC-LOGO_v1` | `LOGO_VECTOR_SET` | `LAYER_OR_GROUP` | `MULTI` | no | no (guarded candidate) |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | `SUPPORT_CONTOUR` | `CLOSED_CONTOUR` | `MAX_ONE` | no | no |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | — | `NONE` | — | no | no (SVG not required) |

`available != active`. Optional components stay inactive until operator activation (later Intake build).

## ACP live authority

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` · owner label **Panou Alucobond casetat** · process `ALUCOBOND_CASED_PANEL`.

## ProductDefinition targets (documented; FinishSetup fix is a later GO)

| Component | Targets |
|-----------|---------|
| Letters | `layer_role_setup`, `selected_layer_refs.vector_litere`, composition letters |
| Logo | `layer_role_setup`, `selected_layer_refs.vector_logo`, composition logo |
| ACP | `mounting_solution`, `svg_support_selection` (schema gap), `support_type=alucobond_cased`, panel/casing/corner |

## Legacy Intake adapter

`LEGACY_INTAKE_SVG_ROLE_ADAPTER` = hardcoded FE `INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS`.  
Do not extend with ACP. Next Intake build consumes this projection.

## Boundaries

No CPP, tasking, DXF, CUT/FOLD, schema/migration/seed, Intake Step 1 UI change in this build.
