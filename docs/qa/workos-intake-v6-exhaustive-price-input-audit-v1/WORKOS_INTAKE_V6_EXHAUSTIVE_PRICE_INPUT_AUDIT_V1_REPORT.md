# WORKOS Intake V6 Exhaustive Price-Input Audit V1 — Final Report

**Owner GO:** `AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1`  
**Generated:** 2026-08-10T11:57:23.337909+00:00  
**Runner:** `backend/scripts/run_intake_v6_exhaustive_price_input_audit_v1.py`  
**Authority:** CPP commercial-price-preview EUR (OFAT)  

## Verdict envelope

```text
WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1 = PASS_WITH_DEFECTS_DOCUMENTED
PRODUCT_CODE_CHANGES = 0
PRICING_RULE_CHANGES = 0
PRODUCT_TRUTH_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
QUOTE_WRITES = 0
ORDER_WRITES = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```

## Baselines (frozen)

| Variant | total EUR | complete_offer | input sha |
|---|---:|---:|---|
| GRADI_EUR_SAFE | 708.5052 | 708.5052 | `9a141b93af41…` |
| BOND_LETTERS_ACM_OPTIONAL | 113.9 | 113.9 | `bc3b1ac90115…` |
| BOND_ACM_INCLUDED | 472.4 | 472.4 | `2898b86f5667…` |

Note: GRADI baseline normalizes golden `face_area_m2` → `letter_face_area_m2` for CPP critical geometry. Mounting template forced OFF for EUR-pure Letters baseline.

## Counts

| Metric | Value |
|---|---:|
| Operator-selectable values audited (scenarios) | 46 |
| PRICED_LINE | 16 |
| ZERO_DELTA_INTENTIONAL | 8 |
| NO_EFFECT | 21 |
| BLOCKER | 1 |
| MISSING_RULE | 0 |
| CURRENCY_MIX | 0 |
| ERROR | 0 |
| Confirmed P0 defects | 1 |
| Confirmed P1 defects | 20 |

## Manual RON special audit

```json
{
  "A_MANUAL_RON_100": {
    "MANUAL_RON_INPUT_ACCEPTED": true,
    "CONTRACT_SOURCE": "commercial_inputs.manual_adjustment_ron / finish_setup.commercial_inputs",
    "CONVERSION_USED": false,
    "FX_SOURCE": "NONE",
    "CPP_RESULT": {
      "status": "ready",
      "subtotal": 708.5052,
      "currency": "EUR",
      "TOTAL_DELTA": 0.0
    },
    "COMPLETE_OFFER_TOTAL": 708.5052,
    "OBSERVED_CLASS": "NO_EFFECT",
    "P0_CURRENCY_POLICY": false
  },
  "B_MANUAL_RON_100": {
    "MANUAL_RON_INPUT_ACCEPTED": true,
    "CONTRACT_SOURCE": "commercial_inputs.manual_adjustment_ron / finish_setup.commercial_inputs",
    "CONVERSION_USED": false,
    "FX_SOURCE": "NONE",
    "CPP_RESULT": {
      "status": "ready",
      "subtotal": 472.4,
      "currency": "EUR",
      "TOTAL_DELTA": 0.0
    },
    "COMPLETE_OFFER_TOTAL": 472.4,
    "OBSERVED_CLASS": "NO_EFFECT",
    "P0_CURRENCY_POLICY": false
  }
}
```

Interpretation: CPP path accepts input and **ignores** it (delta 0, no FX) — not a CPP RON→EUR injection. Separately, FE `intakeV6OfferCalculator` **adds RON into EUR display math without FX** → additional **P0 UI_COMMERCIAL_PRESENTATION** (see UI_HONESTY.md). EUR-law compatibility: **NO / BLOCKED**. Not repaired.

## Plain answers

| Question | Answer |
|---|---|
| How many operator-selectable values audited? | 46 |
| P0 / P1 confirmed defects? | **2 P0** (1 matrix `A_CONFIRMED_FALSE` + 1 UI manual-RON/EUR calculator) / **20 P1** matrix |
| Fields accepted by UI but never reach CPP money? | markup/discount/manual_ron via `commercial_inputs` show **no CPP preview delta** (path likely not applied in preview OFAT) |
| Fields reach CPP lines but not complete_offer correctly? | `A_CONFIRMED_FALSE` (P0 TOTAL_COMPOSITION); mounting forex template **BLOCKER** incomplete config |
| Intentionally non-commercial controls? | light_color; face Oracal color code; stock aluminum return surcharge; `mounting_system` readonly |
| Does every paid operator choice affect official price correctly? | **NO** |
| Letters baseline commercially coherent? | **YES** |
| Letters+ACM baseline commercially coherent? | **YES** (included 472.4 vs optional 113.9) |
| Manual RON compatible with EUR commercial law? | **NO / BLOCKED** — UI adds RON into EUR display without FX; CPP ignores field |
| FIRST ROOT CAUSE TO REPAIR | `UI_FE_OFFER_CALCULATOR_RON_INTO_EUR` (+ commercial_inputs not authoritative in CPP preview) |
| NEXT_RECOMMENDED_BUILD | `WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1` |
| NEXT_TASK | NOT_AUTHORIZED |
| Roadmap awareness | 10/10 |
| Dead Pieces Check | UI commercial adjustments + lighting/PSU/depth qty paths + ACM construction qty + confirm-gate complete_offer |
| Forbidden Scope Respected | YES |

## Artifacts

- OPERATOR_INPUT_LEDGER.md
- scenario_catalog_v1.json
- results.jsonl
- INPUT_PRICE_MATRIX.md
- DEFECTS.md
- ROOT_CAUSE_SUMMARY.md
- NOT_EXERCISED.md
- baselines/
- captures/
- manual_ron_audit.json
