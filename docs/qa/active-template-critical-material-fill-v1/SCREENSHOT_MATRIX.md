# ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 — Screenshot Matrix

Viewport 1440×1100 · FE `:3000` · API `:8020`

| # | File | Steps | Expected | Verdict |
|---|------|-------|----------|---------|
| 1 | `01_material_pricing_overview.png` | Pricing → Preturi materiale | Registry loads; Critical lipsa = 0 | PASS |
| 2 | `02_psu_selector_generic.png` | Click MAT-LED-PSU-12V | Selector familie note; no direct price | PASS |
| 3 | `03_psu_variant_100w.png` | Click MAT-LED-PSU-12V-100W | 16 EUR OWNER_CONFIRMED | PASS |
| 4 | `04_finish_line_critical_cleared.png` | VL overview finish-line panel | No MAT-LED-PSU-12V critical | PASS |
| 5 | `05_vl_breakdown_materials.png` | VL pricing → materials | Concrete PSU variant line | PASS |
| 6 | `06_vl_eic_cpp_reconcile.png` | Totals | EIC 923.2 / CPP 1061 OK | PASS |
