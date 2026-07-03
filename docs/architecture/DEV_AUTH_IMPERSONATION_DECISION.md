# Dev Auth Impersonation for Employee Mobile Testing

## Status

```text
Status: Decision + Implementation
Runtime impact: development-only auth dependency behavior
Production impact: forbidden/guarded
DB impact: none (read-only user lookup)
Frontend impact: none (backend env var only)
```

## Context

Employee Mobile local testing uses dev auth bypass, which previously always returned a synthetic Dev Admin user (`dev-admin-user-00000000`). That blocked testing as other seeded users (e.g. `dev-employee-test-001` linked to employee id 1).

## Decision

In **development/local/test only**, when dev auth bypass is active:

1. If `WORKOS_DEV_AUTH_USER_ID` is set → load that user from the `users` table (read-only).
2. If the user is missing → fail with clear `503 dev_auth_user_not_found` (no silent fallback).
3. If `WORKOS_DEV_AUTH_USER_ID` is unset → keep existing synthetic Dev Admin fallback.

## Mechanism

| Item | Value |
|------|-------|
| Primary | `WORKOS_DEV_AUTH_USER_ID` env var |
| Fallback | Synthetic `dev-admin-user-00000000` |
| Header impersonation | Not implemented (env var sufficient for browser testing via backend restart) |

## Rules

- Impersonation does **not** create User or Employee rows.
- User fields (`email`, `name`, `role`) come from DB.
- Employee Mobile self endpoints use the same `current_user` as `/auth/me`.
- Missing user in DB → explicit dev config error.

## Security guard

```text
If APP_ENV/ENVIRONMENT is not local/development/test, dev_auth_allowed() is false:
- dev bypass token is never issued
- WORKOS_DEV_AUTH_USER_ID is ignored (resolve returns None)
- production/staging require real credentials
```

Implemented in:

- `core.config.resolve_dev_auth_impersonation_user_id()`
- `dependencies.auth._resolve_dev_bypass_user()`

## Examples

```powershell
# Dev Admin (explicit)
$env:WORKOS_DEV_AUTH_USER_ID="dev-admin-user-00000000"

# Normal employee mobile test user
$env:WORKOS_DEV_AUTH_USER_ID="dev-employee-test-001"

# Owner seed user
$env:WORKOS_DEV_AUTH_USER_ID="dev-owner-office-p-media-ro"
```

Restart backend after changing env var.

## Out of scope

- Production impersonation
- OIDC/JWT rewrite
- Automatic user/employee creation
- Frontend header switching
