# WORKOS F7A Owner Review v1 (+ Dashboard → Intake V6)

## Mini decision / overall verdict

```text
F7A IMPLEMENTATION REPORT = ACCEPTED PROVISIONALLY (as input only)
F7A OWNER REVIEW = PASS WITH DOCUMENTED WARNINGS
F7A CONTRACT QUALITY (alias / DAG / minutes / audit / zero-write) = INDEPENDENTLY VERIFIED
DEC-009 RECOMMENDATION = REMAIN A
F7B CONTROLLED MATERIALIZATION PILOT = NOT AUTHORIZED
POST MATERIALIZE DURING THIS REVIEW = NOT EXECUTED
Dashboard → Intake V6 = FAIL (separate UI track; not combined with F7B)
PUSH = NOT EXECUTED
Profitability = NOT READY
Production Ready = NU
```

## Identity

| Field | Expected | Observed |
|-------|----------|----------|
| Repo | `C:\w\psiso` | match |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` | match |
| HEAD | `6c3af83d` | `6c3af83d17d9b6be82ec92563955dbc67dcc8e11` |
| Remote | `0c8a76cd` | match |
| Ahead/behind | `0 / 2` | `0 / 2` |
| Stash | `wip-employee-unrelated` | intact (`stash@{0}`) |

## Working-tree classification

Preexisting untracked (excluded from review commit): U7/C4 docs, capacity-batch*, `_tmp*`, capture scripts, `_u6/_u7_capture.mjs`, etc.

Review evidence created under `docs/qa/workos-f7a-owner-review-v1/` (+ worklog). Capture helper `*.mjs` under that folder classified as tooling — **not** staged.

## Agents

| Agent | Role | ID / artifact |
|-------|------|----------------|
| Lead | Coordinator / consolidation / docs commit | this report |
| A | Architecture & contract | [Architecture](e4cbf4d1-fb36-4aab-a99d-74b67e8c89c6) → `AGENT_A_ARCHITECTURE_CONTRACT_REVIEW.md` |
| B | Runtime / tests / materialize safety | [Runtime](2443833c-f854-412b-936b-0be715102ce2) → `AGENT_B_RUNTIME_TESTS_SAFETY_REVIEW.md` |
| C | Dashboard → Intake V6 | [Dashboard](6825f407-bba6-4b9e-bf67-bcbe89aaf350) → `AGENT_C_DASHBOARD_INTAKE_V6_NAVIGATION_REVIEW.md` + screenshots |

## Commits reviewed

| Commit | Scope |
|--------|-------|
| `31495122` | Backend enrichment + F7A/golden tests + F7A QA |
| `6c3af83d` | F7A QA polish only |

Diff `0c8a76cd..6c3af83d`: **scoped** — no Pricing/HR/Mobile/UI/migrations/materialize service mutation.

## Why DEC-009 remains A (despite green alias/DAG/audit)

Owner B gate requires **all** of: registry-valid fixture WCs, hard premount safety, doc/contract honesty, and written Owner GO. Independent review found:

1. **WC fidelity gap** — fixture stamps `WC_CNC`; ORR / workforce seed uses `WC_CNC_ROUTING` (`REGISTRY_CNC_WORKCENTER_CODE`). Projection from Aggregate works; registry-canonical code not proven. (Transitional `WC_CNC` appears in older capacity tests/parity — not sufficient for B.)
2. **Premount** — BOM-only by fixture convention; no hard exclusion on composition-graph synthesis.
3. **Architecture docs lag** — 08/21/10 still describe linear DAG / pending DEC-003–005.
4. **Materialize never exercised** — audit-only proof ≠ authorize POST.
5. **Dashboard Intake V6 FAIL** — does not block DEC-009 technically, but proves operator entry is not ready; must not be bundled with F7B.

Fixture DAG itself is healthy: preview-native bond←face+side; `DAG_PROCESS_DEPENDENCIES_UNRESOLVED` **absent**.

## Dashboard → Intake V6 (Agent C)

```text
Canonical route = /intake-v6/operator
Dashboard CTA "Cerere Nouă" → /intake (legacy WorkIntake / Cereri)
Shell /intake-v6/* gated as demos → redirect /dashboard
Standalone /intake-v6-app/operator works but orphaned
Verdict = FAIL
Next UI GO = DASHBOARD → INTAKE V6 CANONICAL ENTRY FIX (separate; not with F7B)
```

Screenshots: `docs/qa/workos-f7a-owner-review-v1/screenshots/`.

## Readiness semantics

```text
v2_operational_ready = operational_tasks envelope materialized
NOT = scheduling ready
NOT = capacity ready
NOT = atelier-startable
NOT = Production Ready
```

F7A drafts remain non-materialized.

## Scores (post independent review)

| Dimension | Score |
|-----------|-------|
| Architecture | ≈75/100 |
| Functional spine | ≈72/100 |
| UI/UX (Dashboard entry) | ≈55/100 for Intake entry; shell Atelier home unchanged ≈70 |
| Direction | ≈73/100% |

## Next GO

```text
Functional: Owner written DEC-009 decision (remain A unless gaps closed) — NO auto F7B
UI: DASHBOARD → INTAKE V6 CANONICAL ENTRY FIX (separate build)
```

Do **not** start F7B until Owner writes `DEC-009=B` after gaps above are closed.
