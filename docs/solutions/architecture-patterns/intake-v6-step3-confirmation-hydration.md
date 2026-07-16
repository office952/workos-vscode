---
title: Hydrate Intake V6 Step 3 confirmation checkbox from persisted workspace truth
date: 2026-07-16
problem_type: architecture_pattern
component: frontend_hook
symptoms:
  - Step 3 confirmation checkbox appears unchecked after hard reload
  - Backend finish_setup.internal_draft_quote_confirmed remains true
  - can_create_internal_draft_quote and handoff_allowed stay true while UI looks unconfirmed
root_cause: useState(false) local checkbox never reconciled to finish_setup or handoff preview
tags:
  - intake-v6
  - confirmation
  - hydration
  - step3
  - handoff
module: useIntakeV6FinalHandoff
applies_when:
  - Persisted internal_draft_quote_confirmed must drive the Confirm checkbox
  - Hard reload remount or route remount must not invent unchecked UI truth
  - Upstream finish-setup save resets confirmation and UI must follow
---

# Hydrate Intake V6 Step 3 confirmation checkbox from persisted workspace truth

## Context

Backend confirmation persistence and Quote eligibility were correct. After hard reload the Confirm checkbox still initialized as `useState(false)` and never hydrated from `finish_setup.internal_draft_quote_confirmed` or `operator_confirmation_complete`, so operators saw an unchecked control while the workspace remained confirmed.

## Guidance

1. Treat persisted backend fields as the checkbox source of truth — never leave a session-only default as settled UI.
2. Resolve hydration from handoff when loaded; while preview is refreshing, prefer workspace `finish_setup` so upstream resets are not masked by a stale handoff snapshot.
3. Keep optimistic local state only while a confirmation PUT is in flight; on failure restore the last persisted value.
4. Disable the checkbox and avoid “missing confirmation” warning chrome while hydration is unresolved.
5. Guard refetch apply with a generation counter and a saving ref so stale responses cannot overwrite newer truth.

## Why This Matters

Quote creation must not start from a UI that disagrees with workspace confirmation. Hydration closes the false-unchecked gap without changing reset policy, readiness severity, or pricing.

## When to Apply

- Any Intake V6 Confirm control that mirrors a persisted workspace boolean.
- After reload remount HMR or navigation back to Confirm when backend already holds confirmation.

## Related

- `docs/worklog/realignment/2026-07-16_gradi_curat_step3_confirmation_hydration_fix.md`
- `docs/worklog/realignment/2026-07-16_gradi_curat_step3_confirmation_live_verification.md`
