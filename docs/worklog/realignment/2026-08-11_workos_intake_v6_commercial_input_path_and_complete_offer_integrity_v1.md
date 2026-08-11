# Worklog — WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1

Date: 2026-08-11

## GO

`AUTHORIZE_WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1` → IMPLEMENT / EXECUTE

Owner lock: `MANUAL_RON_POLICY = A`

## Outcome

- Official Ofertă money = backend dry-run `commercial_totals` on CPP base
- Manual RON→EUR via `require_configured_eur_to_ron_rate` when ≠0; `_round_money` only
- FE no longer recalculates official adjusted totals
- Post-freeze offer/review consume quote columns + frozen adjustment trace (identity check)
- `A_CONFIRMED_FALSE` left out of scope
- Evidence under `docs/qa/workos-intake-v6-commercial-input-path-and-complete-offer-integrity-v1/`
- PUSH = NO

## Baseline

`33848981` (VAT + FX closures intact)
