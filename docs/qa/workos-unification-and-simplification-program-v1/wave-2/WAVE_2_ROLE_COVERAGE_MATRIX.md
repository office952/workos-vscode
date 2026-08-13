# Wave 2 role coverage matrix

Do not assume. Source = `frontend/src/lib/rbac.ts` + runtime (`rt-gap-closure-log.json` roleMatrix + V6 proofs).

| Route | Role | ROLE_ALLOWED | SOURCE | NAV_VISIBLE | Runtime landing |
|-------|------|--------------|--------|-------------|-----------------|
| `/intake` | admin | YES | RBAC `view:intake` + runtime | YES | `/intake` |
| `/intake` | sales | YES | RBAC `view:intake` + runtime | YES | `/intake` |
| `/intake-v6/:id/operator` | admin | YES | runtime open existing workspace | YES (via Cereri) | `/intake-v6/IR-MSRB28PU/operator` |
| `/intake-v6/:id/operator` | sales | YES | runtime open existing workspace | YES (via Cereri) | same |
| `/orders` | admin | YES | RBAC `view:orders` + runtime `orders-page` | YES | `/orders` |
| `/orders` | sales | YES | RBAC `view:orders` + runtime `orders-page` | YES | `/orders` |
| `/orders/:id` | admin | YES | same page | — | `/orders/ORD-IV6-V2-1786318810-31` |
| `/orders/:id` | sales | YES | same page | — | same pattern |
| `/clients` | admin | YES | RBAC `view:clients` + runtime | YES | `/clients` |
| `/clients` | sales | YES | RBAC `view:clients` + runtime | YES | `/clients` |
| `/clients/:name` | admin | YES | runtime | — | `/clients/SC CLIENT NOU SRL` |
| `/clients/:name` | sales | YES | runtime | — | same |
| `/quotes` | admin | YES | Wave 1 + RBAC `view:quotes` | YES | observe only |
| `/quotes` | sales | YES | Wave 1 + RBAC | YES | observe only |

App routes are **not** role-wrapped in `App.tsx`. Visibility is nav RBAC. Sales was previously uncovered on orders/clients by capture omission, not by deny.

`ROLE_COVERAGE_RESOLVED = YES`
