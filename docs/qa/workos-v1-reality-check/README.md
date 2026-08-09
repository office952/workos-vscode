# QA — WorkOS V1 Reality Check (Light + Intake + EUR/RON)

**GO:** `AUTHORIZE_WORKOS_V1_REALITY_CHECK_LIGHT_INTAKE_COMMERCIAL_AUDIT`  
**REALITY_CHECK_BASELINE_HEAD:** `1b5315fc`  
**Verdict:** `FAIL_REPAIR_REQUIRED`  
**V1_EXIT_STATUS:** `HOLD_PENDING_REALITY_CHECK`  
**PRODUCT_CODE_CHANGES:** `0`  
**QA_MUTATIONS:** `0`

## Evidence folders

| Folder | Contents |
|--------|----------|
| `light/` | Full-page Light screenshots (intake list, quotes, execution, Intake V6) |
| `commercial/` | Finish numeric deltas, complete_offer currency probe, Intake live Oracal |
| `currency/` | Quotes KPI RON labels vs Intake EUR hero |

## One-line root causes

1. **Sellable RON commercial rules** (`sablon_montaj_forex`, legacy `finisaje_colantare_vopsire`) mix with Letters **EUR presentation** → `complete_offer_total = null`.  
2. **Operator currency formatting** still defaults/labels **RON** on Quote list (and Intake pricing panel hardcodes `Intl` RON) while amounts can be EUR-native.  
3. **Light theme:** shell tokens work; **page-local night hex/slate** remain on commercial/execution surfaces.

Details: worklog `docs/worklog/realignment/2026-08-09_workos_v1_reality_check_light_intake_commercial.md`.
