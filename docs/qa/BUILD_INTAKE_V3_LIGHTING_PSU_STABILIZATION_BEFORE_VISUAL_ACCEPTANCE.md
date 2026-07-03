# BUILD — Intake V3 Lighting / PSU Stabilization Before Visual Acceptance

**Build:** `BUILD_INTAKE_V3_LIGHTING_PSU_STABILIZATION_BEFORE_VISUAL_ACCEPTANCE`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Prior verify:** `3e979a4` — verdict `NEEDS FIX`  
**Boundary:** No CostEngine, inventory, production tasks, UI recomposition, reserve policy change.

---

## 1. Context

Phase 5 lighting plan backend calculates correctly (`172.8 W` → `224.64 W` @ 30% → PSU `200+60=260 W`).  
Verify audit found frontend `proposePsuUnits()` proposed `360 W` (`160+200`) due to JavaScript array comparison with `<`.

This build stabilizes frontend PSU proposal before visual acceptance / Atoms recomposition.

---

## 2. Verdict inițial

`NEEDS FIX` — frontend PSU auto proposal diverged from backend/V2.

---

## 3. Root cause frontend PSU

**Location:** `frontend/src/lib/intakeV3/operatorLightingPlanForm.ts` — former inline greedy search.

**Bug:** `score(picked) < score(best)` compared **arrays** with `<`. In JavaScript this coerces arrays to strings and compares lexicographically, not numeric tuple order.

**Effect at 224.64 W required:**

| Candidate | Total | Chosen by buggy FE | Correct (BE/V2) |
|-----------|-------|--------------------|-----------------|
| 200 + 60 | 260 W | No | **Yes** |
| 160 + 200 | 360 W | **Yes** | No |

---

## 4. Fix PSU

**Change:** `proposePsuUnits()` now delegates to **`allocatePSUCombination()`** from `frontend/src/lib/workIntakeV2/psuAllocation.ts` — same algorithm as V2 operator flow and equivalent to backend `propose_psu_units()`.

**Why reuse instead of patch compare:** eliminates duplicate greedy implementation and prevents future drift.

**Files modified:**

- `frontend/src/lib/intakeV3/operatorLightingPlanForm.ts`
- `frontend/src/lib/intakeV3/operatorLightingPlanForm.test.ts`

**Backend:** unchanged (already correct).

---

## 5. Caz numeric obligatoriu

| Step | Value |
|------|-------|
| Module count | 120 (manual) |
| Module power | 1.44 W |
| Base load | **172.8 W** |
| Reserve | 30% |
| Required | **224.64 W** |
| PSU auto (after fix) | **1×200 W + 1×60 W = 260 W** |
| PSU reserve | **35.36 W** |
| Interzis | **160 + 200 = 360 W** |

Confirmed in:

- backend `test_realistic_120_module_led_psu_chain`
- frontend `proposePsuUnits(224.64)` + `planFromLightingForm` chain test

---

## 6. Reserve policy — V2 15% vs V3 30%

| | V2 | V3 Phase 5 |
|---|-----|------------|
| Constant | `PSU_HEADROOM_RATIO = 0.15` in `volumetricFrontlitIntake.ts` | `DEFAULT_RESERVE_PERCENT = 30` in backend + frontend |
| Status build | **Neschimbat** | **Neschimbat** |

**Owner decision required before commercial activation:**

1. Păstrăm **30%** ca regulă V3 (mai conservatoare) — recomandare implicită pentru acest sprint (backend deja verificat @ 30%).
2. Revenim la **15%** pentru paritate V2.
3. Facem **configurabil per workspace/template** (build separat).

**Duplicare:** `DEFAULT_RESERVE_PERCENT = 30` există în backend service + frontend form — documentat, fără refactor centralizare în acest build.

---

## 7. `module_count` — CONTRACT ONLY (nu implementat)

### V2 (sursă clară)

- **Formula:** `ceil(letter_perimeter_m × 1000 / pitch_mm)` where `pitch_mm = 75 + 25 = 100`.
- **Scope:** job-level total perimeter (not per-letter UI field).
- **`modules_per_letter`:** legacy CostEngine path only (`formula_handlers._handle_led_per_letter` legacy mode); **not** used in V2 `syncLightingPlanning`.
- **Fallback manual:** V2 UI marks `led_module_count` as computed when perimeter exists; manual discouraged via helper text.

### V3 actual

- **`module_count`:** required manual operator input on `lighting_plan`.
- **`modules_per_letter`:** stored in schema/UI, **no calculation effect**.
- **Geometry exists** in operator workspace (`geometryMetrics.total_letter_perimeter_ml`) but **Lighting tab does not consume it**; `intake_v3_lighting_plan_service` has **no perimeter integration**.

### De ce nu implementăm în acest build

| Condiție SAFE IMPLEMENT | Status |
|-------------------------|--------|
| V2 formula clear | Yes |
| V3 inputs available | Partial — geometry on separate API/state, not lighting contract |
| No schema migration | Would need `estimated_module_count` / derivation flags on lighting plan |
| Clear integration point | Missing — requires Lighting tab + backend `draft_lighting_plan` + fail-closed rules |
| Operator confirm/override | Needs UX contract (suggest vs auto-fill) |

**Decizie:** **Varianta 2 — CONTRACT ONLY**

**Build separat propus:** `BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES`

**Contract propus (pentru build viitor):**

1. Input: `total_letter_perimeter_ml` from geometry snapshot (fail-closed if missing).
2. Formula: reuse `computeLedModuleCountFromPerimeter(perimeter_m)` from `volumetricQuoteInput.ts`.
3. Output: prefill/suggest `module_count` on Lighting tab; operator confirms or overrides.
4. Backend: optional `draft_lighting_plan` suggestion from payload geometry snapshot when `module_count` null.
5. Tests: parity with V2 test (18.6 m → 186 modules @ pitch 100).

---

## 8. Teste rulate

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/operatorLightingPlanForm.test.ts src/pages/IntakeV3OperatorWorkspaceApp.test.tsx
```

Results:

| Suite | Result |
|-------|--------|
| `pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q` | **36 passed** |
| `vitest run operatorLightingPlanForm.test.ts IntakeV3OperatorWorkspaceApp.test.tsx` | **34 passed** |

---

## 9. Negative boundaries

- [x] No CostEngine changes
- [x] No inventory / StockMovement mutation
- [x] No ExecutionTask / ExecutionPlan
- [x] No PO / SupplierOrder
- [x] No UI recomposition / Atoms 3-step flow
- [x] No reserve 30% → 15% change
- [x] No invented module_count formula in this build
- [x] Materials preview remains read-only
- [x] Quote remains guarded by readiness
- [x] Technical route unchanged

---

## 10. Recomandare următor pas

1. **Owner confirmă 30% reserve** (sau planifică build de aliniere la 15%).
2. **`BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES`** — wiring perimeter → module_count suggest + operator confirm.
3. Apoi **visual acceptance** sau **`BUILD_OPERATOR_WORKSPACE_ATOMS_3_STEP_FLOW_RECOMPOSITION`**.

**Verdict build:** `PARTIAL — PSU fixed, reserve documented, module_count requires separate build`

---

## Related

- Prior audit: `docs/qa/VERIFY_INTAKE_V3_LIGHTING_PSU_CALCULATION_V2_PARITY.md`
