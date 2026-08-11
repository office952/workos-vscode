# A_CONFIRMED_FALSE_REPRODUCTION

## Baseline

- Variant: `GRADI_EUR_SAFE`
- Snapshot: `docs/qa/workos-intake-v6-exhaustive-price-input-audit-v1/baselines/GRADI_EUR_SAFE.json`
- Seed: `backend/tests/fixtures/intake_v6_golden_gradi/workspace_payload.golden.json`
- Baseline complete offer: **708.5052 EUR** (Oracal 8500 @ confirmed 1260 width)

## Mutation

Audit apply: `{ "kind": "finish", "confirmed": false }`

Script: `backend/scripts/run_intake_v6_exhaustive_price_input_audit_v1.py` → `set_finish`:

1. `finish_setup.confirmed = false`
2. Every `letter_group_finishes[].confirmed = false`

## Observed (audit capture)

File: `docs/qa/workos-intake-v6-exhaustive-price-input-audit-v1/captures/A_CONFIRMED_FALSE.json`

| Field | Value |
|-------|-------|
| Blocker | `COMMERCIAL_CONFIGURATION_INCOMPLETE` (Oracal 8500 confirmed width) |
| `finisaje_oracal_8500_material` | unpriced (`subtotal: null`) |
| `complete_offer_total` | `null` / `COMMERCIAL_PRODUCT_BLOCKED` |
| EUR product subtotals | still ~691.4439 (other lines priced) |
| TOTAL_DELTA | ≈ −17.0613 |
| CLASS | PRICED_LINE + TOTAL_COMPOSITION P0 |

## Why P0

Fail-closed complete offer is correct. Honesty break: partial priced composition can still look like a living offer while official complete/adjusted offer is unavailable.

## Expected after repair

- dry-run: `pricing_status=BLOCKED`, empty `commercial_totals`, `offer_composition_readiness.commercial_composition_complete=false`
- Confirm UI: no final Ofertă money; product EUR labeled as composition-only / not client offer
- priced-write blocked
- Oracal 8500 law unchanged
