# AI_OPERATIONAL_DEFAULTS_V1 — Screenshot Matrix

Viewport ~1440×1100 · FE `http://127.0.0.1:3000` · backend proof `:8020`

| # | File | URL / template | Steps | Expected | Verdict |
|---|------|----------------|-------|----------|---------|
| 01 | `screenshots/01_vl_pricing_overview_ai.png` | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` → Prețuri | open tab, scroll AI | Decizii operaționale AI · 4 rows | PASS |
| 02 | `screenshots/02_vl_ai_decisions_section.png` | VL AI section | crop section | packaging/elec/LED · AI_DECISION · MEDIUM | PASS |
| 03 | `screenshots/03_vl_ai_override_active.png` | VL after PUT LED 0.5 | reload Prețuri | override activ · 0.5 | PASS (then DELETE restore) |
| 04 | `screenshots/04_acm_activation_warnings_ai.png` | ACM Prețuri | open | Activ cu avertismente · shell 5/0 · treat false | PASS |
| 05 | `screenshots/05_acm_ai_defaults.png` | ACM AI section | scroll | packaging + ACM panel labor · LOW | PASS |
| 06 | `screenshots/06_volum_aluminiu_ai_packaging.png` | Volum Aluminiu Prețuri | open | AI activ · packaging band | PASS |
| 07 | `screenshots/07_vl_activation_ai_activ.png` | VL header | open Prețuri | chip **AI activ** · Tehnic/Comercial pregătit | PASS |

## Sincere UI opinion

Readable in ~10 seconds: section title, precedence one-liner, compact AI badges, typed inputs. Not flooded with warning panels. Override/reset is obvious. Remaining fragility: catalog rate-basis mismatch warnings still noisy above the AI section; PREPRESS stays honest OPERATION_ONLY.
