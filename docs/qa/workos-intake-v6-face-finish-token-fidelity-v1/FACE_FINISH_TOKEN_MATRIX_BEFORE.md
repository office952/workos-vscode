# FACE_FINISH_TOKEN_MATRIX_BEFORE

**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_FACE_FINISH_TOKEN_FIDELITY_V1`  
**Baseline HEAD:** `27a0cbac`  
**Capture:** adapter unit probe via `build_v4_pricing_input_preview` (no Owner DB mutation)

## Template mapper (`_template_face_finish_type`)

| UI / persisted token | template type | `_face_oracal_series` |
|---|---|---|
| `none` | `none` | `651` (unused for none) |
| `oracal_641` | **`oracal_651`** | `641` |
| `oracal_651` | `oracal_651` | `651` |
| `oracal_8500` | **`oracal_651`** | `8500` |
| `print_laminate` | `printed_laminated_vinyl` | `651` (unused) |
| `vinyl` (legacy) | `oracal_651` | `651` |
| `printed_vinyl` | `printed_vinyl` | `651` (unused) |

## End-to-end preview (job-level + one letter group)

| selected | persisted (setup) | `quote_input.face_finish_type` | handoff `face_finish_type` | handoff raw / series | matrix `face_finish_type` / template | finish_summary |
|---|---|---|---|---|---|---|
| none | none | `none` | _(no vinyl handoff)_ | — | `none` / `none` | `none` |
| oracal_641 | oracal_641 | **`vinyl`** | **`oracal_651`** | raw=`oracal_641`, series=`641` | `oracal_641` / **`oracal_651`** | **`vinyl`** |
| oracal_651 | oracal_651 | **`vinyl`** | `oracal_651` | raw=`oracal_651`, series=`651` | `oracal_651` / `oracal_651` | **`vinyl`** |
| oracal_8500 | oracal_8500 | `oracal_8500` | **`oracal_651`** + subtype `oracal_8500` | raw=`oracal_8500`, series=`8500` | `oracal_8500` / **`oracal_651`** | `oracal_8500` |
| print_laminate | print_laminate | **`printed_vinyl`** | `printed_laminated_vinyl` | raw=`print_laminate` | `print_laminate` / `printed_laminated_vinyl` | **`printed_vinyl`** |

## CPP contract (unchanged authority)

| rule line | material_gate |
|---|---|
| `finisaje_oracal_641_material` | `finish_setup.face_finish_type == oracal_641` |
| `finisaje_oracal_651_material` | `finish_setup.face_finish_type == oracal_651` |
| `finisaje_oracal_8500_material` | `finish_setup.face_finish_type == oracal_8500` |
| `finisaje_print_laminate_material` | token ∈ `{print_laminate, printed_laminated_vinyl}` |
| `finisaje_aplicare_autocolant_fata` | token ∈ Oracal ∪ print laminate set |
| none | no additional face Oracal / print / aplicare |

## Dry-run bridge gap

`_enrich_quote_input_linked_logo_geometry` does **not** copy workspace `face_finish_type` / `letter_group_finishes` into `quote_input.finish_setup`.  
CPP `_coalesce_quote_input` then lifts top-level `vinyl` / `printed_vinyl` into `finish_setup.face_finish_type`, so series-specific gates miss.

## Defect summary

1. `_map_v4_face_finish`: `oracal_641` / `oracal_651` → V3 `vinyl` (operation catalog), becomes `quote_input.face_finish_type`.
2. `_template_face_finish_type`: all vinyl family → `oracal_651` in handoff / matrix template.
3. Enrich omits commercial face identity → CPP never sees `oracal_641` / `oracal_651` / `print_laminate`.
