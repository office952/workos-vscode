# BUILD: Intake Detail Routing & Blank Page Fix

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `13ec78f`  
**Commit:** `5bc2b3c`

## Why different intakes render different UI shells

| Intake | `product_family` | `confirmed_template_code` | Shell |
|--------|------------------|-------------------------|--------|
| WI-3321 | Casete Luminoase | null | **Generic legacy** — pre-modular families stay on classic `IntakeDetail` (action map, fiscal, backend assist) |
| IR-MQ3C869E | litere_volumetrice | null | **Volumetric modular** — family alone triggers `shouldUseVolumetricIntakePage` |
| WI-SMOKE-P001 | litere_volumetrice | TPL-VOLUMETRIC-LETTERS | **Volumetric modular** — confirmed template + smoke spec |
| IR-TEST-GENERIC | `""` | null | **Generic unresolved** — quick-start generic draft |
| IR-MQ3E7K2V | `""` | null | **Generic unresolved** |

**Expected:** WI-* seed records with human-readable families (Casete Luminoase, etc.) use legacy shell until migrated. IR-* volumetric quick-start drafts with `litere_volumetrice` use modular workspace.

## Root cause — IR-TEST-GENERIC blank page

- **Type:** frontend crash during hook execution (not 404, not API error)
- **Trigger:** `intake_requests.dimensions` was **null** in DB for `IR-TEST-GENERIC`
- **Crash site:** `IntakeDetail.tsx` — `request.dimensions.match(...)` in `parsedDims` / related `useMemo` hooks
- **Symptom:** empty document body (white page), no sidebar content

## Fix

1. **`intakeDetailDimensions.ts`** — null-safe dimension normalize/parse helpers
2. **`dataStore.ts`** — map null `dimensions` → `"—"`, null `product_family` → `""`, null `description` → `""`
3. **`IntakeDetail.tsx`** — use safe parsers; explicit Not Found copy; `InvalidIntakeDataSection`; dev-only workspace diagnostic badge; volumetric route no longer requires `actionSummary` truthy guard to skip render
4. **`intakeDetailRouting.ts`** — explicit `resolveIntakeWorkspaceShell()` (`volumetric_modular` | `generic_unresolved` | `generic_legacy`)
5. **`TemplateWorkspaceRouter.tsx`** — unsupported-template fallback panel instead of `return null`

## Routing decision table

| condition | intended shell | was (before) | safe now |
|-----------|----------------|--------------|----------|
| `product_family === ""` | generic unresolved | crash if `dimensions` null | PASS |
| `litere_volumetrice` / TPL-VOLUMETRIC-LETTERS | volumetric modular | modular | PASS |
| Casete Luminoase / other WI-* families | generic legacy | legacy | PASS |
| missing intake id in list | Not Found | Not Found | PASS |
| `TemplateWorkspaceRouter` enabled, non-volumetric | fallback message | **blank null** | PASS |

## Tests & lint

```
npx vitest run \
  src/lib/intakeDetailDimensions.test.ts \
  src/lib/intakeDetailRouting.test.ts \
  src/pages/IntakeDetail.routing.test.tsx \
  src/pages/IntakeDetail.unresolvedWorkType.test.tsx \
  src/pages/IntakeDetail.volumetricShell.test.tsx \
  src/components/workos/templateIntakeWorkspace/TemplateWorkspaceRouter.test.tsx \
  src/components/workos/NewIntakeDialog.test.tsx
```

**Backend tests:** not run (no backend changes)

## Browser validation

| Route | Result |
|-------|--------|
| `/intake/WI-3321` | Generic legacy, no crash |
| `/intake/IR-MQ3C869E` | Volumetric modular workspace |
| `/intake/IR-TEST-GENERIC` | Generic unresolved (no blank page) |
| `/intake/WI-SMOKE-P001` | Volumetric workspace, spec values intact |
| `/quotes` → Ofertă nouă | Generic QuoteWizard, cancelled |

## Counts

| Entity | Before | After | Δ |
|--------|--------|-------|---|
| Intakes | 15 | 15 | 0 |
| Quotes | 7 | 7 | 0 |
| Orders | 8 | 8 | 0 |

## Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created
- No Reference Catalogs started
- Readiness policy unchanged
- `Product001IntakeSpecEditor` contract unchanged
- `TemplateWorkspaceRouter` remains explicit (+ unsupported fallback)
- Volumetric workspace preserved
- Generic/unresolved route safe
