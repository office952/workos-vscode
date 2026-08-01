# Track F — Product Direction & Operator Review Readiness

| Field | Value |
|-------|--------|
| Mode | **READ-ONLY** · no product-code edits |
| Date | 2026-07-31 |
| Repo | `C:\w\psiso` |
| Branch / SHA | `feat/capacity-batch-20d-scoped-b-92401` · `a1c28854` |
| Surface | `/execution/ops-graph` → `MaterializedOpsGraph.tsx` |
| Scope | FIX-DEC009-MAT-02 / **92401** / plan **13** vs prior MAT-01 **973010** |
| Out of scope | Employee Mobile · new authorize/execute · gap-app productization |

---

## Verdict

**PASS WITH WARNINGS — RO operator review of 92401 is SAFE and RECOMMENDED as the next single-purpose Owner GO.**

| Question | Answer |
|----------|--------|
| RO review 92401 safe (ops=18)? | **YES** — GET-only UI; sessions **0**; actuals **0**; authorize **false**; further POST **422** |
| UI operational vs gap/badge app? | **Operational** on ops-graph path; gaps are trailing honesty tags, not a queue |
| 973010 default fixture hardcode | **WARNING** (hygiene carry) — **not a blocker** |
| Hardcode 92401 / 13 / MAT-02 in UI? | **NO** |
| Next step | **RO operator review 92401** — park HR WIP separately; no product repair |

---

## 1. MaterializedOpsGraph fixture / hardcode check

| Item | 973010 / MAT-01 | 92401 / MAT-02 |
|------|-----------------|----------------|
| UI constant / hardcode | `FIX_DEC009_MAT_01_ORDER_ID = 973010` · label `FIX-DEC009-MAT-01` | **None** — no 92401 / 13 / MAT-02 strings in component |
| Default when `?orderId` omitted | Falls back to **973010** (`parseOrderId`) | Requires `?orderId=92401` or manual Load |
| Fixture shortcut button | **"Fixture 973010"** clears query → MAT-01 | **No** MAT-02 shortcut (by design — do not add) |
| `isFixture` badge | True only for 973010 or `ORD-FIX-DEC009-MAT-01` | Shows `fixture=—` for 92401 |
| Backend registry | `dec009_materialize_gate.py`: MAT-01 historical · `allow_materialize=false` | MAT-02 next-dry · `92401/13` · ops already written |

**973010 default:** **WARNING only.** Convenience for prior admin fixture; operator must explicitly load 92401. Must **not** be “fixed” by hardcoding a 92401 button.

---

## 2. RO operator review safety (92401 · ops=18)

| Check | Live / observed | Safe for RO? |
|-------|---------------|--------------|
| Ops envelope | **18** / plan **13** / activation `e6edbb80…` | **YES** |
| Sessions | **0** (no session tables) | **YES** |
| `execution_reality` | **0** rows for 92401 | **YES** |
| Authorize | `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = false` | **YES** |
| Further POST materialize | **422** DEC-009 for 92401 and 973010 | **YES** |
| Ops-graph mutations | Page is RO — no start/stop/assign/complete/POST | **YES** |
| Prior fixture regression | 973010 ops **12** · hash stable | **YES** |

RO review reads already-materialized truth; it cannot create ops, sessions, or actuals.

---

## 3. UI character — operational vs gap/badge-centric

| Surface | Primary focus | Gap/badge role | Direction fit |
|---------|---------------|----------------|---------------|
| `/execution/ops-graph` | Order identity · DEC-009 strip · **18-row ops table** (seq, status, task, process, WC, depends) · dependency order | Trailing **Gaps** column + accepted-risk copy (`—` / small tags) | **Operational** |
| `/execution` dashboard | Order list · link to ops-graph | CSS `gap-*` layout only | **Operational** |
| `/execution/:order_id` | Plan tasks · start/complete (separate path) | Operational readiness badge on plan | Historical; not expanded this batch |
| Product System / Intake lab | Frozen reference | NOT READY / readiness panels | **Out of scope** — do not expand |

Batch 20E made **zero** UI edits. Ops-graph remains an operator read-model over materialized tasks, not a readiness cockpit or gap queue.

---

## 4. Is ops-graph default 973010 a blocker or warning?

| Class | Rationale |
|-------|-----------|
| **WARNING** | Wrong default if operator opens bare `/execution/ops-graph` expecting 92401 — shows MAT-01 (12 ops) instead |
| **Not a blocker** | Query param `?orderId=92401` and Load input work; no 92401 data loss; no unsafe side effects; integrity audit PASS |

---

## 5. Operator inspect checklist — 92401

Open: **`/execution/ops-graph?orderId=92401`**

| # | Inspect | Expect |
|---|---------|--------|
| 1 | Identity strip | `order_id=92401` · `plan_id=13` · `fixture=—` (not MAT-01) |
| 2 | Metrics | Ops tasks **18** · Sessions **0** or **—** · Actuals **0** |
| 3 | DEC-009 strip | `already materialized (envelope)` · `further POST blocked (DEC-009)` |
| 4 | ExecutionPlanStatesStrip | Has operational tasks; execution **not active** on this page |
| 5 | Task table (18 rows) | Sequence contiguous or noted gaps · depends_on · lifecycle `pending`/plan status |
| 6 | Honest nulls | Minutes / WC / machine_code / assignee as **—** with gap tags (DEC-005/006/CAP-004/012 — not invented) |
| 7 | Labels (OR-09) | Process wording; EUR/ml commercial phrasing softened if present |
| 8 | Dependency order block | Root→leaf order matches planned graph |
| 9 | Audit warnings | `PLANNING_MINUTES_SOURCE_REQUIRED` etc. — backend honesty, not blockers for RO |
| 10 | Regression spot | Load 973010 separately — still **12** ops · unchanged hash |

**Do not** on this pass: POST materialize · authorize flip · start sessions · treat gap tags as a product backlog · expand gap UI.

---

## 6. Recommended next step

| Option | Verdict |
|--------|---------|
| **RO operator review 92401** | **RECOMMENDED** — single-purpose, safe, validates Batch 20E scoped-B outcome in UI |
| Park HR dirty WIP | **Do in parallel / before any mixed-scope GO** — unrelated employee-lifecycle diff on capacity branch |
| Product repair (973010 default, gap column) | **NOT NOW** — WARN carry only; no 92401 hardcode “fix” |
| New authorize + execute / rematerialize | **NO** — authorize false; POST blocked |
| Turn WorkOS into gap/badge app | **FORBIDDEN** |

**Sequence:** (1) Owner RO review 92401 via ops-graph + optional GET/API cross-check · (2) dispose HR WIP on separate lane · (3) only then consider a new explicit Owner GO if further materialize/execute is desired.

---

## Evidence pointers

| Source | Path |
|--------|------|
| Ops-graph component | `frontend/src/pages/MaterializedOpsGraph.tsx` |
| DEC-009 registry | `backend/services/dec009_materialize_gate.py` |
| DB / side effects | `docs/qa/app-integrity-before-next-go/database-side-effects-integrity.md` |
| Product direction | `docs/qa/app-integrity-before-next-go/product-direction-integrity.md` |
| Post-materialize counts | `docs/qa/capacity-batch-20e/post-materialize-operational-verification.md` (handoff evidence) |
| Integrated stamp | `docs/qa/app-integrity-before-next-go/WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md` |

---

## SMART CODE COMPLIANCE (track)

| Gate | Evidence |
|------|----------|
| Read-only / no product edits | This doc only |
| No invent minutes/WC/assign | Live nulls ×18 retained |
| No gap-app productization | Ops-graph operational primary; gaps trailing |
| No Employee Mobile scope | Out of scope |
| Further execute blocked | authorize false · POST 422 |

**Track F stamp: PASS WITH WARNINGS**
