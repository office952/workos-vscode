# Return Cant Pricing UI Visibility Fix Plan

## 1. Purpose

Acest document fixeaza auditul docs-only si planul de remediere pentru cazul in care noile key-uri `return_cant` apar in Pricing UI, dar sunt randate ca lipsa.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
mode = pricing_ui_visibility_fix_plan
```

Acest document nu implementeaza:

- UI changes;
- Pricing value changes;
- seed run;
- DB write;
- runtime backfill;
- Product Truth runtime bridge;
- CostEngine changes.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_READY
```

Semnificatie exacta:

1. cauza locala este suficient de clara pentru a planifica fixul fara ambiguitate critica;
2. blocajul live nu este in UI rendering contract si nici in registry service mapping;
3. blocajul live este lipsa rows-urilor runtime pentru cele sase key-uri noi in `backend/dev.db`;
4. remedierea recomandata este un slice de runtime pricing backfill / seed application controlat, nu un fix UI.

## 3. Local Hypothesis And Discriminating Check

Ipoteza locala falsificabila a fost:

```text
seed source si registry service includ key-urile return_cant,
dar runtime DB-ul curent nu contine rows-urile necesare,
iar Pricing UI afiseaza corect rezultatul lipsa primit din API.
```

Check-ul discriminatoriu minim a fost:

1. citirea seed-urilor, a `backend/services/pricing_registry_service.py`, a paginii `frontend/src/pages/Pricing.tsx` si a testelor dedicate;
2. apel live la `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS`;
3. query read-only in `backend/dev.db` pentru cele sase coduri afectate;
4. query read-only de contrast pentru codurile vechi care apar corect in UI.

Rezultatul a confirmat ipoteza.

## 4. Evidence Summary

### 4.1 Seed source exists

Auditul seed-urilor confirma valori explicite pentru toate key-urile afectate:

- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
  - `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
  - `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
  - `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
  - aceleasi key-uri sunt prezente si in seed-ul simplificat V5, ca dovada suplimentara ca nu lipsesc din sursa de seed.

### 4.2 Registry service path exists

`backend/services/pricing_registry_service.py` include aceste key-uri in registrul template-driven pentru `TPL-VOLUMETRIC-LETTERS_v2` si construieste item-uri `missing_price` doar cand row-ul runtime lipseste sau nu are cost/rata.

Rezultatul live al endpoint-ului a confirmat exact acest comportament:

- key-urile noi apar in `items`;
- `base_cost = null`;
- `status = missing_price`;
- `confidence = missing`.

### 4.3 UI display path is not the cause

`frontend/src/pages/Pricing.tsx` si componentele Pricing afiseaza `Lipsă` doar cand `item.base_cost` este `null` sau statusul este `missing_price`.

Asta inseamna ca UI-ul nu ascunde valori valide; afiseaza fidel payload-ul live primit de la API.

### 4.4 Runtime DB is the missing layer

Query-ul read-only in `backend/dev.db` nu a gasit niciun row pentru:

- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`

Query-ul de contrast a gasit rows active pentru item-urile vechi care apar corect in live UI:

- `MAT-ORACAL-641 = 6.5 EUR`
- `MAT-ORACAL-651 = 9 EUR`
- `MAT-PROFIL-LATERAL-LITERE-{30,60,80,100}MM = {2,3,4,5} EUR`
- `FACE_VINYL_APPLICATION_LABOR = 5 EUR/mp`
- `PAINTING = 4 EUR/ml`

Concluzie locala:

```text
service path present + UI path present + runtime rows missing = runtime DB missing
```

## 5. Required Matrix

| key | expected_value | exists_in_seed_source | exists_in_registry_service | exists_in_tests | appears_in_live_ui | live_ui_value | likely_cause | fix_options | recommended_fix |
|---|---|---|---|---|---|---|---|---|---|
| `RETURN_CANT_VINYL_APPLICATION_LABOR` | `1 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent workcenter seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed workcenter seed/backfill for current runtime DB` |
| `MAT-VOPSEA-RAL-CANT-30MM` | `2 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent material seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed material seed/backfill for current runtime DB` |
| `MAT-VOPSEA-RAL-CANT-60MM` | `2.5 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent material seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed material seed/backfill for current runtime DB` |
| `MAT-VOPSEA-RAL-CANT-80MM` | `3 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent material seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed material seed/backfill for current runtime DB` |
| `MAT-VOPSEA-RAL-CANT-100MM` | `4 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent material seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed material seed/backfill for current runtime DB` |
| `RETURN_CANT_RAL_PAINT_LABOR` | `1 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | `apply idempotent workcenter seed`; `targeted runtime backfill`; `dev bootstrap seeding` | `apply owner-confirmed workcenter seed/backfill for current runtime DB` |

## 6. Root-Cause Bucket Decision

Evaluarea bucket-urilor cerute este:

- `runtime DB missing`: yes, confirmed
- `service mapping issue`: no, disproved by live API payload
- `UI display issue`: no, disproved by direct `base_cost = null` rendering path
- `unknown`: no

## 7. Recommended Fix Slice

Fixul recomandat nu este in Pricing UI.

Fixul recomandat este:

```text
RETURN_CANT_RUNTIME_PRICING_BACKFILL_ALIGNMENT_V1
```

Continut minim recomandat pentru acel slice:

1. aplica idempotent in runtime DB seed-urile owner-confirmed deja existente pentru:
   - `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
   - `backend/seeds/seed_volumetric_workcenter_rates.py`
2. valideaza prin query read-only si prin `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS` ca toate cele sase key-uri au `base_cost` nenul;
3. ruleaza doar testele existente pentru registry/material/workcenter coverage;
4. reverifica live Pricing UI ca aceleasi key-uri nu mai apar ca `missing_price`.

## 8. Fix Options Tradeoff

### Option A — Apply existing owner-confirmed seeds to current runtime DB

Avantaje:

1. foloseste sursele deja existente si testate;
2. este aliniat cu cauza locala confirmata;
3. pastreaza zero schimbari UI si zero schimbari de pricing contract.

Riscuri:

1. trebuie rulat controlat, pentru a nu masca alte lipsuri de env.

### Option B — Add targeted one-off runtime backfill script for only the six keys

Avantaje:

1. foarte ingust;
2. usor de verificat.

Riscuri:

1. dubleaza logic already present in seeds;
2. poate produce doua surse de adevar operationale pentru acelasi set de valori.

### Option C — Change Pricing UI to special-case these keys

Verdict:

1. respins;
2. ar ascunde lipsa reala din registry runtime;
3. ar incalca boundary-ul corect dintre UI si sursa de pricing.

Recomandarea este Option A, cu posibil guard suplimentar de QA dupa backfill.

## 9. Validation Plan For The Future Fix

Validarea minima ceruta dupa implementarea fixului recomandat:

1. query read-only in `backend/dev.db` pentru cele sase key-uri;
2. `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS` trebuie sa returneze `base_cost` si `status = active` pentru toate sase;
3. rerun pentru:
   - `backend/tests/test_return_cant_pricing_registry_keys.py`
   - `backend/tests/test_return_cant_owner_confirmed_materials.py`
   - `backend/tests/test_volumetric_operation_labor_rates.py`
4. reverificare live UI pe `/inventory/pricing`.

## 10. Why This Slice Is READY

Slice-ul este `READY`, nu `BLOCKED`, deoarece:

1. exista sursa seed pentru toate valorile asteptate;
2. exista service path care le expune corect cand rows-urile exista;
3. exista teste dedicate care codifica asteptarile;
4. exista o cauza locala unica si verificabila in runtime DB;
5. nu mai este nevoie de explorare suplimentara pentru a stabili urmatorul fix.