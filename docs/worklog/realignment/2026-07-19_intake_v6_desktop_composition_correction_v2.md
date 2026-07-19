# Worklog — Intake V6 Desktop Composition Correction V2

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Rejected commit:** `1ad841b`  
**Functional baseline:** `9f0efa0`  

## Owner visual findings addressed

Form must lead; alerts assist; tabs own form; product/scope collapsed; one message for composition; pricing without analyzer/dry-run; diagnostic outside operator scroll.

## Pre-flight

See `docs/qa/intake-v6-desktop-composition-correction-v2-2026-07-19/COMPOSITION_CORRECTION_CHECKPOINT.md`.

## ReviewStep before/after

| | Lines | Notes |
|--|------:|-------|
| Before | ~3739 | Owned chrome + panels + inline diagnostic |
| After | ~3725 | Extracted FormRegion + DiagnosticDrawer; diagnostic content still referenced for lazy drawer |

## Composition changes

- Identity strip: compact product row + scope chip
- `IntakeV6ReviewFormRegion`: tabs + attention corner + connected body
- Attention: corner chip `! N probleme` (not full-width slab)
- Pricing: `Preț disponibil după confirmarea produsului.`
- Iluminare: removed 220V helper; hideHeading; no contract dup
- Montaj: flatter; ACM label without Product System; Product System L1 links removed
- Diagnostic: separate drawer, lazy fetch/mount
- Footer: compact weight
- Guidance: strip analyzer/dry-run phrasing

## Warning channels before → after

Full-width band + product + pricing essay + footer + drawer → corner chip + local CTA + footer next action + drawer inventory.

## Tests

57 related Vitest passed (FormRegion, DiagnosticDrawer, BlockerBanner, Composition, LiveCalc, ConfirmStep, Guidance).

## Runtime

ACM `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` · probe: formAboveFold, tabsOwnForm, cornerAttention, diagnosticEntry, no Product System in Montaj.

## Remaining weak points

- Confirmare fully-ready screenshot not achieved (checklist pending) — named honestly
- Confirmare still shows readiness banner + checklist (reduced, not zero duplication)
- ReviewStep still large (content ownership moved, not fully split)
- Global app header “Stare sistem” unchanged
- Footer issues strip still present (calmer)

## Owner acceptance

`PENDING_OWNER_VISUAL_ACCEPTANCE`
