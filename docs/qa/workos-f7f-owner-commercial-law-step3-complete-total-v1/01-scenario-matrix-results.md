# F7F — Owner commercial law scenario matrix (live runtime)

Source: `evidence/runtime-scenario-matrix.json`, produced by `_f7f_runtime_probe.py` against the
live dev stack (`:8000`) via the read-only commercial-price-preview endpoint. Geometry held
constant: face area **A = 2.5 m²**, perimeter 8.0 m, return depth 100 mm, 9 letters.

Baseline with no finish (`F1`) = **490.00 RON**, all letters product.

## Face finish

| Scenario | Material line | Rate | Application line | Rate | Status |
|---|---|---|---|---|---|
| `F1` none | — | — | — | — | ready, no finish lines |
| `F2` Oracal 651 code 021 | `finisaje_oracal_651_material` | **5.00 EUR/m²** → 12.50 EUR | `finisaje_aplicare_autocolant_fata` | **3.00 EUR/m²** → 7.50 EUR | ready |
| `F2b` Oracal 651 code 032 | same line | **5.00 EUR/m²** (identical) | same | 3.00 EUR/m² | ready — **no colour tier** |
| `F3` Oracal 641 | `finisaje_oracal_641_material` | 6.50 EUR/m² → 16.25 EUR | same | 3.00 EUR/m² | ready (rate carried over from F7E, Owner decision open) |
| `F4` Oracal 8500, width missing | `finisaje_oracal_8500_material` | **null** (no guess) | same | 3.00 EUR/m² | **blocked** — `COMMERCIAL_CONFIGURATION_INCOMPLETE` |
| `F4a` Oracal 8500 @ 1000 mm | same | **17.00 EUR/m²** → 42.50 EUR | same | 3.00 EUR/m² | ready |
| `F4b` Oracal 8500 @ 1260 mm | same | **13.50 EUR/m²** → 33.75 EUR | same | 3.00 EUR/m² | ready |
| `F5` print + laminate | `finisaje_print_laminate_material` | **10.00 EUR/m²** → 25.00 EUR | same | 3.00 EUR/m² | ready — F7E `COMMERCIAL_RULE_MISSING` removed |
| `F6` printed_vinyl (no laminate) | — | — | — | — | **blocked** — `COMMERCIAL_RULE_MISSING` |

Owner arithmetic confirmed: A×5+3, A×17+3, A×13.5+3, A×10+3 all hold, tax-exclusive, in EUR.

## Return cant

| Scenario | Result |
|---|---|
| `R1` white_aluminum (stock) | 490.00 RON — **zero delta preserved**, no `finisaje_cant_*` line, no application line |
| `R2` ral_paint | `finisaje_cant_ral_material` 4.00 EUR/ml + `finisaje_cant_ral_labor` 5.00 EUR/ml — **F7E behaviour preserved** |
| `R3` oracal_wrapped | `finisaje_cant_oracal_material` **5.00 EUR/m²** and `finisaje_cant_oracal_labor` **3.00 EUR/m²**, both on the developed wrap area 0.80 m² (8.0 m × 100 mm) |

The cant is charged as a **distinct proven surface** from the face, which is why face and cant can
each carry one application line without double-charging the same square metre.

## ACM sheet (backend tests, `tests/test_f7f_owner_commercial_law_step3_total.py`)

| Variant | Environment | Result |
|---|---|---|
| standard | interior | 15.00 EUR/m² |
| colorat | interior | 15.00 EUR/m² |
| absent | — | 15.00 EUR/m² (owner-confirmed default sheet) |
| oglinda_gold | interior | **40.00 EUR/m² replacement** — exactly one `acm_panel_face_material` line, no surcharge line |
| oglinda_antracit | exterior, no SKU | **blocked** — `TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED` |
| oglinda_antracit | exterior, proven SKU | blocker cleared |
| unknown token | interior | **blocked** — `COMMERCIAL_RULE_MISSING`, price `null` (no fallback to 15) |

## Step 3, workspace IV6-9C5D9538 (`5a5ce742-f50f-47b0-985b-32cc6f2fb6a4`)

Source: `evidence/runtime-step3-dry-run.json`, `evidence/step3-offer-product-breakdown.png`.

| | Before F7F | After F7F |
|---|---|---|
| Litere | folded into one figure (~249.98 EUR presented as the offer) | `Subtotal Litere` = **71.36 EUR + 1 724.44 RON** |
| Panou ACM | absent from the total (A-F4) | `Subtotal Panou ACM` = **190.78 EUR** |
| Complete total | shown as if complete | **`Total ofertă indisponibil`** + reason `COMMERCIAL_CURRENCY_MIX_UNRESOLVED` |
| Currency | hardcoded `?? "RON"` | reported per bucket; no fallback |
| VAT | frontend default 19 / hardcoded 21 | `Prețuri fără TVA (TVA 21% conform politicii fiscale)` from `company_commercial_settings.default_vat_pct` |
