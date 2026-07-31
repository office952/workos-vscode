# Capacity Batch 18 — Track B: OR-07 Drawer Closure

**Mode:** Read-only UI / AppShell display-UX only · **no materialize** · **no invent** · **no mutation controls**  
**Date:** 2026-07-31  
**Route:** `http://127.0.0.1:3000/execution/ops-graph` (fixture `973010` / plan `12`)  
**Product:** `C:\w\psiso` / worktree `C:\w\psiso-or-07` (`office952/workos-vscode`)  
**Prior:** Batch 17 **ACCEPT WITH GAPS** · residual OR-07 AppShell nav occlusion at 390px

---

## Kickoff confirmation

| File | Ownership impact |
|------|------------------|
| `docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md` (workflow-adv) | UI display-only; no frontend business truth; fail-closed |
| `docs/workflow-adv/README.md` + `TERMINOLOGY.md` | Contract index / vocabulary |
| Batch 16 `operator-review.md` OR-07 | Narrow nav covers page — auto-close / content-first |
| Batch 17 `ui-clarity.md` · closure report | OR-07 named residual; P0 OR-01/02/04/06 already closed |
| `AGENTS.md` + `CI_PREFLIGHT_GATE.md` (psiso) | Scope + no CI-skip |

**Allowlist:** `frontend/src/App.tsx` · `frontend/src/App.test.tsx` · `docs/qa/capacity-batch-18/or-07-drawer-closure.md` · `screenshots/or-07/` · `capture-or-07.mjs`.  
**Non-goals:** Materialize POST · sessions/actuals invent · start/stop/assign/complete · Employee Mobile · CostEngine/Pricing/PD · fighting Track C `MaterializedOpsGraph.tsx` (OR-09) · densifying sequence · invent minutes/WC/machine.

```text
KICKOFF READ CONFIRMED — TRACK B OR-07 DRAWER CLOSURE AUTHORIZED (RO display / AppShell UX only)
```

---

## Gap → closure

| ID | Friction (Batch 16/17) | Track B fix |
|----|------------------------|-------------|
| OR-07 | Narrow (390px): AppShell nav rail (220px) occludes ops-graph; identity/tasks not first-fold | Narrow viewport uses **overlay nav drawer**, **starts closed** (content-first); Menu toggle in topbar; backdrop / route change / nav click closes; desktop rail unchanged |

Ops-graph page copy (title/identity/source IDs/warnings/null/owner-risk/RO) remains Batch 17 Track C surface — **not redefined** here. After OR-07, that surface is fully visible at 390px without fighting the nav.

---

## Behavior

| Viewport | Nav mode | Default | Ops-graph first fold |
|----------|----------|---------|----------------------|
| ≥ 768px | `data-nav-mode=rail` | Collapsible rail (existing) | Unchanged |
| &lt; 768px | `data-nav-mode=drawer` | `data-nav-drawer=closed` | Identity · source IDs · DEC-009 · metrics · RO warnings visible |
| Narrow open | Overlay + backdrop | Operator opens via Menu | Content dimmed; drawer dismissible |

Narrow topbar: Menu + WorkOS title; search + EnvironmentBanner chip hidden so Menu is not click-blocked (Staging chip previously overlapped the toggle).

---

## Read-only confirmation

| Control | Present on `/execution/ops-graph`? |
|---------|-------------------------------------|
| Start / stop / assign / complete | **No** |
| POST materialize | **No** |
| Employee Mobile chrome | **No** (desktop shell only; Employee Mobile routes remain standalone) |
| Refresh / Load orderId | Yes (GET only) |

AppShell change does not add mutation — only nav presentation.

---

## Coordination with Track C

| Item | Decision |
|------|----------|
| `MaterializedOpsGraph.tsx` | **Not touched** — Track C owns OR-09 EUR/ml labels |
| Shared risk | None for this PR; OR-07 is AppShell-only |
| Worktree | `C:\w\psiso-or-07` isolated from Track C branch on `C:\w\psiso` |

---

## Screenshots

| File | Viewport | Phase |
|------|----------|-------|
| [`screenshots/or-07/before-ops-graph-desktop.png`](screenshots/or-07/before-ops-graph-desktop.png) | 1440×1100 | Before |
| [`screenshots/or-07/before-ops-graph-narrow.png`](screenshots/or-07/before-ops-graph-narrow.png) | 390×900 | Before — nav occludes content |
| [`screenshots/or-07/before-ops-graph-narrow-content.png`](screenshots/or-07/before-ops-graph-narrow-content.png) | Content crop | Before |
| [`screenshots/or-07/after-ops-graph-desktop.png`](screenshots/or-07/after-ops-graph-desktop.png) | 1440×1100 | After — rail unchanged |
| [`screenshots/or-07/after-ops-graph-narrow.png`](screenshots/or-07/after-ops-graph-narrow.png) | 390×900 | After — drawer closed, content-first |
| [`screenshots/or-07/after-ops-graph-narrow-content.png`](screenshots/or-07/after-ops-graph-narrow-content.png) | Content crop | After |
| [`screenshots/or-07/after-ops-graph-narrow-drawer-open.png`](screenshots/or-07/after-ops-graph-narrow-drawer-open.png) | 390×900 | After — overlay open + backdrop |

Capture: `node docs/qa/capacity-batch-18/capture-or-07.mjs before|after [baseUrl]` (Playwright, GET-only).

---

## Tests

| Check | Result |
|-------|--------|
| `npx vitest run src/App.test.tsx` | **8 passed** |
| OR-07 case | Narrow ops-graph → drawer closed · Menu present · open/close via toggle + backdrop |
| Desktop rail | `data-nav-mode=rail` · no Menu toggle |

---

## Honest UI opinion

**OR-07 CLOSED.** At 390px the ops-graph is content-first: identity (`973010` / `12`), DEC-009 / accepted-risk null labels, metrics 12/0/0, and RO gates are visible without the nav rail stealing the fold. Nav remains available as an explicit overlay.

---

## Files changed

| Path | Role |
|------|------|
| `frontend/src/App.tsx` | Narrow overlay drawer · content-first default · topbar Menu |
| `frontend/src/App.test.tsx` | OR-07 + ThemeProvider harness · rail assertions |
| `docs/qa/capacity-batch-18/or-07-drawer-closure.md` | This report |
| `docs/qa/capacity-batch-18/capture-or-07.mjs` | Screenshot helper |
| `docs/qa/capacity-batch-18/screenshots/or-07/*` | Before/after evidence |

---

## SMART CODE COMPLIANCE

| Gate | Evidence |
|------|----------|
| No materialize | GET-only screenshots · no POST UI |
| No invent PT / minutes / WC / machine | AppShell only; page truth unchanged |
| No Employee Mobile / start-complete | No new mutation; Mobile routes still standalone |
| Frontend no business truth calc | Layout / chrome presentation only |
| Track C coordination | Did not edit `MaterializedOpsGraph.tsx` |
| RO operator surface | Drawer closed by default on ops-graph narrow |

---

## Return summary

| Item | Value |
|------|-------|
| **Closed** | **Y** |
| **Route** | `/execution/ops-graph` |
| **PR** | https://github.com/office952/workos-vscode/pull/36 |
| **SHA** | `29daa494` (tip; code `2b36e695`) |
| **Screenshots** | `docs/qa/capacity-batch-18/screenshots/or-07/{before,after}-*` |
