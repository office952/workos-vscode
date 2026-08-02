# Role inventory (runtime truth)

| Role | Source | Desktop shell | Notes |
|------|--------|---------------|-------|
| `admin` | BE `VALID_ROLES` + FE `Role` | Full nav | DEV fallback default |
| `manager` | BE + FE | Ops + HR + commercial; no pricing/settings | |
| `sales` | BE + FE | Lucrări / Relații / Planificare | No shop floor |
| `operator` | BE + FE | Atelier + Acțiune task + Stații + utilaje/inventar | No Control (U7) |
| `viewer` | BE + FE | Control producție only | Fail-closed |
| `employee_mobile` | BE only | Outside AppShell | Excluded from U7 |

Auth source: `/api/v1/auth/me` → `resolveRole()`. DEV override for QA: `sessionStorage.workos-dev-role` (non-prod only).

## Separation

| Layer | Mechanism |
|-------|-----------|
| UI visibility | `canViewNav` + `projectNavSectionsForRole` |
| UI path access | `pathAllowedForRole` + `ShellPathGuard` (redirect to role home) |
| Backend authorization | unchanged `PERMISSION_MATRIX` / `require_permission` |
