# BUILD: Intake V3 Operator Workspace — Phase 6 E2E Hardening Matrix

**Date:** 2026-06-20  
**Build:** `BUILD_INTAKE_V3_OPERATOR_WORKSPACE_PHASE6_E2E_HARDENING`  
**Status:** PASS

---

## 1. Verdict

**PASS** — Operator Workspace E2E hardening matrix covered via backend integration tests, frontend Vitest hardening block, and runtime smoke on live dev stack. No CostEngine, inventory mutation, execution, or PO side effects introduced.

---

## 2. Branch / HEAD

| Field | Before | After |
|-------|--------|-------|
| Branch | `local/integration-pr4-plus-svg-path` | same |
| HEAD | `758ac6bf0874b7412b475d9644f724486c3b2f2e` | _(updated at commit)_ |

---

## 3. Files changed

| Area | Files |
|------|-------|
| Backend fixtures | `backend/tests/fixtures/intake_v3/multi_layer_ten_layers.svg`, `README.md` |
| Backend E2E matrix | `backend/tests/test_intake_v3_operator_workspace_e2e_hardening.py` (new) |
| Frontend hardening | `frontend/src/pages/IntakeV3OperatorWorkspaceApp.test.tsx` (Phase 6 describe block) |
| QA | this document |

---

## 4. Scenarios covered

| ID | Scenario | Coverage |
|----|----------|----------|
| 6.1 | Simple one-color volumetric letters | Backend E2E — layer finish + non-illuminated + readiness |
| 6.2 | Multi-color same layer / sub-groups | Backend — free layer names + global fallback; sub-group detection documented as limited |
| 6.3 | Multi-layer SVG (10+ layers) | Backend fixture + targets/roles |
| 6.4 | Printed artwork / policromie | Backend (existing + E2E cross-check) |
| 6.5 | Return/Cant global fallback | Backend — `uses_native_layer_finish` false + global return depth |
| 6.6 | Dedicated Return/Cant layer | Backend — CANT layer finish assignment |
| 6.7 | Backing / support setup | Backend — Forex 10mm in finish summary |
| 6.8 | Lighting / LED / PSU | Backend — PSU auto sizes + workspace-level plan persistence |
| 6.9 | Missing geometry / manual fallback | Backend — `hub_missing_face_roll_width` blocks readiness |
| 6.10 | Stale geometry / propagation | Backend — quote propagation stale after layer reconfirm |
| 6.11 | Pending layer blocks quote | Backend — 422 on unconfirmed layer finish PATCH |
| 6.12 | Confirmed setup enables quote preview | Backend — readiness `can_create_quote` + enablement policy guarded |
| 6.13 | Materials read-only | Backend — material-availability boundary flags |
| 6.14 | Production Preview read-only | Backend — production-task-dry-run non-executable |
| 6.15 | Negative boundaries | Backend — no quote/order/plan/movement side effects on operator GETs |
| 6.16 | Runtime stale backend guard | Backend — OpenAPI path count + critical route presence |

Frontend Phase 6 block: all tabs load without HTTP 404 copy, production preview read-only banner, readiness→lighting repair jump, production setup without reservation actions.

---

## 5. Backend tests

```powershell
cd backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe -m pytest `
  tests/test_intake_v3_operator_workspace_e2e_hardening.py `
  tests/test_intake_v3_operator_workspace_runtime_routes.py `
  tests/test_intake_v3_layer_finish_assignments.py `
  tests/test_intake_v3_printed_artwork_layer_finish.py `
  tests/test_intake_v3_lighting_plan.py -q
```

**Result:** `53 passed`

---

## 6. Frontend tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx
```

**Result:** `26 passed`

---

## 7. Runtime smoke result

Dev stack reused (backend `:8000`, frontend `:3000`).

| Check | Result |
|-------|--------|
| `/health` | 200 |
| OpenAPI Phase 3–5 routes | PRESENT |
| Workspace `e8d5b5b8-…` GET endpoints | 200 (layer-finish, targets, lighting-plan) |
| UI operator route | No HTTP 404 / Layer setup unavailable (prior smoke PASS retained) |

Workspace shows legitimate lighting readiness blockers — business logic, not connectivity.

---

## 8. Negative boundary checks

| Boundary | Verified |
|----------|----------|
| No CostEngine coupling | material-availability `costengine_used: false` |
| No pricing final amount in Materials | no commercial price fields in operator materials paths |
| No inventory mutation | boundary flags + side-effect counts unchanged |
| No StockMovement | DB counts unchanged across operator GET matrix |
| No ExecutionTask / ExecutionPlan | dry-run `creates_execution_tasks: false` |
| No PO / SupplierOrder | boundary `creates_purchase_order: false` |
| Quote guarded | enablement policy `can_create_quote_now: false` even when readiness clear |
| Materials read-only | UI banner + API boundary |
| Technical route preserved | existing Vitest technical route test retained |

---

## 9. Known limitations / deferred items

- **SVG sub-group / color-group detection** within a single layer is not fully implemented; global finish fallback remains the safe path (documented in 6.2 test).
- **Dedicated cant layer without fixture** — covered via standard `LAYERED_SVG` CANT layer; no new business logic added.
- **Playwright operator E2E** — not added; pytest + Vitest + documented runtime smoke used instead (matches repo gate pattern).
- **Windows ghost listeners on `:8000`** — operational; `start-dev.ps1` OpenAPI guard from `758ac6b` remains the restart procedure.

---

## 10. Boundary confirmations

- No CostEngine changes
- No pricing commercial coupling
- No inventory mutation / StockMovement
- No ExecutionTask / ExecutionPlan creation from operator workspace
- No PurchaseOrder / SupplierOrder
- No push
- Technical route preserved

---

## 11. Operator Workspace maturity recommendation

| Question | Recommendation |
|----------|------------------|
| Ready for owner visual acceptance? | **Yes** — proceed with Atoms parity review on live workspace |
| Ready to make operator route default? | **Almost** — recommend owner sign-off after visual acceptance; keep technical route |
| Needs more cleanup? | Optional: Playwright smoke later; sub-group detection is future scope |
| Needs backup ZIP? | Optional before wider rollout — not required for this build |

---

## 12. Dev stack restart procedure (runtime guard)

If `/health` is OK but operator tabs show HTTP 404:

1. Run `.\scripts\start-dev.ps1` (kills stale backend missing OpenAPI routes).
2. Confirm OpenAPI workspace path count ≥ 30 and critical routes PRESENT.
3. Re-smoke workspace `e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf/operator`.
