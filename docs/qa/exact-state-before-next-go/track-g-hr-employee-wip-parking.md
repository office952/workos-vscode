# Track G — HR / Employee WIP Parking Recommendation

| Field | Value |
|-------|--------|
| Mode | **READ-ONLY** · git inspection only · no stash / branch / commit / checkout |
| Date | 2026-07-31 |
| Repo | `C:\w\psiso` |
| Branch / SHA | `feat/capacity-batch-20d-scoped-b-92401` · `a1c28854` |
| Scope | Dirty employee-lifecycle WIP vs capacity Batch 20 GO |
| Out of scope | Applying stash, branching, committing, or editing product code |

---

## Verdict

**PARK HR WIP BEFORE CAPACITY GO — restore clean working tree; work already preserved in `stash@{0}`.**

| Question | Answer |
|----------|--------|
| Which files are HR/employee WIP? | **5 modified backend files only** (see §1) |
| Mixed with capacity / execution / dec009 code? | **NO** — backend capacity/execution/dec009 paths are clean at HEAD |
| Safest next action | **`git restore` the 5 files to HEAD** (duplicate already in `stash@{0}: wip-employee-unrelated`) — do **not** leave dirty on capacity GO branch |
| Runtime / preflight risk if left dirty? | **Low–medium** — not on materialize/dec009 hot path, but employee + productive-hours modules are imported by `cost_engine_config`; restarted backend would run WIP code |
| Capacity GO blocker? | **NO** if tree restored to HEAD; **YES (hygiene)** if WIP left dirty during operator review |

---

## 1. Git status — employee WIP

```text
 M backend/models/employees.py
 M backend/routers/employees.py
 M backend/services/employee_productive_hours.py
 M backend/services/employees.py
 M backend/tests/test_employee_lifecycle_foundation.py
```

### Diff stat vs HEAD

```text
 backend/models/employees.py                        | 155 +++--
 backend/routers/employees.py                       | 764 ++++++++++-----------
 backend/services/employee_productive_hours.py      | 494 ++++++++-----
 backend/services/employees.py                      | 716 ++++++++++++-------
 .../tests/test_employee_lifecycle_foundation.py    | 228 +++---
 5 files changed, 1405 insertions(+), 952 deletions(-)
```

Large line churn (router Pydantic model relocation, docstrings, service reshaping) — **no dec009 / 92401 / materialize strings** in the employee-service diff.

---

## 2. Comparison to `feature/employee-lifecycle-foundation`

| Check | Result |
|-------|--------|
| `git diff HEAD feature/employee-lifecycle-foundation -- <5 files>` | **Empty** — committed HEAD already matches lifecycle branch for these paths |
| `git diff feature/employee-lifecycle-foundation -- <5 files>` | **Same 1405/952 stat** — all delta is **uncommitted working-tree WIP on top of merged foundation** |
| Merge-base | `e26e7918` (lifecycle branch tip is ancestor of current HEAD) |

WIP is **follow-on HR refactor**, not missing foundation merge.

---

## 3. Capacity / execution / dec009 cleanliness

| Area | Status |
|------|--------|
| Modified backend code | **Employee stack only** — no dirty `capacity`, `execution`, or `dec009` Python |
| Untracked QA docs | `docs/qa/capacity-batch-{19,20a,20a1,20a2,20b}/`, `docs/qa/app-integrity-before-next-go/` — **untracked only**, not mixed into employee diffs |
| Committed HEAD | Capacity Batch 20d scoped-B stamp at `a1c28854` — **GO-ready at commit layer** |

---

## 4. Existing stash (duplicate safety net)

| Stash | Content |
|-------|---------|
| `stash@{0}` | `On (no branch): wip-employee-unrelated` — **identical** to current working-tree diff on all 5 files |
| `stash@{2}` | Older WIP on `feature/employee-lifecycle-foundation` |

No new stash needed before GO; **`git restore` the 5 paths** is sufficient because `stash@{0}` already holds the same bytes.

---

## 5. Runtime / preflight risk assessment

| Surface | Risk if WIP left dirty |
|---------|-------------------------|
| `/execution/ops-graph` · DEC-009 materialize · 92401/13 | **None** — no dirty files on that path |
| Backend boot / import graph | **Low** — employee modules load; WIP changes behavior only if employee/cost-engine routes exercised |
| `cost_engine_config.py` imports | **Medium (latent)** — imports `employee_productive_hours` + `employees`; WIP could alter productive-hours or validity helpers if those endpoints/jobs run during review |
| Capacity preflight scripts | **Low** — no WIP in dec009/capacity modules; risk only if preflight suite runs full employee lifecycle tests |

**Conclusion:** WIP does **not** corrupt committed capacity GO state, but a **restarted dev backend** would serve unreviewed HR code — park before operator GO for deterministic runtime.

---

## 6. Recommended parking sequence (operator — not executed here)

1. Confirm `git diff stash@{0} -- <5 files>` is empty (already verified **IDENTICAL**).
2. `git restore backend/models/employees.py backend/routers/employees.py backend/services/employees.py backend/services/employee_productive_hours.py backend/tests/test_employee_lifecycle_foundation.py`
3. Verify `git status --short` shows **no** `M` under `backend/` before capacity GO.
4. Resume HR work later from `stash@{0}` on `feature/employee-lifecycle-foundation` (commit separately there).

**Do not:** commit HR WIP onto `feat/capacity-batch-20d-scoped-b-92401` · do not interleave with capacity QA doc commits.

---

## Evidence commands (read-only run)

```powershell
Set-Location C:\w\psiso
git status --short
git diff --stat HEAD -- backend/models/employees.py backend/routers/employees.py backend/services/employees.py backend/services/employee_productive_hours.py backend/tests/test_employee_lifecycle_foundation.py
git diff --stat HEAD feature/employee-lifecycle-foundation -- <same 5 files>
git stash show --stat 'stash@{0}'
git diff 'stash@{0}' -- <same 5 files>   # empty = IDENTICAL
```

---

## Track G stamp

**PARK BEFORE GO — restore 5 employee files to HEAD; WIP safe in `stash@{0}`.**
