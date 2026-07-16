---
title: Logo commercial finish binds existing Pricing Registry rates
date: 2026-07-16
problem_type: pricing-binding
component: commercial-price-proposal
tags: [logo, pricing-registry, currency, cpp, gradi-curat]
---

# Logo commercial finish binds existing Pricing Registry rates

## Problem

Linked-logo CPP print/laminate/application lines failed closed with null prices and owner codes `LOGO_*_COMMERCIAL_RULE`, which looked like missing owner tariffs. Pricing Registry already had owner-confirmed operation rates (`LARGE_FORMAT_PRINT`, `LAMINATION`, `FACE_VINYL_APPLICATION_LABOR`).

## Root cause

Rule catalog had no `registry_pricing_code` mapping; CPP never looked up `workcenter_rates`. Separately, substring scan of forbidden token `workcenter_rate` falsely matched provenance `workcenter_rates`.

## Solution

1. Map logo finish rules to existing registry codes (mapping only — no duplicate tariffs).
2. Resolve active `per_square_meter` rows from `workcenter_rates`; reject `SVC-LAMINATION-SERVICE`.
3. Convert EUR→RON via persisted `company_commercial_settings.eur_to_ron_rate` (fail closed if NULL — do not bootstrap diagnostic 5.0 in this path).
4. Keep montaj fail-closed (`MONTAJ_COMMERCIAL_RULE`).
5. Word-boundary forbidden-hourly scan.

## Prevention

Before asking the owner for a new commercial tariff, inspect `/inventory/pricing` for equivalent active rates under another key/unit/alias.
