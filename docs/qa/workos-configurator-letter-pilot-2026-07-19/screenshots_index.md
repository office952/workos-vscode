# Screenshots — Configurator Letter Pilot

**Date:** 2026-07-19  
**Accepted runtime (PASS evidence):** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8003`  
**Served commit for after screenshots:** `f39c260` (`refactor(intake-v6): apply configurator design pilot to letters`)  
**Workspace:** `e1ba14f2-ceca-4239-9e8e-e87c0e21d65f` (`audit-complete-ui-ux-basic`)  
**Path:** `/intake-v6/{id}/operator` → Configurare  

### Runtime closure (mandatory)

| Runtime | Status for this pilot |
|---------|------------------------|
| `:3000` + `:8003` | **PASS evidence** — after screenshots 03–09 + live probe (`anatomy`/`results`/`decisions`/Montaj = true) captured here after `f39c260` was on HEAD |
| `:3001` | **Not acceptance runtime** — Windows crash exit `3221226505` (operational incident only). Do **not** treat `:3001` as visual-pilot PASS. No restart required for this pack. |

Intermediate “live FE may not include our pilot changes” was resolved by re-capturing on `:3000` with probe all-true after commit `f39c260`.

| # | File | State | Steps | Honest note |
|---|------|-------|-------|-------------|
| 1 | `01_before_letter_config.png` | Before (foundation asset) | Finisaje baseline from design-system foundation pack | Dense 10px cluster; weak anatomy |
| 2 | `02_before_lighting.png` | Before (foundation asset) | Iluminare baseline | Inputs mixed with calc lines |
| 3 | `03_letter_anatomy_presentation.png` | After | Finisaje → scroll to letter cluster | **Litere volumetrice** + Față/Cant/Spate legend visible |
| 4 | `04_face_cant_back_grouping.png` | After | Expand Element 1 | Anatomy zones as decision blocks |
| 5 | `05_lighting_grouping.png` | After | Iluminare tab | Decizii iluminare / alimentare headers |
| 6 | `06_result_summary.png` | After | Scroll to results | **REZULTATE CALCULATE** read-only panel (perimeter, modules, PSU) |
| 7 | `07_technical_disclosure_collapsed.png` | After | Finisaje ownership accordion collapsed | Tokens not on L1 |
| 8 | `08_technical_disclosure_expanded.png` | After | Ownership accordion open | Tokens demoted (11px slate) |
| 9 | `09_confirmation_summary.png` | After | Step 3 Confirmare | No intentional Confirmare redesign |

**Probe (live):** `letterTitle` / `anatomy` / `results` / `decisions` / Montaj panel — all true (`capture_meta.json`).
