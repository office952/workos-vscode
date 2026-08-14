# S2 — Mock / demo / projection honesty

| Field | Value |
|-------|--------|
| Task | `S2_MOCK_DEMO_PROJECTION_HONESTY_V1` |
| Date | 2026-08-14 |
| OD-2 | APPROVED — remove Documents from primary Relații; keep `/documents` |
| Owner DB mutations | 0 |
| Push | NO |
| S3+ | Not authorized |

## Verdict

GS-04 / GS-05 / GS-06 = **PASS** (display + nav entry only).

## What changed

- `/reports` reads as **Proiecție operațională**. Money label is **Valoare comenzi 7z**. Same `reports-summary` source and same KPI math.
- **Documente** removed from primary Relații. Route `/documents` stays. Page marked **ÎN PREGĂTIRE**. CTAs remain disabled.
- Evidență HR keeps live employee identity and makes the demo dossier boundary explicit on list and detail. `/employees` stays LIVE DB.

## Runtime

| Check | Result |
|-------|--------|
| Reports admin light/dark | Projection banner; no “showing real data”; no Revenue 7d |
| Documents nav | Relatii = Clienți + Colaboratori. No `/documents` sidebar link |
| Documents direct | `http://127.0.0.1:3000/documents` works; ÎN PREGĂTIRE; disabled CTAs |
| Sales | `/reports` and `/documents` reachable; Documente not in nav |
| HR list/detail | Live names + DEMO + hybrid copy; program labeled demonstrativ |

## Screenshots

- [s2-reports-admin-light.png](s2-reports-admin-light.png)
- [s2-reports-admin-dark.png](s2-reports-admin-dark.png)
- [s2-documents-admin-light.png](s2-documents-admin-light.png)
- [s2-documents-admin-dark.png](s2-documents-admin-dark.png)
- [s2-hr-list-admin-light.png](s2-hr-list-admin-light.png)
- [s2-hr-detail-admin-light.png](s2-hr-detail-admin-light.png)
- [s2-hr-detail-admin-dark.png](s2-hr-detail-admin-dark.png)

## Tests

```
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/Reports.honesty.test.tsx src/pages/DocumentCenter.honesty.test.tsx src/pages/EmployeeRecords.honesty.test.tsx src/lib/shellNavigation.test.ts src/lib/rbac.test.ts
```

5 files, 53 passed.

## Stop

S3 not authorized. No push. No PR.
