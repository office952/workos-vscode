# Lane C — People / HR page cards

Read-only. No FINAL. C owns these cards.

## `/employees` — Angajați

| Field | Value |
|-------|--------|
| PURPOSE | Canonical operational employee master (identity, assignability, internal pay base, CostEngine labor fields) |
| PRIMARY USER | manager / admin |
| PRIMARY DECISION | Who exists, is active, is assignable, has cost-valid rates |
| SOURCE_OF_TRUTH | `GET /api/v1/entities/employees` |
| MUTATION_OWNER | Employee CRUD + operational-registry authorizations (not clicked) |
| DOWNSTREAM | Attendance roster, payments pay-base, advances roster, execution eligibility |
| Disposition | KEEP — densest HR page; copy separates payroll vs cost intern |

## `/attendance` — Pontaj

| Field | Value |
|-------|--------|
| PURPOSE | Internal attendance exceptions (default-present + manual events) |
| PRIMARY USER | manager / admin (nav); backend also operator |
| PRIMARY DECISION | Record absence/leave/overtime for a month |
| SOURCE_OF_TRUTH | `/api/v1/employee-attendance/summary` + events |
| Class | **ATTENDANCE_TRUTH** (not session, not payroll) |

## `/attendance/effects`

| Field | Value |
|-------|--------|
| PURPOSE | Generate/apply attendance effects from approved requests |
| Class | ATTENDANCE pipeline (request → effect → event) |
| Mutations | generate/apply exist — not clicked |

## `/employees-records` + `/:id` — Evidență HR

| Field | Value |
|-------|--------|
| PURPOSE | HR dossier UX (docs, medicina, alerte) |
| SOURCE_OF_TRUTH | Live names from employee master + **demo** docs/alerts/advances |
| MUTATION_OWNER | none |
| Class | **DEMO_DOSSIER_ON_REAL_EMPLOYEE** — detail `/employees-records/7` proven |

## `/employee-payments` — Plăți

| Field | Value |
|-------|--------|
| PURPOSE | Record tranșe 15/30 paid amounts |
| SOURCE_OF_TRUTH | `/api/v1/employee-payments/situation` (composes attendance + advances + pay base) |
| OWNS | payment records only |
| PRIMARY USER | manager / admin |

## `/employee-advances` — Avansuri

| Field | Value |
|-------|--------|
| PURPOSE | Internal debt ledger (avans / împrumut / reținere) |
| SOURCE_OF_TRUTH | `/api/v1/employee-balances/*` |
| PRIMARY USER | **admin only** |
