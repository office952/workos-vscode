---
title: Site installation binds SITE_INSTALLATION_STANDARD once per job
date: 2026-07-16
problem_type: pricing-binding
component: commercial-price-proposal
tags:
  - site-installation
  - montaj
  - pricing-registry
  - currency
  - cpp
module: commercial_price_proposal
applies_when:
  - volumetric letters V6 site installation is selected
  - owner has confirmed a fixed per-location commercial tariff
---

# Site installation binds SITE_INSTALLATION_STANDARD once per job

## Context

Commercial montaj (`MONTAJ_COMMERCIAL_RULE` / former `VOL_V2_SITE_MOUNT_FUTURE`) blocked Confirmare whenever site installation was selected, because CPP had no owner-confirmed registry tariff. Owner approved a single commercial rule for the current phase: **200 EUR + VAT fixed once per complete job / location**.

## Guidance

1. Seed and keep Pricing Registry code `SITE_INSTALLATION_STANDARD` at **200 EUR**, `rate_basis=per_piece` (commercial unit still `locatie`, quantity forced to 1).
2. Map the CPP `montaj` rule with `registry_pricing_code="SITE_INSTALLATION_STANDARD"`.
3. Resolve via the same registry + company EUR→RON path used for logo finishes (`_load_registry_operation_rate` + `_normalize_unit_price_to_cpp_ron` / `_canonical_eur_to_ron_rate`). Fail closed when the row or FX is missing — never bootstrap a diagnostic FX.
4. Emit **exactly one** `montaj` line for the whole job. Do not charge per letter or per Vector Logo segment. Do not auto-add travel / km / accommodation lines in this phase.
5. Reject hourly commercial bases (`per_hour` registry rows are ignored by the commercial binder).
6. Leave packaging, Quote, and Order creation out of this binding.

## Why This Matters

Operators can quote Bucharest (and the same base outside Bucharest) without inventing rates or waiting on a second owner ask, while travel and special equipment stay explicitly out of the included tariff.

## When to Apply

- Intake V6 / CPP for `TPL-VOLUMETRIC-LETTERS_v2` when `site_installation_included` / mounting scope requires commercial montaj.
- Re-seeding volumetric workcenter rates (`seed_volumetric_workcenter_rates`) — idempotent upsert of `SITE_INSTALLATION_STANDARD`.

## Examples

Before: montaj line with null price → `MONTAJ_COMMERCIAL_RULE` → dry-run / Confirmare blocked.

After (company FX 5.0): one line `montaj` qty=1 unit=`locatie` unit_price=1000 RON subtotal=1000; dry-run net rises by exactly that amount; travel count stays 0; handoff may still show `operator_confirmation_missing` and dossier trigger warnings — those must not be bypassed by this tariff.

Related: [Logo commercial finish registry binding](./logo-commercial-finish-registry-binding.md).
