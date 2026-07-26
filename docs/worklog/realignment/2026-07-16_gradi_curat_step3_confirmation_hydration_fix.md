# GRADI-CURAT Step 3 confirmation hydration fix — 2026-07-16

## Starting HEAD

`da2e0b5` (`feature/product-system-active-path-isolation-v1`)

## Exact root cause

`useIntakeV6FinalHandoff` initialized `confirmInternalDraft` with `useState(false)` and never reconciled it to persisted:

- `workspace.payload.finish_setup.internal_draft_quote_confirmed`
- `handoffPreview.operator_confirmation_complete`

Backend confirmation, readiness, and pricing were already correct; only the checkbox UI lied after remount.

## Previous UI state lifecycle

1. Mount → local `false`
2. Workspace / handoff load → persisted may be `true`
3. Checkbox stayed unchecked
4. Operator saw false “needs confirmation” while `can_create_internal_draft_quote=true`

## Final hydration lifecycle

1. Workspace load → `finish_setup` available
2. While preview loading/refreshing → hydrate from `finish_setup` (disable interaction)
3. Handoff preview settled → hydrate from `operator_confirmation_complete`
4. Reconcile local checkbox to persisted when not saving
5. User click → optimistic local + PUT → refresh handoff → reconcile
6. PUT failure → restore last persisted
7. Upstream finish-setup save → `confirmed=false` → refresh prefers finish_setup during preview load → checkbox unchecked

## Files changed

| File | Role |
|------|------|
| `frontend/src/lib/intakeV6/intakeV6InternalDraftConfirmationHydration.ts` | Pure hydration helpers |
| `frontend/src/lib/intakeV6/intakeV6InternalDraftConfirmationHydration.test.ts` | 17 unit tests |
| `frontend/src/lib/intakeV6/useIntakeV6FinalHandoff.ts` | Wire hydrate / reconcile / stale guards / failed PUT restore |
| `frontend/src/components/workos/intake-v6/IntakeV6ConfirmHandoffPanel.tsx` | Loading / error / checked display |
| `frontend/src/components/workos/intake-v6/IntakeV6ConfirmHandoffPanel.test.tsx` | 4 panel tests |
| `frontend/src/components/workos/intake-v6/IntakeV6FinalConfigurationSummary.tsx` | Pass hydration props |
| `docs/solutions/architecture-patterns/intake-v6-step3-confirmation-hydration.md` | Compound learning |
| Prior live verification artifacts (same commit) | Evidence pack |

## Tests

```
vitest run
  intakeV6InternalDraftConfirmationHydration.test.ts  (17)
  IntakeV6ConfirmHandoffPanel.test.tsx                 (4)
  IntakeV6ConfirmStep.test.tsx                         (9)
→ 30 passed
```

## Hard reload proof

Workspace `11891d68-c4c8-4719-acc5-f8fcb22a44af` with backend `confirmed=true`.

After navigate/reload to Confirm → expand Rezumat → checkbox `checked=true`, `disabled=false`.

Screenshot: `docs/qa/gradi-curat-e2e/screenshots/step3-hydration-after-reload.png`

## Remount proof

Configurare → Confirmare remount → checkbox remained checked.

## Reset proof

Identical PUT `/finish-setup` → `internal_draft_quote_confirmed=false` → reload Confirm → checkbox `checked=false`.

## Reconfirm + final reload

UI checkbox click → API `confirmed=true` → hard reload → checkbox checked again.

Final screenshot: `docs/qa/gradi-curat-e2e/screenshots/step3-hydration-final-confirmed.png` (if present) / browser capture during walkthrough.

## Final confirmed state

- `internal_draft_quote_confirmed=true`
- `operator_confirmation_complete=true`
- `can_create_internal_draft_quote=true`
- `handoff_allowed=true`
- fatals empty
- review_warnings=2 (TRIGGER)
- diagnostic_warnings=3

## Pricing non-regression

- status `V6_PRICED_DRY_RUN_READY`
- net `3513.56` RON
- VAT `737.85` RON
- gross `4251.41` RON

## No Quote/Order proof

`quote_id=null`, `order_id=null`; no handoff-to-offer / create-draft POST in this task.

## Review findings

Bugbot (hydration focus):

1. **Fixed** — while preview refreshing, prefer `finish_setup` over stale handoff so upstream reset is not masked.
2. **Fixed** — while saving, keep optimistic `operatorConfirmationComplete` from local checkbox so UI does not flash unchecked mid-PUT.

## Commit

Scoped commit on this branch; **no push / no PR**.
