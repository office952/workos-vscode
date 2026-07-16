# Decision log — Gradi-curat pricing truth audit + logo commercial correction

**Date:** 2026-07-16  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Baseline HEAD:** `99d5c71`  

## Audit decisions (locked)

| ID | Decision |
|----|----------|
| D1 | Official commercial authority is CPP 7G via priced-quote-dry-run |
| D2 | Pre-correction live gross was 2606.96 RON (letters-only) |
| D3 | 725.16 EUR is internal MB cost |
| D4–D8 | Logos omitted commercially → COMMERCIAL_PARTIAL_NOT_CONFIRMABLE |
| D9 | contains_missing_prices was informational false positive |
| D10 | MIXED_CURRENCY_MISLEADING labeling |

## Owner gates (answered)

| Gate | Answer |
|------|--------|
| G1 | YES |
| G2 | YES — LINKED-CHILD-ONLY |
| G3 | YES — COMPONENTIZED COMMERCIAL RULE |
| G4 | YES — LOGO ILLUMINATION INCLUDED |
| G5 | SITE INSTALLATION REQUIRED / PACKAGING DEFERRED |

## Implementation decisions

| ID | Decision |
|----|----------|
| I1 | Idempotent `seed_tpl_volumetric_logo_v1` only (not root offerable) |
| I2 | CPP linked-logo evaluation under letters root |
| I3 | Reuse DEV_BRIDGE classes for logo face/return/back/LED |
| I4 | Print/laminate/application fail-closed until owner tariffs |
| I5 | LED split letters vs emblem; no double count |
| I6 | Montaj required when installation included |
| I7 | Packaging deferred optional |
| I8 | Informational led_total_watts excluded from missing-price flag |

## Remaining

Owner must configure logo print/laminate/application + montaj commercial tariffs before Confirmare.
