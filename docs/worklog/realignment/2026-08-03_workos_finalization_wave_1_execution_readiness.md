# WorkOS Finalization Wave 1 — Application truth + ExecutionPlan readiness UI

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 |
| Mini decision | Owner GO `FINALIZATION_WAVE_1` — audit + Step 9B RO UI + Decision Pack; DEC-009=A |
| Repo / worktree | canonical `C:\Users\offic\workos_app_vs` · worktree `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `bc5956c5` |
| Final HEAD | see `git rev-parse HEAD` after Wave 1 commit |
| Verdict | `FINALIZATION_WAVE_1 = COMPLETE` |

## Owner GO

```text
DEC-008 = A  (Step 9B read-only UI)
DEC-009 = A  (POST materialize blocked)
MATERIALIZATION = CLOSED
SCHEDULING = HOLD
ASSIGNMENT = CLOSED
SESSIONS = FROZEN
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
F7I rates = unchanged (already Owner-confirmed provisional)
```

## Preflight

```text
PREFLIGHT = PASS
HEAD = bc5956c5
tracked clean; untracked QA leftovers left untouched
FE :3000 + BE :8000 healthy (reuse)
```

## Capability inventory

| System | Classification |
| ------ | -------------- |
| Cursor subagents (explore) | AVAILABLE_AND_RELEVANT (A–D audit) |
| Terminal / git / pytest / vitest / eslint | AVAILABLE_AND_RELEVANT |
| cursor-ide-browser | AVAILABLE_AND_RELEVANT (UI proof) |
| Figma / Sentry / Datadog / Linear / Slack / PostHog | AVAILABLE_NOT_NEEDED / NOT_AUTHENTICATED |
| GitHub write | AVAILABLE_NOT_NEEDED (no push/PR) |
| Security rewrite tooling | AVAILABLE_NOT_NEEDED (proportional RO notes only) |

## Multi-agent method

```text
MULTI_AGENT_AVAILABLE = YES
Agent A — Architecture & Roadmap (explore)
Agent B — Backend & Runtime EP spine (explore)
Agent C — Frontend Execution UI (explore)
Agent D — QA / security / dead pieces (explore)
Coordinator — single writer for integration, tests, runtime, worklog, commit
```

## Current truth map (summary)

| Sistem | Stare |
| ------ | ----- |
| Intake V6 | PROVEN_WITH_GUARDS |
| ProductDefinition / Aggregate | PROVEN_WITH_GUARDS |
| Pricing Catalog + CPP (F7I.1) | PROVEN_WITH_GUARDS |
| EIC | PREVIEW_ONLY |
| Quote / Order Snapshot V2 | PROVEN_WITH_GUARDS |
| EP preview / persist | PROVEN_WITH_GUARDS |
| Materialization audit GET | READ_ONLY |
| Operational tasks / materialize | BLOCKED_BY_OWNER_DECISION (DEC-009=A) |
| Assignment / Sessions | FROZEN / blocked without GO |
| Employee Mobile | FROZEN_FINAL_FINAL |
| Legacy `/price` | LEGACY / DEAD_CANDIDATE (Step 12) |

### Completion levels

| Level | Before Wave 1 | After Wave 1 |
| ----- | ------------- | ------------ |
| L1 Commercial pilot | YES (provisional) | YES |
| L2 Execution planning transparent | PARTIAL | YES (detail + ops-graph honesty) |
| L3–L7 | NO | NO |

## Architecture readback

```text
technical operation source     = ProductAggregate.operations (frozen in Order Snapshot V2)
task contract source           = ProductAggregate.task_contract.task_rules[]
planned task construction      = execution_plan_v2_preview_service (from OS V2)
future operational tasks       = materialize from frozen planned_tasks[] (blocked)
```

**Contradiction resolved:** docs claiming EP driven by `ProductDefinition.processes[]` are `DOC_STATUS_STALE` for V2. Canonical driver is `task_contract.task_rules[]`.

## Status stale corrected

| Claim | Correction |
| ----- | ---------- |
| Step 9B NOT_STARTED | IMPLEMENTED (detail TruthPanel + ops-graph) |
| 7I / F7I NOT_STARTED | F7I.1 COMPLETE provisional |
| processes[] → EP | task_rules[] → EP |

## F7I regression

```text
F7I = RECONFIRMED
NO_F7I_CODE_CHANGE_REQUIRED
OWNER_CONFIRMED_RATES = 4/4 unchanged
```

Targeted pytest F7I + F7I.1 green. Known debts unchanged: linked_logo fixture drift; DISPLAY_RECONCILIATION polish; FINAL_PRICE_ANALYSIS deferred.

## Step 9B implementation

### Before
- `ExecutionPlanV2TruthPanel` orphaned; FE preview used GET vs BE POST
- `/execution/:order_id` framed as runnable “Rezultat execuție” with Start
- Gaps (WC/minutes/orphans/materialize closed) not first-class on detail

### After
- POST preview client fix
- Truth panel mounted on `/execution/:order_id`
- Romanian draft/audit banners; gap badges; orphan ops; deps column
- Session Start/Finalize gated: requires ops in envelope **and** `post_materialize_allowed=true` (always false under DEC-009=A)
- No Materialize / Assign buttons on this surface
- Docs 08 + 21 status sync

## UI proof (880811)

| Element | Evidence |
| ------- | -------- |
| URL | `http://127.0.0.1:3000/execution/880811` |
| Panel | `execution-plan-v2-truth-panel` |
| plan_id | 22 |
| planned_tasks | 5 |
| planned_operations | 10 |
| Status | `partial_missing_planning_minutes` · AUDIT_ONLY · `MATERIALIZED_IN_ENVELOPE · SESSIONS_FROZEN` |
| Gaps | MISSING_ESTIMATED_MINUTES · ORPHAN_NON_OPERATIONAL · MATERIALIZATION CLOSED |
| Actions | Start=0 · Materializează=0 · sessions-blocked notice |
| Light/day | PASS (AuditOnlyNotice light tokens present; app shell dark staging) |
| Dark | NOT_OFFICIALLY_SUPPORTED as separate product theme gate |
| Screenshot | local Cursor temp only — not committed |

## Runtime evidence

| Call | Result |
| ---- | ------ |
| GET pricing/registry | 200 |
| POST plan-v2/preview/880811 | 200 · tasks=5 · ops=10 · no_write=true |
| GET materialization-audit/880811 | 200 · plan=22 · ops_env=5 · post_allowed=false |
| POST preview/973019 | 200 · tasks=18 · ops=14 |
| GET audit/973019 | 200 · plan=21 · ops_env=18 · post_allowed=false |
| Side effects | none (GET audit / POST preview no_write) |

## Protected baselines (RO before=after)

| Order | total_amount | plan | snapshot sha256 prefix | pilot_gate |
| ----- | -----------: | ---: | ---------------------- | ---------- |
| 880811 | 1847.5 | 22 | `a59b6c44…` | closed |
| 973019 | 847.5 | 21 | `2d412e6e…` | N/A (protected forever) |

No accept/convert/reprice/materialize/assign/session.

## Tests

- FE: readiness helper + TruthPanel + ExecutionDetail Step 9B — green; lint green; added to `ci-unit-tests.txt`
- BE: F7I/F7I.1 + step9 audit + DEC-009 + EP preview — green (one preview UNIQUE flake classified INFRASTRUCTURE on first parallel run; passed on retry)

## Security / quality (proportional)

- Horizontal IDOR on order-scoped GETs remains OPEN (permission ≠ object ACL) — roadmap, not Wave 1 rewrite
- GET audit / POST preview no mutation observed
- DEC-009 closed in process; test bypass default-on noted as test risk

## Owner Decision Pack (Wave 2)

### DEC-001 — `svg_geometry_analysis`
| Field | Content |
| ----- | ------- |
| Problema | Contract/flag already non-operational; desktop owns geometry files |
| Variante | A non-op analytics · B merge READINESS · C separate task_rule |
| Recomandare | **A** |
| Confidence | high |
| Owner answer | Confirm A remains |
| Opens | none operational |
| Forbidden | SVG parse in WorkOS |

### DEC-002 — `premount_bar_preparation`
| Field | Content |
| ----- | ------- |
| Problema | Premount BOM vs conditional task |
| Variante | A BOM-only · B conditional task when premount active |
| Recomandare | **A** (current hard ban) unless Owner wants shop task |
| Confidence | high |
| Owner answer | Keep A or switch to B |
| Opens | Wave 2 only if B |

### DEC-003 — RETURN lateral ownership
| Field | Content |
| ----- | ------- |
| Problema | Parent vs module RETURN → duplicate materialization risk |
| Evidence | alias collapse coded; some envelopes still show siblings |
| Variante | A parent canonical · B module · C both (**double-exec risk**) |
| Recomandare | **A** |
| Confidence | high |
| Owner answer | Confirm A for Wave 2 enrichment |
| Opens | Wave 2 upstream ownership |

### DEC-004 — Painting ownership
| Field | Content |
| ----- | ------- |
| Variante | A parent painting · B module PAINTING · C both |
| Recomandare | **A** |
| Confidence | high |
| Owner answer | Confirm A |
| Opens | Wave 2 |

### DEC-005 — Workcenter source
| Field | Content |
| ----- | ------- |
| Problema | WC on Aggregate ops partial; nulls still appear on planned tasks |
| Variante | A enrich parent at compile · B map module alias · C manual after materialize · D registry-only · E controlled combo |
| Recomandare | **E** (A freeze into snapshot + D validation warnings) |
| Confidence | medium |
| Owner answer | Choose A/E |
| Opens | Wave 2 WC truth |

### DEC-006 — Estimated minutes
| Field | Content |
| ----- | ------- |
| Problema | All planning minutes null + `PLANNING_MINUTES_SOURCE_REQUIRED` |
| Variante | A null+warn · B dossier assumptions · C capacity registry · D planner manual · E hybrid |
| Recomandare | **A** until capacity model ready; then **E** (planning ≠ commercial hour) |
| Confidence | high |
| Owner answer | Confirm A for Wave 2/3 |
| Forbidden | commercial hourly sell rate |

### DEC-007 — Dependency model
| Field | Content |
| ----- | ------- |
| Problema | Process/catalog edges; unresolved DAG warnings; linear invent removed |
| Variante | A linear MVP · B finish-aware DAG · C parallel · D hybrid |
| Recomandare | **B** (finish-aware) with D policy for optional LED/folie branches |
| Confidence | medium |
| Owner answer | B or D |
| Example | simple: CNC→form→pack; +LED: after form; +paint: after form before pack; +folie/șablon: finish branch; +premount: BOM-only (DEC-002=A) |

### DEC-008
```text
DEC-008 = A — RECORDED + IMPLEMENTED this Wave
```

### DEC-009
```text
DEC-009 = A — KEEP until Wave 2 enrichment validated
Do not open B before DEC-003/004/005/007 + controlled fixture
```

**Minimum Owner answers to unlock Wave 2:** DEC-003, DEC-004, DEC-005, DEC-007 (and reconfirm DEC-006=A).

## Finalization roadmap (fresh)

| Wave | Objective | Entry | Owner | Forbidden | Exit |
| ---- | --------- | ----- | ----- | --------- | ---- |
| 1 | Truth + EP RO UI + Decision Pack | F7I.1 | DEC-008=A | materialize/sessions | **THIS BUILD** |
| 2 | Upstream task ownership + WC + deps + duplicate prevention | DEC-003/004/005/007 | those DECs | materialize | new fixture snapshot validated |
| 3 | Controlled materialization | Wave 2 exit + DEC-009=B | DEC-009=B | sessions/mobile | ops tasks on fixture |
| 4 | Workcenters/utilaje/capacity | Wave 3 | capacity GO | commercial hourly | WC resolvable |
| 5 | Employees eligibility | Wave 4 | HR GO | forced assign | eligibility RM |
| 6 | Assignment + scheduling | Wave 5 | assign GO | mobile | assigned fixture |
| 7 | Sessions + actuals | Wave 6 | sessions GO | quote reprice | actual minutes |
| 8 | Profitability | Wave 7 | profit GO | write-back quote | margins |
| 9 | Canonical UI labels | parallel late | labels GO | redesign | zero preview-as-official |
| 10 | Step 12 cleanup | stable pilot | per-piece | bulk delete | dead removed |
| 11 | Employee Mobile final-final | Waves 3–8 | mobile GO | early mobile | E2E |
| 12 | Pilot production verification | Wave 11 | release GO | silent scope creep | release readiness |

Parallelizable: Wave 9 labels with Wave 2 docs; commercial final pricing review **independent** of Waves 3–6 but not required to open DEC-009.

## Dead Pieces Check

```text
Dead pieces discovered: ExecutionPlanV2TruthPanel was DEAD_CANDIDATE (orphaned) — revived
Dead pieces touched: TruthPanel + hook (reactivated); legacy generatePlan CTA labeled
Dead pieces removed: NONE
Why removal was not allowed: Step 12 separate Owner GO
Step 12 impact: none
```

## DB / forbidden scope

No migration/reset/reseed. No SVG/DWG. No materialize/assign/session writes. No rate changes. No push/PR.

## Files changed (Wave 1)

- `frontend/src/api/execution.ts`
- `frontend/src/pages/ExecutionDetail.tsx`
- `frontend/src/pages/ExecutionDetail.step9b.test.tsx`
- `frontend/src/components/execution/ExecutionPlanV2TruthPanel.tsx` (+ test)
- `frontend/src/components/execution/executionPlanV2Readiness.ts` (+ test)
- `frontend/src/components/execution-result/WorkPanel.tsx`
- `frontend/scripts/ci-unit-tests.txt`
- `docs/architecture/app-flows/08_EXECUTION_PLAN_FLOW.md`
- `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
- this worklog

## Exact next step

```text
Do not start Wave 2 automatically.
Return Owner Decision Pack for DEC-001..007 and DEC-009.
Minimum for Wave 2: DEC-003, DEC-004, DEC-005, DEC-007.
Keep DEC-009=A until Wave 2 enrichment implemented and validated.
Wave 2 = canonical task ownership + workcenter source + dependency policy +
duplicate prevention + new-fixture snapshot validation — no materialize.
```

## Direction / completion scores

```text
direction alignment score = 88/100
operational completion score = 28/100
```

(L1 strong + L2 Wave 1; L3–L7 still closed.)

## Method / opinion

Audit-first with four read-only agents exposed the real gap: Step 9B pieces existed but were unwired / method-mismatched, so the operator detail page lied by looking runnable. Smallest coherent fix was reconnect + honesty gates + Decision Pack — not a redesign and not opening materialization. Result is usable for Owner decisions; the shop is still correctly closed.
