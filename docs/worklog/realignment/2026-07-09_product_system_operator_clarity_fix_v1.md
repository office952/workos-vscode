# Product System Operator Clarity Fix V1

**Date:** 2026-07-09  
**HEAD before:** `405596c` — Improve Product System catalog UX with comfortable layout and compact chrome  
**Task:** PRODUCT_SYSTEM_OPERATOR_CLARITY_FIX_V1  
**Scope:** Frontend-only label/copy clarity (no backend, no seed, no activation)

## Problems addressed

1. Guards showed `WI=true` when `noWorkIntakeExposure === true` — operator could read as Work Intake ON.
2. Summary showed bare `7 dosare` while component-first had `0/7` live rows (contract fixture vs live catalog).
3. Prominent green `+ Șablon nou` contradicted readonly catalog messaging.

## Changes

### Inert guard labels (`ComponentFirstReadonlyCandidatePanel.tsx`, `componentFirstReadonlyUiShared.tsx`)

- Replaced `WI=true` / `Pricing=true` / `PD=true` grid with `ComponentFirstInertGuardLabels`.
- Explicit operator copy: `Work Intake exposure: blocked`, `Pricing activation: blocked`, etc.

### Summary metrics (`ProductSystemUnifiedCatalog.tsx`, `ProductSystem.tsx`)

- Renamed metric to **Dosare contract** (`product-system-summary-dossier-contract`).
- Added **Randuri live comp-first** (`0/7` fraction) separate from dossier contract count.
- Compact summary line: `7 dosare contract · 0/7 randuri live` (never bare `7 dosare`).

### Component-first overview

- Added `product-system-component-first-dossier-contract-summary`: Dossier contract 7/7 vs Runtime dossier rows not linked yet.

### Create CTA (`ProductSystem.tsx`)

- Removed prominent header `+ Șablon nou`.
- Moved to **Design-time (admin)** section in library ⋮ menu with note: *Admin design-time only — not operator quoting*.

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

- 62 + 38 tests passed (100 total).

## Screenshots

`docs/qa/product-system-operator-clarity-fix-v1/screenshots/`

## Boundaries respected

- No backend / DB / seed / migration / activation / Pricing / Work Intake exposure changes.
- Entity classification and buckets unchanged.
- Active root and candidate labels preserved.
