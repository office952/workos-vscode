# CPP_FACE_LINE_TRACE

## Authority (unchanged)

| Face token | Material line | Application |
|---|---|---|
| `oracal_641` | `finisaje_oracal_641_material` @ 6.5 EUR/m² | `finisaje_aplicare_autocolant_fata` @ 3.0 EUR/m² |
| `oracal_651` | `finisaje_oracal_651_material` @ 5.0 EUR/m² | same aplicare |
| `oracal_8500` | `finisaje_oracal_8500_material` @ 17/13.5 by width | same aplicare |
| `print_laminate` | `finisaje_print_laminate_material` @ 10.0 EUR/m² | same aplicare |
| `none` | _(none)_ | _(none)_ |

`PRICING_RULE_CHANGES = 0` — existing `commercial_rules_volumetric_v2` rows remain authority.

## Adapter → CPP proof (unit)

From `tests/test_intake_v6_face_finish_token_fidelity.py`:

| selected | material line present | unit price |
|---|---|---|
| 641 | `finisaje_oracal_641_material` | 6.5 |
| 651 | `finisaje_oracal_651_material` | 5.0 |
| 8500 @ 1260 | `finisaje_oracal_8500_material` | 13.5 |
| print_laminate | `finisaje_print_laminate_material` | 10.0 |
| none | no Oracal/print/aplicare | — |

## Owner workspace read-only repro

Workspace: `03a1da1e-003a-4139-9668-59ac6bcec812`  
`OWNER_DEV_DB_MUTATIONS = 0`

| Field | Value |
|---|---|
| operator_face | `oracal_641` |
| quote_input_face | `oracal_641` |
| finish_setup_face | `oracal_641` |
| handoff | raw=`oracal_641`, type=`oracal_641`, series=`641` |
| CPP face lines | `finisaje_oracal_641_material` 6.5 → subtotal 2.1439; `finisaje_aplicare_autocolant_fata` 3.0 → 0.9895 |
| CPP status | `ready` |

Cant Oracal lines remain independent (`finisaje_cant_oracal_*`) and are not face-series collapse.
