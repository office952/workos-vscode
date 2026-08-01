# Workspace / Git Integrity

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**SHA:** `a1c28854`

---

## Current state

| Item | Value |
|------|-------|
| Top-level | `C:/w/psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD | `a1c28854` — Merge PR #37 scoped-B 92401/13 |
| Ahead of remote tracking | `origin/feat/capacity-batch-20d-scoped-b-92401: ahead 1` (merge tip) |

### Recent log (10)

```text
a1c28854 Merge pull request #37 from office952/feat/capacity-batch-20d-scoped-b-92401
1454343b feat(execution): stamp scoped-B for FIX-DEC009-MAT-02 / 92401 / 13
73879218 fix(capacity): Batch 18 OR-09 EUR/ml ops-graph label closure (#35)
ca1bd053 fix(ui): Batch 18 OR-07 narrow AppShell drawer content-first (#36)
58f61dad Merge pull request #33 …
fdc5fd2a Merge pull request #34 …
24fb0a5a docs(qa): stamp Batch 17 Track C PR #34 and SHA
044c2dce fix(ui): Batch 17 Track C ops-graph operator clarity
d7eedf83 docs(qa): stamp Batch 17 Track B PR and SHA
cf6a0e1a fix(execution): enrich GET plan with ops-graph read clarity
```

---

## Dirty classification

### Modified (product code) — **unrelated / suspicious for capacity path**

| File | Classification | Notes |
|------|----------------|-------|
| `backend/models/employees.py` | **Unrelated WIP** | Large local diff vs HEAD (~HR lifecycle). Not part of Batches 20A–20E allowlist. |
| `backend/routers/employees.py` | **Unrelated WIP** | Same |
| `backend/services/employee_productive_hours.py` | **Unrelated WIP** | Same |
| `backend/services/employees.py` | **Unrelated WIP** | Same; still contains historical `is_valid_for_cost_engine` helper (pre-existing pattern; dirty looks like reformat/move). |
| `backend/tests/test_employee_lifecycle_foundation.py` | **Unrelated WIP** | Same |

**Diff scale:** 5 files, +1405 / −952 lines vs HEAD.  
**Not identical** to `feature/employee-lifecycle-foundation` tip either → local unfinished HR work sitting on the capacity branch checkout.

### Untracked (QA docs) — **expected from recent capacity batches**

| Path | Classification |
|------|----------------|
| `docs/qa/capacity-batch-19/` | Expected batch QA (partial local pack) |
| `docs/qa/capacity-batch-20a/` | Expected |
| `docs/qa/capacity-batch-20a1/` | Expected |
| `docs/qa/capacity-batch-20a2/` | Expected |
| `docs/qa/capacity-batch-20b/` | Expected (incomplete vs handoff; `readiness-gates.md` present) |

Canonical Owner reports for 20B–20E live primarily in  
`C:\w\workos-atoms-ui-chrome-handoff\` (not all mirrored into `psiso/docs/qa`).

---

## Folder integrity

| Folder / signal | Present? |
|-----------------|----------|
| `backend/` | Yes |
| `frontend/` | Yes |
| `docs/qa/` | Yes |
| `exports/` | Yes |
| `.github/` | Yes |
| `.workos-dev-detached.json` | Yes (live stack metadata) |
| Missing core app folders | **No** |
| Stale checkout behavior on this path | **No** — active branch, not detached |
| Cursor reinstall impact on contents | **Not observed** — repo contents, HEAD, and live stack intact |

---

## Context files requested (presence)

| File | Location / status |
|------|-------------------|
| `AGENTS.md` | **Present** in `C:\w\psiso` |
| `CI_PREFLIGHT_GATE.md` | **Present** in handoff `C:\w\workos-atoms-ui-chrome-handoff\` (+ rule `.cursor/rules/ci-preflight-gate.mdc`) |
| `CAPACITY_BATCH_20E_CONTROLLED_SCOPED_B_MATERIALIZE_REPORT.md` | **Present** in handoff (not in psiso root) |
| `CAPACITY_BATCH_20E_WORKLOG.md` | **Present** in handoff |
| `CAPACITY_BATCH_20D_OWNER_STAMP_LIVE_SCOPED_B_REPORT.md` | **Present** in handoff |
| `CAPACITY_BATCH_20C_SCOPED_B_OWNER_AUTH_PREP_REPORT.md` | **Present** in handoff |
| `CAPACITY_BATCH_20B_AUTH_PACKAGE_92401_REPORT.md` | **Present** in handoff |
| `project_sources/01-03_PRODUCT_DEFINITION_COMPILER.md` (and siblings) | **MISSING** under `C:\w\psiso`, handoff, and scanned `C:\w\*` neighbors — **not invented** |

---

## Verdict

**PASS WITH WARNINGS** — Workspace/git identity is sound and core folders intact. Warning: large unrelated employee-lifecycle dirty tree on the capacity branch must not be silently mixed into the next Owner GO.
