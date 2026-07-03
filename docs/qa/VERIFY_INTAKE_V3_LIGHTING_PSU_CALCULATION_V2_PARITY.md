# VERIFY — Intake V3 Lighting / LED / PSU Calculation vs V2 Parity

**Purpose:** Read-only audit + E2E probe confirming Phase 5 `lighting_plan` calculates and surfaces LED/PSU correctly, and documenting V2 vs V3 differences before UI recomposition / owner visual acceptance.

**Boundary:** No CostEngine, pricing, inventory, StockMovement, ExecutionTask/Plan, PO/SupplierOrder changes. No production workspace mutation during audit.

---

## 1. Verdict

**NEEDS FIX** (before owner visual acceptance)

V3 **backend** lighting math is internally consistent and tested. **Frontend auto PSU proposal diverges from backend/V2** due to JavaScript array comparison in `proposePsuUnits()` (`score(picked) < score(best)` compares strings, not numeric tuples). Additionally, V3 is **not V2-parity** for module-count derivation or PSU reserve percent (15% vs 30%).

**Before owner visual acceptance:**

| Item | Recommendation |
|------|----------------|
| **Frontend `proposePsuUnits` score compare** | **Fix immediately** — one-line logic parity with backend/`psuAllocation.ts` |
| Module count source | **NEEDS BUILD** — `BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES` |
| Reserve policy (15% vs 30%) | **Owner decision** — align V3 to V2 (15%) or document intentional 30% |
| `modules_per_letter` UI field | **NEEDS FIX (UX)** — field is optional metadata only; misleads operators until wired or relabeled |
| PSU wattages + backend greedy | **Match V2** after frontend compare fix |

---

## 2. Branch / HEAD

| | |
|---|---|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (audit start) | `a41e475` — Phase 6 E2E hardening PASS |
| Tracked modifications at start | None (`?? tmp/` only) |
| HEAD (after verify commit) | _(see git log after commit)_ |

---

## 3. V2 logic found

**Canonical sources**

- `frontend/src/lib/workIntakeV2/lightingPlanning.ts` — `syncLightingPlanning()`
- `frontend/src/lib/workIntakeV2/psuAllocation.ts` — `allocatePSUCombination()`, `computeRequiredPsuWatts()`
- `frontend/src/lib/volumetricFrontlitIntake.ts` — `computeLedLoadWatts()`, `PSU_HEADROOM_RATIO = 0.15`
- `frontend/src/lib/volumetricQuoteInput.ts` — `computeLedModuleCountFromPerimeter()`
- `frontend/src/lib/workIntakeV2/lightingPlanning.test.ts` — reference scenario

**Module count (LED modules path)**

- **Derived from perimeter**, not operator-entered when geometry exists.
- Formula: `ceil(letter_perimeter_m × 1000 / pitch_mm)` where `pitch_mm = 75 + 25 = 100` (`VOLUMETRIC_LED_PITCH_MM`).
- UI helper explicitly says: do not enter manually if perimeter is complete.
- **`modules_per_letter` is not used in V2 lighting planning.**

**Total LED watts**

- Modules: `module_count × led_module_power_w` (via `computeLedLoadWatts()`).
- Strip alternate path: `perimeter × w_per_ml` from strip density.

**PSU reserve**

- **`PSU_HEADROOM_RATIO = 0.15` (15%)**, not 30%.
- Required: `total_led_watts × 1.15` (`computeRequiredPsuWatts()`).

**PSU auto proposal**

- Standard wattages: **60, 100, 160, 200** (`VOLUMETRIC_PSU_WATTAGE_OPTIONS`).
- Greedy search: fewest units → minimum overshoot → tie-break on max unit.
- Reference test: perimeter 18.6 m, 1.44 W → 267.84 W load, **308.02 W required**, PSU **`[160, 160]`**.

**Manual override**

- Underpowered manual config → blocker until fixed or documented.
- Manual config that **differs from auto** but meets required watts → **`needs_stock_override`** until `psu_override_reason` is set.

---

## 4. V3 current logic (Phase 5)

**Canonical sources**

- `backend/services/intake_v3_lighting_plan_service.py` — `sync_lighting_plan()`, `propose_psu_units()`, `validate_lighting_plan_entry()`
- `frontend/src/lib/intakeV3/operatorLightingPlanForm.ts` — mirror calculations for operator UI
- Schemas: `backend/schemas/intake_v3.py`, `frontend/src/lib/intakeV3/lightingPlanContracts.ts`

**Module count**

- **`module_count` is required manual operator input** (blocker if missing).
- **`modules_per_letter` exists in schema/UI but is not used in any calculation** — stored only on PATCH.

**Total watts**

- `estimated_total_watts = module_power_w × module_count` (backend + frontend).

**PSU reserve**

- **`DEFAULT_RESERVE_PERCENT = 30`** (configurable per plan via `reserve_percent`).

**Required watts**

- `required_watts_with_reserve = estimated_total_watts × (1 + reserve_percent/100)`.

**PSU auto proposal**

- Same wattages and same greedy scoring as V2 (`propose_psu_units` / `proposePsuUnits`).

**Manual override**

- Insufficient PSU capacity → blocker **`BLOCKER_INSUFFICIENT_PSU_CAPACITY`** unless `manual_override_reason` is set.
- No V2-style **`needs_stock_override`** when manual PSU differs from auto but is sufficient.

**Downstream**

- `summarize_lighting_plan()` → workspace preview `lighting_summary`
- Materials tab: read-only LED/PSU rows (`IntakeV3OperatorLightingMaterialsPreview`)
- Readiness: `collect_lighting_issues()` — quote blocked until plan confirmed and complete
- **No CostEngine / pricing coupling** in lighting_plan path

---

## 5. V2 vs V3 comparison table

| Topic | V2 logic | V3 current logic | Match? | Gap | Recommendation |
|-------|----------|------------------|--------|-----|----------------|
| Module count | Perimeter pitch `ceil(perim×1000/100)` | Manual `module_count` | **No** | V3 does not derive from geometry | **BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES** |
| `modules_per_letter` | Not used | Field present, stored, **unused in calc** | **No** | Misleading optional field | Wire derivation or relabel/remove until build |
| Surface/perimeter LED | Yes (modules + strip) | Modules manual; strip enum only | **Partial** | No strip/perimeter calc in V3 lighting_plan | Defer strip path to dedicated build |
| Total watts | `count × power` or strip load | `module_count × module_power_w` | **Partial** | Same formula once count known | OK after count derivation build |
| PSU reserve | **15%** headroom | **30%** default | **No** | Different required watts | Owner policy: align to 15% or document 30% |
| PSU wattages | 60/100/160/200 | 60/100/160/200 | **Yes** | — | — |
| PSU greedy auto | Same scoring | Same scoring in Python; **JS array `<` bug in `proposePsuUnits`** | **No (UI/save path)** | Auto proposal can pick 360 W vs backend 260 W at 224.64 W required | **Fix score compare before visual acceptance** |
| Manual override reason | Required for underpowered **and** auto-divergent manual | Required for underpowered only | **Partial** | V3 less strict on stock override | Optional hardening build |
| Materials / pricing | V2 quote path separate | Read-only preview, no price | **N/A** | By design Phase 5 | OK |
| Production module specs (0.72/1.44 W, 75 mm pitch) | Configurable intake + CostEngine perimeter handler | Operator-entered power/count | **N/A** | Values not hardcoded in lighting service | OK — CostEngine untouched |

---

## 6. E2E probe result

### Scenario A — Owner example (V3 manual model)

Inputs: 120 modules, 1.44 W/module, 30% reserve, auto PSU (`modules_per_letter=10` stored but not used).

| Metric | Expected (manual model) | Actual (backend `sync_lighting_plan`) |
|--------|-------------------------|----------------------------------------|
| `module_count` | 120 (manual) | 120 |
| `estimated_total_watts` | 172.8 | **172.8** |
| `required_watts_with_reserve` | 224.64 | **224.64** |
| PSU proposal | ≥ 224.64 W | **1×200 W + 1×60 W = 260 W** |
| `psu_reserve_w` | 260 − 224.64 = **35.36** | **35.36** |

**Note:** Illustrative `2×160 W = 320 W` also covers load but is **not** chosen — greedy algorithm minimizes overshoot (same as V2 `allocatePSUCombination`).

### Scenario B — V2 reference (perimeter 18.6 m, 1.44 W, 15%)

| Metric | V2 (`lightingPlanning.test.ts`) | V3 if same count entered manually @ 30% |
|--------|----------------------------------|----------------------------------------|
| Module count | 186 (from perimeter) | 186 (would be manual) |
| Total watts | 267.84 | 267.84 |
| Required watts | **308.02** (×1.15) | **348.19** (×1.30) |
| Auto PSU | **[160, 160]** | **[200, 160]** |

---

## 7. API / runtime result

| Check | Result |
|-------|--------|
| `pytest tests/test_intake_v3_lighting_plan.py` | **PASS** (incl. new realistic chain + modules_per_letter gap tests) |
| PATCH → GET persistence | **PASS** (`test_patch_persists_confirmed_plan` — preview `lighting_summary.module_count == 120`) |
| Readiness blocker when unconfirmed | **PASS** (`BLOCKER_UNCONFIRMED_LIGHTING_PLAN`) |
| Confirmed incomplete → 422 | **PASS** |
| Real workspace `e8d5b5b8-…` dev.db | **GET-safe read-only**: workspace exists; **no `lighting_plan` persisted yet** (`support_context` null). No PATCH applied. |
| Live stack `:8000` health | **200** at audit time |

---

## 8. UI smoke result

| Check | Result |
|-------|--------|
| Vitest `IntakeV3OperatorWorkspaceApp.test.tsx` | **PASS** — Lighting tab renders module power/count, PSU card, computed **74.88 W** required (80×0.72×1.3) |
| Vitest `operatorLightingPlanForm.test.ts` | **PASS** — incl. modules_per_letter non-derivation + 120-module chain |
| Operator UI labels | `Module count` = free numeric input; `Modules per letter (optional)` — **no helper explaining non-derivation** |
| Materials preview | Read-only LED + PSU rows; explicit note: no stock reserve / no PO |
| Inventory / order actions | **Absent** on Lighting tab (asserted in tests) |

Browser on real workspace not re-run for lighting fields (empty plan in dev.db); component-level tests + code review used instead.

---

## 9. Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_lighting_plan.py tests/test_intake_v3_operator_workspace_e2e_hardening.py -q
# 36 passed (after verify tests added)

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx src/lib/intakeV3/operatorLightingPlanForm.test.ts
# 31 passed (after verify tests added)
```

---

## 10. Gaps found

1. **Module count derivation** — V2 perimeter-based; V3 manual-only.
2. **`modules_per_letter`** — present in UI/schema, not wired to calculations (GAP / misleading).
3. **Reserve percent** — V2 15%; V3 default 30%.
4. **Strip LED path** — V2 computes from perimeter + density; V3 `led_system` enum without equivalent calc.
5. **Manual override semantics** — V2 requires reason when manual PSU ≠ auto proposal; V3 only when underpowered.
6. **Frontend PSU greedy bug** — `proposePsuUnits()` uses `score(a) < score(b)` on arrays (lexicographic string compare). Example: required 224.64 W → backend **260 W** (200+60), frontend **360 W** (160+200). Affects **Apply auto PSU proposal** and **`planFromLightingForm` save path**.
7. **Frontend live PSU display** — `syncLightingFormCalculations()` does not auto-fill PSU rows; operator must click **Apply auto PSU proposal** or save (backend `sync_lighting_plan` fills correctly on persist only when client sends empty `psu_units`).
8. **Production business constants** (0.5 EUR/module, cable consumables) — **not in lighting_plan** (correct for Phase 5); CostEngine `_handle_led_per_letter` uses perimeter pitch separately — **not modified**.

---

## 11. Recommendation

| Path | When |
|------|------|
| **Fix frontend PSU score compare** | **Before visual acceptance** — restores parity with backend + V2 |
| **Proceed to UI recomposition** | Only after PSU compare fix **and** owner accepts manual module_count + 30% reserve |
| **`BUILD_LIGHTING_MODULE_COUNT_DERIVATION_RULES`** | Before production parity if V2 perimeter counting is required |
| **Fix before visual acceptance (minimal UX)** | Relabel or hide `modules_per_letter` until derivation exists; document 30% vs 15% |
| **Do not merge V3 reserve to CostEngine** | Out of scope |

---

## 12. Boundary confirmations

- [x] No CostEngine changes
- [x] No commercial pricing
- [x] No inventory / StockMovement
- [x] No ExecutionTask / ExecutionPlan
- [x] No PO / SupplierOrder
- [x] Materials preview read-only
- [x] Quote remains guarded by lighting readiness blockers
- [x] No push
