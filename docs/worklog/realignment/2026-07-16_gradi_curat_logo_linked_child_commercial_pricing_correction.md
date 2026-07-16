# 2026-07-16 — Gradi-curat logo linked-child commercial pricing correction

## Starting HEAD

`99d5c71` on `feature/product-system-active-path-isolation-v1`

## Root cause

CommercialPriceProposal evaluated only `commercial_rules_volumetric_v2` letters modules. Linked logo segments existed in ProductDefinition / material-breakdown but never entered CPP. Live `TPL-VOLUMETRIC-LOGO_v1` was absent from Product System availability (404 aggregate/PD).

## Live template truth

- Before: logo not in template-availability (8 templates)
- After idempotent `seed_tpl_volumetric_logo_v1`: present as `candidate_product`, `quote_offerable=false`, `root_offerable=false`, `linked_child_offerable=true`
- Parent `components_json` filled for PA namespacing (linked-child-only; not root offerable)

## Registry/data decision

Narrow seed only via existing `seed_tpl_volumetric_logo_v1` (idempotent). No migration. No full reseed. No root-offerable activation.

## ProductDefinition before/after

- Before: letters PD linked segments yes; standalone logo PD 404
- After: letters PD linked segments unchanged; standalone logo PD still not a root offer path; composition remains letters root

## ProductAggregate before/after

- Before: `linked_logo_segments: 0` (template missing)
- After: `linked_logo_segments: 2` with namespaced `comp_logo_*::logo_instance_00x` components

## CPP before/after

- Before: net 2154.51 / gross 2606.96 RON letters-only; 0 logo lines
- After (partial, fail-closed): proposal subtotal **2439.52 RON** priced lines; dry-run `commercial_totals` null while blockers present
- Letter body lines (`debitare_fata`, `modelare_cant`, `debitare_spate`, finish, sablon) amounts unchanged
- Letter LED qty **85** (was 145 mis-attributed); logo LED **30+30**
- Logo 1/2: face/return/back priced; print/laminate/application null (owner tariffs pending); montaj required null

## EIC non-regression

Internal MB **725.16 EUR** unchanged; `contains_missing_prices` now **false** (informational `led_total_watts` excluded)

## Logo illumination

G4: FRONT_LIT / area_lit / cool — emblem 60 modules split across logos; letters 85; no double count in commercial LED lines

## Installation

G5: montaj commercially required when `installation_template` / site install active — fail-closed missing tariff (blocker)

## Packaging

Deferred / nonblocking warning path (`AMBALARE_COMMERCIAL_RULE`)

## Missing-price behavior

V6 informational-row false positive fixed; commercial missing keys are exact owner decision codes (logo print/lam/app + montaj)

## Currency/VAT

CPP RON; MB EUR separate; VAT 21% when totals authorized

## Tests

- `tests/test_commercial_price_proposal_linked_logo.py`: **12 passed**
- PA linked logo composition: **9+ passed** (HTTP endpoint fixture caveats remain for unseeded TestClient)
- Known pre-existing: `test_post_endpoint_returns_preview` 404 for direct commercial-price-preview route

## Runtime evidence

Workspace `11891d68-c4c8-4719-acc5-f8fcb22a44af` dry-run after seed+code:
- Logo commercial lines present for both instances
- Blockers: MONTAJ + LOGO_PRINT/LAMINATE/APPLICATION + COMMERCIAL_REVIEW_NOT_READY
- Confirmare not allowed (honest)

## Remaining blocker

Owner must configure commercial tariffs for logo print/laminate/application and site-install montaj before commercial ready.

## Next step

Owner configure missing commercial tariffs → same-workspace dry-run should reach commercial ready without inventing prices in code.

## Commits

(see git log for this phase)
