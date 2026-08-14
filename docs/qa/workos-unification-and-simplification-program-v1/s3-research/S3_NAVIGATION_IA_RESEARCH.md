# S3 — Navigation / information architecture research

| Field | Value |
|-------|--------|
| Task | `S3_NAVIGATION_AND_INFORMATION_ARCHITECTURE_ALIGNMENT_V1` |
| Phase | ROOT-CAUSE RESEARCH ONLY |
| Date | 2026-08-14 |
| HEAD | `0bff1f394d6f4e484d513789c92546be2a4bc75c` |
| AHEAD / BEHIND | 0 / 0 |
| Implementation | NO |
| Commit / Push | NO |

Discipline: navigation placement ≠ system ownership. A group move must make an existing truth easier to find. It must not change route, RBAC, backend, or authority.

---

## Baseline

Local HEAD = remote HEAD = `0bff1f39` (`fix(workos): clarify support surface truth`). Tracked product tree clean. Leftover `??` QA/tmp files ignored.

`CURRENT_WORKOS_FROZEN_AS_REFERENCE` remains ON. No S3 product exception is active.

---

## Required synthesis

```text
PAYMENTS_ROUTE = /employee-payments
PAYMENTS_CURRENT_GROUP = Management
PAYMENTS_VISIBLE_ROLES = admin, manager
PAYMENTS_PURPOSE = Operational payment tranches (15/30); not fiscal payroll
PAYMENTS_CURRENT_IA = MISPLACED
PAYMENTS_RECOMMENDED_GROUP = OAMENI

ADVANCES_ROUTE = /employee-advances
ADVANCES_CURRENT_GROUP = Management
ADVANCES_VISIBLE_ROLES = admin
ADVANCES_PURPOSE = Internal employee balance ledger; not official accounting
ADVANCES_CURRENT_IA = MISPLACED
ADVANCES_RECOMMENDED_GROUP = OAMENI

OPS_GRAPH_ROUTE = /execution/ops-graph
OPS_GRAPH_CURRENT_GROUP = Producție
OPS_GRAPH_VISIBLE_ROLES = admin, manager
OPS_GRAPH_PURPOSE = Materialized execution-graph audit + controlled assign (no start/stop)
OPS_GRAPH_CLASSIFICATION = MIXED (audit-primary; not everyday production)
OPS_GRAPH_RECOMMENDED_GROUP = OWNER_DECISION — not Administrare

REALITY_REVIEW_ROUTE = /execution/reality-review
REALITY_REVIEW_CURRENT_GROUP = NONE (deep-link only)
REALITY_REVIEW_VISIBLE_ROLES = nav: none; direct: admin, manager, sales
REALITY_REVIEW_PURPOSE = Read-only operational gaps dashboard
REALITY_REVIEW_CLASSIFICATION = AUDIT_ONLY
REALITY_REVIEW_RECOMMENDED_GROUP = KEEP_DEEP_LINK (do not invent a sidebar item)

OPERATOR_ROUTE_STATUS = ACTIVE_COMPAT (/operator)
OPERATOR_NAV_RECOMMENDATION = KEEP_AS_IS (Producție)

TABLET_ROUTE_STATUS = ACTIVE_COMPAT (/tablet)
TABLET_NAV_RECOMMENDATION = KEEP_AS_IS (Producție)

PRODUCT_SYSTEM_CURRENT_PLACEMENT = Lucrări → Produse (/product-system/products)
PRODUCT_SYSTEM_S3_ACTION = NO_CHANGE
NO_CHANGE / OWNER_DECISION_REQUIRED = OWNER_DECISION_REQUIRED (Ops-Graph home only)

PRIMARY_NAV_SOURCE = frontend/src/lib/shellNavigation.ts SHELL_NAV_SECTIONS
MOBILE_NAV_SOURCE = same projectNavSectionsForRole() via AppShell drawer
SAME_CONFIG = YES

SECONDARY_NAV_CONTRADICTIONS =
  1. Planificare header still links Ops-Graph + Reality Review (audit doors, not sidebar)
  2. personalNavigation.ts lists people+money together but is NOT wired to AppShell
  3. Shop-floor next-step already points action to /operator and /tablet (justifies keeping them in Producție)

RBAC_IMPACT_IF_MOVED = EXPECTED = NONE
  (group change only; navKeys / canViewNav / pathAllowedForRole stay)
ROUTE_CHANGES_REQUIRED = EXPECTED = NO
BACKEND_CHANGES_REQUIRED = EXPECTED = NO

OWNER_DECISION_REQUIRED = YES
DECISION = Where does Ops-Graph live after demotion from everyday Producție?
OPTIONS =
  A. New Sistem / Audit section (manager+admin; do NOT merge with Administrare)
  B. Keep in Producție with existing AUDIT badge (lowest habit break)
  C. Move under Administrare (REJECT — manager would inherit an Administrare section or lose the item)
RECOMMENDED = A if Owner wants demotion; B if Owner wants zero new IA nouns
TRADEOFF = A adds a group; B leaves an audit item beside Atelier; C lies about admin vs manager
RECOMMENDED_IMPLEMENTATION_BOUNDARY =
  SAFE NOW (OD-10): move Plăți + Avansuri items into Oameni in SHELL_NAV_SECTIONS only
  WAIT: Ops-Graph group; do not add Reality Review to primary nav; no Product System move
```

---

## Nav source map

| Candidate | PRIMARY_NAV_SOURCE | SECONDARY_ENTRY_POINTS | ROLE_FILTER | STATUS_BADGE_SOURCE | PROGRAMMATIC_NAV |
|-----------|--------------------|------------------------|-------------|---------------------|------------------|
| Plăți | `SHELL_NAV_SECTIONS` management | Payments → `/employees` when pay-base missing; no Attendance/Advances links | `navKey: payments` → `view:payments` | none | none |
| Avansuri | same | none | `navKey: advances` → `view:advances` (admin) | none | none |
| Ops-Graph | `SHELL_NAV_SECTIONS` productie | Planificare header `Ops graph (RO)` | `canViewNav("ops_graph")` manager/admin + `view:execution` | `status: "audit"` | fixture/order form on page |
| Reality Review | **not in sidebar** | Planificare `Review Realitate`; DEV `/reports/operational` | `pathAllowedForRole` → `canViewNav("execution")` | none | none |
| /operator | productie | Shop-floor next-step; execution detail hint | `view:operator` | `status: "compat"` + label `(legacy)` | `?orderId=` |
| /tablet | productie | Shop-floor next-step | `view:shopfloor` | `status: "compat"` + label `(legacy)` | `/tablet/:stationId` |
| Product System | lucrari `Produse` | Intake detail; PS internal links | `view:products` | none | prefix match `end: false` |

`AppShell` desktop rail and narrow drawer both call `projectNavSectionsForRole(role)`. `personalNavigation.ts` is test-only.

---

## RBAC runtime (not sidebar inference)

`workos-dev-role` probes on live `:3000` (2026-08-14):

| Role | Plăți nav / direct | Avansuri nav / direct | Ops-Graph nav / direct | Reality Review nav / direct | /operator | /tablet | Produse |
|------|--------------------|-----------------------|------------------------|-----------------------------|-----------|---------|---------|
| admin | YES / YES | YES / YES (nav) | YES / YES | NO / (allowed by code) | YES | YES | YES |
| manager | YES / YES (`Plăți angajați`) | NO / redirect `/shop-floor` | YES / YES (`Ops graph`) | NO / YES (`Operational Reality Review`) | YES | YES | YES |
| sales | NO / redirect `/quotes` | NO / (blocked) | NO / redirect `/quotes` | NO / YES | NO | NO | YES |
| operator | NO / redirect `/shop-floor` | NO | NO / redirect `/shop-floor` | NO / redirect `/shop-floor` | YES (`Operator View`) | YES (`Atelier — Stații`) | NO / redirect `/shop-floor` |

Backend (code, not changed):

- Payments: `employee_payments.read/write` = admin, manager
- Advances: authenticated user only — FE is the real role gate (pre-existing; out of S3)
- Reality Review: authenticated user only — FE `view:execution` is the real role gate
- Ops-Graph: execution APIs; FE extra manager/admin gate

S3 must not change any of these.

---

## Light / dark (observe only)

- Dark badges: `AUDIT` / `COMPAT` / `PREVIEW` = `rgb(98,112,132)` on `rgb(11,15,25)` — readable, dim.
- Light badges: `rgb(115,130,150)` on white; PREVIEW reads clearer than AUDIT/COMPAT.
- Truncation on 220px rail: `Acțiune task (legacy)`, `Control producție`.
- Group headings are clear. No COMPAT/AUDIT unreadability that justifies a visual redesign in S3.

---

## Hypothesis test

Target:

```text
OAMENI = Angajați, Pontaj, Evidență HR, Plăți, Avansuri
PRODUCȚIE = Atelier, Planificare, Rulări, compat action surfaces if justified
SISTEM / AUDIT = Ops-Graph, Reality Review
```

Confirmed:

- Plăți/Avansuri under Management is MISPLACED vs people-money task. OD-10 already says MOVE to Oameni. Moving the nav entry does not move Payment/Advance ownership.
- `/operator` and `/tablet` belong in Producție: they are the live action doors; Atelier is monitor. Shop-floor next-step already says so.
- Reality Review is **not** in primary nav. “Move to Sistem” would be a **new** sidebar item, not a move. Sales can already deep-link it.

Contradiction:

- Target IA also parks Harta + Guvernanță in SISTEM / AUDIT. Those items are **admin-only** today (`Administrare`). Ops-Graph is **manager+admin**. Putting Ops-Graph inside `Administrare` would either show manager an Administrare heading or hide Ops-Graph. That is why Option C is rejected.

---

## Roadmap checkpoint

```text
Roadmap awareness = 8/10
Where is S3 in the global simplification plan? = Wave 3 of S1–S8 (GS-09 + GS-10)
Cât sunt în direcția stabilită = 80%
Does S3 still offer high user value for low/medium risk? = YES
```

Value holds only if S3 stays a findability wave: people-money next to people; audit not pretending to be everyday production. It fails if it becomes “move menus until they look pretty,” invents Sistem as a Level-1 system, or adds Reality Review as a new primary door.

---

## Stop

Research complete. No implementation. No commit. No push. No S4.
