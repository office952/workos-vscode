# BUILD: Generic Quick Start Fallback Review

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `e6e96bb`  
**Scope:** Frontend-only — generic quick-start semantics

## Problem summary

“Nu știu încă / Cerere generică” resolved to `servicii_montaj` via `resolveGenericFamilyId()`. That was technically valid in the Product Families registry but semantically wrong: operators and reporting could interpret the draft as real montaj/service work.

## Backend / schema constraints (audit)

| Question | Finding |
|----------|---------|
| Is `product_family` required by backend create schema? | Yes — Pydantic field is `str` (required key). |
| Is `product_family` nullable in DB? | **No** — `Column(String, nullable=False)`. |
| Enum constraint? | **No** — free string; validated against registry only when truthy. |
| Can create API accept empty `product_family`? | **Yes** — validation runs only `if data.product_family:`; empty string skips registry check. |
| Verified live create with `""`? | **PASS** — HTTP 201, `product_family: ""` persisted. |
| Existing generic registry family? | **No** dedicated `cerere_generica` / `unspecified` family in seeds. |
| Why was `servicii_montaj` used? | Frontend fallback when generic needed a “valid” slug without backend nullable support. |

## Decision taken — **Option A (preferred)**

Store generic/unresolved quick-start drafts with **empty `product_family`** (`""`):

- Not a fake montaj family
- No migration / new enum value
- UI masks empty family as **“Nespecificat”**
- `TemplateWorkspaceRouter` does not route to volumetric (empty family fails `isLitereVolumetriceFamily`)
- Readiness remains blocked (template neconfirmat, etc.)

Future recommendation: add explicit nullable `product_family` or canonical `cerere_generica` registry family in a dedicated schema migration — not required for this fix.

## Payload behavior

| Work type | `product_family` | `product_spec_json` | `confirmed_template_code` | `status` |
|-----------|------------------|----------------------|---------------------------|----------|
| Generic quick start | `""` (empty) | omitted | null | `new` |
| Litere volumetrice | `litere_volumetrice` | omitted | null | `new` |
| Print / banner | `print_large_format` | omitted | null | `new` |

## UI behavior (generic/unresolved)

**Quick Start dialog**
- Generic card hint: “Creează o cerere draft și alegi tipul lucrării mai târziu.”
- No internal slug shown

**Work Intake list / detail panel**
- `formatIntakeProductFamilyLabel()` → **Nespecificat**

**Intake detail (generic path)**
- `UnresolvedWorkTypeSection`: tip lucrare neales, template neconfirmat, spec neîncepută
- Primary CTA: **Alege tip lucrare**
- No `Product001IntakeSpecEditor`, no volumetric workspace
- `Marchează Gata pt. Ofertă` disabled
- Template assist API skipped while family unresolved

## Tests & lint

```
npx vitest run \
  src/lib/intakeProductFamilyDisplay.test.ts \
  src/lib/intakeQuickStartWorkTypes.test.ts \
  src/components/workos/NewIntakeDialog.test.tsx \
  src/pages/IntakeDetail.unresolvedWorkType.test.tsx \
  (+ volumetric/router regressions)
```

**Result:** PASS

**ESLint:** PASS (pre-existing hook-deps warnings in `IntakeDetail.tsx` unchanged)

**Backend tests:** not run (no backend changes)

## Browser validation

### Smoke A — generic quick start
- Created `IR-MQ3E7K2V` via “Nu știu încă / Cerere generică”
- Redirected to `/intake/IR-MQ3E7K2V`
- Detail shows **Tip lucrare: Nespecificat**, unresolved section, **Alege tip lucrare**
- No “Servicii montaj” / `servicii_montaj` visible
- No volumetric workspace, no quote handoff

### Smoke B — volumetric regression
- `/intake/WI-SMOKE-P001` loads **VolumetricLettersWorkspace** (`TPL-VOLUMETRIC-LETTERS`, Litere volumetrice luminoase)
- Saved spec values visible: 4800 / 600 / 60 / 2.88 / 18 / 9
- Simulare ofertă tab reachable; cost options + Calculează preliminar available
- CostEngine baseline **844.41 EUR** confirmed via `test_simulate_cost_unchanged_after_dossier` (no backend changes in this task)

### Smoke C — quotes regression
- `/quotes` → **Ofertă nouă** opens generic QuoteWizard (Nume client + Șablon produs steps)
- **Anulează** — no quote created

## Counts

| Entity | Before | After | Δ |
|--------|--------|-------|---|
| Intakes | 14 | 15 | +1 (smoke `IR-MQ3E7K2V`) |
| Quotes | 7 | 7 | 0 |
| Orders | 8 | 8 | 0 |

## Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created
- No Reference Catalogs started
- Readiness policy unchanged
- `Product001IntakeSpecEditor` contract unchanged
- `TemplateWorkspaceRouter` preserved
- Volumetric quick-start preserved
- Generic QuoteWizard preserved

## Files changed

- `frontend/src/lib/intakeProductFamilyDisplay.ts` *(new)*
- `frontend/src/lib/intakeProductFamilyDisplay.test.ts` *(new)*
- `frontend/src/lib/intakeQuickStartWorkTypes.ts`
- `frontend/src/lib/intakeQuickStartWorkTypes.test.ts`
- `frontend/src/components/workos/IntakeWorkTypePicker.tsx`
- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/components/workos/NewIntakeDialog.test.tsx`
- `frontend/src/pages/WorkIntake.tsx`
- `frontend/src/pages/IntakeDetail.tsx`
- `frontend/src/pages/IntakeDetail.unresolvedWorkType.test.tsx` *(new)*
