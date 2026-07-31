# Track A — HR / Employee WIP Parking Review

**Mode:** READ-ONLY · recommendation only · **parking NOT performed**  
**Date:** 2026-07-31  
**Repo:** `C:\w\psiso`  
**Branch / SHA:** `feat/capacity-batch-20d-scoped-b-92401` / `a1c28854`

---

## Dirty classification

| Path | Class |
|------|-------|
| `backend/models/employees.py` | **HR/employee WIP** |
| `backend/routers/employees.py` | **HR/employee WIP** |
| `backend/services/employees.py` | **HR/employee WIP** |
| `backend/services/employee_productive_hours.py` | **HR/employee WIP** |
| `backend/tests/test_employee_lifecycle_foundation.py` | **HR/employee WIP** |
| `docs/qa/capacity-batch-*` | **docs/reporting** |
| `docs/qa/app-integrity-before-next-go/` | **docs/reporting** |
| `docs/qa/exact-state-before-next-go/` | **docs/reporting** |
| `docs/qa/operator-review-92401/` | **docs/reporting** (this GO) |
| Capacity / execution / dec009 product files | **clean** — none dirty |
| Frontend | **clean** |
| Generated/local config | **none** in status |
| Suspicious unknown product dirty | **none** |

**Diff scale (HR):** 5 files · +1405 / −952 vs HEAD.

---

## Safety net already present

| Item | Evidence |
|------|----------|
| `stash@{0}` | `wip-employee-unrelated` |
| Stash content | Same 5 files · same +1405/−952 stat |
| Relation to HEAD | Follow-on HR refactor on top of already-merged lifecycle foundation |

---

## Parking options (ranked)

| Option | Verdict | Why |
|--------|---------|-----|
| **A. `git restore` 5 employee files to HEAD** | **RECOMMENDED** | WIP already duplicated in `stash@{0}`; restores deterministic capacity checkout; no new stash needed |
| B. New stash | Unnecessary | Duplicate of `stash@{0}` |
| C. Separate branch now | Optional later | Resume HR on `feature/employee-lifecycle-foundation` from stash |
| D. Separate commit on capacity branch | **Do not** | Mixes HR into capacity lane |
| E. Leave untouched | Acceptable only if Owner accepts latent risk | Restarted backend can load WIP employee modules |
| F. Stop and ask Owner | Only if stash identity disputed | Not needed — stash matches |

**This GO did not run restore/stash/commit/checkout.**

---

## Recommendation to Owner

**Approve later (explicit Owner action):** restore the 5 HR files to HEAD, keep `stash@{0}`, resume HR on a separate branch/lane.

Until then: RO review of 92401 remains safe (no dirty files on ops-graph/materialize path), but parking is still the hygiene prerequisite for a clean capacity checkout.
