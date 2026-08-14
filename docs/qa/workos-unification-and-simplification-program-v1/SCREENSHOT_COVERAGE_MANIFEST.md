# Screenshot coverage manifest

A folder of PNGs is **not** sufficient. Every capture must have a row.

Wave 1 primary evidence is **full scroll exhaustion** on the real container (`main.overflow-auto`).
The first capture pass scrolled `window` and is **superseded** for home-page completeness (`FULL_VERTICAL_SCROLL = FAIL` on those rows).
Nav-follow landings remain first-viewport only by Wave 1 charter (destinations are not fully audited).

Coverage: `COVERED` · `STATE_NOT_REACHED` · `NOT_APPLICABLE`

Wave 5 gap-closure shots are **not** copied here. See [`wave-5/WAVE_5_EVIDENCE_RECONCILIATION.md`](wave-5/WAVE_5_EVIDENCE_RECONCILIATION.md) and [`wave-5/runtime/rt-gap-closure-log.json`](wave-5/runtime/rt-gap-closure-log.json) (18 shots, `/employees-records/7` only).

## Surface scroll exhaustion

| route | role | theme | tab | container | SCROLL_START | SCROLL_END | SCROLL_MAX | BOTTOM_REACHED | NEW_CONTENT_AFTER_FINAL_SCROLL | SCROLL_SEGMENT_COUNT | FULL_VERTICAL_SCROLL | NESTED_SCROLL_CONTAINERS |
|-------|------|-------|-----|-----------|--------------|------------|------------|----------------|--------------------------------|----------------------|----------------------|--------------------------|
| `/dashboard` | admin | light | default | `main.overflow-auto` | 0 | 1299 | 1299 | YES | NO | 3 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| `/quotes` | admin | light | default | `main.overflow-auto` | 0 | 4440 | 4440 | YES | NO | 7 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| `/quotes` | admin | light | Ciornă | `main.overflow-auto` | 0 | 488 | 488 | YES | NO | 2 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| `/quotes` | admin | light | Tarifat | `main.overflow-auto` | 0 | 640 | 640 | YES | NO | 2 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| `/quotes` | admin | light | Acceptat | `main.overflow-auto` | 0 | 2464 | 2464 | YES | NO | 5 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| `/quotes` | admin | light | quote-selected | `main.overflow-auto` | 0 | 4389 | 4389 | YES | NO | 7 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| `/shop-floor` | admin | light | default | `main.overflow-auto` | 0 | 818 | 818 | YES | NO | 3 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| `/quotes` | sales | light | default | `main.overflow-auto` | 0 | 4440 | 4440 | YES | NO | 7 | **PASS** | main.relative.z-0.flex-1 max=4440 |
| `/shop-floor` | operator | light | default | `main.overflow-auto` | 0 | 818 | 818 | YES | NO | 3 | **PASS** | main.relative.z-0.flex-1 max=818 |
| `/dashboard` | admin | dark | default | `main.overflow-auto` | 0 | 1299 | 1299 | YES | NO | 3 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| `/quotes` | admin | dark | default | `main.overflow-auto` | 0 | 4440 | 4440 | YES | NO | 7 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| `/quotes` | admin | dark | Ciornă | `main.overflow-auto` | 0 | 488 | 488 | YES | NO | 2 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| `/quotes` | admin | dark | Tarifat | `main.overflow-auto` | 0 | 640 | 640 | YES | NO | 2 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| `/quotes` | admin | dark | Acceptat | `main.overflow-auto` | 0 | 2464 | 2464 | YES | NO | 5 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| `/quotes` | admin | dark | quote-selected | `main.overflow-auto` | 0 | 4389 | 4389 | YES | NO | 7 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| `/shop-floor` | admin | dark | default | `main.overflow-auto` | 0 | 818 | 818 | YES | NO | 3 | **PASS** | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| `/quotes` | sales | dark | default | `main.overflow-auto` | 0 | 4440 | 4440 | YES | NO | 7 | **PASS** | main.relative.z-0.flex-1 max=4440 |
| `/shop-floor` | operator | dark | default | `main.overflow-auto` | 0 | 818 | 818 | YES | NO | 3 | **PASS** | main.relative.z-0.flex-1 max=818 |
| `/dashboard` | admin | light | appshell-nav | `workos-shell-nav` | 0 | 624 | 624 | YES | NO | 2 | **PASS** | workos-shell-nav |
| `/dashboard` | admin | dark | appshell-nav | `workos-shell-nav` | 0 | 624 | 624 | YES | NO | 2 | **PASS** | workos-shell-nav |

Surfaces exhausted: **20**. FAIL: **0**.

## Segment rows (exhausted surfaces)

| # | route | role | theme | viewport | scroll | tab/subtab | expandable | overlay | link dest | state | file | coverage | FULL_VERTICAL_SCROLL | BOTTOM_REACHED | SCROLL_SEGMENT_COUNT | NESTED_SCROLL_CONTAINERS |
|---|-------|------|-------|----------|--------|------------|------------|---------|-----------|-------|------|----------|----------------------|----------------|----------------------|--------------------------|
| 1 | `/dashboard` | admin | light | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_dashboard/default/s00-y0.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 2 | `/dashboard` | admin | light | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_dashboard/default/s01-y804.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 3 | `/dashboard` | admin | light | 1440x900 | y=1299 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_dashboard/default/s02-y1299.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 4 | `/quotes` | admin | light | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s00-y0.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 5 | `/quotes` | admin | light | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s01-y804.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 6 | `/quotes` | admin | light | 1440x900 | y=1608 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s02-y1608.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 7 | `/quotes` | admin | light | 1440x900 | y=2412 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s03-y2412.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 8 | `/quotes` | admin | light | 1440x900 | y=3216 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s04-y3216.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 9 | `/quotes` | admin | light | 1440x900 | y=4020 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s05-y4020.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 10 | `/quotes` | admin | light | 1440x900 | y=4440 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/default/s06-y4440.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 11 | `/quotes` | admin | light | 1440x900 | y=0 | Ciornă | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Ciornă/s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| 12 | `/quotes` | admin | light | 1440x900 | y=488 | Ciornă | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Ciornă/s01-y488.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| 13 | `/quotes` | admin | light | 1440x900 | y=0 | Tarifat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Tarifat/s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| 14 | `/quotes` | admin | light | 1440x900 | y=640 | Tarifat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Tarifat/s01-y640.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| 15 | `/quotes` | admin | light | 1440x900 | y=0 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Acceptat/s00-y0.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 16 | `/quotes` | admin | light | 1440x900 | y=804 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Acceptat/s01-y804.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 17 | `/quotes` | admin | light | 1440x900 | y=1608 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Acceptat/s02-y1608.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 18 | `/quotes` | admin | light | 1440x900 | y=2412 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Acceptat/s03-y2412.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 19 | `/quotes` | admin | light | 1440x900 | y=2464 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/Acceptat/s04-y2464.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 20 | `/quotes` | admin | light | 1440x900 | y=0 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s00-y0.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 21 | `/quotes` | admin | light | 1440x900 | y=804 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s01-y804.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 22 | `/quotes` | admin | light | 1440x900 | y=1608 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s02-y1608.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 23 | `/quotes` | admin | light | 1440x900 | y=2412 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s03-y2412.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 24 | `/quotes` | admin | light | 1440x900 | y=3216 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s04-y3216.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 25 | `/quotes` | admin | light | 1440x900 | y=4020 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s05-y4020.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 26 | `/quotes` | admin | light | 1440x900 | y=4389 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_quotes/quote-selected/s06-y4389.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 27 | `/shop-floor` | admin | light | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_shop-floor/default/s00-y0.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 28 | `/shop-floor` | admin | light | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_shop-floor/default/s01-y804.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 29 | `/shop-floor` | admin | light | 1440x900 | y=818 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/light/_shop-floor/default/s02-y818.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 30 | `/quotes` | sales | light | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s00-y0.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 31 | `/quotes` | sales | light | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s01-y804.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 32 | `/quotes` | sales | light | 1440x900 | y=1608 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s02-y1608.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 33 | `/quotes` | sales | light | 1440x900 | y=2412 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s03-y2412.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 34 | `/quotes` | sales | light | 1440x900 | y=3216 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s04-y3216.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 35 | `/quotes` | sales | light | 1440x900 | y=4020 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s05-y4020.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 36 | `/quotes` | sales | light | 1440x900 | y=4440 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/light/_quotes/default/s06-y4440.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 37 | `/shop-floor` | operator | light | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/light/_shop-floor/default/s00-y0.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 38 | `/shop-floor` | operator | light | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/light/_shop-floor/default/s01-y804.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 39 | `/shop-floor` | operator | light | 1440x900 | y=818 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/light/_shop-floor/default/s02-y818.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 40 | `/dashboard` | admin | dark | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_dashboard/default/s00-y0.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 41 | `/dashboard` | admin | dark | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_dashboard/default/s01-y804.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 42 | `/dashboard` | admin | dark | 1440x900 | y=1299 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_dashboard/default/s02-y1299.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=1299 |
| 43 | `/quotes` | admin | dark | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s00-y0.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 44 | `/quotes` | admin | dark | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s01-y804.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 45 | `/quotes` | admin | dark | 1440x900 | y=1608 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s02-y1608.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 46 | `/quotes` | admin | dark | 1440x900 | y=2412 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s03-y2412.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 47 | `/quotes` | admin | dark | 1440x900 | y=3216 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s04-y3216.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 48 | `/quotes` | admin | dark | 1440x900 | y=4020 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s05-y4020.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 49 | `/quotes` | admin | dark | 1440x900 | y=4440 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/default/s06-y4440.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4440 |
| 50 | `/quotes` | admin | dark | 1440x900 | y=0 | Ciornă | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Ciornă/s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| 51 | `/quotes` | admin | dark | 1440x900 | y=488 | Ciornă | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Ciornă/s01-y488.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=488 |
| 52 | `/quotes` | admin | dark | 1440x900 | y=0 | Tarifat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Tarifat/s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| 53 | `/quotes` | admin | dark | 1440x900 | y=640 | Tarifat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Tarifat/s01-y640.png` | COVERED | PASS | YES | 2 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=640 |
| 54 | `/quotes` | admin | dark | 1440x900 | y=0 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Acceptat/s00-y0.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 55 | `/quotes` | admin | dark | 1440x900 | y=804 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Acceptat/s01-y804.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 56 | `/quotes` | admin | dark | 1440x900 | y=1608 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Acceptat/s02-y1608.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 57 | `/quotes` | admin | dark | 1440x900 | y=2412 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Acceptat/s03-y2412.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 58 | `/quotes` | admin | dark | 1440x900 | y=2464 | Acceptat | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/Acceptat/s04-y2464.png` | COVERED | PASS | YES | 5 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=2464 |
| 59 | `/quotes` | admin | dark | 1440x900 | y=0 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s00-y0.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 60 | `/quotes` | admin | dark | 1440x900 | y=804 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s01-y804.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 61 | `/quotes` | admin | dark | 1440x900 | y=1608 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s02-y1608.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 62 | `/quotes` | admin | dark | 1440x900 | y=2412 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s03-y2412.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 63 | `/quotes` | admin | dark | 1440x900 | y=3216 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s04-y3216.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 64 | `/quotes` | admin | dark | 1440x900 | y=4020 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s05-y4020.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 65 | `/quotes` | admin | dark | 1440x900 | y=4389 | quote-selected | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_quotes/quote-selected/s06-y4389.png` | COVERED | PASS | YES | 7 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=4389 |
| 66 | `/shop-floor` | admin | dark | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_shop-floor/default/s00-y0.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 67 | `/shop-floor` | admin | dark | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_shop-floor/default/s01-y804.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 68 | `/shop-floor` | admin | dark | 1440x900 | y=818 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/admin/dark/_shop-floor/default/s02-y818.png` | COVERED | PASS | YES | 3 | workos-shell-nav max=624; main.relative.z-0.flex-1 max=818 |
| 69 | `/quotes` | sales | dark | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s00-y0.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 70 | `/quotes` | sales | dark | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s01-y804.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 71 | `/quotes` | sales | dark | 1440x900 | y=1608 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s02-y1608.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 72 | `/quotes` | sales | dark | 1440x900 | y=2412 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s03-y2412.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 73 | `/quotes` | sales | dark | 1440x900 | y=3216 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s04-y3216.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 74 | `/quotes` | sales | dark | 1440x900 | y=4020 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s05-y4020.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 75 | `/quotes` | sales | dark | 1440x900 | y=4440 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/sales/dark/_quotes/default/s06-y4440.png` | COVERED | PASS | YES | 7 | main.relative.z-0.flex-1 max=4440 |
| 76 | `/shop-floor` | operator | dark | 1440x900 | y=0 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/dark/_shop-floor/default/s00-y0.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 77 | `/shop-floor` | operator | dark | 1440x900 | y=804 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/dark/_shop-floor/default/s01-y804.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 78 | `/shop-floor` | operator | dark | 1440x900 | y=818 | default | none | none | — | scroll-segment | `wave-1/screenshots/scroll/operator/dark/_shop-floor/default/s02-y818.png` | COVERED | PASS | YES | 3 | main.relative.z-0.flex-1 max=818 |
| 79 | `/dashboard` | admin | light | 1440x900 | y=0 | appshell-nav | none | none | — | scroll-segment | `wave-1/screenshots/scroll/nav/light/nav-s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav |
| 80 | `/dashboard` | admin | light | 1440x900 | y=624 | appshell-nav | none | none | — | scroll-segment | `wave-1/screenshots/scroll/nav/light/nav-s01-y624.png` | COVERED | PASS | YES | 2 | workos-shell-nav |
| 81 | `/dashboard` | admin | dark | 1440x900 | y=0 | appshell-nav | none | none | — | scroll-segment | `wave-1/screenshots/scroll/nav/dark/nav-s00-y0.png` | COVERED | PASS | YES | 2 | workos-shell-nav |
| 82 | `/dashboard` | admin | dark | 1440x900 | y=624 | appshell-nav | none | none | — | scroll-segment | `wave-1/screenshots/scroll/nav/dark/nav-s01-y624.png` | COVERED | PASS | YES | 2 | workos-shell-nav |

## Nav-follow first viewport (not a full page audit)

These rows prove `FOLLOWED=YES`. `FULL_VERTICAL_SCROLL = N/A` — destination pages are out of Wave 1 full-audit scope.

| # | route | role | theme | viewport | scroll | tab/subtab | expandable | overlay | link dest | state | file | coverage | FULL_VERTICAL_SCROLL | BOTTOM_REACHED | SCROLL_SEGMENT_COUNT | NESTED_SCROLL_CONTAINERS |
|---|-------|------|-------|----------|--------|------------|------------|---------|-----------|-------|------|----------|----------------------|----------------|----------------------|--------------------------|
| 83 | `/intake` | admin | light | 1440x900 | top | none | none | none | /intake | nav-landing | `wave-1/screenshots/admin/light/009-admin-light-intake-nav-Cereri.png` | COVERED | N/A | NO | 1 | — |
| 84 | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | admin | light | 1440x900 | top | none | none | none | /product-system/products/TPL-VOLUMETRIC-LETTERS_v2 | nav-landing | `wave-1/screenshots/admin/light/010-admin-light-product-system_products_TPL-VOLUMETRIC-LETTERS_v2-nav-Produse.png` | COVERED | N/A | NO | 1 | — |
| 85 | `/quotes` | admin | light | 1440x900 | top | none | none | none | /quotes | nav-landing | `wave-1/screenshots/admin/light/011-admin-light-quotes-nav-Oferte.png` | COVERED | N/A | NO | 1 | — |
| 86 | `/orders` | admin | light | 1440x900 | top | none | none | none | /orders | nav-landing | `wave-1/screenshots/admin/light/012-admin-light-orders-nav-Comenzi.png` | COVERED | N/A | NO | 1 | — |
| 87 | `/shop-floor` | admin | light | 1440x900 | top | none | none | none | /shop-floor | nav-landing | `wave-1/screenshots/admin/light/013-admin-light-shop-floor-nav-Atelier.png` | COVERED | N/A | NO | 1 | — |
| 88 | `/execution` | admin | light | 1440x900 | top | none | none | none | /execution | nav-landing | `wave-1/screenshots/admin/light/014-admin-light-execution-nav-Planificare.png` | COVERED | N/A | NO | 1 | — |
| 89 | `/execution/machine-runs` | admin | light | 1440x900 | top | none | none | none | /execution/machine-runs | nav-landing | `wave-1/screenshots/admin/light/015-admin-light-execution_machine-runs-nav-Rul_ri_utilaj.png` | COVERED | N/A | NO | 1 | — |
| 90 | `/execution/ops-graph` | admin | light | 1440x900 | top | none | none | none | /execution/ops-graph | nav-landing | `wave-1/screenshots/admin/light/016-admin-light-execution_ops-graph-nav-Ops-Graph.png` | COVERED | N/A | NO | 1 | — |
| 91 | `/operator` | admin | light | 1440x900 | top | none | none | none | /operator | nav-landing | `wave-1/screenshots/admin/light/017-admin-light-operator-nav-Ac_iune_task_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 92 | `/tablet` | admin | light | 1440x900 | top | none | none | none | /tablet | nav-landing | `wave-1/screenshots/admin/light/018-admin-light-tablet-nav-Sta_ii_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 93 | `/employees` | admin | light | 1440x900 | top | none | none | none | /employees | nav-landing | `wave-1/screenshots/admin/light/019-admin-light-employees-nav-Angaja_i.png` | COVERED | N/A | NO | 1 | — |
| 94 | `/attendance` | admin | light | 1440x900 | top | none | none | none | /attendance | nav-landing | `wave-1/screenshots/admin/light/020-admin-light-attendance-nav-Pontaj.png` | COVERED | N/A | NO | 1 | — |
| 95 | `/employees-records` | admin | light | 1440x900 | top | none | none | none | /employees-records | nav-landing | `wave-1/screenshots/admin/light/021-admin-light-employees-records-nav-Eviden_HR.png` | COVERED | N/A | NO | 1 | — |
| 96 | `/utilaje` | admin | light | 1440x900 | top | none | none | none | /utilaje | nav-landing | `wave-1/screenshots/admin/light/022-admin-light-utilaje-nav-Utilaje.png` | COVERED | N/A | NO | 1 | — |
| 97 | `/inventory` | admin | light | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/admin/light/023-admin-light-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |
| 98 | `/inventory/pricing` | admin | light | 1440x900 | top | none | none | none | /inventory/pricing | nav-landing | `wave-1/screenshots/admin/light/024-admin-light-inventory_pricing-nav-Pre_uri.png` | COVERED | N/A | NO | 1 | — |
| 99 | `/clients` | admin | light | 1440x900 | top | none | none | none | /clients | nav-landing | `wave-1/screenshots/admin/light/025-admin-light-clients-nav-Clien_i.png` | COVERED | N/A | NO | 1 | — |
| 100 | `/colaboratori` | admin | light | 1440x900 | top | none | none | none | /colaboratori | nav-landing | `wave-1/screenshots/admin/light/026-admin-light-colaboratori-nav-Colaboratori.png` | COVERED | N/A | NO | 1 | — |
| 101 | `/documents` | admin | light | 1440x900 | top | none | none | none | /documents | nav-landing | `wave-1/screenshots/admin/light/027-admin-light-documents-nav-Documente.png` | COVERED | N/A | NO | 1 | — |
| 102 | `/dashboard` | admin | light | 1440x900 | top | none | none | none | /dashboard | nav-landing | `wave-1/screenshots/admin/light/028-admin-light-dashboard-nav-Control_produc_ie.png` | COVERED | N/A | NO | 1 | — |
| 103 | `/reports` | admin | light | 1440x900 | top | none | none | none | /reports | nav-landing | `wave-1/screenshots/admin/light/029-admin-light-reports-nav-Rapoarte.png` | COVERED | N/A | NO | 1 | — |
| 104 | `/employee-payments` | admin | light | 1440x900 | top | none | none | none | /employee-payments | nav-landing | `wave-1/screenshots/admin/light/030-admin-light-employee-payments-nav-Pl_i.png` | COVERED | N/A | NO | 1 | — |
| 105 | `/employee-advances` | admin | light | 1440x900 | top | none | none | none | /employee-advances | nav-landing | `wave-1/screenshots/admin/light/031-admin-light-employee-advances-nav-Avansuri.png` | COVERED | N/A | NO | 1 | — |
| 106 | `/modules` | admin | light | 1440x900 | top | none | none | none | /modules | nav-landing | `wave-1/screenshots/admin/light/032-admin-light-modules-nav-Harta.png` | COVERED | N/A | NO | 1 | — |
| 107 | `/governance` | admin | light | 1440x900 | top | none | none | none | /governance | nav-landing | `wave-1/screenshots/admin/light/033-admin-light-governance-nav-Guvernan_.png` | COVERED | N/A | NO | 1 | — |
| 108 | `/settings` | admin | light | 1440x900 | top | none | none | none | /settings | nav-landing | `wave-1/screenshots/admin/light/034-admin-light-settings-nav-Set_ri.png` | COVERED | N/A | NO | 1 | — |
| 109 | `/demo/commercial-spine` | admin | light | 1440x900 | top | none | none | none | /demo/commercial-spine | nav-landing | `wave-1/screenshots/admin/light/035-admin-light-demo_commercial-spine-nav-Demo_Commercial_Spine.png` | COVERED | N/A | NO | 1 | — |
| 110 | `/demo/volumetric-letter-preview` | admin | light | 1440x900 | top | none | none | none | /demo/volumetric-letter-preview | nav-landing | `wave-1/screenshots/admin/light/036-admin-light-demo_volumetric-letter-preview-nav-Demo_Volumetric_Preview.png` | COVERED | N/A | NO | 1 | — |
| 111 | `/product-system/blueprint-dossier` | admin | light | 1440x900 | top | none | none | none | /product-system/blueprint-dossier | nav-landing | `wave-1/screenshots/admin/light/037-admin-light-product-system_blueprint-dossier-nav-Blueprint_Dossier.png` | COVERED | N/A | NO | 1 | — |
| 112 | `/reports/operational` | admin | light | 1440x900 | top | none | none | none | /reports/operational | nav-landing | `wave-1/screenshots/admin/light/038-admin-light-reports_operational-nav-Rapoarte_opera_ionale.png` | COVERED | N/A | NO | 1 | — |
| 113 | `/intake` | admin | dark | 1440x900 | top | none | none | none | /intake | nav-landing | `wave-1/screenshots/admin/dark/047-admin-dark-intake-nav-Cereri.png` | COVERED | N/A | NO | 1 | — |
| 114 | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | admin | dark | 1440x900 | top | none | none | none | /product-system/products/TPL-VOLUMETRIC-LETTERS_v2 | nav-landing | `wave-1/screenshots/admin/dark/048-admin-dark-product-system_products_TPL-VOLUMETRIC-LETTERS_v2-nav-Produse.png` | COVERED | N/A | NO | 1 | — |
| 115 | `/quotes` | admin | dark | 1440x900 | top | none | none | none | /quotes | nav-landing | `wave-1/screenshots/admin/dark/049-admin-dark-quotes-nav-Oferte.png` | COVERED | N/A | NO | 1 | — |
| 116 | `/orders` | admin | dark | 1440x900 | top | none | none | none | /orders | nav-landing | `wave-1/screenshots/admin/dark/050-admin-dark-orders-nav-Comenzi.png` | COVERED | N/A | NO | 1 | — |
| 117 | `/shop-floor` | admin | dark | 1440x900 | top | none | none | none | /shop-floor | nav-landing | `wave-1/screenshots/admin/dark/051-admin-dark-shop-floor-nav-Atelier.png` | COVERED | N/A | NO | 1 | — |
| 118 | `/execution` | admin | dark | 1440x900 | top | none | none | none | /execution | nav-landing | `wave-1/screenshots/admin/dark/052-admin-dark-execution-nav-Planificare.png` | COVERED | N/A | NO | 1 | — |
| 119 | `/execution/machine-runs` | admin | dark | 1440x900 | top | none | none | none | /execution/machine-runs | nav-landing | `wave-1/screenshots/admin/dark/053-admin-dark-execution_machine-runs-nav-Rul_ri_utilaj.png` | COVERED | N/A | NO | 1 | — |
| 120 | `/execution/ops-graph` | admin | dark | 1440x900 | top | none | none | none | /execution/ops-graph | nav-landing | `wave-1/screenshots/admin/dark/054-admin-dark-execution_ops-graph-nav-Ops-Graph.png` | COVERED | N/A | NO | 1 | — |
| 121 | `/operator` | admin | dark | 1440x900 | top | none | none | none | /operator | nav-landing | `wave-1/screenshots/admin/dark/055-admin-dark-operator-nav-Ac_iune_task_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 122 | `/tablet` | admin | dark | 1440x900 | top | none | none | none | /tablet | nav-landing | `wave-1/screenshots/admin/dark/056-admin-dark-tablet-nav-Sta_ii_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 123 | `/employees` | admin | dark | 1440x900 | top | none | none | none | /employees | nav-landing | `wave-1/screenshots/admin/dark/057-admin-dark-employees-nav-Angaja_i.png` | COVERED | N/A | NO | 1 | — |
| 124 | `/attendance` | admin | dark | 1440x900 | top | none | none | none | /attendance | nav-landing | `wave-1/screenshots/admin/dark/058-admin-dark-attendance-nav-Pontaj.png` | COVERED | N/A | NO | 1 | — |
| 125 | `/employees-records` | admin | dark | 1440x900 | top | none | none | none | /employees-records | nav-landing | `wave-1/screenshots/admin/dark/059-admin-dark-employees-records-nav-Eviden_HR.png` | COVERED | N/A | NO | 1 | — |
| 126 | `/utilaje` | admin | dark | 1440x900 | top | none | none | none | /utilaje | nav-landing | `wave-1/screenshots/admin/dark/060-admin-dark-utilaje-nav-Utilaje.png` | COVERED | N/A | NO | 1 | — |
| 127 | `/inventory` | admin | dark | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/admin/dark/061-admin-dark-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |
| 128 | `/inventory/pricing` | admin | dark | 1440x900 | top | none | none | none | /inventory/pricing | nav-landing | `wave-1/screenshots/admin/dark/062-admin-dark-inventory_pricing-nav-Pre_uri.png` | COVERED | N/A | NO | 1 | — |
| 129 | `/clients` | admin | dark | 1440x900 | top | none | none | none | /clients | nav-landing | `wave-1/screenshots/admin/dark/063-admin-dark-clients-nav-Clien_i.png` | COVERED | N/A | NO | 1 | — |
| 130 | `/colaboratori` | admin | dark | 1440x900 | top | none | none | none | /colaboratori | nav-landing | `wave-1/screenshots/admin/dark/064-admin-dark-colaboratori-nav-Colaboratori.png` | COVERED | N/A | NO | 1 | — |
| 131 | `/documents` | admin | dark | 1440x900 | top | none | none | none | /documents | nav-landing | `wave-1/screenshots/admin/dark/065-admin-dark-documents-nav-Documente.png` | COVERED | N/A | NO | 1 | — |
| 132 | `/dashboard` | admin | dark | 1440x900 | top | none | none | none | /dashboard | nav-landing | `wave-1/screenshots/admin/dark/066-admin-dark-dashboard-nav-Control_produc_ie.png` | COVERED | N/A | NO | 1 | — |
| 133 | `/reports` | admin | dark | 1440x900 | top | none | none | none | /reports | nav-landing | `wave-1/screenshots/admin/dark/067-admin-dark-reports-nav-Rapoarte.png` | COVERED | N/A | NO | 1 | — |
| 134 | `/employee-payments` | admin | dark | 1440x900 | top | none | none | none | /employee-payments | nav-landing | `wave-1/screenshots/admin/dark/068-admin-dark-employee-payments-nav-Pl_i.png` | COVERED | N/A | NO | 1 | — |
| 135 | `/employee-advances` | admin | dark | 1440x900 | top | none | none | none | /employee-advances | nav-landing | `wave-1/screenshots/admin/dark/069-admin-dark-employee-advances-nav-Avansuri.png` | COVERED | N/A | NO | 1 | — |
| 136 | `/modules` | admin | dark | 1440x900 | top | none | none | none | /modules | nav-landing | `wave-1/screenshots/admin/dark/070-admin-dark-modules-nav-Harta.png` | COVERED | N/A | NO | 1 | — |
| 137 | `/governance` | admin | dark | 1440x900 | top | none | none | none | /governance | nav-landing | `wave-1/screenshots/admin/dark/071-admin-dark-governance-nav-Guvernan_.png` | COVERED | N/A | NO | 1 | — |
| 138 | `/settings` | admin | dark | 1440x900 | top | none | none | none | /settings | nav-landing | `wave-1/screenshots/admin/dark/072-admin-dark-settings-nav-Set_ri.png` | COVERED | N/A | NO | 1 | — |
| 139 | `/demo/commercial-spine` | admin | dark | 1440x900 | top | none | none | none | /demo/commercial-spine | nav-landing | `wave-1/screenshots/admin/dark/073-admin-dark-demo_commercial-spine-nav-Demo_Commercial_Spine.png` | COVERED | N/A | NO | 1 | — |
| 140 | `/demo/volumetric-letter-preview` | admin | dark | 1440x900 | top | none | none | none | /demo/volumetric-letter-preview | nav-landing | `wave-1/screenshots/admin/dark/074-admin-dark-demo_volumetric-letter-preview-nav-Demo_Volumetric_Preview.png` | COVERED | N/A | NO | 1 | — |
| 141 | `/product-system/blueprint-dossier` | admin | dark | 1440x900 | top | none | none | none | /product-system/blueprint-dossier | nav-landing | `wave-1/screenshots/admin/dark/075-admin-dark-product-system_blueprint-dossier-nav-Blueprint_Dossier.png` | COVERED | N/A | NO | 1 | — |
| 142 | `/reports/operational` | admin | dark | 1440x900 | top | none | none | none | /reports/operational | nav-landing | `wave-1/screenshots/admin/dark/076-admin-dark-reports_operational-nav-Rapoarte_opera_ionale.png` | COVERED | N/A | NO | 1 | — |
| 143 | `/intake` | sales | light | 1440x900 | top | none | none | none | /intake | nav-landing | `wave-1/screenshots/sales/light/083-sales-light-intake-nav-Cereri.png` | COVERED | N/A | NO | 1 | — |
| 144 | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | sales | light | 1440x900 | top | none | none | none | /product-system/products/TPL-VOLUMETRIC-LETTERS_v2 | nav-landing | `wave-1/screenshots/sales/light/084-sales-light-product-system_products_TPL-VOLUMETRIC-LETTERS_v2-nav-Produse.png` | COVERED | N/A | NO | 1 | — |
| 145 | `/quotes` | sales | light | 1440x900 | top | none | none | none | /quotes | nav-landing | `wave-1/screenshots/sales/light/085-sales-light-quotes-nav-Oferte.png` | COVERED | N/A | NO | 1 | — |
| 146 | `/orders` | sales | light | 1440x900 | top | none | none | none | /orders | nav-landing | `wave-1/screenshots/sales/light/086-sales-light-orders-nav-Comenzi.png` | COVERED | N/A | NO | 1 | — |
| 147 | `/execution` | sales | light | 1440x900 | top | none | none | none | /execution | nav-landing | `wave-1/screenshots/sales/light/087-sales-light-execution-nav-Planificare.png` | COVERED | N/A | NO | 1 | — |
| 148 | `/inventory` | sales | light | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/sales/light/088-sales-light-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |
| 149 | `/clients` | sales | light | 1440x900 | top | none | none | none | /clients | nav-landing | `wave-1/screenshots/sales/light/089-sales-light-clients-nav-Clien_i.png` | COVERED | N/A | NO | 1 | — |
| 150 | `/documents` | sales | light | 1440x900 | top | none | none | none | /documents | nav-landing | `wave-1/screenshots/sales/light/090-sales-light-documents-nav-Documente.png` | COVERED | N/A | NO | 1 | — |
| 151 | `/dashboard` | sales | light | 1440x900 | top | none | none | none | /dashboard | nav-landing | `wave-1/screenshots/sales/light/091-sales-light-dashboard-nav-Control_produc_ie.png` | COVERED | N/A | NO | 1 | — |
| 152 | `/reports` | sales | light | 1440x900 | top | none | none | none | /reports | nav-landing | `wave-1/screenshots/sales/light/092-sales-light-reports-nav-Rapoarte.png` | COVERED | N/A | NO | 1 | — |
| 153 | `/intake` | sales | dark | 1440x900 | top | none | none | none | /intake | nav-landing | `wave-1/screenshots/sales/dark/099-sales-dark-intake-nav-Cereri.png` | COVERED | N/A | NO | 1 | — |
| 154 | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | sales | dark | 1440x900 | top | none | none | none | /product-system/products/TPL-VOLUMETRIC-LETTERS_v2 | nav-landing | `wave-1/screenshots/sales/dark/100-sales-dark-product-system_products_TPL-VOLUMETRIC-LETTERS_v2-nav-Produse.png` | COVERED | N/A | NO | 1 | — |
| 155 | `/quotes` | sales | dark | 1440x900 | top | none | none | none | /quotes | nav-landing | `wave-1/screenshots/sales/dark/101-sales-dark-quotes-nav-Oferte.png` | COVERED | N/A | NO | 1 | — |
| 156 | `/orders` | sales | dark | 1440x900 | top | none | none | none | /orders | nav-landing | `wave-1/screenshots/sales/dark/102-sales-dark-orders-nav-Comenzi.png` | COVERED | N/A | NO | 1 | — |
| 157 | `/execution` | sales | dark | 1440x900 | top | none | none | none | /execution | nav-landing | `wave-1/screenshots/sales/dark/103-sales-dark-execution-nav-Planificare.png` | COVERED | N/A | NO | 1 | — |
| 158 | `/inventory` | sales | dark | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/sales/dark/104-sales-dark-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |
| 159 | `/clients` | sales | dark | 1440x900 | top | none | none | none | /clients | nav-landing | `wave-1/screenshots/sales/dark/105-sales-dark-clients-nav-Clien_i.png` | COVERED | N/A | NO | 1 | — |
| 160 | `/documents` | sales | dark | 1440x900 | top | none | none | none | /documents | nav-landing | `wave-1/screenshots/sales/dark/106-sales-dark-documents-nav-Documente.png` | COVERED | N/A | NO | 1 | — |
| 161 | `/dashboard` | sales | dark | 1440x900 | top | none | none | none | /dashboard | nav-landing | `wave-1/screenshots/sales/dark/107-sales-dark-dashboard-nav-Control_produc_ie.png` | COVERED | N/A | NO | 1 | — |
| 162 | `/reports` | sales | dark | 1440x900 | top | none | none | none | /reports | nav-landing | `wave-1/screenshots/sales/dark/108-sales-dark-reports-nav-Rapoarte.png` | COVERED | N/A | NO | 1 | — |
| 163 | `/shop-floor` | operator | light | 1440x900 | top | none | none | none | /shop-floor | nav-landing | `wave-1/screenshots/operator/light/112-operator-light-shop-floor-nav-Atelier.png` | COVERED | N/A | NO | 1 | — |
| 164 | `/execution/machine-runs` | operator | light | 1440x900 | top | none | none | none | /execution/machine-runs | nav-landing | `wave-1/screenshots/operator/light/113-operator-light-execution_machine-runs-nav-Rul_ri_utilaj.png` | COVERED | N/A | NO | 1 | — |
| 165 | `/operator` | operator | light | 1440x900 | top | none | none | none | /operator | nav-landing | `wave-1/screenshots/operator/light/114-operator-light-operator-nav-Ac_iune_task_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 166 | `/tablet` | operator | light | 1440x900 | top | none | none | none | /tablet | nav-landing | `wave-1/screenshots/operator/light/115-operator-light-tablet-nav-Sta_ii_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 167 | `/utilaje` | operator | light | 1440x900 | top | none | none | none | /utilaje | nav-landing | `wave-1/screenshots/operator/light/116-operator-light-utilaje-nav-Utilaje.png` | COVERED | N/A | NO | 1 | — |
| 168 | `/inventory` | operator | light | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/operator/light/117-operator-light-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |
| 169 | `/shop-floor` | operator | dark | 1440x900 | top | none | none | none | /shop-floor | nav-landing | `wave-1/screenshots/operator/dark/121-operator-dark-shop-floor-nav-Atelier.png` | COVERED | N/A | NO | 1 | — |
| 170 | `/execution/machine-runs` | operator | dark | 1440x900 | top | none | none | none | /execution/machine-runs | nav-landing | `wave-1/screenshots/operator/dark/122-operator-dark-execution_machine-runs-nav-Rul_ri_utilaj.png` | COVERED | N/A | NO | 1 | — |
| 171 | `/operator` | operator | dark | 1440x900 | top | none | none | none | /operator | nav-landing | `wave-1/screenshots/operator/dark/123-operator-dark-operator-nav-Ac_iune_task_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 172 | `/tablet` | operator | dark | 1440x900 | top | none | none | none | /tablet | nav-landing | `wave-1/screenshots/operator/dark/124-operator-dark-tablet-nav-Sta_ii_legacy_.png` | COVERED | N/A | NO | 1 | — |
| 173 | `/utilaje` | operator | dark | 1440x900 | top | none | none | none | /utilaje | nav-landing | `wave-1/screenshots/operator/dark/125-operator-dark-utilaje-nav-Utilaje.png` | COVERED | N/A | NO | 1 | — |
| 174 | `/inventory` | operator | dark | 1440x900 | top | none | none | none | /inventory | nav-landing | `wave-1/screenshots/operator/dark/126-operator-dark-inventory-nav-Inventar.png` | COVERED | N/A | NO | 1 | — |

## States not reached (Wave 1)

| route | state | coverage | blocker |
|-------|-------|----------|---------|
| `/dashboard` | risks-expanded | NOT_APPLICABLE | fewer than 5 risky jobs; expand control absent |
| `/quotes` | QuoteSendDialog submit | NOT_APPLICABLE | mutation out of bounds |
| `/quotes` | + Ofertă nouă wizard | STATE_NOT_REACHED | create path would mutate records |
| `/quotes` | accept / reject / convert | STATE_NOT_REACHED | mutating CTAs |
| `/shop-floor` | empty / error board | STATE_NOT_REACHED | live DB is dense and healthy |
| AppShell | narrow nav drawer | STATE_NOT_REACHED | Wave 1 viewport 1440; drawer is mobile-only |

## Wave 4 pointer (do not copy rows here)

Product System / Modules / Governance captures: [`wave-4/WAVE_4_SCREENSHOT_COVERAGE_SUMMARY.md`](./wave-4/WAVE_4_SCREENSHOT_COVERAGE_SUMMARY.md) · [`wave-4/runtime/rt-capture-log.json`](./wave-4/runtime/rt-capture-log.json). 21 surfaces, 109 shots, scroll FAIL=0.

Gap closure (do not copy rows): [`wave-4/WAVE_4_EVIDENCE_RECONCILIATION.md`](./wave-4/WAVE_4_EVIDENCE_RECONCILIATION.md) · [`wave-4/runtime/rt-gap-closure-log.json`](./wave-4/runtime/rt-gap-closure-log.json). 27 surfaces, 87 shots, scroll FAIL=0.

## Wave 5 pointer (do not copy rows here)

HR / resources / admin / reports: [`wave-5/WAVE_5_SCREENSHOT_COVERAGE_SUMMARY.md`](./wave-5/WAVE_5_SCREENSHOT_COVERAGE_SUMMARY.md) · [`wave-5/runtime/rt-capture-log.json`](./wave-5/runtime/rt-capture-log.json). 54 surfaces, 170 shots, scroll FAIL=0.

