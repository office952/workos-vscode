# 2026-08-02 — UI Wave 4 scorecard (U4A)

## Scope

Read-only desktop AppShell audit on `feat/ui-wave4-scorecard-v1` at base `10fca478`. Employee Mobile, product/backend business code, database state, and protected order `973019` were not changed.

## Evidence reviewed

- `frontend/src/App.tsx`, `components/workos/AppShell.tsx`, `lib/shellNavigation.ts`, and `lib/rbac.ts`
- Wave 0 AppShell/day-mode/role-navigation report
- Wave 1 commercial-flow report
- Wave 2 execution-flow report and Wave 3 closure audit
- Wave 3 Product/Admin report and F3/U3 hardening report
- Full route baseline inventory/scorecard
- Actual-cost job-closure decision gate and profitability actual-read-model reports
- `ExecutionDetail.tsx` and `ProfitabilityActualReadPanel.tsx`

## Findings

- The shell, Romanian-first navigation, and primary commercial spine have materially improved.
- Execution Detail has the best factual evidence for the next UI group, but it is overloaded and closure truth remains distributed.
- Profitability is correctly honest: actual minutes can be present while labor cost, material cost, actual margin, and closure remain unavailable.
- Fresh Wave 4 runtime/console proof was not captured because U3 documented an incompatible API identity blocker; this audit does not relabel historical console results as current.

## Decision

Recommend U4B: **Execution Closure + Profitability operational truth**, limited to manager/admin decision support over backend-provided evidence. No job-close mutation, actual-cost calculation, inventory mutation, or Product Truth authority is justified by this audit.

## Files written

- `docs/qa/workos-ui-wave4-v1/FULL_APPLICATION_SCORECARD.md`
- `docs/qa/workos-ui-wave4-v1/route-matrix.md`
- `docs/qa/workos-ui-wave4-v1/role-surface-matrix.md`
- `docs/qa/workos-ui-wave4-v1/top-10-gaps.md`
- `docs/qa/workos-ui-wave4-v1/wave4-selection-decision.md`
- this worklog
