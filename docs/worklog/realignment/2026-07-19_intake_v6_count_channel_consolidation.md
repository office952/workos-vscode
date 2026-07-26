# Worklog — Intake V6 count channel consolidation

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `46ead84`

## Checkpoint

`docs/qa/intake-v6-count-channel-consolidation-2026-07-19/COUNT_CHANNEL_CONSOLIDATION_CHECKPOINT.md`

## Selected model

Guidance Model owns attention inventory published from sticky issues; footer/drawer/sticky consume the same counts.

## Consumers

Sticky summaryTitle · footer countsLabel · drawer toggle/groups.

## Tests

36 Vitest PASS.

## Risks

Information rows still large (pricing/header) — correctly separated as Informații, not Blocante.

## Commit

`refactor(intake-v6): consolidate guidance count channels`
