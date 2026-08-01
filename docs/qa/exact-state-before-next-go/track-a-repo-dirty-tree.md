# Track A — Repo / Dirty Tree Truth

**Mode:** READ-ONLY  
**Date:** 2026-07-31  
**Repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**SHA:** `a1c28854`

---

## Identity

| Item | Value |
|------|-------|
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD | `a1c28854` — Merge PR #37 scoped-B 92401/13 |
| Tip ancestry | Capacity 14→18→20D stamp merges present |

---

## Dirty inventory (classified)

### Modified product code — **HR/employee WIP** (park separately)

| File | Class | Action |
|------|-------|--------|
| `backend/models/employees.py` | HR/employee WIP | **Park** — should not ride capacity GO |
| `backend/routers/employees.py` | HR/employee WIP | **Park** |
| `backend/services/employees.py` | HR/employee WIP | **Park** |
| `backend/services/employee_productive_hours.py` | HR/employee WIP | **Park** |
| `backend/tests/test_employee_lifecycle_foundation.py` | HR/employee WIP | **Park** |

**Diff scale:** 5 files · +1405 / −952 vs HEAD.  
**Not mixed** with capacity/execution/dec009 product files.  
**Preserved already** in `stash@{0}` (`wip-employee-unrelated`) with same 5-file stat — see Track G.

### Untracked — **docs/reporting only** (safe to leave / expected)

| Path | Class | Action |
|------|-------|--------|
| `docs/qa/capacity-batch-19/` … `20b/` | capacity/current batch expected (partial local QA) | Leave · Owner stamps live in handoff |
| `docs/qa/app-integrity-before-next-go/` | docs/reporting only (integrity GO) | Leave |
| `docs/qa/exact-state-before-next-go/` | docs/reporting only (this discovery) | Leave |

### Not present (clean)

| Class | Status |
|-------|--------|
| Capacity/execution/dec009 **product** dirty | **None** |
| Frontend dirty | **None** |
| Generated/local config dirty (`.env`, etc.) | **None** observed in `git status --short` |
| Suspicious unknown product files | **None** beyond HR WIP |

---

## Recent log (15)

```text
a1c28854 Merge PR #37 feat/capacity-batch-20d-scoped-b-92401
1454343b feat(execution): stamp scoped-B for FIX-DEC009-MAT-02 / 92401 / 13
73879218 fix(capacity): Batch 18 OR-09 …
ca1bd053 fix(ui): Batch 18 OR-07 …
… capacity 17 / 15 / 14d / 14b DEC-009 gate …
```

---

## Verdict

**Understood.** Only dangerous ambiguity is **HR WIP sitting on the capacity branch checkout**. Capacity product tree at HEAD is clean. QA untracked docs are expected reporting artifacts.

**Recommendation:** Park HR WIP before next capacity Owner GO (restore recommendation in Track G — discovery only; not applied here).
