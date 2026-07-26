# MATERIAL_MARKET_PRICE_REGISTRY_V1 — Screenshot Matrix

Viewport 1440×1100 · FE `:3000` · API `:8020`

| # | Path | URL / steps | Expected | Verdict |
|---|------|-------------|----------|---------|
| 01 | `screenshots/01_pricing_overview.png` | `/inventory/pricing` | Pricing shell | PASS |
| 02 | `screenshots/02_material_registry.png` | Catalog → Preturi materiale | Registry panel + counts | PASS |
| 03 | `screenshots/03_missing_prices.png` | filter Pret lipsa | Missing visible, not hidden | PASS |
| 04 | `screenshots/04_acm_3mm_detail.png` | MAT-ACM-BOND-3MM | 15 EUR/mp · OWNER_CONFIRMED | PASS |
| 05 | `screenshots/05_registry_full.png` | filter Toate | Full list | PASS |
| 06 | `screenshots/06_vl_material_breakdown.png` | VL → Desfasurator → Materiale | Purchase provenance on lines | PASS |
| 07 | `screenshots/07_acm_breakdown.png` | ACM → Desfasurator | Shell honest | PASS |
