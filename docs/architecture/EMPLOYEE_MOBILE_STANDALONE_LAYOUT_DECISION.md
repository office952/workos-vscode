# Employee Mobile Standalone Layout — Decision

## Status

| Field | Value |
|-------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | Frontend routing/layout only |
| **Backend impact** | none |
| **DB impact** | none |
| **Payroll impact** | none |

## Regula principală

> **Employee Mobile routes must render outside the desktop WorkOS shell.**

## Rute afectate

```text
/employee-app
/employee-app/requests
/employee-app/attendance
/employee-app/review
/employee-app/team
```

Aceste rute folosesc `EmployeeMobileStandaloneRoot` + layout Employee Mobile (header + bottom nav).

## Rute neafectate

```text
/attendance
/attendance/effects
/work-intake, /intake, /intake-v2
/quotes, /orders
/inventory, /inventory/pricing
/product-system
/dashboard, /employees, etc.
```

Rămân în `AppShell` (sidebar + topbar desktop).

## Root cause (pre-fix)

`/employee-app/*` era definit **în interiorul** `AppShell` (`App.tsx`), ca rută sibling cu Dashboard/Attendance. Sidebar-ul și topbar-ul desktop se montau pentru toate rutele autentificate.

## Fix

`AuthenticatedAppRoutes` separă:

```text
/employee-app/*  → EmployeeMobileStandaloneRoot (fără AppShell)
*                → AppShell (desktop)
```

Auth guard (`RuntimeProtectedOutlet`) rămâne comun; doar layout-ul diferă.

## UX rules

Employee Mobile layout:

- fără sidebar desktop;
- fără topbar desktop (search, alerte critice ERP);
- header Employee Mobile propriu;
- bottom nav Employee Mobile;
- container mobile-first (`max-w-lg`, centrat pe desktop);
- PWA `start_url` rămâne `/employee-app`.

## Security rules

- Separarea de layout **nu** este securitate;
- backend guards rămân sursa de adevăr;
- frontend nu relaxează roluri;
- attendance CRUD rămâne admin/operator only.

## Deferred

- native app;
- offline mode / service worker;
- push notifications;
- advanced device detection;
- role-based perfect hiding în frontend;
- multi-firm branding per company.
