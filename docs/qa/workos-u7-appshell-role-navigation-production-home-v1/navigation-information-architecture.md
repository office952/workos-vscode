# Navigation information architecture (U7)

## Central model

- `frontend/src/lib/shellNavigation.ts` — sections, labels, home, path allowlist
- `frontend/src/lib/rbac.ts` — permissions + `canViewNav`
- `AppShell.tsx` — presentation only
- `RoleHomeRedirect.tsx` — `/` and `*`
- `ShellPathGuard.tsx` — UI path redirect (not backend auth)

## Section order

Lucrări → Producție → Oameni → Resurse → Relații → Management → Administrare → DEV tooling (admin+DEV only)

## U7 changes vs Wave 0

1. Atelier → `/shop-floor` (was Shop Floor label; tablet was wrongly labeled Atelier)
2. Control producție moved to Management
3. Operator/Tablet relabeled as compat action surfaces
4. Role home redirects
5. Operator loses `view:dashboard` (no Control noise)
6. DEV demos only for admin
