# RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_V1

## Verdict

```text
RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_READY
```

## Scope checked

- docs-only audit and fix plan
- no UI changes
- no Pricing value changes
- no seed run
- no DB write
- no Product Truth changes
- no CostEngine changes

## Accepted HEAD

- `3f9725b`

## Decision summary

Pricing UI nu este cauza locala a mismatch-ului pentru noile key-uri `return_cant`.

Auditul a confirmat urmatorul lant:

1. valorile asteptate exista in seed source;
2. registry service include key-urile in payload-ul template-driven;
3. UI-ul afiseaza `Lipsă` doar cand API-ul livreaza `base_cost = null`;
4. runtime DB-ul curent nu contine rows-urile necesare pentru cele sase key-uri noi.

Decizia corecta pentru urmatorul slice este deci un fix de runtime pricing backfill / seed application, nu un fix UI.

## Root cause decision

- `runtime DB missing`: confirmed
- `service mapping issue`: disproved
- `UI display issue`: disproved
- `unknown`: disproved

## Required matrix summary

| key | expected_value | exists_in_seed_source | exists_in_registry_service | exists_in_tests | appears_in_live_ui | live_ui_value | likely_cause | recommended_fix |
|---|---|---|---|---|---|---|---|---|
| `RETURN_CANT_VINYL_APPLICATION_LABOR` | `1 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed workcenter seed/backfill |
| `MAT-VOPSEA-RAL-CANT-30MM` | `2 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed material seed/backfill |
| `MAT-VOPSEA-RAL-CANT-60MM` | `2.5 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed material seed/backfill |
| `MAT-VOPSEA-RAL-CANT-80MM` | `3 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed material seed/backfill |
| `MAT-VOPSEA-RAL-CANT-100MM` | `4 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed material seed/backfill |
| `RETURN_CANT_RAL_PAINT_LABOR` | `1 EUR/ml` | yes | yes | yes | yes | `Lipsă / Rată lipsă / Blochează calcul complet` | `runtime_db_missing` | apply owner-confirmed workcenter seed/backfill |

## Evidence summary

### Live API

`GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS` a returnat item-urile noi cu:

- `base_cost = null`
- `status = missing_price`
- `confidence = missing`

### Runtime DB read-only

`backend/dev.db` nu are rows pentru:

- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`

In acelasi timp, rows active exista pentru codurile vechi validate deja in UI:

- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `FACE_VINYL_APPLICATION_LABOR`
- `PAINTING`

## Recommended next slice

```text
RETURN_CANT_RUNTIME_PRICING_BACKFILL_ALIGNMENT_V1
```

Scope minim pentru acel slice:

1. aplica seed-urile owner-confirmed deja existente in runtime DB-ul activ;
2. valideaza DB + API + live UI;
3. ruleaza doar testele dedicate Pricing Registry.

## Validation

- read-only audit only
- live API check performed
- runtime DB read-only check performed
- no build required
- no tests run in acest slice docs-only