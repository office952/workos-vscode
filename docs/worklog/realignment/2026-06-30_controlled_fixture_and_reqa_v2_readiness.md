# Controlled QA Fixture + Re-QA V2 Readiness Bindings — 2026-06-30

## 1. Status

**PASS**

Controlled local V2 fixture created in `dev.db` without DB reset. Re-QA verified all three Step 9.3.5.1 bindings with real data:

- ExecutionDetail readiness badge — **PASS**
- OperatorProductionBlueprintPanel readiness chip — **PASS**
- OperationalReports plan metrics — **PASS**

**Caveat:** UI verified at `v2_operational_ready` (post-materialize). `v2_not_materialized` browser state not captured in a separate pre-materialize pass (fixture persisted + materialized in one controlled run).

## 2. Scope

Controlled local QA fixture + manual Re-QA on `C:\Users\offic\Desktop\workos-active` only. Owner GO for fixture data in `dev.db` only. No code changes, no script changes, no commit, no push. Did not touch `C:\Users\offic\workos`.

## 3. Architecture readback summary

| Doc | Note |
|-----|------|
| `README.md` | Target-arch docs only; 7G+ needs owner GO |
| `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md` | Intake → Quote → Order → ExecutionPlan → Actuals |
| `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` | Frozen snapshot at order conversion |
| `10_EXECUTION_PLAN_TASK_GRAPH.md` | V2 envelope; plan from snapshot; no pricing in plan |
| `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md` | Actuals post-order; sessions separate |
| `16_PROFITABILITY_ANALYSIS.md` | Not in scope |
| `17_UI_NAVIGATION_AND_LABELING_POLICY.md` | Labels only for Step 11 |
| `18_GOVERNANCE_SETTINGS_POLICY.md` | Settings governance |
| `19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md` | Classify; no auto-delete |
| `20_ROADMAP_STEPS_7G_TO_12.md` | **7G runtime NOT STARTED** |

## 4. Fixture discovery

Scripts found (read-only audit):

| Script | Verdict |
|--------|---------|
| `backend/scripts/seed_commercial_e2e_fixture.py` | **NOT RUN** — uses QuoteOrchestrator, pricing/CostEngine path, runs global prerequisite seeds, deletes E2E fixture orders |
| `backend/scripts/seed_canonical_order_for_e2e.py` | **RUN** — idempotent INSERT/reuse one order; no DB reset; no migration |
| `backend/scripts/seed_sync_all.py` | **NOT RUN** — global seed |
| `backend/scripts/backfill_intake_v6_order_snapshots.py` | **NOT RUN** — backfill scope too broad |
| `backend/scripts/dev_seed_employee_mobile_sandu_fixture.py` | **NOT RUN** — mobile out of scope |

No dedicated dev script exists for V2 order + plan + materialize without commercial/pricing path.

## 5. Fixture selected

**Hybrid controlled approach (owner GO):**

1. `seed_canonical_order_for_e2e.py` — safe canonical order (`O-E2E-SPRINT33`)
2. Inline one-shot Python (not committed) importing existing test helper `tests.test_execution_plan_v2_preview._seed_v2_order_with_snapshot` + services:
   - `create_execution_plan_v2_from_order`
   - `materialize_execution_plan_v2_operational_tasks`

**Why safe:**

- No DB drop/reset/rebuild
- No migration
- No global seed sync
- No QuoteOrchestrator invocation in V2 path
- No ExecutionReality / session writes (`no_sessions_created: true` on materialize)
- Inserts/reuses scoped rows only (order `88001`, plan `1`)
- Uses frozen test OrderSnapshotV2 shape already validated in pytest

**Why not `seed_commercial_e2e_fixture.py`:** touches forbidden pricing/QuoteOrchestrator and runs volumetric price seeds.

## 6. Exact commands run

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'

# 1) Safe canonical order seed
.\.venv\Scripts\python.exe scripts\seed_canonical_order_for_e2e.py

# 2) Controlled V2 fixture (inline python -c, not committed)
#    - _seed_v2_order_with_snapshot(order_id=88001)
#    - create_execution_plan_v2_from_order(88001)
#    - materialize_execution_plan_v2_operational_tasks(88001)
```

**Note:** Attempt to generate legacy v1 plan for order `1` via `create_plan_from_order` failed with **412 GATE_PRECONDITION_FAILED** (BLK-08 canonical task types, BLK-09) — gate strict mode active. Did not bypass gate. V2 QA used order `88001` instead.

## 7. Data created/reused

| Entity | ID / value |
|--------|------------|
| Canonical order | `order_id=1`, code `O-E2E-SPRINT33` (created; no plan) |
| V2 QA order | `order_id=88001`, code `ORD-QA-V2-READINESS-88001` |
| Execution plan | `plan_id=1`, `plan_format=v2_envelope` |
| Operational tasks | `cnc_face_cut`, `electrical_wiring` (count **2**) |
| Backend readiness | `v2_operational_ready` |
| Materialize | `execution_tasks_created=true`, `no_sessions_created=true` |
| Operator tasks | `JOB-88001` tasks visible on `/operator` after materialize |

## 8. What I checked

### Pre-flight

| Check | Result |
|-------|--------|
| Git clean except worklogs | **PASS** |
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `37ada83` |
| Backend :8000 PID 40396 | healthy |
| Frontend :3000 PID 29544 | HTTP 200 |

### Backend API validation

| URL | Status | Key fields |
|-----|--------|------------|
| `GET /api/v1/execution/plan/88001` | **200** | `operational_readiness_status=v2_operational_ready`, `operational_tasks_count=2`, `plan_format=v2_envelope`, `execution_tasks_created=true` |
| `GET /api/v1/operator/orders/88001/production-blueprint` | **200** | `operational_readiness_status=v2_operational_ready`, `operational_tasks_count=2` |
| `GET /api/v1/operational-reports/summary` | **200** | `plan_operational_tasks_total=2`, `plan_orders_v2_not_materialized=0` |
| `GET /health` | **200** | unchanged |

### Browser Re-QA

#### A. ExecutionDetail — **PASS**

| Item | Result |
|------|--------|
| URL | `http://127.0.0.1:3000/execution/88001` |
| Page load | OK |
| `execution-plan-operational-readiness` | **Present** |
| Badge text | `Operational tasks ready` |
| Backend alignment | Matches `v2_operational_ready` |
| Tasks in plan | 2 operational tasks shown (not `planned_tasks[]` fallback) |
| Console | No blocking errors |
| Network | Plan loads; gate card shows BLOCKED for re-generation (plan exists) — expected |

#### B. OperatorProductionBlueprintPanel — **PASS**

| Item | Result |
|------|--------|
| URL | `http://127.0.0.1:3000/operator` |
| Panel mounted | **Yes** (`operator-production-blueprint-panel`) |
| `operator-blueprint-operational-readiness` | **Present** |
| Chip text | `Operational tasks ready` |
| Backend alignment | Matches blueprint API |
| Operator tasks | Face CNC Cut, Electrical Wiring for JOB-88001 |
| Layout | No major shift observed |

#### C. OperationalReports — **PASS**

| Item | Result |
|------|--------|
| URL | `http://127.0.0.1:3000/reports/operational` |
| Taskuri operaționale plan | **2** |
| Comenzi V2 nematerializate | **0** |
| Coherent with fixture | Yes (materialized V2 plan) |

## 9. What I did not check

- `v2_not_materialized` badge text in browser (pre-materialize snapshot)
- Employee Mobile
- Pricing / `/price` / CostEngine / QuoteOrchestrator runtime
- ExecutionReality / session start
- Step 7G / 10 / 11 / 12
- `seed_commercial_e2e_fixture.py` execution
- Automated test suites

## 10. Files changed

| File | Change | In scope | Commit |
|------|--------|----------|--------|
| `docs/worklog/realignment/2026-06-30_controlled_fixture_and_reqa_v2_readiness.md` | Created (this file) | YES | none |
| `backend/dev.db` | Local fixture rows inserted | YES (owner GO) | not tracked |

No other repo files modified. Accidental script file created during session was deleted before completion.

## 11. Tests / validation

| Action | Result |
|--------|--------|
| Fixture audit (read-only) | PASS |
| `seed_canonical_order_for_e2e.py` | PASS (order 1 created) |
| V2 inline fixture | PASS |
| Backend API probes | PASS |
| Browser Re-QA (3 zones) | PASS |
| pytest / validate:frontend | Not run |

## 12. Runtime status

| Service | PID | Status |
|---------|-----|--------|
| Backend :8000 | 40396 | healthy |
| Frontend :3000 | 29544 | HTTP 200 |
| Duplicate backend | None | |

## 13. Console / network findings

- No Vite overlay or blocking console errors on QA pages
- ExecutionDetail gate card shows blockers for **re-generating** plan when plan already exists — not a readiness binding defect
- Operational reports summary loads without 4xx
- Operator tasks loaded from live DB after materialize

## 14. Commit

**No commit created.**

## 15. Forbidden path confirmation

| Constraint | Confirmed |
|------------|-----------|
| No mobile | YES |
| No pricing / `/price` touched in fixture path | YES (V2 test snapshot only) |
| No CostEngine / QuoteOrchestrator in V2 fixture path | YES |
| No ExecutionReality / sessions | YES (`no_sessions_created`) |
| No DB reset | YES |
| No global reseed | YES |
| No migrations | YES |
| No push | YES |
| No redesign | YES |
| No backend/frontend implementation | YES |
| No script file changes committed | YES |
| No `C:\Users\offic\workos` | YES |

## 16. What remains

1. Optional: separate QA pass for `v2_not_materialized` UI label before materialize
2. Canonical order `1` plan generation blocked by gate — separate owner decision if legacy path needed
3. Deferred UI slices: OperatorView/ShopFloor `order_operational_readiness`, Dashboard/Reports
4. Commit worklogs when owner approves docs commits
5. Dedicated idempotent `scripts/seed_qa_v2_readiness_fixture.py` could be added later (out of scope)

## 17. Owner decisions needed

1. Approve dedicated QA seed script in repo (optional, cleaner than test-helper import)
2. Next slice: **A** OperatorView/ShopFloor binding vs **C** 9.3.6 audit vs **D** Step 10 audit
3. Whether to commit worklogs under `docs/worklog/realignment/`

## 18. Next recommended step

**Owner decision** for next slice (no auto-implementation):

- **A.** Minimal UI binding slice 2 — OperatorView/ShopFloor `order_operational_readiness` chips
- **B.** Dashboard/Reports empty-state helper text
- **C.** Step 9.3.6 `operational_reality_review` audit
- **D.** Step 10 actuals/profitability hardening audit

## 19. Direction score

**Cat sunt in directia stabilita: 86/100%**

- Step 9.3.5.1 bindings verified end-to-end with real V2 fixture
- Runtime green throughout
- 7G runtime still not started (by design)
- Fixture path used test helper import — acceptable for QA but not yet a first-class dev script
