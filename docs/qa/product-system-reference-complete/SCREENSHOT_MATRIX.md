# PRODUCT_SYSTEM_REFERENCE_COMPLETE — Screenshot matrix

Viewport 1440×1100 · FE `:3000` · API `:8020` · capture: `capture_screenshots.mjs`

| # | File | URL | Fixture | Steps | Visible truth | Expected | Verdict |
|---|------|-----|---------|-------|---------------|----------|---------|
| 1 | `screenshots/01_reference_complete_status.png` | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | VL v2 | Open detail → wait `reference-complete-panel` | Overall PASS + READY_FOR_DOCUMENTATION_HANDOFF | Reference closure visible | PASS |
| 2 | `screenshots/02_accepted_limitations.png` | same | VL v2 | Expand limitations | 9 accepted limitations listed | Limitations explicit, not blockers | PASS |
| 3 | `screenshots/03_eic_cpp_distinction.png` | same → Pricing tab | `vl_letters_demo_v1` | Open pricing totals | EIC production cost vs CPP reconciliation | Finish line = EIC | PASS |
| 4 | `screenshots/04_psu_selector_and_zero_critical.png` | `/inventory/pricing` | market registry | Preturi materiale → row `MAT-LED-PSU-12V` | variant_selector · no generic price · critical cleared | Selector honesty | PASS |

No redundant historic pack reproduced.
