# FREEZE_AND_COMPATIBILITY

## Freeze path

1. Product aggregate materials carry `formula_id` / `formula_params` (incl. gates).
2. `apply_technical_material_requirements` filters inactive variants, then evaluates formulas.
3. Registered `return_wrap_area` → Model A `derived` when perimeter + depth present.
4. Unregistered `return_paint_consumption` → Model A intent, `source_missing`, qty null.
5. Result frozen into Quote Snapshot V2 / Order PA materials.
6. Ops-graph projects RO statuses (v2).

## Compatibility

| Snapshot vintage | Behavior |
|------------------|----------|
| Pre-contract (92401) | null qty → `legacy_unspecified`; not rewritten |
| Post-contract wrap freeze | `derived` + numeric m² when inputs owned |
| Post-contract paint freeze | emit when gate matches; qty null until yield owned |
| Formula-less | Model D `reference_only` (unchanged) |

## Non-goals (unchanged)

No inventory qty, no material_inputs wiring, no materialize, no pricing truth, no FE calculation.
