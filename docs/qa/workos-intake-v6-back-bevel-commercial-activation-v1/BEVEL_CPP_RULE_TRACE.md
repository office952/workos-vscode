# BEVEL_CPP_RULE_TRACE

```text
line_code = sanfren_spate
label = Șanfren CNC spate Forex 10 mm
module = debitare_spate
pricing_rule_code = VOL_V2_BACK_BEVEL_CNC_ML
registry = CNC_ROUTER
gate = back_bevel_enabled OR backing_bevel_perimeter_ml > 0
```

Pass factor applied after registry resolve:

```text
unit_price = 1.5 × FOREX_10MM_BEVEL_PASSES_OWNER(2) = 3.0 EUR/ml
qty = contour ml
subtotal = qty × 3.0
```

Not added to F7I.1 owner-provisional set. Classified as workcenter-reuse provisional.
