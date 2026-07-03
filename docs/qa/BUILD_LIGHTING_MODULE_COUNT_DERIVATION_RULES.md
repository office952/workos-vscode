# BUILD — Lighting Module Count Derivation Rules

**Build:** `BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `23a0140` — PSU stabilization  
**Boundary:** No CostEngine, inventory, reserve change, backend contract migration.

---

## 1. Context

After PSU stabilization (`23a0140`), V3 still required **manual** `module_count` while V2 derived it from **total letter perimeter** using pitch 100 mm. Geometry exists in operator workspace via geometry metrics snapshot, but Lighting tab did not consume it.

---

## 2. De ce este necesar

Operatorii trebuie să vadă o sugestie auditabilă (formula V2) și să confirme/aplice manual — fără auto-confirmare silențioasă și fără formulă inventată.

---

## 3. Formula V2 confirmată

**Sursă:** `frontend/src/lib/volumetricQuoteInput.ts` — `computeLedModuleCountFromPerimeter()`

```text
pitch_mm = VOLUMETRIC_LED_MODULE_LENGTH_MM + VOLUMETRIC_LED_MODULE_GAP_MM = 75 + 25 = 100
module_count = ceil(letter_perimeter_m × 1000 / pitch_mm)
```

**Scope:** job-level total perimeter (`letter_perimeter_m`), not per-letter UI field.  
**Tests V2:** `volumetricQuoteInput.test.ts`, `lightingPlanning.test.ts`, `formula_handlers._handle_led_per_letter` (perimeter pitch mode).

`modules_per_letter` in V2 lighting flow: **not used** (legacy CostEngine letter-count mode only).

---

## 4. Date V3 disponibile

| Source | Field | Unit | Scope |
|--------|-------|------|-------|
| Geometry metrics snapshot | `perimeters.total_letter_perimeter_ml` | **meters** (mapped to `letter_perimeter_m` in backend legacy dict) | **Workspace total** |
| Operator workspace hook | `state.geometryMetrics` | API response | Loaded per tab sections |

Backend `intake_v3_lighting_plan_service.py`: **unchanged** — still computes watts/PSU from operator-supplied `module_count`.

---

## 5. Decizie: **SAFE IMPLEMENT**

Condiții îndeplinite:

- Formula V2 clară și testată
- Perimetru disponibil în geometry snapshot (fail-closed if missing)
- Integrare locală frontend (helper + Lighting tab)
- Fără migration / fără backend contract change
- Operator apply + manual override protejat
- Readiness neschimbat (`module_count` + confirm checkbox)

---

## 6. Implementare

### Helper (nou)

`frontend/src/lib/intakeV3/lightingModuleCountDerivation.ts`

- `resolveLetterPerimeterMFromGeometry()` — extrage `total_letter_perimeter_ml`
- `suggestLedModuleCountFromPerimeterM()` — delegă la `computeLedModuleCountFromPerimeter`
- `buildLightingModuleCountSuggestion()` — metadata formulă + sursă

### Lazy load geometry on Lighting tab

`operatorWorkspaceLoadSections.ts`: `lighting: ["geometry"]`

### UI minim (fără redesign)

`IntakeV3OperatorLightingSetupCard.tsx`:

- Afișează sugestia + formula + sursă
- Buton **Apply geometry suggestion**
- Notă când `module_count` este manual diferit de sugestie
- `modules_per_letter` relabel: optional manual note — **not used for suggestion**

`IntakeV3OperatorLightingTab.tsx`:

- Calculează sugestia din `state.geometryMetrics`
- `moduleCountManualOverride` local — nu se persistă în backend
- Apply setează `module_count`; edit manual marchează override

### Suggested vs confirmed

| Concept | Behavior |
|---------|----------|
| `suggestedModuleCount` | Calcul local din geometry — **not persisted** |
| `module_count` | Valoare finală trimisă la backend la Save |
| Auto-fill | **Nu** — operator apasă Apply |
| Manual override | Protejat — edit manual nu e suprascris de recalcul sugestie |
| Readiness | Neschimbat — `is_confirmed` + `module_count` required |

### Backend

**Nu modificat.** Derivarea rămâne operator-facing; backend primește `module_count` confirmat la PATCH.

### Reserve / PSU

**Neschimbate** (30% reserve, `allocatePSUCombination` allocator).

---

## 7. `modules_per_letter`

Păstrat ca câmp optional manual note; **nu** folosit la derivare. Eliminarea completă = build UX separat.

---

## 8. Teste rulate

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/lightingModuleCountDerivation.test.ts src/lib/intakeV3/operatorLightingPlanForm.test.ts src/pages/IntakeV3OperatorWorkspaceApp.test.tsx
```

Results:

| Suite | Result |
|-------|--------|
| `pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q` | **36 passed** |
| `vitest run lightingModuleCountDerivation.test.ts operatorLightingPlanForm.test.ts IntakeV3OperatorWorkspaceApp.test.tsx` | **41 passed** |

**Runtime UI smoke:** frontend `:3000` not verified live; replaced by workspace vitest (geometry suggestion + apply button).

---

## 9. Boundary confirmations

- [x] No CostEngine
- [x] No inventory / StockMovement mutation
- [x] No ExecutionTask / ExecutionPlan / PO / SupplierOrder
- [x] No UI recomposition / Atoms 3-step
- [x] No reserve 30% change
- [x] No PSU allocator change
- [x] V2 formula reused — no invented LED math
- [x] Materials read-only preserved
- [x] Quote guarded preserved
- [x] Technical route preserved
- [x] Layer name not used as production truth (uses geometry snapshot total perimeter)

---

## 10. Recomandare următor pas

1. Owner confirmă **30% reserve** vs V2 15% (decizie rămasă deschisă).
2. Runtime smoke pe workspace real cu geometry completă.
3. Apoi **visual acceptance** / `BUILD_OPERATOR_WORKSPACE_ATOMS_3_STEP_FLOW_RECOMPOSITION`.

**Verdict build:** `PASS — module_count derivation implemented safely`

---

## Related

- `docs/qa/VERIFY_INTAKE_V3_LIGHTING_PSU_CALCULATION_V2_PARITY.md`
- `docs/qa/BUILD_INTAKE_V3_LIGHTING_PSU_STABILIZATION_BEFORE_VISUAL_ACCEPTANCE.md`
