# BUILD: New Intake Quick Start UI Alignment

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `6d1c049` (layout reconfiguration)  
**Scope:** Frontend-only — `NewIntakeDialog` quick start UX

## UI problem summary (before)

Step 2 of “Cerere Nouă” behaved like a technical CRM form:

| UI area | Issue | Impact |
|---------|-------|--------|
| Product family | Native `<select>` with `label (family_id)` | Internal codes prominent; awkward long dropdown overlay |
| Registry hint | `Registry: {family_id}` under select | Exposed implementation detail to operators |
| Embedded spec editor | `Product001IntakeSpecEditor` in dialog for volumetric | Wrong place for quick-start; felt like a database form |
| Layout | Uneven `max-w-2xl` grid, dimensions/qty/notes clutter | Not template-first; poor visual balance |
| Disabled CTA | `Creează Cerere` disabled with no explanation | Operator had to guess missing fields |
| Auto-select | First registry family selected on load | Hidden default; not “what kind of work?” |

## What changed

1. **Curated work-type card picker** (`IntakeWorkTypePicker` + `intakeQuickStartWorkTypes.ts`) replaces the native family dropdown as primary UX.
2. **Step 2 layout** rebuilt: compact client summary + “Schimbă client”, section “Ce vrei să produci?”, section “Date cerere” (canal, prioritate, livrare, descriere scurtă).
3. **Removed** `Product001IntakeSpecEditor`, dimensions, quantity, notes, and registry slug hints from the quick-start dialog.
4. **Disabled CTA reason** shown in footer: e.g. `Completează: tip lucrare, descriere.`
5. **Post-create navigation** — `WorkIntake` now routes to `/intake/{code}` so volumetric drafts open the modular workspace immediately.

## Picker / card decision

- Human-readable curated list (not Reference Catalogs):
  - Litere volumetrice *(enabled)*
  - Print / banner *(enabled)*
  - Nu știu încă / Cerere generică *(enabled)*
  - Casete luminoase, Autocolant / sticker, Semnalistică, Totem / pylon *(disabled — “În curând”)*
- Internal `family_id` values live in `data-family-id` only; never shown as primary labels.
- Registry still loaded to validate/selectable state; generic resolves to first safe non-volumetric family (`servicii_montaj` preferred).

## Disabled CTA behavior

`getQuickStartMissingRequirements()` drives footer copy:

- Missing work type → `tip lucrare`
- Missing description → `descriere`
- Registry unavailable → dedicated registry message
- Client remains required on step 1 only (unchanged); not blocking on step 2.

## Draft creation behavior

| Selection | `product_family` | `product_spec_json` | `status` | Next screen |
|-----------|------------------|---------------------|----------|-------------|
| Litere volumetrice | `litere_volumetrice` | omitted (empty draft) | `new` | `VolumetricLettersWorkspace` via `TemplateWorkspaceRouter` |
| Print / banner | `print_large_format` | omitted | `new` | Standard intake detail |
| Generic | resolved safe family (e.g. `servicii_montaj`) | omitted | `new` | Standard intake detail |

No quote or order created by quick start.

## Tests & lint

```
npx vitest run \
  src/components/workos/NewIntakeDialog.test.tsx \
  src/components/workos/IntakeWorkTypePicker.test.tsx \
  src/lib/intakeQuickStartWorkTypes.test.ts \
  src/components/workos/templateIntakeWorkspace/TemplateWorkspaceRouter.test.tsx \
  src/pages/IntakeDetail.volumetricShell.test.tsx
```

**Result:** 27/27 PASS

```
npx eslint \
  src/components/workos/NewIntakeDialog.tsx \
  src/components/workos/IntakeWorkTypePicker.tsx \
  src/lib/intakeQuickStartWorkTypes.ts \
  src/pages/WorkIntake.tsx
```

**Result:** PASS (no issues)

Backend tests: not run (no backend changes).

## Browser validation

| Check | Result |
|-------|--------|
| Modal aligned, grouped sections | PASS |
| Card picker (no awkward family dropdown) | PASS |
| No internal codes as main labels | PASS |
| Disabled reason visible | PASS |
| Litere volumetrice selection clear | PASS |
| Draft create + redirect to workspace | PASS — `IR-MQ3C869E` |
| No quote/order from smoke | PASS |
| WI-SMOKE-P001 workspace | PASS |
| WI-SMOKE-P001 simulation baseline | PASS — **844.41 EUR** |
| `/quotes` → Ofertă nouă → generic wizard | PASS |

## Counts

| Entity | Before | After | Δ |
|--------|--------|-------|---|
| Intakes | 11 | 12 | +1 (smoke draft) |
| Quotes | 7 | 7 | 0 |
| Orders | 8 | 8 | 0 |

**New intake:** `IR-MQ3C869E` — Litere volumetrice QA quick start smoke draft

## Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created (smoke intake draft only)
- No Reference Catalogs started
- Readiness policy unchanged
- `Product001IntakeSpecEditor` contract unchanged (removed from dialog only)
- `TemplateWorkspaceRouter` preserved
- Volumetric workspace preserved (WI-SMOKE-P001 + new draft)
- Generic QuoteWizard preserved

## Files changed

- `frontend/src/lib/intakeQuickStartWorkTypes.ts` *(new)*
- `frontend/src/lib/intakeQuickStartWorkTypes.test.ts` *(new)*
- `frontend/src/components/workos/IntakeWorkTypePicker.tsx` *(new)*
- `frontend/src/components/workos/IntakeWorkTypePicker.test.tsx` *(new)*
- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/components/workos/NewIntakeDialog.test.tsx`
- `frontend/src/pages/WorkIntake.tsx`
