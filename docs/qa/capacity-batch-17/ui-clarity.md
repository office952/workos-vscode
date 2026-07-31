# Capacity Batch 17 — Track C: UI Clarity / Operator Admin Surface

**Mode:** Read-only UI clarity only · **no materialize** · **no mutation controls**  
**Date:** 2026-07-31  
**Route:** `http://127.0.0.1:3000/execution/ops-graph` (fixture `973010` / plan `12`)  
**Product:** `C:\w\psiso` (`office952/workos-vscode`)  
**Prior:** Batch 16 **UNDERSTANDABLE_WITH_FRICTION** · Track B read-model PR #33

---

## Kickoff confirmation

| File | Ownership impact |
|------|------------------|
| `docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md` (workflow-adv) | UI display-only; no frontend business truth; fail-closed |
| `docs/workflow-adv/README.md` + `TERMINOLOGY.md` | Contract index / vocabulary |
| Batch 16 operator validation report (handoff) | Friction list OR-01…OR-06 to close |
| Track B `docs/qa/capacity-batch-17/read-model-clarity.md` | API honesty fields — consume, do not redefine |
| `AGENTS.md` + `CI_PREFLIGHT_GATE.md` (psiso) | Scope + no CI-skip |

**Allowlist:** `frontend/src/pages/MaterializedOpsGraph.tsx` · `.test.tsx` · `docs/qa/capacity-batch-17/ui-clarity.md` · `screenshots/` · capture script.  
**Non-goals:** Materialize POST · sessions/actuals invent · start/stop/assign/complete · Employee Mobile · CostEngine/Pricing/PD · fighting Track B API types · densifying sequence.

```text
KICKOFF READ CONFIRMED — TRACK C UI CLARITY AUTHORIZED (RO display only)
```

---

## Batch 16 friction → Track C close

| ID | Friction | Track C fix |
|----|----------|-------------|
| OR-01 | No status column | **Status** column — prefers Track B `read_clarity.lifecycle.display_label` (`materialized_pending_execution`) / raw `operational_status` |
| OR-02 | Machine col showed type while chips said `machine_code=null` | Split **Type** (`machine_type`) vs **Code** (`machine_code`) — never coalesce |
| OR-03 | Seq gap 11–12 unexplained | Sequence note from `ops_graph_read_clarity.sequence` or local gap scan — “absent (not invented)” |
| OR-04 | 5–6 warning chips × 12 rows | One compact **Gaps** tag per row (`min · plan-src · mach-code · WC · assignee · warn`); detail in `title` |
| OR-06 | `materialize=BLOCKED` vs already materialized | Strip copy: **further POST blocked** · **envelope=already materialized** |
| Mobile / production language | Employee Mobile + “Producție” breadcrumb | Removed Mobile strip line · breadcrumb **Execution** · title **Ops graph** · `execution=not active` |
| Badge noise | Long null chips | Short gap tags + page-level accepted-risks line |

---

## What the RO surface shows (live fixture)

| Field | Value | Source |
|-------|-------|--------|
| Fixture | `FIX-DEC009-MAT-01` | Identity strip |
| Order / plan | `973010` / `12` | GET plan |
| Ops tasks | **12** | plan / Track B counts_guard |
| Sessions | **0** | `audit.guards.creates_sessions === false` |
| Actuals | **0** | GET reality empty / 404→0 |
| DEC-009 | **A** · further POST blocked · envelope already materialized | dashboard-stats + audit |
| Execution | **not active** | RO surface assertion (no sessions/start) |
| Status | plan lifecycle (`pending` / `materialized_pending_execution`) | raw + Track B lifecycle |
| Sequence | `1…10,13,14` · gaps `11,12` | Track B sequence or local |

---

## Read-only confirmation

| Control | Present? |
|---------|----------|
| Start / stop / assign / complete | **No** |
| POST materialize | **No** |
| Employee Mobile controls / chrome | **No** |
| Refresh / Load orderId | Yes (GET only) |

Footer `ops-graph-readonly-footer` restates the contract.

---

## Empty / loading / error

| State | Behavior |
|-------|----------|
| Loading | Spinner + “Loading operational plan…” (`ops-graph-loading`) |
| Empty ops | Plan present, `tasks.length===0` (`ops-graph-empty`) |
| Error | Plan GET failure banner (`ops-graph-error`) |
| Soft audit miss | Plan still renders; Sessions `—` until audit |

---

## Coordination with Track B

- Rebased onto `origin/fix/capacity-batch-17-read-model-clarity` (PR #33).
- UI prefers `task.read_clarity` + `plan.ops_graph_read_clarity` when present.
- Fallback local gap/sequence logic remains if enrichment absent (stale backend).
- Does **not** redefine honesty classifications — display only.

---

## Screenshots

| File | Viewport | Phase |
|------|----------|-------|
| [`screenshots/before-ops-graph-desktop.png`](screenshots/before-ops-graph-desktop.png) | 1440×1100 | Before (Batch 15 UI) |
| [`screenshots/before-ops-graph-narrow.png`](screenshots/before-ops-graph-narrow.png) | 390×900 | Before |
| [`screenshots/before-ops-graph-narrow-content.png`](screenshots/before-ops-graph-narrow-content.png) | Content crop | Before |
| [`screenshots/after-ops-graph-desktop.png`](screenshots/after-ops-graph-desktop.png) | 1440×1100 | After Track C |
| [`screenshots/after-ops-graph-narrow.png`](screenshots/after-ops-graph-narrow.png) | 390×900 | After |
| [`screenshots/after-ops-graph-narrow-content.png`](screenshots/after-ops-graph-narrow-content.png) | Content crop | After |

Capture: `node docs/qa/capacity-batch-17/capture-ops-graph.mjs before|after` (Playwright, GET-only).

---

## Honest UI opinion

**Improved to UNDERSTANDABLE** for Operator/Admin review of the fixture graph.

- Identity, counts (12 / 0 / 0), DEC-009, and RO / no-execution state are first-fold clear.
- Type vs Code ends the machine assignment lie; Status ends the “no lifecycle” lie.
- Gap tags + page accepted-risks line keep honesty without chip wallpaper.
- Remaining friction: commercial strings inside some `display_name` values (backend labels, e.g. EUR/ml) — out of Track C scope; narrow viewport still shares AppShell drawer occlusion (OR-07).

Not a shop-floor status board — and it no longer pretends to be one.

---

## Files changed (Track C)

| Path | Role |
|------|------|
| `frontend/src/pages/MaterializedOpsGraph.tsx` | RO clarity UI · Track B consumer |
| `frontend/src/pages/MaterializedOpsGraph.test.tsx` | Unit tests (metrics · RO · gaps · errors) |
| `docs/qa/capacity-batch-17/ui-clarity.md` | This report |
| `docs/qa/capacity-batch-17/screenshots/*` | Before/after evidence |
| `docs/qa/capacity-batch-17/capture-ops-graph.mjs` | Screenshot helper |

Track B files (`execution_ops_graph_read_clarity.py`, API types, `read-model-clarity.md`) owned by PR #33 — present via rebase, not reauthored here.

---

## Tests

| Check | Result |
|-------|--------|
| `npx vitest run src/pages/MaterializedOpsGraph.test.tsx` | **3 passed** |
| Live GET plan `973010` | 200 · 12 tasks (pre-existing fixture) |
| Mutation controls in DOM | Absent (unit + design) |

---

## SMART CODE COMPLIANCE

| Gate | Evidence |
|------|----------|
| No materialize | GET plan + audit + reality only |
| No invent minutes/WC/machine_code | `—` + gap tags; Type ≠ Code |
| No densify sequence | Gaps listed explicitly |
| No Employee Mobile / start-complete | Removed chrome; no action buttons |
| Track B coordination | Rebased; consumes `read_clarity` |
| Frontend no business truth calc | Display + format only |
| RO operator surface | Footer + tests |

---

## Return summary

| Item | Value |
|------|-------|
| **Route** | `/execution/ops-graph` |
| **Files** | `MaterializedOpsGraph.tsx` · `.test.tsx` · `docs/qa/capacity-batch-17/ui-clarity.md` · screenshots |
| **RO** | **Confirmed** |
| **Screenshots** | `docs/qa/capacity-batch-17/screenshots/{before,after}-*` |
| **PR** | https://github.com/office952/workos-vscode/pull/34 (stacked on Track B #33) |
| **SHA** | `044c2dce` |
