# pricing-truth-evidence

Plan-mode artifact. Canonical JSON body below (no customer SVG).  
Rename/copy to `pricing-truth-evidence.json` at docs-only commit if required.

```json
{
  "task": "WORKOS-GRADI-CURAT-PRICING-TRUTH-AUDIT-FINAL-OWNER-REPORT",
  "captured_at": "2026-07-16",
  "audit_baseline_head": "99d5c71",
  "branch": "feature/product-system-active-path-isolation-v1",
  "runtime": {
    "backend": "http://127.0.0.1:8001",
    "frontend": "http://127.0.0.1:3000",
    "workspace_id": "11891d68-c4c8-4719-acc5-f8fcb22a44af",
    "svg_path_noted_not_dumped": "C:\\Users\\offic\\Desktop\\fisiere-teste-svg\\gradi-curat.svg"
  },
  "verdict": {
    "audit_classification": "GRADI_CURAT_PRICING_FIRST_BLOCKER_FOUND",
    "commercial_safety": "COMMERCIAL_PARTIAL_NOT_CONFIRMABLE",
    "primary_blocker_category": "COMMERCIAL_RULE",
    "can_operator_confirm": false,
    "logo_template_classification": "PARTIAL_LINKED_CHILD",
    "missing_prices_classification": "FALSE_POSITIVE_INFORMATIONAL_ROW",
    "currency_classification": "MIXED_CURRENCY_MISLEADING"
  },
  "commercial_totals_live": {
    "source_endpoint": "GET /api/v1/intake-v6/workspaces/{id}/priced-quote-dry-run",
    "authority": "commercial_price_proposal_7g",
    "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "subtotal_net": 2154.51,
    "vat_rate": 21.0,
    "vat_amount": 452.45,
    "total_gross": 2606.96,
    "currency": "RON",
    "ui_label": "Valoare estimată cu TVA",
    "can_create_quote_snapshot": false,
    "can_write_quote_totals": false,
    "stale_value_not_live": "2587.94_RON_recalled_do_not_use"
  },
  "internal_mb_totals_live": {
    "source": "material-breakdown",
    "material_cost_total": 725.16,
    "estimated_cost_total": 725.16,
    "currency": "EUR",
    "contains_missing_prices": true
  },
  "cpp_lines": [
    {"code": "debitare_fata", "pricing_rule_code": "VOL_V2_FACE_CNC_ML", "quantity": 21.1675, "unit": "ml", "commercial_unit_price": 25.0, "subtotal": 529.1875, "component_code": "comp_face_litere"},
    {"code": "modelare_cant_aluminiu", "pricing_rule_code": "VOL_V2_RETURN_PROFILE_ML", "quantity": 21.1675, "unit": "ml", "commercial_unit_price": 30.0, "subtotal": 635.025, "component_code": "comp_lateral_litere"},
    {"code": "debitare_spate", "pricing_rule_code": "VOL_V2_BACK_CNC_M2_DEV_BRIDGE", "quantity": 1.2638, "unit": "m2", "commercial_unit_price": 20.0, "subtotal": 25.276, "component_code": "comp_spate_litere"},
    {"code": "sistem_led_module", "pricing_rule_code": "VOL_V2_LED_MODULE_PIECE", "quantity": 145, "unit": "buc", "commercial_unit_price": 5.0, "subtotal": 725.0, "component_code": "comp_led_litere"},
    {"code": "sursa_led", "pricing_rule_code": "VOL_V2_LED_PSU_PIECE", "quantity": 1.0, "unit": "buc", "commercial_unit_price": 150.0, "subtotal": 150.0, "component_code": "comp_led_litere"},
    {"code": "finisaje_colantare_vopsire", "pricing_rule_code": "VOL_V2_FINISH_M2_OR_MINIMUM", "quantity": 1.2638, "unit": "m2", "commercial_unit_price": 35.0, "subtotal": 44.233, "component_code": "comp_finisaj_litere"},
    {"code": "sablon_montaj_forex", "pricing_rule_code": "VOL_V2_SABLON_FOREX_DEV_BRIDGE", "quantity": 3.0523, "unit": "m2", "commercial_unit_price": 15.0, "subtotal": 45.7845, "component_code": "comp_finisaj_litere"},
    {"code": "ambalare", "pricing_rule_code": "VOL_V2_PACKAGING_PENDING", "quantity": null, "commercial_unit_price": null, "subtotal": null, "owner_decision_required": true},
    {"code": "montaj", "pricing_rule_code": "VOL_V2_SITE_MOUNT_FUTURE", "quantity": null, "commercial_unit_price": null, "subtotal": null, "owner_decision_required": true}
  ],
  "logo_cpp": {
    "logo_1_lines": [],
    "logo_2_lines": [],
    "null_price_logo_lines": false,
    "fallback_letter_lines": false,
    "duplicated_logo_lines": false,
    "linked_child_enters_cpp": false
  },
  "composition_items": [
    {"composition_item_id": "letters", "template_code": "TPL-VOLUMETRIC-LETTERS_v2", "source_layer_ids": ["pseudo:maria", "pseudo:soare", "pseudo:ana", "pseudo:gradinita"], "status": "suggested"},
    {"composition_item_id": "logo", "template_code": "TPL-VOLUMETRIC-LOGO_v1", "source_layer_ids": ["logo_instance_001", "logo_instance_002"], "status": "suggested"}
  ],
  "logo_template_live": {
    "code": "TPL-VOLUMETRIC-LOGO_v1",
    "template_availability_api": false,
    "product_definition_standalone": "404",
    "aggregate_standalone": "template_not_found",
    "letters_pd_linked_segments": true,
    "letters_pa_linked_logo_segments": 0,
    "db_row_direct_sqlite": "UNPROVEN_this_pass"
  },
  "contains_missing_prices": {
    "live": true,
    "predicate": "qty>0 && estimated_cost is None && material_cost is None",
    "predicate_file": "backend/services/intake_v6_offer_scope_live_calc_service.py::_is_price_missing_material",
    "exact_rows": [{"material_key": "led_total_watts", "quantity": 108.75, "price_source": "informational_only", "unit_price": null, "material_cost": null}],
    "classification": "FALSE_POSITIVE_INFORMATIONAL_ROW",
    "primary_blocker": false
  },
  "geometry_live_summary": {
    "letter_face_area_m2_sum": 1.2637622559580237,
    "cpp_face_return_ml": 21.1675,
    "cnc_face_ml": 24.6488,
    "cnc_back_ml": 26.7471,
    "return_material_m_base": 31.6382,
    "logo_bbox_m2_each": 0.4002,
    "logo_service_m2_with_waste": 0.4802,
    "led_modules": 145,
    "led_watts_informational": 108.75,
    "psu_count": 1
  },
  "diagnostic_cost_plus_non_authority": {
    "diagnostic_only": true,
    "internal_cost_total": 725.16,
    "internal_cost_currency": "EUR",
    "eur_to_ron_rate": 5.0,
    "subtotal_net": 4894.83,
    "total_gross": 5922.74,
    "currency": "RON"
  },
  "owner_gates": ["G1", "G2", "G3", "G4", "G5"],
  "probe_files": [
    "_probe_priced-quote-dry-run.json",
    "_probe_material-breakdown.json",
    "_probe_product-definition.json",
    "_probe_aggregate.json",
    "_probe_logo-pd.json",
    "_probe_logo_aggregate.json",
    "_probe_template-availability.json",
    "_probe_workspace.json",
    "_probe_pricing-input-preview.json"
  ],
  "svg_contents_included": false
}
```
