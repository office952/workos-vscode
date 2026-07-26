# Intake V6 — Live Calculation Balance V1 — Screenshots

**Workspace:** `22ef834d-f2d0-453b-a7a7-118928c98a39`  
**Route:** http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator

| File | URL | Pas | Tab | Stare | Click path | Element așteptat |
|------|-----|-----|-----|-------|------------|------------------|
| `01_step2_live_calculation_before.png` | — | 2 | Finisaje | — | — | **Indisponibil** — captură pre-implementare ratată; vezi audit în worklog |
| `02_step2_live_calculation_balanced_default.png` | route + Review | 2 | Finisaje (default) | calcul disponibil | Progress → Review | `intake-v6-review-calculator-panel`, titlu „Calcul estimativ live”, hint preview |
| `03_step2_live_calculation_with_blocker.png` | route + Review | 2 | Finisaje | blocker activ | Progress → Review | banner blocker + panou estimativ secundar |
| `04_step2_live_calculation_subtotals.png` | route + Review | 2 | Finisaje | detalii linii | „Detalii linii” sheet | subtotaluri în sheet, filtre în sheet |
| `05_step2_live_calculation_incomplete_state.png` | — | 2 | — | incomplet | — | **Indisponibil** pe fixture — workspace are dry-run; acoperit de test unitar `intake-v6-live-estimate-unavailable` |
| `06_step2_diagnostic_collapsed_regression.png` | route + Review | 2 | Finisaje | diagnostic colapsat | scroll la accordion | `intake-v6-review-technical-details` colapsat |
| `07_step2_iluminare_regression.png` | route + Review | 2 | Iluminare | fără pill ON | tab Iluminare | tab fără pill ON, calc panel vizibil |
| `08_step1_badge_noise_regression.png` | route | 1 | — | straturi confirmate | Progress → Straturi | badge noise redus Pas 1 |
| `09_step3_no_intentional_changes.png` | route | 3 | — | confirmare | Progress → Confirmare | Pas 3 neschimbat |
