# Screenshots — Display label normalization

**Date:** 2026-07-19  
**Baseline:** `b1ba2ff`  
**Runtime:** FE `:3001` · BE `:8003`  
**SVG:** `litere-cu-fundal-acm-segmentat.svg`

| File | Section | Expected |
|------|---------|----------|
| `01_page1_labels.png` | Page 1 | Element N; no pseudo fill |
| `02_finisaje_layer_rows.png` | Finisaje | Operator titles; no pseudo fill |
| `03_confirmare_summary.png` | Confirmare | May be absent if Continuă blocked — see E2E note |
| `04_review_chrome.png` | Page 2 | Review chrome after Finisaje |
| `05_unknown_or_neutral_safe.png` | Fallback | Neutral-safe capture |
| `06_montaj_unchanged.png` | Montaj | Fundal cluster present |

## Honest visual opinion

Finisaje letter headers now match Page 1 language (Element N / formă). Persistence remains technical under the hood. Confirmare capture depends on Continuă gate (composition); unit/summary path covers the same helper.
