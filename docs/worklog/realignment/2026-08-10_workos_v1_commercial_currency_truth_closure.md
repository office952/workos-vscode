# Worklog — WORKOS V1 Commercial Currency Truth Closure

```text
DATE = 2026-08-10
OWNER GO = AUTHORIZE_WORKOS_V1_COMMERCIAL_CURRENCY_TRUTH_CLOSURE
BASELINE_HEAD = 73131e41
BRANCH = feat/f7i-owner-rate-activation
RESULT = PASS_P0_COMMERCIAL_CURRENCY
V1_EXIT = HOLD
NEXT = WORKOS_V1_LIGHT_THEME_SYSTEMIC_CLOSURE
```

## Problem (reality check RC1–RC4)

Active Letters CPP RON sell lines under EUR presentation (`finisaje_colantare_vopsire`, `sablon_montaj_forex`) nulled `complete_offer_total` via mix. Intake/Quotes invented RON/EUR labels independent of backend stamp.

## Repair

### Backend

- Never emit `finisaje_colantare_vopsire` (RON catch-all) on Letters sell path.
- Never emit `sablon_montaj_forex` RON; forex selection → `COMMERCIAL_CONFIGURATION_INCOMPLETE` / `SABLON_MONTAJ_FOREX_V1=BLOCKED_PENDING_OWNER_EUR_SELL_RATE`.
- Dry-run / write totals: no invent `RON` when presentation currency missing.
- Legacy rule defs retained (classified); emission = 0.

### Frontend

- `formatCommercialAmount` + `extractQuoteCurrencyFromLineItems` → `null` when missing (no invent).
- Intake PricingInputPanel / QuoteCommercialSpine / Quotes / Quote panels / PDF: amount+currency from backend or honesty string.

### Not touched

- Policy A FX, Execution, MachineRun, Light systemic theme, finish Oracal/RAL/print formulas, DB schema.

## Proof

- Pytest: `test_commercial_price_proposal_preview.py` 34 passed (paper EUR complete offer, Oracal/RAL deltas, forex fail-closed, synthetic mix).
- Vitest: `quoteCurrency.test.ts` 12 passed.
- Runtime: CPP paper Oracal EUR; forex blocked without RON; dry-run workspace EUR complete offer; Intake UI EUR; Quotes empty → `monedă indisponibilă`.
- Evidence: `docs/qa/workos-v1-commercial-currency-truth-closure/`.

## Roadmap impact

```text
COMMERCIAL_OFFER = DONE_FOR_V1
BOUNDED_UI_HONESTY = PARTIAL_REOPEN_LIGHT_THEME_REMAINING
WORKOS_V1_EXIT_VERIFICATION = HOLD (Light + golden E2E remaining)
```

## LETTERS_FREEZE_STATE

Commercial rules data edits are DEV catalog / service gate only; no FREEZE ON operational content mutation. No schema migration.
