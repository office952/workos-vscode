# Route reconciliation (U6 → U7)

| Route | Class | Nav label (U7) | Group |
|-------|-------|----------------|-------|
| `/shop-floor` | PRODUCTION_PRIMARY | Atelier | Producție |
| `/execution` | PRODUCTION_SECONDARY | Planificare | Producție |
| `/execution/ops-graph` | DIAGNOSTIC_AUDIT | Ops-Graph (audit) | Producție |
| `/operator` | PRODUCTION_SECONDARY | Acțiune task (compat) | Producție |
| `/tablet` | PRODUCTION_SECONDARY | Stații (compat) | Producție |
| `/dashboard` | MANAGEMENT | Control producție (preview) | Management |
| `/intake` `/quotes` `/orders` `/clients` | COMMERCIAL | Cereri/Oferte/… | Lucrări/Relații |
| `/product-system/*` | PRODUCT_CONFIGURATION | Produse | Lucrări |
| `/inventory/pricing` | ADMIN | Prețuri | Resurse |
| `/settings` `/governance` `/modules` | ADMIN | Setări/… | Administrare |
| `/employee-app*` | EMPLOYEE_MOBILE_EXCLUDED | — | outside shell |
| `/execution/:id` ProductSystem preview | PREEXISTING_BROKEN | — | not nav-owned |

Employee Mobile remains outside AppShell (unchanged).
