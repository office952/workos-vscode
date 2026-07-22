# CE Shared Map — MAT-LED-PSU-12V

| Field | Value |
|-------|--------|
| material_code | MAT-LED-PSU-12V |
| material_role | variant_selector / family_placeholder |
| active_templates | role references (LED modules); priced path uses variants |
| quantity_source | psu_count + selected_psu_watts |
| variant_selector | quote_input.selected_psu_watts \| psu_watts |
| resolved_variant | MAT-LED-PSU-12V-{60\|100\|160\|200}W |
| price_source | OWNER_CONFIRMED on variant rows |
| unit | buc |
| current_status | selector missing direct price (intentional) |
| canonical | yes as selector; no as purchase SKU |
| duplicate_of | n/a — expands to 4 SKUs |
| readiness_effect | warning when variants ready; not price_incomplete on generic |
| CPP_reader | resolved variant rate via volumetric_material_rate_resolver |
| EIC_reader | material_MAT-LED-PSU-12V-{W}W lines |
| remediation | Outcome A — classify selector; no generic price |
| data_write_required | no (no unit_cost write) |
| risk | low |
| confidence | high |
