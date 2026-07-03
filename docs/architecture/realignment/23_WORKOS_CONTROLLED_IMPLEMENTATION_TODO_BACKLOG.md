# 23 — WorkOS Controlled Implementation Todo Backlog

**Version:** 1.0.0  
**Status:** Prepared execution backlog for controlled implementation  
**Date:** 2026-06-30  
**Scope:** Convert the alignment plan into implementation-ready task groups with gates, evidence, and validation.

**Related:** [22_WORKOS_ALIGNMENT_EXECUTION_PLAN.md](./22_WORKOS_ALIGNMENT_EXECUTION_PLAN.md) · [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md) · [21_WORKOS_IMPLEMENTATION_ROUTE.md](./21_WORKOS_IMPLEMENTATION_ROUTE.md)

---

## 1. Purpose

This document is the executable todo layer for controlled WorkOS realignment.

It is intentionally more granular than the roadmap and more operational than the alignment plan.

Each task is prepared with:

1. a stable task id
2. implementation target
3. prerequisites
4. owner-go requirement
5. validation expectation
6. completion evidence

---

## 2. Execution rules

1. Never open a downstream implementation task while its upstream truth task is still red.
2. Never convert owner-unknown semantics into local defaults.
3. Prefer fresh controlled fixtures over mutating historical evidence.
4. Every completed task must leave behind a worklog or equivalent validation evidence.
5. No materialization, sessions, or assignment runtime without explicit owner GO.

---

## 3. Status legend

| Status | Meaning |
| ------ | ------- |
| `READY` | can be implemented now without new owner input |
| `PREPARED_BLOCKED_BY_OWNER` | technically prepared, blocked by owner decision |
| `PREPARED_BLOCKED_BY_UPSTREAM` | technically prepared, blocked by unfinished upstream slice |
| `WATCH_ONLY` | should be monitored, not implemented yet |

---

## 4. Implementation backlog

### Track A — Documentation and truth hygiene

#### TODO-A01 — Complete realignment status sync

- Status: `READY`
- Goal: remove remaining doc wording drift across roadmap-facing files.
- Targets: `docs/architecture/realignment/*.md`
- Prerequisites: none
- Actions:
1. scan for lingering `NOT STARTED` wording that contradicts preview/runtime truth
2. align Step 9 wording everywhere to preview / persist / materialization / sessions split
3. align Step 10 wording everywhere to MVP read-only truth, not full profitability
- Validation:
1. grep for conflicting status phrases
2. manual diff review on changed docs only
- Evidence of done:
1. synced docs index
2. worklog entry citing the changed files

#### TODO-A02 — Publish controlled backlog references

- Status: `READY`
- Goal: link this backlog from the docs that operators will actually open.
- Targets: `README.md`, `22_WORKOS_ALIGNMENT_EXECUTION_PLAN.md`
- Prerequisites: backlog doc exists
- Actions:
1. add cross-links to the backlog
2. keep wording explicit that this is execution backlog, not target architecture
- Validation:
1. clickable links resolve
- Evidence of done:
1. updated references in both files

### Track B — Read-only truth expansion

#### TODO-B01 — Add V2 chain summary to order detail

- Status: `READY`
- Goal: expose snapshot-to-plan truth on the order page, not only execution detail.
- Targets: `frontend/src/pages/Orders.tsx`, nearby components/api contracts
- Prerequisites:
1. existing read-only Step 9B truth layer on execution detail
2. stable order route for `88002`
- Actions:
1. show snapshot V2 presence and source code
2. show execution plan draft presence and counts when available
3. keep the surface read-only and clearly labeled
- Validation:
1. focused UI test for order detail rendering
2. browser verification on `/orders/88002`
- Evidence of done:
1. order detail shows snapshot/plan linkage without write actions

#### TODO-B02 — Add V2 snapshot truth card to quote detail surfaces

- Status: `READY`
- Goal: make the frozen snapshot state visible where quote review happens.
- Targets: quote detail components / routing surfaces used by quote review
- Prerequisites:
1. identify the canonical quote detail surface currently used in runtime
- Actions:
1. show accepted snapshot V2 id/code/status
2. show readiness and owner-decision warnings read-only
3. ensure no legacy `/price` output is misread as canonical V2 truth
- Validation:
1. focused browser verification on quote review path
2. narrow frontend typecheck if contracts change
- Evidence of done:
1. quote review page distinguishes preview vs frozen truth

#### TODO-B03 — Label remaining preview/audit-only execution surfaces

- Status: `READY`
- Goal: reduce `MISLEADING_UI` risk without opening write-paths.
- Targets: execution, orders, quotes, product preview surfaces
- Prerequisites: none
- Actions:
1. inventory labels that imply production truth
2. relabel them to preview, audit-only, internal, or legacy as appropriate
3. avoid redesign; adjust wording only
- Validation:
1. grep for key misleading labels
2. browser spot checks on affected routes
- Evidence of done:
1. no core V2 page implies preview data is official execution truth

### Track C — Owner decision packet preparation

#### TODO-C01 — Prepare DEC-003 owner packet

- Status: `READY`
- Goal: package the canonical RETURN operation decision for a fast owner answer.
- Targets: decision doc/worklog packet only
- Prerequisites: current task graph evidence collected
- Actions:
1. show current duplicate return-related operations
2. propose canonical path options with impact notes
3. isolate what changes in preview, persist, and materialization if each option is chosen
- Validation:
1. technical review of option table for completeness
- Evidence of done:
1. decision-ready packet with explicit ask

#### TODO-C02 — Prepare DEC-004 owner packet

- Status: `READY`
- Goal: package canonical painting path decision.
- Targets: decision doc/worklog packet only
- Prerequisites: inspect current painting occurrences in task/operation snapshots
- Actions:
1. show all painting-related occurrences and labels
2. separate product aggregate semantics from operational semantics
3. prepare owner options and consequences
- Validation:
1. evidence references point to current runtime and snapshot truth
- Evidence of done:
1. owner can answer without asking for another technical audit

#### TODO-C03 — Prepare DEC-005 and DEC-006 policy packet

- Status: `READY`
- Goal: package workcenter source policy and estimated minutes source policy together.
- Targets: decision doc/worklog packet only
- Prerequisites: current null workcenter / null minutes evidence available
- Actions:
1. show exact null coverage in current task graph
2. compare source-of-truth options: aggregate, registry, workcenter mapping, derived formulas
3. state which choices remain warnings vs blockers
- Validation:
1. packet maps directly to current `planned_tasks[]` gaps
- Evidence of done:
1. explicit policy table for owner GO

#### TODO-C04 — Prepare DEC-007 and DEC-009 packet

- Status: `READY`
- Goal: package dependency policy and materialization GO into one decision checkpoint.
- Targets: decision doc/worklog packet only
- Prerequisites:
1. current linear dependency evidence
2. materialization audit evidence
- Actions:
1. show current dependency model and its limitations
2. define minimum semantic bar for materialization GO
3. define negative cases that still block POST materialization
- Validation:
1. checklist can be used as go/no-go gate before implementation
- Evidence of done:
1. explicit materialization readiness gate outside code

### Track D — Upstream enrichment preparation

#### TODO-D01 — Map duplicate operation families

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: produce the concrete implementation map for duplicate canonicalization.
- Targets: product aggregate / task contract producing services
- Prerequisites:
1. DEC-003
2. DEC-004
3. current duplicate evidence from persisted order `88002`
- Actions:
1. list duplicate parent/module operation families
2. classify each as canonical, alias, derived, or non-operational
3. mark which ones affect task rule emission
- Validation:
1. fixture comparison before/after on preview only
- Evidence of done:
1. implementation map accepted before code changes

#### TODO-D02 — Prepare workcenter population slice

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: define the exact implementation slice for workcenter truth.
- Targets: aggregate/task contract builders and related schemas
- Prerequisites: DEC-005
- Actions:
1. decide source field per task family
2. define fallback policy explicitly
3. keep null when truth is unknown rather than inventing values
- Validation:
1. preview payload diff on fresh fixture
- Evidence of done:
1. workcenter population plan is code-ready

#### TODO-D03 — Prepare estimated minutes population slice

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: define the exact implementation slice for minutes truth.
- Targets: task contract builders / planning preview
- Prerequisites: DEC-006
- Actions:
1. choose source hierarchy for estimated minutes
2. define warning-only vs blocking cases
3. preserve `planning_minutes_source` provenance in payload
- Validation:
1. preview payload diff on fresh fixture
- Evidence of done:
1. minutes population plan is code-ready

#### TODO-D04 — Prepare DAG dependency slice

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: replace naive linear dependencies with approved DAG semantics.
- Targets: dependency assembly logic in task contract / execution preview path
- Prerequisites: DEC-007
- Actions:
1. define canonical predecessor rules by task family
2. define fan-in / fan-out constraints
3. mark invalid cycles as hard blockers
- Validation:
1. preview comparison on fresh fixture with dependency assertions
- Evidence of done:
1. DAG slice ready for controlled implementation

### Track E — Fresh fixture chain

#### TODO-E01 — Create fresh controlled V2 fixture

- Status: `PREPARED_BLOCKED_BY_UPSTREAM`
- Goal: avoid proving new semantics on stale historical evidence.
- Targets: controlled QA fixture only
- Prerequisites:
1. selected upstream enrichment slices complete
2. owner GO where required
- Actions:
1. create or refresh fixture intake
2. freeze snapshot V2
3. accept quote
4. convert to order snapshot V2
- Validation:
1. DB audit confirms fresh quote snapshot and order snapshot linkage
- Evidence of done:
1. new fixture order id and snapshot id recorded in worklog

#### TODO-E02 — Re-run Step 9 preview/persist on fresh fixture

- Status: `PREPARED_BLOCKED_BY_UPSTREAM`
- Goal: verify the improved chain before materialization.
- Targets: preview + persist endpoints only
- Prerequisites: TODO-E01 complete
- Actions:
1. preview execution plan V2
2. persist draft execution plan
3. run materialization audit GET
- Validation:
1. response evidence matches expected workcenter/minutes/dependency improvements
2. no new duplicate semantic regressions
- Evidence of done:
1. fresh fixture worklog with payload highlights

### Track F — Blocked runtime slices after GO

#### TODO-F01 — Controlled materialization implementation

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: open POST materialization only after semantic gate closure.
- Targets: materialization endpoint and audit agreement
- Prerequisites:
1. DEC-009
2. fresh fixture pass
- Actions:
1. execute POST materialization on approved fixture
2. verify idempotency and duplicate protection
3. verify readiness state after materialization
- Validation:
1. endpoint behavior checks
2. DB audit of resulting persisted truth
- Evidence of done:
1. operational task truth exists on approved fixture only

#### TODO-F02 — Workcenter/utilaj operational context

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: attach tasks to usable operational context after materialization.
- Targets: workcenter and utilaj linkage surfaces
- Prerequisites:
1. TODO-F01
2. workcenter policy implemented
- Actions:
1. map materialized tasks to workcenters
2. expose machine context where authoritative
3. keep capacity boundary non-commercial
- Validation:
1. runtime checks on execution/operator surfaces
- Evidence of done:
1. each operational task has coherent placement context

#### TODO-F03 — Sessions and execution actuals

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: record real execution on canonical V2 tasks only.
- Targets: start/end task flow, execution reality persistence
- Prerequisites:
1. TODO-F01
2. TODO-F02
- Actions:
1. connect start-task/end-task to materialized task truth
2. persist execution reality
3. guard non-materialized orders strictly
- Validation:
1. endpoint checks
2. DB audit of `execution_reality`
- Evidence of done:
1. non-zero execution reality on approved fixture

#### TODO-F04 — Actual profitability loop

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: finish actual post-job profitability without touching frozen commercial truth.
- Targets: profitability analysis services and UI consumers
- Prerequisites:
1. TODO-F03
- Actions:
1. keep accepted revenue frozen
2. compute actual cost from recorded execution truth
3. expose actual margin read-only
- Validation:
1. focused profitability checks on a session-backed order
- Evidence of done:
1. actual margin is no longer null on the controlled order

### Track G — Late cleanup and boundary enforcement

#### TODO-G01 — Pricing Registry separation

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: enforce commercial/internal/capacity boundary in registry UX.
- Targets: pricing registry UI and related labels
- Prerequisites:
1. stable V2 path after materialization and upstream truth improvements
- Actions:
1. split registry categories
2. relabel hourly/capacity entries
3. prevent V2 reliance on legacy pricing shortcuts
- Validation:
1. UI verification and targeted tests if present
- Evidence of done:
1. registry no longer suggests unified cost-plus pricing truth

#### TODO-G02 — Step 11 labeling sweep

- Status: `PREPARED_BLOCKED_BY_OWNER`
- Goal: finish labeling policy without redesign.
- Targets: core V2 routes
- Prerequisites: stable truth surfaces are present
- Actions:
1. label preview vs frozen vs internal vs audit-only vs legacy consistently
2. remove misleading wording from core pages
- Validation:
1. grep + browser sweep of core routes
- Evidence of done:
1. no open `MISLEADING_UI` findings on core paths

#### TODO-G03 — Dead pieces classification and cleanup packet

- Status: `WATCH_ONLY`
- Goal: prepare cleanup candidates, but do not remove them yet.
- Targets: legacy paths, dead code candidates, stale UI entry points
- Prerequisites: canonical V2 path stable enough to compare against legacy
- Actions:
1. classify candidates as active, compatibility, misleading, or dead
2. record evidence per candidate
3. do not delete anything without a separate owner decision
- Validation:
1. evidence list only
- Evidence of done:
1. cleanup packet ready for later owner review

---

## 5. Suggested execution order

Implement in this order unless owner explicitly overrides:

1. TODO-A01
2. TODO-A02
3. TODO-B01
4. TODO-B03
5. TODO-C01
6. TODO-C02
7. TODO-C03
8. TODO-C04
9. TODO-D01
10. TODO-D02
11. TODO-D03
12. TODO-D04
13. TODO-E01
14. TODO-E02
15. TODO-F01
16. TODO-F02
17. TODO-F03
18. TODO-F04
19. TODO-G01
20. TODO-G02
21. TODO-G03

---

## 6. Best next tasks right now

If implementation continues immediately without waiting for new business semantics, the best prepared tasks are:

1. TODO-A01 — remaining documentation truth sync
2. TODO-A02 — publish backlog references
3. TODO-B01 — add V2 chain summary to order detail
4. TODO-B03 — label remaining preview/audit-only surfaces
5. TODO-C01 / TODO-C02 / TODO-C03 / TODO-C04 — prepare owner decision packets

These are the highest-value tasks that keep the system moving without violating current governance.