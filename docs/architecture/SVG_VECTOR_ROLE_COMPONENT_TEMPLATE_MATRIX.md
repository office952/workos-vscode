# Matrix — SVG vector roles ↔ Component / Product Templates

Audit matrix 2026-07-17. Labels are owner-facing; codes are technical.

## Current options (Step 1 owner dropdown)

| Optiune actuală | Cod | Product Template | Component Template | PD / payload field | Runtime consumer |
|-----------------|-----|------------------|--------------------|--------------------|------------------|
| Vector Litere | `face` | Recommended `TPL-VOLUMETRIC-LETTERS_v2` | Process `FACE` (indirect) | `layer_role_setup`, `selected_layer_refs.role=vector_litere` | Composition recommendation |
| Vector Logo | `printed_artwork` | Recommended `TPL-VOLUMETRIC-LOGO_v1` (candidate) | Logo modules (scaffold) | `vector_logo` | Composition (non-offerable root) |

## Latent layer catalog (not Step 1 select)

| Optiune | Cod | Product Template | Component / note | PD field | Consumer |
|---------|-----|------------------|------------------|----------|----------|
| Fundal / suport / bond / caseta | `support_panel` | **Pending** `TPL-BOND-CASETAT` | Stale vs ACM boxed | composition item pending | Warning `SUPPORT_TEMPLATE_PENDING` |
| Decupaj interior | `inner_hole` | — | Illumination/hole helpers | layer_role_setup | Analyzer / Bond linkage |
| Gauri montaj | `drill` | — | — | layer_role_setup | Production hint |
| Referinta / ghidaj | `reference` | — | — | layer_role_setup | Hint |
| Ignora strat | `ignore` | — | — | layer_role_setup | Excluded |
| Cant / volum | `return` | Linked cant module | Process `CANT` | layer_role_setup | Latent |
| Spate / backing | `backing` | Back module | Process `BACK` | layer_role_setup | Latent |
| Vinil aplicat | `vinyl` | — | Finish path | layer_role_setup | Latent |
| De confirmat | `unknown` | — | — | layer_role_setup | Pending |

## Closed-contour roles (parallel panel)

| Optiune | Cod | Product Template | Process / component | PD field | Consumer |
|---------|-----|------------------|---------------------|----------|----------|
| Panou Alucobond casetat | `ALUCOBOND_CASED_PANEL` | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Process `ALUCOBOND_CASED_PANEL` | Intended `svg_support_selection` + `mounting_solution` | Mounting / PD (partial) |
| Fundal plat | `FLAT_BACKGROUND` | — | None (inactive casing) | selection status | Isolation |
| Contur decorativ | `DECORATIVE_CONTOUR` | — | None | selection | Isolation |
| Element grafic | `GRAPHIC_ELEMENT` | — | None | selection | Isolation |
| Ignoră | `IGNORE` | — | None | selection | Isolation |

## Recommended target matrix (not implemented)

| Geometry unit | Geometric role (generic) | Assignable component (from PS) | Technical codes |
|---------------|--------------------------|--------------------------------|-----------------|
| Layer / path group (letters) | Contur litere / Vector litere | Letters body (FACE…) under letters product | `face` → letters root |
| Layer / artwork (logo) | Contur logo / Vector logo | Logo child when activated | `printed_artwork` → `TPL-VOLUMETRIC-LOGO_v1` |
| Closed outer contour | Contur suport | Optional: Panou Alucobond casetat **or** metal bars **or** none | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / `METAL_SUPPORT` |
| Decorative closed | Contur decorativ | Ignore / no component | — |

Rules:

- Role ≠ material.
- Component list comes from **active Product Template composition**, not FE hardcode.
- Retire `TPL-BOND-CASETAT` as recommendation target; use ACM boxed or metal PS templates.
- One support instance in V1.
