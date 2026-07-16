# 2026-07-16 — Intake V6 step-scoped confirmation banner + Vector Logo copy

**Task:** `WORKOS-INTAKE-V6-STEP-SCOPED-CONFIRMATION-BANNER-AND-VECTOR-LOGO-COPY-V1`  
**Starting HEAD:** `8f3d74d`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Operator URL:** `http://127.0.0.1:3000/intake-v6/11891d68-c4c8-4719-acc5-f8fcb22a44af/operator`

## Observed Step 2 banner (before)

With only fatal `operator_confirmation_missing`, Step 2 showed a red primary banner:

- "1 problemă blochează Confirmarea"
- "Handoff-ul către ofertă reală este blocat."

That gate is only actionable on Step 3.

## Backend vs UI truth

- Backend: `operator_confirmation_missing` remains a real fatal gate; handoff_allowed stays false until explicit confirmation.
- Persistence: `PUT .../internal-draft-quote-confirmation` (not generic finish-setup) owns `finish_setup.internal_draft_quote_confirmed`.
- UI defect: presentation used global `!handoffAllowed` for the Step 2 red banner, so a future-step gate inflated the current-step problem count.

## Old / new step-scoping

| Step | Before | After |
|------|--------|-------|
| 1 / 2 | Red primary banner when only confirmation missing | No red primary; optional neutral "Confirmarea finală se efectuează în Pasul 3." |
| 3 | Actionable confirmation blocker | Unchanged actionable primary pointing at the checkbox |
| Confirmed | Cleared | Cleared; no false next-step guidance |

Primary blocker count uses `filterStepScopedFatalBlockers` — excludes `operator_confirmation_missing` off Step 3.

## Wording changes (Vector Logo)

Active user-facing copy updated (internal `artwork_*` / module codes unchanged):

- Finisaje tab: `Față · cant · Vector Logo`
- Section description: `Față, cant și Vector Logo…`
- Layer cards / confirm summary: `Vector Logo N` (0..N, not hardcoded Logo 1/2)
- Blocker formatters: artwork-execution messages → Vector Logo

## Query-string diagnosis

- Product step navigation is React state; `buildIntakeV6OperatorPath` does not append `?step=…`.
- Malformed `?step%3Dconfirm%26hydrationProof%3Dfinal` came from verification tooling treating a full query as one `URLSearchParams` key.
- Added `buildIntakeV6OperatorSearch` as the correct discrete-key helper; no broad router rewrite.

## Files changed

- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.ts` (+ tests)
- `frontend/src/lib/intakeV6/intakeV6StepScopedConfirmationUi.test.ts` (new)
- `frontend/src/lib/intakeV6/intakeV6OperatorRoutes.ts`
- `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewHeaderStatus.ts` (+ tests)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx` (+ tests)
- `frontend/src/components/workos/intake-v6/IntakeV6ConfirmDashboard.tsx`
- This worklog + `docs/solutions/architecture-patterns/intake-v6-step-scoped-confirmation-banner.md`

## Tests

Focused Vitest (7 files): **81 passed**.

Includes step-scoped surfacing, Vector Logo copy, query construction, hydration non-regression, ConfirmStep.

## Browser proof

- Confirmed + Step 2: no red confirmation/handoff banner; Vector Logo tab/cards; pricing dry-run unchanged.
- Reset via finish-setup path → Step 2 neutral guidance; Step 3 unchecked + actionable blocker.
- Reconfirm via dedicated confirmation endpoint / UI; hard reload hydrates checked.
- Nav 3→1→2→3: empty product `search` (no double-encoding); no stale red banner when confirmed.

## Final workspace truth

- `internal_draft_quote_confirmed=true`
- handoff `operator_confirmation_complete=true`, fatal list empty
- Pricing dry-run: net **3513.56** · VAT **737.85** · gross **4251.41** RON
- No Quote/Order created by this task

## Review findings

- P2 fixed: loading-only suppresses false-red banner; permanent fetch failure still banners.
- P3: query helper kept as characterization of correct encoding (product step nav does not need it).
- P3: badges for deferred confirmation use `NEEDS_CONFIRMATION` instead of false `READY`.

## Commit

On branch `feature/product-system-active-path-isolation-v1` (this commit). No push. No PR.
