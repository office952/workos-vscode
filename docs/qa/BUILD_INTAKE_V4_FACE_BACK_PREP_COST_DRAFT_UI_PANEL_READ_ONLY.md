# BUILD — Intake V4 Face-Back Prep CNC Cost Draft UI Panel (Read-Only)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** read-only UI panel; no ProductSystem registry, CostEngine, quote/order, or production side effects

---

## 1. Purpose

Surface the existing **`TPL-VOLUMETRIC-FACE-BACK-PREP`** CNC cost draft in Intake V4 operator UI so internal verification is visible — not hidden behind API-only access.

---

## 2. Where the panel appears

**Intake V4 → Review step → Detalii tehnice / debug** (`IntakeV4TechnicalDetailsAccordion`)

Component: `IntakeV4FaceBackPrepCostDraftPanel`  
Wired in: `IntakeV4ReviewStep.tsx` (top of technical details accordion)

---

## 3. Endpoint used

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft?shanfren_forex=
```

Frontend: `getIntakeV4FaceBackPrepCostDraft()` in `intakeV4Api.ts`

---

## 4. What the panel displays

- Template key + version (`TPL-VOLUMETRIC-FACE-BACK-PREP`, `v1-cnc-only`)
- Material rows (plexiglas 3 mm, Forex 10 mm): key, sqm, unit price, cost, status
- CNC operation rows: label, task key, perimeter ml, **pass_count**, EUR/ml/pass, cost, perimeter source/confidence
- Formula summary (P_face × 2 × 1.5; P_back × 3 × 1.5; P_back × 5 × 1.5 when shanfren)
- Totals: materials, CNC operations, internal draft total (or unavailable message)
- Warnings (including vector perimeter)
- Draft task order (preview only)
- Read-only boundary line

---

## 5. Vector perimeter rule (UI)

When `vector_perimeter_missing_or_low_confidence` warning is present, panel shows:

```txt
Perimetrul vectorial lipsește sau are încredere scăzută. Costul CNC nu se calculează din bbox/nesting.
```

Total shows unavailable message when perimeter/manual blocks calculation.

---

## 6. Pass-count formulas displayed

| Case | Formula |
|------|---------|
| Plexiglas face | P_face × 2 × 1.5 EUR |
| Forex no shanfren | P_back × 3 × 1.5 EUR |
| Forex with shanfren | P_back × 5 × 1.5 EUR |

Table rows show separate pass counts: face cut 1 + shanfren 1; back cut 3 + shanfren 2 (when active).

---

## 7. Shanfren Forex toggle

Local checkbox **Șanfren Forex activ** (default `false`).  
Not persisted to DB. Refetches endpoint with `shanfren_forex=true|false`.

---

## 8. Read-only boundaries (visible in panel)

```txt
Nu creează quote · Nu creează taskuri reale · Nu consumă stock · Nu scrie ExecutionPlan/tasks_json · Nu folosește CostEngine final
```

Response flags `creates_quote`, `creates_real_tasks`, `consumes_stock` remain false (backend contract).

---

## 9. What this build does NOT include

- ProductSystem registry changes
- CostEngine final pricing
- Quote / order creation
- Real tasks / ExecutionPlan / `tasks_json`
- Stock consumption
- Finishes: Oracal, print, lamination, policromie
- Commercial quote UI

---

## 10. Files changed

| File | Role |
|------|------|
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | Types + `getIntakeV4FaceBackPrepCostDraft` |
| `frontend/src/lib/intakeV4/intakeV4FaceBackPrepCostDraftDisplay.ts` | Formatting + formula helpers |
| `frontend/src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.tsx` | Panel UI |
| `frontend/src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.test.tsx` | Vitest |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Mount in technical details |

---

## 11. Tests

Backend (unchanged):

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
```

Frontend:

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.test.tsx
```

**Result:** backend 11 passed; frontend panel Vitest 5 passed.
