# WORKOS_FX_COMMERCIAL_AUTHORITY_CLOSURE_V1_REPORT

## A. VERDICT

**PASS** (bounded FX authority closure)

## B. REPO IDENTITY

- Branch: `feat/f7i-owner-rate-activation`
- HEAD before: `e276c9a0`
- HEAD after: `17ae316f`
- Commit: `17ae316f` — `fix(commercial): enforce explicit EUR RON authority`

## C. ROOT CAUSE

Same Settings FX field consumed with fail-open invent/`persist` of `5.0` and schema ALTER on read, while Logo/CPP expected fail-closed.

## D. CANONICAL FX AUTHORITY

`company_commercial_settings.eur_to_ron_rate` via `require_configured_eur_to_ron_rate` / `resolve_configured_eur_to_ron_rate`.

## E–G. FALLBACKS / WRITE-ON-READ / SCHEMA-ON-READ

- Silent live `5.0` removed from money paths
- GET does not persist FX
- GET does not ALTER; explicit bootstrap helper only for demo/test

## H–N. Behaviors

Settings nullable + UI honesty; Quote→Order explicit/block; profitability freeze; Logo/CPP aligned; dry-run official EUR without inventing FX; demo explicit seed; no historical rewrite.

## O–Q. VAT / tests / runtime

VAT suites green; matrix A–H covered; runtime mutating proof on isolated pytest DB; live `/settings` screenshot read-only.

## R–T. Governance / files / commit

SETTINGS_OWNERSHIP EUR/RON row; evidence pack under `docs/qa/workos-fx-commercial-authority-closure-v1/`; commit required at PASS; PUSH=NO.

## Plain answers

```
Does missing FX silently become 5.0?
NO

Can Settings GET write an FX value?
NO

Can Settings GET alter schema?
NO

Does Quote→Order use explicit configured FX?
YES

Does missing FX block EUR→RON conversion?
YES

Does profitability freeze the same configured rate?
YES

Do Logo/CPP use the same missing-rate discipline?
YES

Was manual RON changed?
NO

Were historical orders/quotes rewritten?
NO

DB_SCHEMA_CHANGES = 0
PRICING_CHANGES = 0
PRODUCT_TRUTH_MUTATIONS = 0
VAT_BEHAVIOR_CHANGED = NO
PUSH = NO

FIRST REMAINING ROOT CAUSE =
Societate static company profile mixed with commercial Settings (identity not live) — or Intake V6 manual RON commercial-input integrity (Owner pick by severity)

NEXT_RECOMMENDED_BUILD =
WORKOS_SETTINGS_SOCIETATE_IDENTITY_AUTHORITY_V1
(or WORKOS_INTAKE_V6_MANUAL_RON_COMMERCIAL_INPUT_INTEGRITY_V1 if Owner prioritizes money path)

NEXT_TASK =
NOT_AUTHORIZED
```
