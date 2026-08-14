# Wave 5 report — Resources / Admin / HR

| Field | Value |
|-------|--------|
| Date | 2026-08-14 |
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM_V1` |
| Wave | `WAVE_5_RESOURCES_ADMIN_HR_AUDIT_V1` |
| Authorization | READ-ONLY AUDIT |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Baseline HEAD | `9cbcc7e556496c956c3466617cc4ee316f734662` |
| Remote parity | LOCAL=REMOTE, AHEAD=0, BEHIND=0 |
| Implementation | NO |
| Mutations (all listed domains) | 0 |
| Stack | detached start (`dev-detached.ps1`); `:3000` + `:8000` HTTP 200 |
| Next task | **NOT_AUTHORIZED** |

## Verdict

**PASS — support domain mapped; employee-record detail closed in gap closure.**

These pages do **not** form one coherent operational model. They are a **lateral belt** of real registries (employees, pontaj, payments, advances, inventory stock, pricing registry, machines) plus **placeholders** (documents, HR dossier demo, inventory automation) and **same-truth projections** (colaboratori vs inventory suppliers).

They do **not** replace Wave 2 sold-work, Wave 3 execution, or Wave 4 compiler spine.

Gap closure: `WAVE_5_GAP_CLOSURE_REPORT.md`. No page FINAL. No Wave 6. No implementation. No commit. No push.

## Scope

14 primary routes + attendance/effects + operational reports. Observer-only into commercial/execution.

## Orchestration

| Role | Status |
|------|--------|
| C | PASS — HR cards |
| E | PASS — resources/admin cards |
| F G H A B | PASS — observers |
| RT | PASS — 54/170, fail=0 |
| ORCH | PASS — this file |
| REV | PASS |

## Answer

Support systems accumulated **parallel pages and projections**. Core HR money/attendance/master boundaries are mostly **clear**. Documents and Evidență HR look more complete than they are. Colaboratori duplicates Inventory. Reports project live order money, not frozen snapshots.

## Top findings

1. `/employees` is the only live employee master.
2. Attendance ≠ session ≠ working (Wave 3 invariant holds on HR).
3. Payment ≠ advance ≠ labor cost — copy is honest; payments only read-compose.
4. Evidență HR = **DEMO_DOSSIER_ON_REAL_EMPLOYEE**; `/employees-records/:id` is **DEFINED_AND_REACHABLE** via row `<button>` (Wave 5 “no `<a>`” was a selector miss).
5. Colaboratori and Inventory Furnizori = **SAME_TRUTH_DIFFERENT_PROJECTION**.
6. `/documents` = **MOCK** (no store / upload / download).
7. Pricing registry ≠ official offer (Wave 2 snapshot still wins).
8. Utilaje catalog ≠ MachineRun.
9. `/reports` money = **LIVE_OPERATIONAL_PROJECTION** (`Orders.total_amount`; no snapshot).
10. Pontaj RBAC = **MIXED** — manager UI yes / API 403 proven; operator inverse.

## Stop

`COMMIT = NO`. `PUSH = NO`. `WAVE_6 = NOT_AUTHORIZED`.  
`WAVE_5_CLOSED = YES`. Evidence remains local until Owner asks to commit.
