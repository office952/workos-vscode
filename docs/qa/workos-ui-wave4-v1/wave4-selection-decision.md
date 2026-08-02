# Wave 4 selection decision

## Decision

Select **Execution Closure + Profitability operational truth** for U4B, constrained to a manager/admin decision-support presentation over existing backend evidence.

This is not a claim that WorkOS can now close jobs or calculate actual profit. It is the highest-value UI group because the application already has:

- backend-refreshed planned task and recorded-reality evidence on `/execution/:order_id`;
- `PostJobTruthPanel` and a management-only `ProfitabilityActualReadPanel`;
- explicit unavailable reasons and a labelled legacy profitability panel;
- documented blockers: employee-cost policy, material actual money, incomplete task coverage, and no canonical job-closed authority.

The audit therefore supports a UI that answers: **what is complete, what is missing, what values are factual, and what decision remains blocked?** It must not add an actual-cost formula, a closure mutation, or substitute legacy analysis for truth.

## Why this group over alternatives

| Candidate | Evidence strength | Decision |
|---|---|---|
| Execution Closure + Profitability operational truth | Strong existing read surfaces and explicit blockers; manager/admin role fit; largest cross-route gap | **Select** |
| Shop Floor / Operator restyle | Existing U2 warnings support it, but it would improve presentation while leaving post-job decision truth fragmented | Defer |
| Pricing reliability | Material functional debt exists, but the known test failure and protected pricing scope need a dedicated corrective GO | Defer |
| Product System / admin polish | U3 covered the primary story; reference freeze limits expansion | Defer |
| People/money surfaces | Sensitive and separate from operational closure | Defer |

## U4B boundary

Allowed:

- Reorganise existing execution/post-job/profitability presentation into an explicit closure-readiness story.
- Preserve planned, actual operational, commercial frozen, estimated internal, and actual-cost truths as visibly separate.
- Surface backend reason codes and unavailable conditions in Romanian-first operator/manager language.
- Keep legacy profitability visibly non-authoritative or remove it from the primary decision path only if its existing contract allows.
- Add focused visual regression and permission tests; capture day/dark runtime proof only against a compatible backend identity.

Forbidden:

- Job close/reopen action, auto-close, or lifecycle authority.
- Frontend cost/margin calculations, labor-money conversion, or fake zero values.
- Pricing, CostEngine, inventory, snapshot, or Product Truth business changes.
- Employee Mobile and unauthorised changes to controlled assignment.

## Exit evidence required before accepting U4B

1. Manager/admin sees one first-fold closure state: ready, incomplete, or blocked with backend reasons.
2. Operator sees operational completion/readiness only; no salary or margin data.
3. No actual-margin or actual-cost positive state unless the backend says it is available.
4. Existing task actions continue to refetch backend truth; no optimistic closure state.
5. Compatible FE/BE runtime screenshots in day and dark, plus a console capture for the selected path.
6. Targeted tests prove permission visibility, missing-data semantics, and legacy/non-authoritative labelling.
