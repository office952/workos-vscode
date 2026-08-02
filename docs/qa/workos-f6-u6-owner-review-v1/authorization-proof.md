# Authorization proof — C3

| Gate | Evidence | Fail mode |
|------|----------|-----------|
| Close/reopen permission | `execution.job_close` = admin/manager only | fail-closed |
| Operator cannot close | `test_closure_readiness_operator_v1.py` | PASS |
| Closure readiness read | `execution.closure_readiness` for admin/manager/operator (C2) | read-only |
| CostsCompletenessPanel | management-gated (C2) | UI hide ≠ auth; API still permissioned |
| Material mutations when closed | HTTPException `execution_closed_mutation_blocked` | fail-closed |

No fail-open path observed in F6/U6 chain.
