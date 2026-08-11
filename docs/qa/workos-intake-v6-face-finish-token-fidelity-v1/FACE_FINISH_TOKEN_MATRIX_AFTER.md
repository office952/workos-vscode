# FACE_FINISH_TOKEN_MATRIX_AFTER

**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_FACE_FINISH_TOKEN_FIDELITY_V1`  
**Baseline before:** `27a0cbac`  
**Capture:** `build_v4_pricing_input_preview` after adapter repair

## Template mapper (`_template_face_finish_type`)

| UI / persisted token | template type |
|---|---|
| `none` | `none` |
| `oracal_641` | `oracal_641` |
| `oracal_651` | `oracal_651` |
| `oracal_8500` | `oracal_8500` |
| `print_laminate` | `printed_laminated_vinyl` |
| `vinyl` (legacy generic) | `oracal_651` |

## End-to-end preview

| selected | `quote_input.face_finish_type` | handoff `face_finish_type` | handoff series | matrix template | finish_summary |
|---|---|---|---|---|---|
| none | `none` | _(no vinyl handoff)_ | — | `none` | `none` |
| oracal_641 | `oracal_641` | `oracal_641` | `641` | `oracal_641` | `oracal_641` |
| oracal_651 | `oracal_651` | `oracal_651` | `651` | `oracal_651` | `oracal_651` |
| oracal_8500 | `oracal_8500` | `oracal_8500` | `8500` | `oracal_8500` | `oracal_8500` |
| print_laminate | `print_laminate` | `printed_laminated_vinyl` | — | `printed_laminated_vinyl` | `print_laminate` |
| mixed 641+651 | job-level dominant (641) | per-group `oracal_641` + `oracal_651` | `641` + `651` | both preserved | dominant |

## Dry-run enrich

Workspace `face_finish_type` / `letter_group_finishes` are bridged into `quote_input.finish_setup`.  
Collapsed adapter values `vinyl` / `printed_vinyl` are overwritten by the workspace operator token when present.
