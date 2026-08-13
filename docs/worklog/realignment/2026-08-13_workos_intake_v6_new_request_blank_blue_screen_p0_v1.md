# Worklog — Intake V6 new-request blank blue screen P0

**Date:** 2026-08-13  
**Task:** `WORKOS_INTAKE_V6_NEW_REQUEST_BLANK_BLUE_SCREEN_P0_V1`  
**Mode:** `/ce-debug`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Baseline tip:** `55017ec3`

## Outcome

Blank blue AppShell was an uncaught React render exception:  
`IntakeV6PricingInputPanel` called `.toLocaleString()` on null `eurToRonRate` before company FX hydrated.  
D2 was **not** the blank-screen root cause; bootstrap/D2 identity thrash still hardened.

## Evidence

`docs/qa/workos-intake-v6-new-request-blank-blue-screen-p0-v1/`

## Owner DB

`OWNER_DEV_DB_MUTATIONS = 0` (synthetic QA workspace created for empty-state only).

## Push

`PUSH = NO` — Owner authorizes separately.
