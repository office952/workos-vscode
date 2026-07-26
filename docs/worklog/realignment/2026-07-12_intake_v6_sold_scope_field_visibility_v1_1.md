# Intake V6 sold scope field visibility V1.1

**Task:** `INTAKE_V6_SOLD_SCOPE_FIELD_VISIBILITY_V1_1`  
**HEAD before:** `e2abebc`  
**Date:** 2026-07-12

## Loop root cause

Step 1 (`IntakeV6OfferScopePanel`) entered a hydrate → autosave → reload cycle:

1. **Unstable `onSave`** — inline wrapper in `IntakeV6SvgAnalyzerStep` recreated every render; autosave `useEffect` depended on it.
2. **False dirty for legacy workspaces** — local `full_product` without persisted `offer_scope` looked unconfirmed and kept PUT-ing.
3. **Autosave `useEffect`** — deps included `onSave`, `saving`, and `soldModules` array reference; each successful save updated payload → hydrate → next tick saved again.
4. **Unstable persisted arrays** — `readPersistedOfferScope` produced new `soldModules` references on each payload read.

**Repeated endpoint:** `PUT /api/v1/intake-v6/workspaces/{id}/offer-scope`

**Requests before fix (observed):** continuous PUT spam on Step 1 mount (10+ per few seconds on legacy workspaces).

**Requests after fix:** 0 on mount; 1 per explicit user action (radio/checkbox).

## Loop fix

- Extracted equality helpers in `intakeV6OfferScopeState.ts` (`normalizeSoldModules`, `serializeOfferScopeState`, `shouldPersistOfferScope`).
- Removed autosave `useEffect`; save only on full-product radio or subset checkbox toggle.
- Stable `handleSaveOfferScope` via `useCallback` in Step 1 shell.
- Hydrate local state only when `persisted.serialized` changes; `onSaveRef` + in-flight serialized guard.
- Legacy workspaces without `offer_scope` no longer auto-save on mount.

## Visibility logic

Canonical helper: `resolveSoldScopeFieldVisibility()` in `intakeV6SoldScopeVisibility.ts`.

| Sold scope | Review shows | Review hides |
|------------|--------------|--------------|
| full_product | FACE, RETURN-CANT, BACK (unchanged) | — |
| FACE | face zones / letter face fields | cant, back |
| RETURN-CANT | cant material, depth, thickness, finish | face, back |
| BACK | backing finish integration | face, cant |
| FACE + RETURN-CANT | union of both | back |

Scoped readiness: `countIncompleteLetterGroupsForScope` / `countIncompleteArtworkFinishesForScope`.

On deselect (backend + frontend policy): preserve field values, invalidate confirmations once, exclude hidden modules from readiness/payload.

## Tests

**Frontend (Vitest):** 23 tests — offer scope panel loop guards, state serialization, visibility matrix, scoped confirmation counts.

**Backend (pytest):** 10 tests in `test_intake_v6_offer_scope_persistence.py` including deselect confirmation invalidation.

**Commands:**

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6OfferScopePanel.test.tsx src/lib/intakeV6/intakeV6OfferScopeState.test.ts src/lib/intakeV6/intakeV6SoldScopeVisibility.test.ts src/lib/intakeV6/intakeV6SoldScopeFinishConfirmation.test.ts

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_offer_scope_persistence.py -q
```

## Screenshots

Captured:

- `docs/qa/intake-v6-sold-scope-field-visibility-v1_1/screenshots/01_step1_full_product_stable.png`

Playwright spec added: `frontend/e2e/intake-v6-sold-scope-field-visibility-v1.spec.ts` (Review subset states require seeded workspace + live backend save).

## Files

- `frontend/src/lib/intakeV6/intakeV6OfferScopeState.ts`
- `frontend/src/lib/intakeV6/intakeV6SoldScopeVisibility.ts`
- `frontend/src/lib/intakeV6/intakeV6SoldScopeFinishConfirmation.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopePanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayerCardColumnHeader.tsx`
- `backend/services/intake_v6_workspace_service.py`
- Tests + e2e spec listed above

## Commit

`Fix Intake V6 Step 1 loop and align sold scope fields`

## Deferred scope

- Full Playwright Review screenshots (FACE-only, RETURN-CANT-only, BACK-only, FACE+RETURN-CANT, re-enable reconfirmation) pending seeded fixture + backend on target machine.
- LIGHTING/ELECTrical/FINISH/MOUNTING visibility (forbidden).
- Product System component taxonomy changes (forbidden).
