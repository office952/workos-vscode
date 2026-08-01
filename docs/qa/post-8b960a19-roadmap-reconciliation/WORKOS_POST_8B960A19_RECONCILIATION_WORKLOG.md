# WORKLOG — Post-8b960a19 Roadmap Reconciliation

## Status

`PASS WITH WARNINGS` — audit complete; docs-only commit local; **not pushed**.

## Mini-decizia

Large read-only audit after Capacity Batch + `8b960a19` to reconcile open decisions vs runtime and recommend one upstream materials Owner GO. No product implementation.

## Repo state înainte

```text
branch = feat/capacity-batch-20d-scoped-b-92401
HEAD   = 8b960a1955e72c64e36847d3b14a4df9c6142116
remote = same
ahead/behind = 0/0
stash@{0} = wip-employee-unrelated (intact)
no merge/rebase/amend
```

## Architecture readback

ProductDefinition → ProductAggregate → Snapshot V2 → ExecutionPlan envelope → Ops-graph RO. Frozen technical materials attach from `orders.snapshot_v2_json.product_aggregate_snapshot.materials`. Pricing/Inventory/HR/Mobile remain outside. EIC/product truth confirmation rules respected (no invent).

## Document drift

- App-flow Execution Plan still describes Step 9B NOT_STARTED and 12/17 fixture shapes.
- June 2026 Step9 semantic review anchored on 88002/plan2 — historical.
- Current operator surface is ops-graph for 92401/18/22.

## Commit history inspected

Capacity Batch chain through DEC-009 OD3 gate, ops-graph introduction, Batch 17–18 clarity, scoped-B MAT-02, topo-order `89e021c7`, materials honesty `7b23b209`, frozen materials `8b960a19`.

## Runtime proof

- GET `/api/v1/execution/plan/92401` → plan 13, 18 tasks, 22 frozen materials, null qty ×22
- GET materialization-audit → `already_materialized_in_envelope`, `post_materialize_allowed=false`
- SQLite: PA materials 22; PD roles 24; readiness key absent; reality_92401=0; authorize constant False
- Browser: honesty note + Nespecificată ×22; zeroQty display 0; metrics 18/0/0/DEC-009=A

## Source trace

Full 22-row matrix in `FROZEN_MATERIAL_SOURCE_TRACE_MATRIX.md`. formula_id on 20/22; duplicates are provenance/variant parallel; premount roles inactive.

## Decision reconciliation

See `OWNER_DECISION_STATUS_MATRIX.md`. DEC-009 remains blocked for further POST. DEC-004 closed. DEC-003 partial (sibling RETURN ops remain). DEC-008 realized via ops-graph.

## Quantity source analysis

Model A preferred where formula_id exists; Model D for formula-less sets; Model E rejected; active-variant Owner filter required before treating all 22 as concurrent requirements.

## Component ownership analysis

Dominant COMPONENT_OWNED; linked_module composition emits return/ACM families; Product Template must not silently become qty owner.

## Alternativele comparate

A recommended; B/C/D/E/F deferred or rejected — see `NEXT_BUILD_OPTIONS_AND_RECOMMENDATION.md`.

## Dead pieces

Classified without deletion — see report §33.

## Files created

Entire pack under `docs/qa/post-8b960a19-roadmap-reconciliation/` including screenshots.

## Files not modified

- backend/, frontend/, migrations, fixtures, product tests
- project_sources (absent / not copied)
- other QA packs
- stash
- decision registers outside this pack (no retrospective rewrite)

## Tests/checks

Live GET + SQLite RO + browser RO + CDP text proof.

## Tests not run

Full pytest / frontend test:ci (docs-only audit).

## Boundaries

No materialize, authorize, execute, sessions, actuals, inventory fill, procurement mutation, pricing lookup for technical qty, topo/SEQ changes, UI redesign, stash ops, push.

`BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False` confirmed.

## Stash confirmation

`stash@{0}: wip-employee-unrelated` untouched.

## Blockers

Upstream quantity/ownership/active-variant undecided; material→op absent; further materialize unauthorized.

## Warnings

Architecture doc lag; RETURN sibling ops in envelope; WC on PA not envelope; working tree still has unrelated untracked Capacity QA dirs (left alone).

## Roadmap awareness

Old roadmap not treated as live status; reconciled against tip + 92401.

## Next Owner GO

```text
OWNER GO — Upstream Material Quantity & Ownership Contract
```

## Direction score

**97/100%**

## Docs-only commit

| Field | Value |
|-------|-------|
| Message | `Reconcile post-capacity roadmap and material truth` |
| Scope | `docs/qa/post-8b960a19-roadmap-reconciliation/` only |
| SHA | local tip after this pack — verify with `git log -1 --oneline -- docs/qa/post-8b960a19-roadmap-reconciliation` |
| Ahead/behind after | **1 / 0** |
| Push | **not pushed** |
