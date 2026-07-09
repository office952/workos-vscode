# 2026-07-09 - return cant e2e ui readonly verification v1

HEAD before:

- `3855b58`

Task:

- `RETURN_CANT_E2E_UI_READONLY_VERIFICATION_V1`

URLs checked:

- `http://127.0.0.1:3000/intake`
- `http://127.0.0.1:3000/intake-v6/IR-MRBWV5GY/operator`
- `http://127.0.0.1:3000/inventory/pricing`
- `http://127.0.0.1:8000/docs`

Runtime notes:

- backend was not running at start
- frontend was not running at start
- frontend started successfully with local Vite on `127.0.0.1:3000`
- backend started successfully via `scripts/dev-backend.ps1`
- `npm run dev:backend` is not available in this checkout even though earlier repo guidance referenced it

Main findings:

1. Intake V6 review for the live workspace `IR-MRBWV5GY` exposes `Vector Logo` cant fields and a disciplined blocked awareness panel for `return_cant`.
2. The cant UI still uses old finish labels (`Alb`, `Negru`, `Auriu`, `Argintiu`, `Vopsit RAL`, `Oracal 651`) instead of the target umbrella terminology (`Culoare Stoc`, `Folie autocolanta`, `Vopsit RAL`).
3. The current live row showed `Oracal 651 · 80 mm` with `Culoare Oracal cant = Oracal 651-020 — Golden yellow`.
4. Product Truth awareness behavior looked correct: blocked, context-only perimeter, no false confirmed state, canonical `components.return_cant.confirmation_state` visible.
5. Pricing UI is the decisive blocker: all requested new `return_cant` keys are present in the live page text but rendered as `Lipsă / Rată lipsă / Blochează calcul complet` instead of the expected values.
6. Non-regression items remain correct in Pricing UI text:
   - `MAT-ORACAL-641 = 6,50 EUR`
   - `MAT-ORACAL-651 = 9,00 EUR`
   - `MAT-PROFIL-LATERAL-LITERE-30MM = 2,00 EUR`
   - `MAT-PROFIL-LATERAL-LITERE-60MM = 3,00 EUR`
   - `MAT-PROFIL-LATERAL-LITERE-80MM = 4,00 EUR`
   - `MAT-PROFIL-LATERAL-LITERE-100MM = 5,00 EUR`

Important QA blockers recorded:

- `UI terminology alignment pending`
- `stock_color_label_input_missing`
- `catalog_supports_broader_series_but_ui_runtime_limited`

Screenshot artifacts:

- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-overview.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-vector-logo-cant-zone.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-blocked-awareness.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-overview.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-all-entries.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-return-cant.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-ral-cant.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-oracal.png`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-profile.png`

Capture note:

- integrated-browser screenshot capture was reliable enough for Pricing artifacts
- Intake capture on disk suffered clipping / blank-area degradation, so the strongest Intake evidence remains the live accessibility snapshot plus the presence of generated artifacts

Decision:

- `RETURN_CANT_E2E_UI_READONLY_BLOCKED`

Reason:

- cannot mark this verification PASS while the Pricing UI still shows the new `return_cant` keys as missing rates instead of the expected values

Next recommended prompt:

- `RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_V1`