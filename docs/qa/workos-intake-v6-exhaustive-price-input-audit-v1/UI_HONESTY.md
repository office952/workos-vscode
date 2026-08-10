# UI honesty spot-check (P0 + sample P1)

**Method:** Compare operator-facing commercial expectation vs CPP OFAT capture. Full browser mutation of every cell was NOT required for API forge; this section records honesty classification for prioritized rows.

| scenario | severity | UI_MATCHES_CPP | UI_MATCHES_DRY_RUN | Classification | Notes |
|---|---|---|---|---|---|
| A_CONFIRMED_FALSE | P0 | N_A_LIVE | N_A | TOTAL_COMPOSITION | CPP: lines change + `complete_offer` invalid (`COMMERCIAL_PRODUCT_BLOCKED` family). UI confirm gate must not show a healthy complete total when confirmed=false. |
| A_MARKUP_10 | P1 | NO (likely) | N_A | UI_COMMERCIAL_PRESENTATION / NORMALIZATION | Review “Adaos %” is operator-visible; CPP preview OFAT with `commercial_inputs.markup_percent=10` produced **TOTAL_DELTA=0**. Frontend offer calculator may apply markup locally — risk of UI≠CPP. |
| A_DISCOUNT_5 | P1 | NO (likely) | N_A | same as markup | Same path. |
| A_MANUAL_RON_100 | P0 (UI) | **NO** | N_A | UI_COMMERCIAL_PRESENTATION + CURRENCY_COMPOSITION | `intakeV6OfferCalculator.ts` does `base + markup + manualAdjustmentRon` with **no FX** — RON units added into EUR display math. CPP preview ignores the field (delta 0). Dual truth: UI can show wrong EUR; CPP does not convert. **Do not repair in this GO.** |
| A_MOUNT_TMPL_FOREX_ON | P1 | N_A | N_A | CPP_RULE_SELECTION | Preview **BLOCKER** `COMMERCIAL_CONFIGURATION_INCOMPLETE` — template on without full prep config. |
| A_LED_POWER_* / A_PSU_* | P1 | UNKNOWN | N_A | CPP_RULE_SELECTION | UI recomputes module/PSU counts live; CPP OFAT showed no money delta for power/PSU watt changes on fixed geometry — verify whether lighting money is qty-frozen at geometry, not watt selection. |
| B_ACM_* construction | P1 | UNKNOWN | N_A | NORMALIZATION / COMPOSITION | ACM included baseline priced (472.4 vs 113.9 optional); fold/thickness/L1/foil/sheet OFAT produced no further line deltas — qty may be under-bound to mutated nested paths. |

```text
UI_HONESTY_SPOT_CHECK = DOCUMENTED
BROWSER_FULL_MATRIX = NOT_REQUIRED_FOR_API_FORGE
```
