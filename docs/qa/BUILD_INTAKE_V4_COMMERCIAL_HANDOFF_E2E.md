# BUILD_INTAKE_V4_COMMERCIAL_HANDOFF_E2E

**Date:** 2026-06-22  
**Status:** PASS (scoped commercial handoff — UI path; API stale gap documented)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `f82bf6a5741cf9f61e1a42133e384f45ad3a7e30`  
**Commit:** none (awaiting user confirmation)

---

## Purpose

Verify Intake V4 **Confirm → draft quote / QuoteWizard handoff** after boundary lock — without Pricing Foundation, CostEngine changes, or V2/V3 off-scope edits.

---

## Files modified

| File | Change |
|------|--------|
| `frontend/e2e/intake-v4-commercial-handoff.spec.ts` | **New** — UI handoff + stale UI gate |
| `frontend/e2e/helpers/intakeV4Live.ts` | Draft quote + entity quote + linkage assertion helpers |
| `backend/tests/test_intake_v4_commercial_quote.py` | Analysis-bundle seed; snapshot/linkage assertions; missing-bundle gate |

**Not modified:** CostEngine, Pricing Foundation, V2/V3 unstaged files, `tmp/`.

---

## E2E scenarios

| Test | Verifies |
|------|----------|
| `Confirm → draft quote → QuoteWizard with IV4 snapshot linkage` | Full pilot → artwork execution resolved → Confirm checkboxes → `create-draft-quote` 201 → `/quotes/{code}` → QuoteWizard method step → entity quote `draft`, `grand_total=0`, `IV4-{workspace}` linkage, snapshot fields |
| `Confirm handoff UI blocked after re-upload without analysis-bundle re-persist` | UI progress Confirm/Review disabled + unsaved banner (operator path fail-closed) |

**Note:** Direct `POST create-draft-quote` after local re-upload **without** `PUT analysis-bundle` may still return **201** with persisted backend snapshot (API gap — not UI). Follow-up: align handoff gate with hash/sync boundary on backend.

**E2E pilot note:** `pbl-complex.svg` may include artwork layers — E2E selects `print_laminate` before `intake-v4-confirm-finish` (backend blocks `artwork_execution_undecided`).

### Command

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-commercial-handoff.spec.ts
```

**Result:** 2 passed (~7–40s depending on analyzer warm-up) with dev stack on :8000/:3000

---

## Backend tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_commercial_quote.py -q
```

**Fix applied:** `_seed_ready_workspace` now uses `PUT analysis-bundle` + `finish_setup.confirmed` (aligned with boundary lock). Pre-boundary seed via legacy `POST .../svg` alone was the prior failure — not a `db_manager` / seed_build4 issue.

**Result:** 3 passed

---

## PASS criteria checklist

| Criterion | Status |
|-----------|--------|
| Confirm does not hand off on stale analysis (UI) | ✅ E2E stale UI test |
| Confirm does not hand off on stale analysis (API direct) | ⚠️ gap documented |
| `quote_input_payload` present and coherent | ✅ |
| IV4 snapshot linkage (`intake_v4_linkage_v1`) | ✅ |
| QuoteWizard receives `productSpec` via nav state (not breakdown) | ✅ UI opens wizard |
| Intake V4 does not invent commercial totals | ✅ `grand_total=0`, line items 0 |
| Missing registry remains pricing review path | ✅ `requires_pricing_review` |
| No V2/V3 off-scope in diff | ✅ |
| Repeatable E2E (repo fixture) | ✅ `pbl-complex.svg` |

---

## Boundary

**In scope:** E2E commercial handoff, backend commercial quote test repair, linkage assertions.

**Out of scope:** Pricing Foundation, CostEngine, ACM/bond, UI polish, push, commit without user OK.

---

## Remaining blockers for V4 production-ready

1. **API handoff hash sync** — `create-draft-quote` should fail when operator re-uploads locally without `PUT analysis-bundle` (UI already blocks)
2. Pricing / Prices Foundation — informative registry costs in dev/staging
3. QuoteWizard deep hydrate audit (Phase C) — full parity with IV4 snapshot beyond prefill
4. Deprecate legacy `POST .../svg` from operator UX
5. Frontend TS debt (`validate:frontend`)
6. Casetare bond adapter — explicit later scope

---

## Commit recommendation

**Separate commit** from `f82bf6a` boundary lock:

`test(intake-v4): add commercial handoff e2e and fix quote pytest seed`
