# S3 — People-money navigation alignment

| Field | Value |
|-------|--------|
| Task | `S3_NAVIGATION_AND_INFORMATION_ARCHITECTURE_ALIGNMENT_V1` |
| Date | 2026-08-14 |
| OD-10 | APPROVED |
| Ops-Graph | OPTION B — keep in Producție + AUDIT |
| Owner DB mutations | 0 |
| Push | NO |
| S4 | Not authorized |

## Verdict

GS-09 = **IMPLEMENTED**. GS-10 = **DEFERRED_PARTIAL**. Findability only.

## What changed

Two primary-nav items moved in `SHELL_NAV_SECTIONS`:

- Plăți `/employee-payments` → Oameni
- Avansuri `/employee-advances` → Oameni

Management now contains only Control producție (PREVIEW) and Rapoarte.

Unchanged: routes, RBAC, backend, Ops-Graph, Reality Review (off-nav), `/operator`, `/tablet`, Product System.

## Runtime

| Check | Result |
|-------|--------|
| Admin Oameni | Angajați, Pontaj, Evidență HR, Plăți, Avansuri |
| Admin Management | Control producție, Rapoarte — no money items |
| Admin click Plăți | `/employee-payments` → Plăți angajați |
| Admin click Avansuri | `/employee-advances` → Avansuri / Datorii |
| Manager Oameni | includes Plăți; Avansuri absent |
| Manager `/employee-advances` | redirect `/shop-floor` |
| Sales `/employee-payments` | redirect `/quotes`; no money nav |
| Operator `/employee-payments` | redirect `/shop-floor`; no money nav |
| Ops-Graph | still Producție + AUDIT |
| COMPAT | `/operator` and `/tablet` unchanged |
| Reality Review | still absent from sidebar |
| Drawer 390px | same Oameni / Management grouping |

## Screenshots

- [s3-admin-dark-oameni.png](s3-admin-dark-oameni.png)
- [s3-admin-dark-plati.png](s3-admin-dark-plati.png)
- [s3-admin-light-oameni.png](s3-admin-light-oameni.png)
- [s3-manager-light-oameni.png](s3-manager-light-oameni.png)
- [s3-admin-drawer-390.png](s3-admin-drawer-390.png)

## Owner visual verification

1. Admin — `http://127.0.0.1:3000/dashboard` — role admin — Oameni ends with Plăți + Avansuri — Management has no money items.
2. Manager — `http://127.0.0.1:3000/employee-payments` — role manager — Oameni has Plăți — Avansuri absent = YES.
3. Production — any AppShell page — Ops-Graph AUDIT in Producție — Acțiune task / Stații COMPAT — no Reality Review item.
4. Responsive — viewport 390px — open drawer — same grouping.

## Stop

No push. No S4.
