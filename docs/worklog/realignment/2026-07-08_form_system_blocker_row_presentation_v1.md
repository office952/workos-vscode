# Form System Backbone Blocker Row Presentation V1

## Purpose

Add a read-only blocker-row presentation layer on top of the existing Form System Backbone readiness blockers so matching field-addressed blockers can appear relaxed after runtime confirmation without hiding or deleting any backbone blocker rows.

## Previous Limitation

The awareness model already relaxed matching field rows after runtime SVG confirmation, but blocker rows were still rendered as a raw list from backbone readiness. That created a presentation mismatch where a field could show confirmed while its corresponding blocker row still appeared fully active.

## Scope And Boundary

- Frontend only.
- No backend endpoint changes.
- No readiness mutation.
- No Product Truth or ProductDefinition writes.
- No Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB changes.
- No blocker deletion or hiding.
- No broad/global blocker relaxation.

## Audit Findings

- Blocker rows were built in the awareness model from `backbone.blockers ?? backbone.readiness?.blockers ?? []`.
- The panel rendered those blocker rows through awareness, but only as a flattened `{ code, component, message }` list.
- Backbone blocker objects carry `field_key`, `owning_component`, `blocker_code`, `state`, `blocks`, and `message`.
- Field-addressed blockers are the entries whose `field_key` points at a concrete field such as `svg.layer_group_role` or `svg.selected_layer_group`.
- Broad/global blockers are represented by non-field or boundary-style keys such as `readiness.product_truth_blockers` and must remain active.
- The existing runtime readiness policy already identifies whether a matching field-level warning can relax after runtime confirmation.
- The UI did not need copy rewrites; a small relaxed badge/copy on matching field-level blocker rows was sufficient.

## Implementation

- Added `blockerRows` to the awareness model as a presentation layer derived from backbone blockers plus runtime readiness policy decisions.
- Preserved the existing `blockers` list for compatibility.
- Added blocker presentation metadata:
  - `fieldKey`
  - `severity`
  - `isFieldAddressed`
  - `isBroadOrGlobal`
  - `canRelax`
  - `reason`
  - `trace`
- Rendered relaxed matching field-level blockers with a small inline note: `Resolved by runtime confirmation; kept for backbone audit.`
- Left broad/global blockers active and visible.

## Files Changed

- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.test.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx`

## Validation

### Focused Tests

From `frontend/`:

```powershell
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.test.ts src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.test.ts src/lib/intakeV6/formSystemBackboneAwareness.test.ts
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx
```

Results:

- Awareness-focused suites passed.
- Panel suite passed after updating the compact summary expectation to reflect the two-blocker fixture.

### Runtime Smoke

- `/intake-v6/IR-MRBMAK7Z/operator`
  - Review step loads.
  - Form System Backbone panel expands.
  - `svg.layer_group_role` shows `operator_confirmed / confirmed`.
  - `svg.selected_layer_group` shows `operator_confirmed / confirmed`.
  - Matching blocker rows remain visible and show relaxed presentation.
  - Product Truth boundary warning remains visible.
  - Other blocker rows such as face and finish gaps remain active.
- `/intake`
  - `Cerere Nouă` modal still opens.
  - Normal click stalled again; direct `evaluate((node) => node.click())` still works in this app.
- `/product-system`
  - Letters still shows `offerable`.
  - Logo still shows `candidate / not Work Intake`.

## Proof Blockers Were Not Hidden

- The original backbone-derived `blockers` list remains in the awareness model.
- The new `blockerRows` layer is presentation-only and is derived from those same backbone blockers.
- Relaxed rows remain rendered; they are not removed from the list.
- Broad/global blockers are still rendered as active rows.

## Remaining Risks

- The panel still truncates blocker rows to the first four entries, so some broad/global blockers may be outside the visible slice depending on ordering.
- Relaxation currently applies only where the existing runtime readiness policy can positively match the field-addressed blocker.

## Recommended Next Slice

Consider a small follow-up to surface broad/global blockers more explicitly when they fall outside the visible top-four slice, without changing readiness semantics or row ordering authority.