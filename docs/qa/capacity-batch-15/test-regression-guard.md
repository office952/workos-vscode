# Capacity Batch 15 — Track C: Tests / Regression Guard

**Mode:** Pytest + Vitest + unauthorized POST probe (expect **422**) · **no successful materialize** · **no new ops**  
**Date:** 2026-07-29  
**Product:** `C:\w\psiso` (`office952/workos-vscode`) · branch coordination `fix/capacity-batch-15-ops-graph-ui`  
**Fixture:** `FIX-DEC009-MAT-01` · `973010` / plan `12`  
**Prior:** Batch 14D **ACCEPT** · Track A read-model QA present  
**Evidence:** `evidence/capacity-batch-15/` (shared with Track A; Track C added POST probe artifact)

---

## Kickoff confirmation (Smart Code / contracts)

| File | Ownership impact |
|------|------------------|
| `docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md` | Testing + API boundary + no invent |
| `docs/workflow-adv/README.md` | Contracts index; EIC finish line; no WorkOS import into Workflow-ADV product |
| `docs/workflow-adv/TERMINOLOGY.md` | Ops / PT / FREEZE vocabulary |
| `CAPACITY_BATCH_14D_OD3_LIVE_REVERIFY_GATE_HARDENING_REPORT.md` | Accepted baseline ops=12 · OD3 gate · no extra materialize |

**Allowlist:** backend regression tests · FE read-only UI tests (coord with Track B) · unauthorized POST probe · this report · evidence JSON  
**Non-goals:** successful materialize · authorize unlock · sessions/actuals · CostEngine/Pricing · Employee Mobile · invent minutes/WC/deps

```text
KICKOFF READ CONFIRMED — TRACK C IMPLEMENTATION AUTHORIZED (tests/QA only)
```

---

## 1. SHA / branch / preflight

| Item | Value | Class |
|------|-------|-------|
| Floor | ≥ PR #30 / `5e4027a3` | — |
| Local `HEAD` at test time | `5e4027a3` (main tip) | **PASS** |
| Working branch | `fix/capacity-batch-15-ops-graph-ui` (coord with Track B) | **PASS** |
| OD3 live | `gate_landed=true` · `identity_version=capacity-batch-14d/v1` · capability `execution.dec009_od3_gate` | **PASS** |
| Authorize | `batch_execute_materialize_authorized=false` · live DEC-009=`A` | **PASS** |
| Launcher `git_commit` | `a1b759c8` (known stamp lag; OD3 identity preferred) | WARN |

Evidence: `evidence/capacity-batch-15/local_compatibility.json` · `repo_sha.json`.

---

## 2. Tests run

### Backend (pytest)

```text
cd backend
.venv\Scripts\python.exe -m pytest \
  tests/test_capacity_batch_15_read_model_regression.py \
  tests/test_dec009_materialize_gate.py \
  tests/test_step9_materialization_audit.py::test_audit_returns_audit_only_mode \
  tests/test_system_local_compatibility.py::SystemLocalCompatibilityTest::test_endpoint_exposes_od3_runtime_identity \
  -q
→ 15 passed
```

New file: `backend/tests/test_capacity_batch_15_read_model_regression.py`

| Test | Asserts |
|------|---------|
| `test_batch_15_scoped_b_and_authorize_defaults_unchanged` | Scoped B `973010`/`12`/`FIX-DEC009-MAT-01`; authorize false |
| `test_batch_15_unauthorized_materialize_still_hard_rejects` | OD3 enforce → **422** `DEC009_MATERIALIZE_BLOCKED` |
| `test_batch_15_read_model_coherent_after_materialize` | After unit-bypass materialize: planned↔ops keys, deps, audit `already_materialized_*`, guards RO, reality unchanged |
| `test_batch_15_unauthorized_post_does_not_duplicate_ops` | Already-materialized + OD3 POST → **422**; ops count + `activation_hash` stable |

### Frontend (vitest)

```text
cd frontend
pnpm exec vitest run src/pages/MaterializedOpsGraph.test.tsx
→ 2 passed
```

Allowlisted in `frontend/scripts/ci-unit-tests.txt` (Track B + Track C).

| Assert | Result |
|--------|--------|
| Default order **973010** / fixture label / plan **12** | **PASS** |
| Metrics show ops **12**, sessions **0** | **PASS** |
| DEC-009=`A` strip | **PASS** |
| No Start / Stop / Assign / Complete / Materialize buttons | **PASS** |
| Employee Mobile **out of scope** | **PASS** |
| Error state on plan GET failure | **PASS** |

---

## 3. Live unauthorized POST probe (422 OK)

```text
POST /api/v1/execution/plan-v2/materialize-tasks/973010 → 422
error=DEC009_MATERIALIZE_BLOCKED
blockers=[live_dec009_A_blocked, batch_execute_materialize_not_authorized]
batch_execute_materialize_authorized=false
```

| After probe | Value | Class |
|-------------|-------|-------|
| GET plan `operational_tasks_count` | **12** | **PASS** |
| GET plan `tasks.length` | **12** | **PASS** |
| Audit `operational_tasks_in_envelope_count` | **12** | **PASS** |
| Audit status | `already_materialized_in_envelope` | **PASS** |
| `post_materialize_allowed` | `false` | **PASS** |
| Successful materialize (201) | **NONE** | **PASS** |

Evidence: `evidence/capacity-batch-15/post_unauthorized_973010.json` · refreshed `execution_plan_973010.json` · `materialization_audit_from_order_973010.json`.

**Note:** Track A intentionally issued no POST. Track C issued **one unauthorized probe only** (hard-reject). No envelope mutation; hash/`ops=12` unchanged vs Track A / 14D baseline `15bde334…`.

---

## 4. Ops remain 12 / no duplicate POST

| Check | Expected | Actual | Evidence | Class |
|-------|----------|--------|----------|-------|
| Ops count | 12 | 12 | plan + audit + Track A `summary.json` | **PASS** |
| Unique keys | 12 | 12 (Track A) | `summary.json` | **PASS** |
| Activation hash | `15bde334c5c6eb4ad1c5cd6adceac1bb` | same (Track A) | `summary.json` | **PASS** |
| Duplicate materialize | blocked | OD3 422 before 409 | POST probe + pytest | **PASS** |
| Unit: no cardinality inflate | stable | pytest | `test_batch_15_unauthorized_post_does_not_duplicate_ops` | **PASS** |

---

## 5. UI mutation controls

Track B surface: `/execution/ops-graph` (`MaterializedOpsGraph.tsx`) — read-only.

| Control class | Present? | Class |
|---------------|----------|-------|
| Start / Stop / Assign / Complete | **No** | **PASS** |
| Materialize button | **No** | **PASS** |
| Employee Mobile start/shop controls | **No** (footer + strip: out of scope) | **PASS** |
| Refresh / Load orderId (GET only) | Yes — navigation/read only | **PASS** |

Static/test evidence: `MaterializedOpsGraph.test.tsx` · screenshots under `docs/qa/capacity-batch-15/screenshots/` (Track B).

---

## 6. Git diff review

Working tree on `fix/capacity-batch-15-ops-graph-ui` (coordinated with Track B; not all Track C-owned):

| Path | Owner track | Role |
|------|-------------|------|
| `backend/tests/test_capacity_batch_15_read_model_regression.py` | **C** | New regression suite |
| `frontend/src/pages/MaterializedOpsGraph.test.tsx` | B+C | RO UI guards (+ Employee Mobile / materialize asserts) |
| `frontend/scripts/ci-unit-tests.txt` | B | Allowlist FE test |
| `frontend/src/pages/MaterializedOpsGraph.tsx` | B | RO ops graph page |
| `frontend/src/App.tsx` · `ExecutionDashboard.tsx` · `api/execution.ts` | B | Route + GET audit client types |
| `docs/qa/capacity-batch-15/screenshots/*` | B | Desktop/narrow shots |

**Scope verdict:** Narrow to Batch 15 read/visibility/tests. No CostEngine, no authorize flip, no materialize write-path redesign, no Employee Mobile enablement.

---

## Verification table (Track C)

| # | Check | Expected | Actual | Evidence | Class |
|---|-------|----------|--------|----------|-------|
| 1 | SHA / branch ≥ `5e4027a3` | floor met | `5e4027a3` | `repo_sha.json` / git | **PASS** |
| 2 | 14D accepted report read | ACCEPT baseline | read | 14D report | **PASS** |
| 3 | Runtime OD3 fresh proof | gate landed | true | `local_compatibility.json` | **PASS** |
| 4 | Fixture mapping 973010/12 | scoped B | unchanged constants + live plan | pytest + GET | **PASS** |
| 5 | Ops remain 12 | 12 | 12 | plan/audit/summary | **PASS** |
| 6 | No successful materialize | no 201 | 422 only | POST probe | **PASS** |
| 7 | Sessions 0 | 0 | 0 (Track A) | `summary.json` | **PASS** |
| 8 | ExecutionActuals 0 | 0 | reality 973010=0 | Track A | **PASS** |
| 9 | Unauthorized materialize blocked | 422 | 422 | probe + pytest | **PASS** |
| 10 | No duplicate ops after probe | still 12 | 12 | after GET | **PASS** |
| 11 | Read-model coherence tests | green | 15 pytest passed | command log above | **PASS** |
| 12 | UI no mutation controls | none | none | vitest | **PASS** |
| 13 | FE tests green | pass | 2/2 | vitest | **PASS** |
| 14 | Git diff scope | narrow | Batch 15 only | git status | **PASS** |
| 15 | Preflight authorize false | false | false | compat | **PASS** |

---

## PR / delivery

| Item | Status |
|------|--------|
| Backend regression tests | Landed on `test/capacity-batch-15-regression-guard` @ `07262fea` |
| Track C PR | https://github.com/office952/workos-vscode/pull/31 |
| FE tests | Remain on Track B WIP branch `fix/capacity-batch-15-ops-graph-ui` (avoid fight); green locally |
| Handoff report | This file (+ `docs/qa/…` in PR #31) |

---

## Stamp (Track C)

**PASS** — unauthorized materialize remains **422**; live ops remain **12**; backend regression suite green; FE RO/mutation guards green; no successful materialize in Batch 15 Track C.

### Remaining warnings (inherited, not regressions)

- F7 OD1 workcenter-null (Owner-accepted)
- Launcher `git_commit` lag vs HEAD
- `estimated_time_minutes` null + planning-source warn on most tasks (expected honesty)

### Blockers

**None** for Track C scope.
