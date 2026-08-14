# Worklog — WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM V1

| Field | Value |
|-------|--------|
| Date | 2026-08-14 |
| GO | Global synthesis evidence commit V1 |
| Boundary | Docs / evidence only |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Owner DB mutations | 0 |
| Wave 0–2 commit | `4bc988c0` (pushed) |
| Wave 3 commit | `2af20f4e` (pushed) |
| Wave 4 commit | `9cbcc7e5` (pushed) |
| Wave 5 commit | `4018cf271cee156b8014f19c7928f7fd781cefa3` (pushed) |
| Synthesis commit | local evidence only (this GO); **PUSH = NO** |

## Done

- Waves 1–5 remotely closed at `4018cf27`. `WAVE_5_EVIDENCE = REMOTE_CLOSED`.
- `GLOBAL_AUDIT_PHASE = SUFFICIENT_FOR_SYNTHESIS`. No new domain audit.
- Global synthesis pack written under `docs/qa/workos-unification-and-simplification-program-v1/global-synthesis/`.
- Current model = **PARTIAL**. Target model = **DEFINED**. Level-1 systems = **7**.
- Recommended commercial teaching: Cerere → Intake V6 → Ofertă → Comandă. Product System = admin language.
- First implementation wave if Owner later authorizes: **S1** (nav / truth labeling). Not started.
- REV = **PASS_WITH_GAPS** (family-level route table; no silent finding drop).

## Evidence

Canonical: `global-synthesis/GLOBAL_SYNTHESIS_REPORT.md`  
REV: `global-synthesis/GLOBAL_CONSISTENCY_REVIEW.md`  
Registries: `orchestration/canonical/README.md` now points synthesis SoT for purpose / duplicate / legacy / backlog.

## Stop (synthesis, historical)

`NEXT_TASK = NOT_AUTHORIZED` was the synthesis close. Owner later authorized S1 only. Record below.

---

# S1 — Commercial truth and workflow honesty (2026-08-14)

| Field | Value |
|-------|--------|
| GO | `S1_COMMERCIAL_TRUTH_AND_WORKFLOW_HONESTY_V1` |
| Boundary | Frontend display / FLUX membership / readiness copy |
| Implementation | YES (labels only) |
| Unfreeze | NO (bounded display exception; freeze remains ON) |
| Owner DB mutations | 0 |
| Synthesis baseline | `506007a3` |
| Push | NO |

## Done

- GS-01: `COMMERCIAL_FLOW_STAGES` = Cereri → Oferte → Comenzi. Strip removed from Product System layout. Commercial breadcrumbs / next-step copy no longer teach Cerere → Produs.
- GS-02: V6 live rail uses Estimare curentă / Estimare cu TVA / Estimare netă. Amounts still from priced-quote-dry-run `commercial_totals`.
- GS-03: `ready_for_quote` display = Marcat intern. Enum/API/DB unchanged. No V6 join.
- Deferred: Lucrări sidebar Produse, Product System page title, `productsNextStepHint`.

## Runtime

- `/intake` admin+sales, light+dark: FLUX without Produse; sidebar Produse still there.
- `/quotes` sales light: same FLUX.
- `/intake-v6/IR-MSRB28PU/operator`: Estimare curentă **729,04 EUR** (Wave 2 live observation was 725,25 EUR; dry-run drifted independently of S1).
- Readiness card **Marcat intern** = 0. Non-ready **Nou** rows visible. No `ready_for_quote` list row (`STATE_NOT_REACHED` for row chip).

Evidence: `docs/qa/workos-unification-and-simplification-program-v1/s1-runtime/`.

## Stop (S1, historical)

`NEXT_TASK = NOT_AUTHORIZED` was the S1 close. Owner later authorized S2 only. Record below.

---

# S2 — Mock / demo / projection honesty (2026-08-14)

| Field | Value |
|-------|--------|
| GO | `S2_MOCK_DEMO_PROJECTION_HONESTY_V1` |
| Boundary | Reports copy; Documents nav entry + page honesty; HR records copy |
| Implementation | YES (display / nav display only) |
| Unfreeze | NO (bounded exception; freeze remains ON) |
| Owner DB mutations | 0 |
| OD-2 | APPROVED — REMOVE_FROM_PRIMARY_NAV + KEEP_ROUTE |
| Push | NO |

## Done

- GS-04: `/reports` title and banner = Proiecție operațională. Money label = Valoare comenzi 7z. Same API and KPI math.
- GS-05: Documente removed from Relații. `/documents` kept. Page = ÎN PREGĂTIRE. No store/API.
- GS-06: Evidență HR list/detail hybrid copy. Program labeled demonstrativ. `/employees` remains LIVE DB.

## Runtime

- `/reports` admin + sales: projection wording; Relatii without Documente.
- `/documents` direct route works; sidebar has no `/documents` link.
- `/employees-records` and `/employees-records/7`: live identity + demo dossier boundary.

Evidence: `docs/qa/workos-unification-and-simplification-program-v1/s2-runtime/`.

## Stop (S2, historical)

`NEXT_TASK = NOT_AUTHORIZED` was the S2 close. Owner later authorized S3 only. Record below.

---

# S3 — People-money navigation alignment (2026-08-14)

| Field | Value |
|-------|--------|
| GO | `S3_NAVIGATION_AND_INFORMATION_ARCHITECTURE_ALIGNMENT_V1` |
| Boundary | Primary nav grouping only (`SHELL_NAV_SECTIONS`) |
| Implementation | YES (findability; two menu items) |
| Unfreeze | NO (bounded nav-group exception; freeze remains ON) |
| OD-10 | APPROVED — Plăți + Avansuri → Oameni |
| Ops-Graph | OPTION B — keep in Producție with AUDIT |
| Owner DB mutations | 0 |
| Push | NO |

## Done

- GS-09: Plăți (`/employee-payments`) and Avansuri (`/employee-advances`) moved from Management to Oameni. Same `navKey`s, routes, and `canViewNav` filters.
- GS-10: DEFERRED_PARTIAL. Ops-Graph stays in Producție with existing AUDIT badge. No Sistem / Audit group.
- Reality Review remains deep-link only. `/operator` and `/tablet` remain ACTIVE_COMPAT. Product System stays Lucrări → Produse.

## Runtime

- Admin: Oameni = Angajați, Pontaj, Evidență HR, Plăți, Avansuri. Management = Control producție, Rapoarte.
- Manager: Oameni includes Plăți, not Avansuri. Direct `/employee-advances` still redirects to `/shop-floor`.
- Sales / operator: no money nav; direct payments still redirect to role home.
- Drawer 390px uses the same projected groups.

Evidence: `docs/qa/workos-unification-and-simplification-program-v1/s3-runtime/`.

## Stop (S3, historical)

`NEXT_TASK = NOT_AUTHORIZED` was the S3 close. Owner later authorized S4 Option B only. Record below.

---

# S4 — Technical-model leak reduction (2026-08-14)

| Field | Value |
|-------|--------|
| GO | `S4_TECHNICAL_MODEL_LEAK_REDUCTION_V1` |
| Option | B — Atelier/operator leaks + planning chrome demotion |
| Boundary | Display only. No i18n project. No execution/task logic. |
| Implementation | YES |
| Unfreeze | NO (bounded display exception; freeze remains ON) |
| Owner DB mutations | 0 |
| Push | NO |

## Done

- GS-15: Shop Floor breadcrumb → Atelier. Workcenter card titles use existing tablet station names (CNC, Lăcătușerie / Sudură, Modelare litere). P2 English chrome (`Blocked Jobs`, `tick #`) left in place.
- Operator primary task title never falls back to raw `node:` / `task:` id. Fallback: display_label → component label → `Task producție`.
- Component role badge uses existing Romanian role map, not `root product`.
- Release policy raw string moved into collapsed Detalii politică. Logic unchanged.
- Tablet routing explanation uses operation/station human names. Routing logic unchanged.
- Planning `/execution` first fold: capacity strip + EXECUTION PLAN strip collapsed under Detalii tehnice planificare. `NEEDS ASSIGNMENT TRUTH` → necesită atribuire. DEC-009 / IMPLEMENTED_INACTIVE retained inside details.
- Execution detail V2 truth panel collapsed under Detalii tehnice plan. Panel/model still exists.
- Machine-run `task_key` moved into per-participant Detalii tehnice. No live run existed at QA (`STATE_NOT_REACHED`).
- Intake V6 not reopened.

## Runtime

- `/shop-floor` admin light+dark: H1 + breadcrumb Atelier; WC titles human; no Shop Floor / CNC_ROUTING.
- `/operator` admin light: primary titles human (`T06 Claim Probe`); Producție permisă; policy in details.
- `/tablet/print` light+dark: routing `Operație … → Print` / `Rutare neconfirmată pentru …`.
- `/execution` admin dark: first fold operational; implementation chrome only after opening Detalii tehnice planificare.
- `/execution/92401`: V2 panel collapsed as Detalii tehnice plan.
- `/execution/machine-runs`: no active run.

Evidence: `docs/qa/workos-unification-and-simplification-program-v1/s4-runtime/`.

## Stop

`NEXT_TASK = NOT_AUTHORIZED`. Do not start S5. No push, PR, cleanup, or unfreeze.
