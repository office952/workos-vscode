# ROOT_CAUSE_SUMMARY

Group defects by shared cause (not one ticket per scenario).

## FIRST_ROOT_CAUSE_TO_REPAIR (Owner priority)

**`UI_FE_OFFER_CALCULATOR_RON_INTO_EUR` + `COMMERCIAL_INPUTS_NOT_AUTHORITATIVE_IN_CPP_PREVIEW`**

- Frontend [`intakeV6OfferCalculator.ts`](../../../frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts) applies `manualAdjustmentRon` directly onto the EUR base (`base + markup + manualAdjustmentRon`) with **no FX contract**.
- CPP OFAT accepts the payload path but produces **TOTAL_DELTA=0** (no conversion, no apply).
- Same family: markup/discount OFAT also show **no CPP preview delta** while UI calculator mutates displayed totals locally.
- Repair build must pick **one authority** (CPP/dry-run) for official totals and stop dual FE money math — not 20 micro-patches.

---

## QTY_OR_BACKING_DEPTH_NO_CPP_DELTA (5 scenarios)
- Boundary cluster: CPP_RULE_SELECTION
- Severity mix: {'P1': 5}
- Scenarios: A_DEPTH_30, A_DEPTH_80, A_DEPTH_100, A_BACK_forex_10_no_bevel, A_BACK_forex_10_with_bevel
- Shared rationale sample: expected commercial effect but no line/total delta

## LIGHTING_PSU_SELECTION_NO_CPP_DELTA (6 scenarios)
- Boundary cluster: CPP_RULE_SELECTION
- Severity mix: {'P1': 6}
- Scenarios: A_LED_STRIP, A_LED_POWER_1.0, A_LED_POWER_1.44, A_PSU_100, A_PSU_160, A_PSU_200
- Shared rationale sample: expected commercial effect but no line/total delta

## MOUNTING_TEMPLATE_OR_SITE_COMMERCIAL_PATH (2 scenarios)
- Boundary cluster: CPP_RULE_SELECTION
- Severity mix: {'P1': 2}
- Scenarios: A_MOUNT_TMPL_FOREX_ON, A_MOUNT_SITE_ON
- Shared rationale sample: expected price; blocked ['COMMERCIAL_CONFIGURATION_INCOMPLETE']

## COMMERCIAL_ADJUSTMENTS_NOT_IN_CPP_PREVIEW (2 scenarios)
- Boundary cluster: CPP_RULE_SELECTION
- Severity mix: {'P1': 2}
- Scenarios: A_MARKUP_10, A_DISCOUNT_5
- Shared rationale sample: expected commercial effect but no line/total delta

## CONFIRM_GATE_VS_COMPLETE_OFFER (1 scenarios)
- Boundary cluster: TOTAL_COMPOSITION
- Severity mix: {'P0': 1}
- Scenarios: A_CONFIRMED_FALSE
- Shared rationale sample: line pricing changed but complete_offer invalid

## ACM_CONSTRUCTION_MUTATION_NO_LINE_DELTA (5 scenarios)
- Boundary cluster: CPP_RULE_SELECTION
- Severity mix: {'P1': 5}
- Scenarios: B_ACM_FOLD_1, B_ACM_THICKNESS_4, B_ACM_L1_80, B_ACM_FOIL_AFTER_FRAME, B_ACM_SHEET_COLORAT
- Shared rationale sample: expected commercial effect but no line/total delta

