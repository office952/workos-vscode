# Role visibility matrix — Wave 0 shell nav

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Source | `frontend/src/lib/rbac.ts` + `frontend/src/lib/shellNavigation.ts` |
| Fail-closed | Unknown role → `viewer`; unknown nav key → hidden |
| DEV tooling | Visible when `VITE_ENABLE_DEV_AUTH=true` and non-prod (any resolved role) |

Legend: **Y** = visible in sidebar · **—** = hidden · **DEV** = only with DEV auth flag

| Nav label | Route | viewer | operator | sales | manager | admin |
|-----------|-------|:------:|:--------:|:-----:|:-------:|:-----:|
| Cereri | `/intake` | — | — | Y | Y | Y |
| Produse | `/product-system/products` | — | — | Y | Y | Y |
| Oferte | `/quotes` | — | — | Y | Y | Y |
| Comenzi | `/orders` | — | — | Y | Y | Y |
| Planificare | `/execution` | — | — | Y | Y | Y |
| Ops-Graph | `/execution/ops-graph` | — | — | — | Y | Y |
| Atelier | `/tablet` | — | Y | — | Y | Y |
| Control producție | `/dashboard` | Y | Y | Y | Y | Y |
| Shop Floor | `/shop-floor` | — | Y | — | Y | Y |
| Operator | `/operator` | — | Y | — | Y | Y |
| Angajați | `/employees` | — | — | — | Y | Y |
| Pontaj | `/attendance` | — | — | — | Y | Y |
| Evidență HR | `/employees-records` | — | — | — | Y | Y |
| Utilaje | `/utilaje` | — | Y | — | Y | Y |
| Inventar | `/inventory` | — | Y | Y | Y | Y |
| Prețuri | `/inventory/pricing` | — | — | — | — | Y |
| Clienți | `/clients` | — | — | Y | Y | Y |
| Colaboratori | `/colaboratori` | — | — | — | Y | Y |
| Documente | `/documents` | — | — | Y | Y | Y |
| Rapoarte | `/reports` | — | — | Y | Y | Y |
| Plăți | `/employee-payments` | — | — | — | Y | Y |
| Avansuri | `/employee-advances` | — | — | — | — | Y |
| Harta | `/modules` | — | — | — | — | Y |
| Guvernanță | `/governance` | — | — | — | — | Y |
| Setări | `/settings` | — | — | — | — | Y |
| DEV demos / diag | `/demo/*`, Intake V6 diag, Blueprint, Rapoarte operaționale | DEV | DEV | DEV | DEV | DEV |

## Per-role ops home (one clear story)

| Role | Primary ops home in nav | Hidden peers |
|------|-------------------------|--------------|
| viewer | Control producție | Everything else (except DEV tooling when flag on) |
| operator | Atelier (+ Shop Floor / Operator) | Lucrări commercial, HR, money, Administrare |
| sales | Lucrări (Cereri→Comenzi) | Shop Floor / Operator / Atelier, HR, money, Prețuri, Administrare |
| manager | Planificare (+ Ops-Graph) | Prețuri, Avansuri, Administrare |
| admin | Full IA | — |

## Notes

- Routes remain reachable by URL even when hidden from nav (no route deletion).
- No fake in-UI role switcher — role comes from `/api/v1/auth/me` (or DEV fallback `role: admin`).
- Backend impersonation via `WORKOS_DEV_AUTH_USER_ID` still controls which user `/auth/me` returns; FE projects nav from that role.
