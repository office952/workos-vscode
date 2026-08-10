# WORKOS_VAT_SNAPSHOT_BOUNDARY_INTEGRITY_V1_REPORT

## A. Verdict

**PASS** (bounded freeze-boundary repair)

## B. HEAD

- Before: `79c0f6e1`
- After: tip of `feat/f7i-owner-rate-activation` containing `fix(commercial): preserve frozen VAT across offer review`

## C–F. Source / root cause / frozen source

- Root cause: post-freeze offer/pricing-review called `get_default_vat_pct` on frozen CPP net
- Frozen VAT source chosen: **`notes.commercial_adjustment_trace.vat_percent`** (already stamped at priced write; Order already consumed it)
- Canonical because: durable without schema; aligns Order convert; CPP rate was always null historically

## G–H. Fixes

- Offer: frozen resolver + restamp notes rate on write
- Pricing-review post-freeze: frozen resolver; pre-freeze unchanged

## I–M. Behaviors

- Pre-freeze: Settings default still used for new work / dry-run / new freeze CPP stamp
- Quote persisted amounts unchanged by later Settings edits
- Order: retains notes `accepted_vat_percent` path (regression covered via Scenario A notes integrity)
- Documents: unchanged (still no live Settings GET); Settings copy does not over-claim documents
- Historical: no rewrite; missing provenance fail-closed

## N–Q. UI / tests / runtime / Owner DB

- Settings copy updated for freeze honesty
- 28 pytest passed
- Mutating proof on isolated test DB only; OWNER_DEV_DB_MUTATIONS = 0

## R–S. Files / commits

See git commit. Key code: `frozen_commercial_vat_resolver.py`, offer + pricing-review services, freeze stamp, Settings copy, tests, QA pack.

## T. Governance

No new Modules system; ownership semantics unchanged beyond runtime honesty.

## U–V. Remaining

- FIRST REMAINING ROOT CAUSE = FX fail-open (`get_eur_to_ron_rate` default 5.0) vs Logo/CPP fail-closed
- Remaining Settings: Societate static identity mixed authority; Cost Intern vs Modules LEGACY honesty

## W. Next

```
NEXT_RECOMMENDED_BUILD = WORKOS_FX_COMMERCIAL_AUTHORITY_CLOSURE_V1
NEXT_TASK = NOT_AUTHORIZED
```

## Plain answers

```
Can Settings VAT change after a quote is frozen without changing that quote's authoritative review gross?
NO

Does a new quote use the new Settings VAT?
YES

Does Quote→Order retain frozen VAT?
YES

Were historical rows rewritten?
NO

Were DB migrations added?
NO

Was FX behavior changed?
NO

FIRST REMAINING ROOT CAUSE =
FX fail-open vs fail-closed consumer discipline (Settings eur_to_ron_rate)

NEXT_RECOMMENDED_BUILD =
WORKOS_FX_COMMERCIAL_AUTHORITY_CLOSURE_V1

NEXT_TASK =
NOT_AUTHORIZED
```
