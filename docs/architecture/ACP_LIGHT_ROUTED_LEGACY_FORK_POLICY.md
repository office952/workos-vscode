# TPL-ACP-LIGHT-ROUTED — Legacy Fork Policy

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Status | `PARALLEL_LEGACY_COST_PATH` |
| Intake V6 composition authority | **false** |
| Face-treatment authority | **false** |
| Live shell authority | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

## Policy

1. Do **not** delete the template or its seeds.
2. Do **not** use it as SVG bindable / FinishSetup face-treatment authority.
3. Do **not** auto-import CostEngine components, task rules, or pricing into V6 face modules.
4. Reject bindings that set `component_template_code = TPL-ACP-LIGHT-ROUTED` for new Intake V6 selection.
5. Migration into local face modules requires a dedicated owner GO.

## Known consumers (inventory — no cleanup in this GO)

- `seed_tpl_acp_light_routed` / `seed_sync_all`
- CostEngine / QuoteWizard hierarchical `quote_input`
- `svg_layer_template_mapping` label map
- ProductSystem gate / registry linkage tests
- E2E script `e2e_test_tpl_acp_light_routed.py`

## Deprecation

Not marked deprecated: runtime still uses the parallel Cost path without a full V6 replacement for illuminated cabinet quoting.
