# PRODUCT_PRICE_BREAKDOWN_V1 — Screenshot Matrix

Viewport: 1440×1100 · FE `http://127.0.0.1:3000` · API proof `:8020` · capture: `capture_screenshots.mjs`

| # | Path | URL / steps | Expected | Verdict |
|---|------|-------------|----------|---------|
| 01 | `screenshots/01_vl_overview.png` | VL → Prețuri template | Studio + Desfășurător present | PASS |
| 02 | `screenshots/02_vl_totals.png` | scroll totals | Intern 923.20 · Comercial 1061.00 · CPP/EIC OK · fixture `vl_letters_demo_v1` | PASS |
| 03 | `screenshots/03_vl_materials.png` | filter Materiale | material / gap lines visible | PASS |
| 04 | `screenshots/04_vl_machine.png` | filter Utilaje | machine formulas | PASS |
| 05 | `screenshots/05_vl_labor.png` | filter Manoperă | labor / commercial labor lines | PASS |
| 06 | `screenshots/06_vl_ai.png` | filter Decizii AI | AI contribution lines | PASS |
| 07 | `screenshots/07_vl_full_page.png` | full page | reconcile visible end-to-end | PASS |
| 08 | `screenshots/08_acm_shell.png` | ACM → Prețuri | shell breakdown · treatments chip | PASS |
| 09 | `screenshots/09_acm_treatments_blocked.png` | ACM chip | `Tratamente ACM blocate` | PASS |
| 10 | `screenshots/10_logo_preview.png` | Logo → Prețuri | AI preview · no fake commercial total | PASS |
| 11 | `screenshots/11_volum_aluminiu_child.png` | Volum Aluminiu | child perimeter slice · not root | PASS |

Capture log: `screenshots/capture_log.json`
