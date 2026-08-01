# Track B — Batch Truth (20B→20E + Integrity Before Next GO)

**Mode:** READ-ONLY reconstruction · no product edits  
**Date:** 2026-07-31  
**Canonical repo:** `C:\w\psiso`  
**SHA (`main`):** `a1c28854` (PR #37 merged)  
**Sources:** handoff reports 20B–20E · `WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md` · `evidence/capacity-batch-20e/summary_batch_20e.json` · `authorize_flag_state_final.txt` · workflow-adv `docs/qa/capacity-batch-20e/*.md`

---

## Batch stamps (accepted state)

| Batch | Stamp | What closed |
|-------|-------|-------------|
| **20B** | **ACCEPT** | Auth package charter for `FIX-DEC009-MAT-02` / **92401** / plan **13** (docs only; no POST) |
| **20C** | **ACCEPT** | Scoped-B Owner **prep** (definition + include/forbid boundary; **no live stamp**) |
| **20D** | **ACCEPT** | **Live scoped-B stamp** for 92401/13/MAT-02 · OD3 identity `capacity-batch-20d/v1` · PR #37 |
| **20E** | **ACCEPT WITH WARNINGS** | Exactly **one** controlled materialize POST → **201** · 18 ops · authorize restored **false** |
| **Integrity** | **PASS WITH WARNINGS** | Post-20E audit: runtime/DB/boundaries/tests clean enough to plan next GO |

---

## Live operational state (post-20E + integrity)

| Surface | Value | Notes |
|---------|-------|-------|
| Ops **92401** / plan **13** | **18** | Materialized in 20E · activation `e6edbb80…` |
| Ops **973010** / plan **12** | **12** | Unchanged · activation `15bde334…` |
| Planned **92401** | **18** | Retained |
| Sessions | **0** | No session/pontaj tables · `no_sessions_created=true` |
| ExecutionActuals / `execution_reality` | **0** / **0** | Both orders |
| `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED` | **false** | Source + live (post hard restart) |
| `LIVE_DEC009` | **A / BLOCKED** | Fail-closed |
| Unauthorized POST 92401 / 973010 | **422** × 2 | Proven after restore |
| Scoped-B live identity | **92401 / 13 / FIX-DEC009-MAT-02** | MAT-01 historical · `allow_materialize=false` |

Evidence: `summary_batch_20e.json` · `authorize_flag_state_final.txt` · integrity DB section.

---

## Scope: live vs not live

| Dimension | Live now | Not live / forbidden |
|-----------|----------|----------------------|
| Scoped-B next-dry | **92401 / 13 / MAT-02** (`SCOPED_B_STAMPED`) | MAT-01 stamp **does not** cover 92401 |
| Materialize | **92401 done once** (18 ops) | Further POST **422** until new Owner GO |
| Authorize execute | **false** (restored) | Permanent True · general execute rollout |
| DEC-009 gate | **A / BLOCKED** | Auto execute · rematerialize 973010 |
| Sessions / actuals / Mobile | **0 / none** | Start-stop-assign · Employee Mobile · scheduling |
| Pricing / CostEngine / PD | Untouched | Minutes→price · commercial edits |
| UI | Ops-graph operational · no 92401 hardcode | Gap/badge productization · 92401 UI hardcode |

---

## Direct answers

| Question | Answer |
|----------|--------|
| **What was accepted?** | 20B auth package · 20C scoped-B prep · 20D live scoped-B stamp · 20E controlled materialize (18 ops) · integrity **PASS WITH WARNINGS** |
| **What remains warning?** | See §Warnings below |
| **What was explicitly not authorized?** | See §Not authorized below |
| **Live vs not live?** | Live: 92401 scoped-B + 18 materialized ops · 973010 historical 12 ops. Not live: sessions, actuals, Mobile, scheduling, general execute, further materialize |
| **Materialize already run?** | **Yes** — exactly once in 20E · `POST …/materialize-tasks/92401` → **HTTP 201** · ops **0→18** |
| **Authorize restored?** | **Yes** — `source_constant=False` · `live_batch_execute_materialize_authorized=False` · **422×2** after hard restart |
| **Sessions/actuals still 0?** | **Yes** — sessions **0** · reality **0/0** (92401/973010) per 20E + integrity |
| **Another execute forbidden until Owner GO?** | **Yes** — authorize **false** · DEC-009 **A** · unauthorized POST **422** · integrity recommends new explicit GO for any further materialize/execute |

---

## Warnings (carry forward)

| # | Warning | Source |
|---|---------|--------|
| 1 | Authorize reload lag — uvicorn reload missed False until hard restart; mid-window 92401 probe **409** | 20E §18 |
| 2 | `PLANNING_MINUTES_SOURCE_REQUIRED` on materialize response (planning honesty, not pricing) | 20E |
| 3 | F7 / minutes·WC null ×18 — do not invent | 20B–20E |
| 4 | UI-H1: ops-graph default fixture still **973010** (MAT-01) — do not “fix” by hardcoding 92401 | 20B–integrity |
| 5 | Unrelated dirty **employee-lifecycle** WIP on capacity branch checkout | Integrity |
| 6 | `project_sources/*` pack **missing on disk** | Integrity |
| 7 | Runtime: `svgpathtools` / intake_v5 import warning; browserslist stale | Integrity |
| 8 | Partial local `docs/qa/capacity-batch-20*` mirrors — handoff is Owner stamp home | Integrity |
| 9 | Track B G13 execute residuals (20B) — closed by 20D/20E for scoped-B path; general execute still gated | 20B |

---

## Explicitly not authorized (all batches + integrity)

| Category | Forbidden |
|----------|-----------|
| Execute / materialize | General execute rollout · auto execute · rematerialize **973010** · second POST **92401** without new GO |
| Operational | Sessions · ExecutionActuals · start/stop/assign/complete · Employee Mobile · scheduling |
| Truth / product | Invent minutes/WC/machine/deps/`task_rules` · Pricing/CostEngine/PD/Capacity formula edits |
| UI / direction | Hardcode 92401/MAT-02 UI · gap/badge productization · readiness cockpit as product |
| Scope | MAT-01 scoped-B reused as 92401 cover · any other `order_id` · permanent authorize **True** |

---

## Recommended next step (from reports — not a GO)

| Option | Status |
|--------|--------|
| Operator / read-model review of 92401 ops graph (`?orderId=92401`) | Suggested when Owner chooses |
| Sessions / Mobile / scheduling | **No** without new Owner GO |
| Further materialize / execute | **No** — requires new explicit Owner GO + authorize flip window |
| Park/clean HR dirty tree | Separate HR lane |

---

## Evidence pointers

| Artifact | Path |
|----------|------|
| 20B report | `C:\w\workos-atoms-ui-chrome-handoff\CAPACITY_BATCH_20B_AUTH_PACKAGE_92401_REPORT.md` |
| 20C report | `C:\w\workos-atoms-ui-chrome-handoff\CAPACITY_BATCH_20C_SCOPED_B_OWNER_AUTH_PREP_REPORT.md` |
| 20D report | `C:\w\workos-atoms-ui-chrome-handoff\CAPACITY_BATCH_20D_OWNER_STAMP_LIVE_SCOPED_B_REPORT.md` |
| 20E report | `C:\w\workos-atoms-ui-chrome-handoff\CAPACITY_BATCH_20E_CONTROLLED_SCOPED_B_MATERIALIZE_REPORT.md` |
| Integrity report | `C:\w\workos-atoms-ui-chrome-handoff\WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md` |
| 20E summary JSON | `C:\w\workos-atoms-ui-chrome-handoff\evidence\capacity-batch-20e\summary_batch_20e.json` |
| Authorize final | `C:\w\workos-atoms-ui-chrome-handoff\evidence\capacity-batch-20e\authorize_flag_state_final.txt` |
