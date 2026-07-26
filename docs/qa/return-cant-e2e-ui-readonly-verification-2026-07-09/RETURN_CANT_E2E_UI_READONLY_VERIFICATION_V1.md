# RETURN_CANT_E2E_UI_READONLY_VERIFICATION_V1

## Verdict

```text
RETURN_CANT_E2E_UI_READONLY_BLOCKED
```

Blocajul principal nu este runtime-ul sau accesul la pagini, ci faptul ca Pricing UI nu expune noile key-uri `return_cant` cu valorile asteptate; ele apar in view-ul UI ca intrari lipsa / rate lipsa.

## Accepted HEAD

- `3855b58`

## Runtime status

- backend: running on `http://127.0.0.1:8000`
- frontend: running on `http://127.0.0.1:3000`
- startup note: helperul `npm run dev:backend` nu exista in acest checkout; backend-ul a fost pornit cu `scripts/dev-backend.ps1`, frontend-ul cu Vite local

## URLs verificate

- `http://127.0.0.1:3000/intake`
- `http://127.0.0.1:3000/intake-v6/IR-MRBWV5GY/operator`
- `http://127.0.0.1:3000/inventory/pricing`
- `http://127.0.0.1:8000/docs`

## Screenshot artifacts

### Intake / V6

- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-overview.png`
  - intended to show the active Intake V6 review workspace
  - actual artifact is degraded / mostly blank because of integrated-browser capture clipping bug
- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-vector-logo-cant-zone.png`
  - intended to show the expanded `Vector Logo` cant section
  - actual artifact is degraded / not reliable as standalone proof
- `C:\Users\offic\workos_app_vs\logs\return-cant-intake-v6-blocked-awareness.png`
  - intended to show the blocked read-only awareness panel for `return_cant`
  - actual artifact is degraded / not reliable as standalone proof

### Pricing

- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-overview.png`
  - general Pricing page capture
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-all-entries.png`
  - Pricing page after `Toate intrările`, used to confirm presence of requested codes in UI text
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-return-cant.png`
  - search/filter result for `RETURN_CANT_`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-ral-cant.png`
  - search/filter result for `MAT-VOPSEA-RAL-CANT-`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-oracal.png`
  - search/filter result for `MAT-ORACAL-`
- `C:\Users\offic\workos_app_vs\logs\return-cant-pricing-search-profile.png`
  - search/filter result for `MAT-PROFIL-LATERAL-LITERE-`

## Intake V6 findings

### Exact page / route

- `http://127.0.0.1:3000/intake-v6/IR-MRBWV5GY/operator`
- page state reached from:
  1. `http://127.0.0.1:3000/intake`
  2. open first listed request `IR-MRBWV5GY`
  3. click `Deschide Intake V6`
  4. remain on step `Review` > tab `Finisaje`

### What is visible

- `Vector Logo` row is present in review
- cant summary is visible as `Oracal 651 · 80 mm`
- expanded cant fields show old UI options:
  - `Alb`
  - `Negru`
  - `Auriu`
  - `Argintiu`
  - `Vopsit RAL`
  - `Oracal 651`
- current row shows:
  - `Finisaj cant / volum = Oracal 651`
  - `Adâncime cant / volum (mm) = 80`
  - `Culoare Oracal cant = Oracal 651-020 — Golden yellow`

### What should have been visible for alignment

- target terminology closer to:
  - `Culoare Stoc`
  - `Folie autocolanta`
  - `Vopsit RAL`
- stock color should have a meaningful atelier-facing label source, not only hardcoded options
- cant UI would ideally expose broader catalog semantics if runtime is expected to grow beyond `Oracal 651`

### Missing / blocked in UI

- `UI terminology alignment pending`
- `stock_color_label_input_missing`
- `catalog_supports_broader_series_but_ui_runtime_limited`

### Vector Litere / Vector Logo coverage

- `Vector Logo` cant zone was observed directly in this workspace
- no `Vector Litere` cant section was present in this specific workspace, so that part was not visually verified on live data in this run

### Verdict

```text
BLOCKED
```

Reason:

1. read-only review surface is reachable and useful;
2. but terminology is still on the old model for cant choices;
3. stock-color semantic target is not represented as a dedicated atelier-facing label input;
4. the workspace observed only one live `Vector Logo` case, not a full letters/logo matrix.

## Pricing UI findings

### Exact page / route

- `http://127.0.0.1:3000/inventory/pricing`

### Verified non-regression items visible in UI text

- `MAT-ORACAL-641` shows `6,50 EUR`
- `MAT-ORACAL-651` shows `9,00 EUR`
- `MAT-PROFIL-LATERAL-LITERE-30MM` shows `2,00 EUR`
- `MAT-PROFIL-LATERAL-LITERE-60MM` shows `3,00 EUR`
- `MAT-PROFIL-LATERAL-LITERE-80MM` shows `4,00 EUR`
- `MAT-PROFIL-LATERAL-LITERE-100MM` shows `5,00 EUR`

These match the expected non-regression values.

### New `return_cant` keys observed in UI text

After switching to `Toate intrările`, the page text contains:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

### Actual UI state for the new keys

Observed snippets from the live Pricing page show:

- `RETURN_CANT_VINYL_APPLICATION_LABOR` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`
- `MAT-VOPSEA-RAL-CANT-30MM` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`
- `MAT-VOPSEA-RAL-CANT-60MM` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`
- `MAT-VOPSEA-RAL-CANT-80MM` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`
- `MAT-VOPSEA-RAL-CANT-100MM` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`
- `RETURN_CANT_RAL_PAINT_LABOR` -> `Lipsă` / `Rată lipsă` / `Blochează calcul complet`

### Expected values that were NOT shown in Pricing UI

- `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`

### Verdict

```text
BLOCKED
```

Reason:

UI visibility exists, but the new `return_cant` entries are rendered as missing instead of showing the expected live values.

## Product Truth / awareness findings

### What was observed

The read-only blocked panel in Intake V6 states:

- `Return/cant component preview este blocat.`
- `RETURN_CANT_MAPPER_BLOCKED`
- `quote_geometry.letter_perimeter_m ramane context-only`
- `Lipseste components.face.confirmed_perimeter confirmed`
- `Lipseste components.return_cant.confirmation_state = confirmed`

Runtime evidence shown in the panel includes:

- perimeter source observed = `quote_geometry.letter_perimeter_m`
- dependency face perimeter = `quote_geometry.letter_perimeter_m`
- confirmation state path = `components.return_cant.confirmation_state`

### Policy compliance observed

- the UI does **not** falsely declare `confirmed`
- the UI keeps `blocked` when confirmed perimeter is missing
- the UI explicitly treats `quote_geometry.letter_perimeter_m` as `context_only`
- the UI keeps `components.return_cant.confirmation_state` in missing/blocked territory
- the UI is read-only and does not present itself as writing Product Truth

### Verdict

```text
PASS for blocked/read-only awareness semantics
```

This area is the strongest part of the UI verification run.

## Canonical runtime container path awareness

### Observed

- the blocked awareness panel explicitly references `components.return_cant.confirmation_state`
- no live UI text was observed exposing `components.returnCant` as target final
- no live UI text was observed exposing `components.return.*` as target final

### Verdict

```text
PASS with note
```

The canonical path is visible in awareness text. No direct live evidence of legacy runtime path exposure was found in this run.

## Terminology alignment

### Current UI

- old cant finish labels still visible directly in combobox:
  - `Alb`
  - `Negru`
  - `Auriu`
  - `Argintiu`
  - `Vopsit RAL`
  - `Oracal 651`

### Target terminology

- `Culoare Stoc`
- `Folie autocolanta`
- `Vopsit RAL`

### What is aligned

- `Vopsit RAL` already exists as visible UI term
- RAL/Oracal color selector concepts exist structurally in the review field component model

### What remains pending

- stock-color umbrella terminology is not visible
- vinyl umbrella terminology is not visible; UI still names the concrete current variant `Oracal 651`
- current UI suggests a narrower runtime than the catalog/system contracts allow

### Verdict

```text
UI terminology alignment pending
```

## Agent opinion about the UI

UI-ul are doua fete foarte diferite.

Partea buna:

1. awareness-ul Product Truth pentru `return_cant` este surprinzator de clar si disciplinat;
2. panoul blocat spune explicit ce nu este confirmat si nu pretinde ca sistemul este ready;
3. folosirea `components.return_cant.confirmation_state` in textul read-only este in directia corecta.

Partea slaba:

1. operatorul vede inca modelul vechi de termeni pentru cant, ceea ce risca sa amestece `stock_color` cu culori hardcoded si `vinyl_application` cu un singur produs concret (`Oracal 651`);
2. lipsa unui input sau model clar pentru `stock_color_label` face zona mai rigida decat contractul tinta;
3. Pricing UI este in prezent cel mai problematic punct: noile key-uri exista in pagina, dar apar ca lipsa/rata lipsa, ceea ce poate induce concluzia falsa ca implementarea nu exista.

Verdictul meu sincer:

- awareness UI pentru Product Truth este acceptabil momentan;
- UI-ul de selectie cant este utilizabil, dar semantic ramas in urma;
- Pricing UI pentru noile `return_cant` keys nu este acceptabil ca verificare finala, pentru ca nu reflecta valorile asteptate.

## Forbidden scope confirmation

- no UI changes
- no Pricing changes
- no adapter changes
- no Product Truth writes
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB migration
- no seed run

## Validation

- safety gate executed
- backend/frontend startup verified
- UI routes opened live in integrated browser
- screenshots captured as artifacts in `logs/`
- read-only observations gathered from live page snapshots and UI text
- `git diff --check`
- docs-only diff only
