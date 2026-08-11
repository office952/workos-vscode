# REQUEST_TRACE

## Before (audit)

See `docs/qa/workos-intake-v6-e2e-operator-reality-performance-ux-audit-v1/PERFORMANCE_REQUEST_TRACE.md`:  
`face_finish` → 8 groups including productionDryRun, productionHandoff, taskPreview, orderBoundReadiness.

## After — Step 2 remount (runtime, no mutation)

File: `network/step2_remount_after.json`

Offer-critical observed:

- pricing-input-preview (67 ms)
- material-breakdown (132 ms)
- quote-handoff-preview (227 ms)
- priced-quote-dry-run (705 ms)
- logical-list-read-model (721 ms)

Production/diagnostic observed: **none**

## Confirm entry (read-only)

Confirm still loads binding, nesting, breakdown, pricing, quote-handoff, priced-quote — no production-task fan-out required for Confirm checklist.
