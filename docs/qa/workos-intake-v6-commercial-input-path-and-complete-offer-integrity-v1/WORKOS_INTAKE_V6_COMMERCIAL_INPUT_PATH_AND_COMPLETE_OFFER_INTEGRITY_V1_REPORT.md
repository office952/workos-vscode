# WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1_REPORT

## A. VERDICT

**PASS**

## B. REPO IDENTITY

- Branch: `feat/f7i-owner-rate-activation`
- HEAD before: `33848981`
- HEAD after: `bf7960c9`
- Commit: `bf7960c9` — `fix(commercial): unify Intake V6 commercial input authority`

## C. ROOT CAUSE

Dual money authority: FE recalculated adjusted offer totals (RON into EUR) while dry-run was the real applier; Manual RON had no FX; post-freeze offer zeroed adjustments.

## D–H. Policies

- Markup / Discount: dry-run authoritative; order base→markup→manual→discount→VAT verified
- Manual RON: **Policy A** — backend FX conversion when ≠0
- Complete offer: CPP composition base vs adjusted `commercial_totals` headline

## I–N. Surfaces

- FE official money authority removed for adjusted totals
- CPP line sum unchanged as product composition
- Quote priced-write + frozen trace retain adjustments
- Post-freeze offer/review consume frozen quote truth
- Order copies frozen truth (no re-adjustment)

## O–P. Regressions

- VAT_BEHAVIOR_CHANGED = NO
- FX_BEHAVIOR_CHANGED = NO

## Q–T. Audit / UI / runtime / tests

See PRICE_INPUT_REGRESSION, RUNTIME_PROOF, TEST_RESULTS (53 BE + 38 FE).

## U–Z

Files/commits in git. Governance: NO_CHANGE (existing commercial settings ownership sufficient). Remaining root causes in REMAINING_PRICE_INPUT_DEFECTS.md.

```
Does frontend independently calculate official adjusted money?
NO

Can RON be added directly into EUR?
NO

Does markup affect authoritative CPP money?
YES (dry-run commercial_totals on CPP base; not CPP line sum)

Does discount affect authoritative CPP money?
YES (same)

What is canonical manual RON policy?
A — TRUE RON ADJUSTMENT (backend FX conversion)

Does manual RON require configured FX?
YES when manual_adjustment_ron != 0 and commercial currency is not RON

Does complete_offer_total equal authoritative commercial truth?
NO for adjusted offer — complete_offer_total is pre-adjustment composition; commercial_totals is official Ofertă money

Are commercial adjustments frozen before Order?
YES

Does Order recalculate adjustments?
NO

VAT_BEHAVIOR_CHANGED = NO
FX_BEHAVIOR_CHANGED = NO
DB_SCHEMA_CHANGES = 0
PRICING_RULE_CHANGES = 0
PRODUCT_TRUTH_MUTATIONS = 0
HISTORICAL_BACKFILL = NO
TASK_ARTIFACTS_COMMITTED = YES
PUSH = NO

FIRST_REMAINING_ROOT_CAUSE =
A_CONFIRMED_FALSE confirm-gate / TOTAL_COMPOSITION (or Societate static identity)

NEXT_RECOMMENDED_BUILD =
WORKOS_INTAKE_V6_CONFIRM_GATE_COMPLETE_OFFER_INTEGRITY_V1

NEXT_TASK =
NOT_AUTHORIZED
```
