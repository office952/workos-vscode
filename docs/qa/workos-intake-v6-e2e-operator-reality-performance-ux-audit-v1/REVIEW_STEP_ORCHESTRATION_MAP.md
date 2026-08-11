# REVIEW_STEP_ORCHESTRATION_MAP

Source: `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` @ `303add0f`

## Verdict

**Does ReviewStep currently do too much?** **YES**

It orchestrates finish editing + offer rail + confirm-gate surfacing + production dry-runs + form-system diagnostics + commercial spine on Step 2.

## Critical path (keep)

1. Finish / commercial autosave (`PUT finish-setup`)
2. Quote-handoff preview (blockers)
3. Offer rail quartet: material-breakdown, logical-list, pricing-input-preview, priced-quote-dry-run (+ face/back prep)
4. Template + modular contracts + product-system binding
5. Company commercial settings (VAT/FX)
6. ACM geometry when ACM sold

## Leave interactive critical path (recommendation only)

1. production-task-dry-run, production-handoff-preview, task-generation-dry-run, order-bound-task-readiness — Confirm/Production/diagnostic only
2. task-preview + AI assist — stop eager mount fetch
3. product-definition-preview — fetch when Composition opens
4. QuoteCommercialSpinePanel (+ duplicate dry-run) — Confirm / drawer-open
5. Tighten post-autosave fan-out so production groups do not refresh on every finish selector

## Eager GETs on Step 2 enter (~17)

See companion `READ_MODEL_COST_AND_VALUE_MAP.md`.

## Dead smell

- `activeTasks` useMemo unused
- Commercial spine re-fetches priced dry-run already owned by parent
