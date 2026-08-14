# Global legacy / dead reconciliation

Waves 1–5 combined. A REMOVE_CANDIDATE needs: no runtime, nav, API, test contract, or compat obligation, plus a replacement.

| Surface | Status | Why |
|---------|--------|-----|
| `/intake` · `/intake-v6` | ACTIVE_REQUIRED | Commercial entry |
| `/quotes` · `/orders` | ACTIVE_REQUIRED | Sold work |
| `/shop-floor` | ACTIVE_REQUIRED | Canonical monitor |
| `/execution` · `/:id` | ACTIVE_REQUIRED | Plan truth |
| `/operator` | ACTIVE_COMPAT | Live action API |
| `/tablet` | ACTIVE_COMPAT | Live station UI |
| `/intake/:id` | ACTIVE_COMPAT | Redirect |
| `/employee-app-v2` | SPECIALIZED | Mobile |
| `/employee-app` | LEGACY_REFERENCED | v1 sibling; still routed |
| Ops-Graph · Reality Review | AUDIT_ONLY | Live read |
| `/reports/operational` | AUDIT_ONLY | DEV |
| PS planned sections | PLACEHOLDER | Routed, unwired |
| `/documents` | PLACEHOLDER | MOCK hub |
| `/employees-records` | DEMO | Demo dossier |
| `/demo/*` | DEMO | Lab |
| Settings Societate profile | PLACEHOLDER | Mock |
| Inventory Automatizare | PLACEHOLDER | Mock |
| `/modules` · `/governance` | ACTIVE_REQUIRED | Admin map (PARTIAL accuracy) |
| HR / inventory / pricing / machines | ACTIVE_REQUIRED | Lateral belt |
| `MaterialPriceRegistry.tsx` | REMOVE_CANDIDATE | File-only orphan; unwired |
| FE `/intake-v4` residue | LEGACY_UNUSED | Wave 2: no App route; E2E leftover. Not a live nav item. File/test cleanup only after proving no contract. |
| Nav routes | — | **REMOVE_CANDIDATE_COUNT = 0** |

Do not mark `/operator` or `/tablet` dead. They are the current action path.
