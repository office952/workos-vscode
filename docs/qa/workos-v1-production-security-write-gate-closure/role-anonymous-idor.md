# Role / anonymous / IDOR

## Roles (effective)

`admin`, `manager`, `sales`, `operator`, `viewer`, `employee_mobile`

## Sensitive employee / payments

| Operation | admin | manager | sales | operator | viewer | mobile |
|-----------|-------|---------|-------|----------|--------|--------|
| Employee list operational fields | ALLOW | ALLOW | ALLOW* | ALLOW | ALLOW* | ALLOW* |
| Employee HR cost fields | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| Employee payments situation | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| HR capacity lifecycle | ALLOW | ALLOW | DENY | DENY | DENY | DENY |

\* Authenticated read of operational projection only (no salary/cost).

## Anonymous (prod posture: `dev_auth_allowed=False`)

| Route | Expected |
|-------|----------|
| GET employees | 401 |
| GET employee-payments | 401 |
| GET/POST intake-v5 | 404 (unmounted) |
| GET /auth/me | 401 |

## IDOR (representative — prior closures retained)

Assignment / session / MachineRun / ExecutionPlan writers remain permission + object-scope gated from earlier PASS builds. This GO did not reopen those writers; regressions remain auth-required.

Wrong-object denial continues to return 403/404 per existing contracts — no sensitive salary payload on error paths for operator projection.
