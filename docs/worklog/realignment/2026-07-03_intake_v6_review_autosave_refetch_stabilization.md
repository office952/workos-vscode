# Intake V6 Review autosave/refetch stabilization

## Task
- Stabilize Intake V6 page 2 / Review without redesign.
- Audit the exact cause of the save/refetch loop.
- Separate local draft behavior from persisted-preview refresh behavior.
- Reduce broad refetch after simple form edits.
- Preserve existing Product Truth, readiness, and preview semantics.

## Exact cause audit
- Review controls mutate local Review state immediately on each interaction.
- Autosave persists the full `finish_setup` payload after a short debounce.
- Preview panels were refetching off a shared persisted key derived from `workspace.updated_at` plus footprint override revision.
- Successful save updates the workspace revision, which retriggered most Review preview effects even for narrow changes such as lighting or a numeric mounting field.
- Review also rehydrated local form state from payload on workspace refresh, so the same save could trigger a visible `save -> refetch all -> rehydrate all` chain.
- The loop was systemic and not limited to LED controls.

## Implementation summary
- Added a small domain-to-preview mapping helper so Review changes can request only the downstream preview groups they actually affect.
- Replaced the broad `persistedReviewRefetchKey` dependency in Review preview effects with local refetch counters per preview group.
- Tracked dirty Review domains during local edits and only refreshed the corresponding preview slices after a successful save.
- Kept sheet-footprint override refresh explicit instead of relying on workspace revision churn.
- Changed payload rehydration to be differential: local Review state now only syncs from payload when there are no local edits pending, and only when the normalized persisted value is meaningfully different.
- Changed save rehydration to be differential as well, so backend normalization is applied only when it actually differs from the just-saved local body.
- Added slower autosave policy for long-form numeric/commercial edits and blur-save for mounting template area.

## Files touched
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`

## Validation run
### Passed
- Static diagnostics on touched files: no errors.
- Focused Vitest:
  - `src/lib/intakeV6/intakeV6ReviewRefetchDomains.test.ts`

### Partial / gap
- No dedicated existing test harness was present for `IntakeV6ReviewStep` autosave/refetch behavior.
- Live browser re-verification of the full operator Review interaction was not rerun in this slice, so the behavioral validation here is code-path and static-check driven.
- A broader frontend `tsc --noEmit` check was attempted from the frontend app root; the command did not provide a final result in-session, so it is not counted as a completed validation gate.

## Residual risk
- Domain mapping is intentionally conservative but still manual; future Review controls should register their dirty domain explicitly or they may under-refresh downstream previews.
- ReviewStep remains a large orchestration surface, so missing component-level tests still leave regression risk around autosave timing.

## Next safe step
- Add a focused ReviewStep interaction test that covers:
  1. lighting select change -> save -> only pricing/breakdown/handoff style previews refresh
  2. mounting area typing -> no rapid save churn while typing
  3. save response with normalized payload -> local form only updates when normalization changes meaningfully