# BUILD: Intake V3 Operator Workspace — Runtime Connectivity Fix

**Date:** 2026-06-20  
**Build:** `BUILD_INTAKE_V3_OPERATOR_WORKSPACE_RUNTIME_CONNECTIVITY_FIX`  
**Status:** PASS

---

## 1. Verdict

**PASS** — Root cause was a **stale backend process** on port 8000 (pre–Phase 3 code). Current repo registers all operator routes correctly. Dev stack now detects and replaces stale backends; frontend shows actionable errors on HTTP 404.

---

## 2. Branch / HEAD

| Field | Before | After |
|-------|--------|-------|
| Branch | `local/integration-pr4-plus-svg-path` | same |
| HEAD | `434c4b538c5392c5849cc63f899af2ae6f0c2097` | _(updated at commit)_ |

---

## 3. Git status

**Before:** tracked clean; `?? tmp/`  
**After:** connectivity fix committed; `?? tmp/`

---

## 4. Runtime issue observed

Browser on `/intake-v3/e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf/operator`:

- SVG & Layers: **"Layer setup unavailable."** (`GET /layer-role-confirmation` → 404)
- Finishes: **Layer Finish Setup** → `HTTP 404: {"detail":"Not Found"}`

---

## 5. Root cause

| Hypothesis | Verdict |
|------------|---------|
| A. Endpoint not mounted in code | **No** — fresh `main.app` includes all routes |
| B. Frontend wrong URL | **No** — paths match backend prefix |
| C. Route prefix mismatch | **No** |
| **D. Stale backend process** | **Yes — primary** |
| E. Stale frontend | **No** — Vite proxy correct |
| F. Old workspace payload | **No** — workspace exists; routes 404 before handler |
| G. Routes in tests only | **No** — same router module |
| H. Wrong port/API base | **No** — proxy → :8000 |
| I. Auth masked as 404 | **No** — FastAPI route-not-found |

**Mechanism:** Multiple long-lived uvicorn instances on port 8000 from earlier sessions. `scripts/start-dev.ps1` reused any backend passing `/health` without checking OpenAPI for Phase 3+ routes. Stale OpenAPI had ~19 workspace paths; current code has **45** including `layer-finish-assignments`, `layer-role-confirmation`, `lighting-plan`.

---

## 6. Endpoints tested — BEFORE fix (live :8000)

| Endpoint | Status | Meaning |
|----------|--------|---------|
| `GET .../workspaces/{id}` | 200 | Stale server alive |
| `GET .../preview` | 200 | Stale preview OK |
| `GET .../layer-role-confirmation` | **404** | Route not in stale app |
| `GET .../layer-finish-assignments` | **404** | Route not in stale app |
| `GET .../layer-finish-assignments/targets` | **404** | Route not in stale app |
| `GET .../lighting-plan` | **404** | Route not in stale app |
| OpenAPI | Missing operator paths | Confirms stale build |

---

## 7. Fix implemented

1. **`scripts/start-dev.ps1`** — `Test-IntakeV3OperatorWorkspaceRoutesOk` + `Test-BackendDevReady`; if `/health` OK but operator routes missing, **stop stale PID** and start fresh backend.
2. **`backend/tests/test_intake_v3_operator_workspace_runtime_routes.py`** — asserts routes on real `main.app` + OpenAPI.
3. **`frontend/src/lib/intakeV3/operatorApiErrors.ts`** — maps HTTP 404 to restart-backend guidance.
4. **UI hooks** — `useIntakeV3OperatorWorkspace`, `IntakeV3OperatorLayerFinishSetup`, `IntakeV3OperatorLightingTab` use formatted errors.

No CostEngine, inventory, or new features.

---

## 8. Endpoints tested — AFTER fix (current code via TestClient)

Workspace `e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf`:

| Endpoint | Status |
|----------|--------|
| `GET .../layer-finish-assignments` | **200** |
| `GET .../layer-role-confirmation` | **200** |
| `GET .../lighting-plan` | **200** |

**Operator action:** Restart dev stack so port 8000 serves current code:

```powershell
.\scripts\start-dev.ps1
```

Stale-backend detection runs automatically on next start.

---

## 9. Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_operator_workspace_runtime_routes.py tests/test_intake_v3_layer_finish_assignments.py tests/test_intake_v3_printed_artwork_layer_finish.py tests/test_intake_v3_lighting_plan.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx src/lib/intakeV3/operatorApiErrors.test.ts
```

**Results:** backend **33/33 PASS**; frontend **24/24 PASS**

---

## 10. Manual smoke result

- Current application code serves operator routes (**200** on real workspace via TestClient).
- Live port 8000 on the audit machine still held ghost stale listeners until manual process cleanup; **`start-dev.ps1` fix prevents recurrence** by not reusing stale backends.
- After `.\scripts\start-dev.ps1`, browser should load layer role / finish / lighting without raw HTTP 404.

---

## 11. Boundary confirmations

| Boundary | ✓ |
|----------|---|
| No CostEngine | ✓ |
| No pricing coupling | ✓ |
| No inventory mutation | ✓ |
| No StockMovement | ✓ |
| No ExecutionTask/ExecutionPlan | ✓ |
| No PO/SupplierOrder | ✓ |
| Quote guarded preserved | ✓ |
| Materials read-only preserved | ✓ |
| Technical route preserved | ✓ |
| No Phase 6 work | ✓ |
| No push | ✓ |

---

## 12. Phase 6 safe now?

**Conditionally yes** — after restarting dev stack once so port 8000 runs commit `434c4b5+` with operator routes. Do **not** start Phase 6 until browser smoke confirms Finishes/Lighting tabs load without 404.
