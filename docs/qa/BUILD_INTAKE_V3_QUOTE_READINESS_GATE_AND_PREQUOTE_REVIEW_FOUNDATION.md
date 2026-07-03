# BUILD — INTAKE_V3_QUOTE_READINESS_GATE_AND_PREQUOTE_REVIEW_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `81468dc` — finish variation material and pricing preview summary  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Add **Quote Readiness Gate** and **Pre-Quote Review** foundation for Intake V3. Operators see a full checklist, blockers, warnings, pricing/handoff preview summaries, and next recommended action — **without** real quote/order/execution plan creation.

## Quote readiness vs general readiness

| Layer | Service | Purpose |
|-------|---------|---------|
| **General readiness** | `evaluate_intake_v3_readiness` | Section completion, legacy `ReadinessReport`, `can_create_quote` when blockers cleared (still not wired to real quote in V3) |
| **Quote readiness gate** | `evaluate_intake_v3_quote_readiness` | Pre-quote operator gate; **`can_create_quote` always false**; max status `ready_preview_only` |

Quote readiness **composes** readiness, pricing input adapter, handoff adapter, and finish variation summary — no new CostEngine formulas.

## Checklist sections

1. Workspace (payload, template, title, not archived)
2. Client / product (template, dimensions, support mode, illuminated)
3. SVG / vector (raw analysis, confirmed model, counts, raw vs confirmed separation)
4. Finishes (global + assignment validation + variation summary)
5. Pricing input preview (candidate, blockers, variation notes, no final price)
6. Production handoff preview (non-executable, group labels when variations)
7. Safety (no quote/order/plan/inventory; preview-only boundary)

## Severity model

| Severity | Status | Meaning |
|----------|--------|---------|
| `blocker` | `fail` | Must resolve before future quote step |
| `warning` | `warn` | Operator review recommended |
| `info` | `info` | Preview-only / boundary messaging |
| `pass` | `pass` | Check satisfied |

**Quote gate status:**

- `blocked` — any blocker
- `warning` — actionable warnings (variations, raw SVG warnings, missing title, etc.)
- `ready_preview_only` — no blockers and no gate warnings (material estimate warnings may still appear in checklist)

## Backend

- `backend/services/intake_v3_quote_readiness_service.py`
- Schemas: `IntakeV3QuoteReadinessItem`, `IntakeV3QuoteReadinessResult`, `IntakeV3PreQuoteReview`, `IntakeV3PreQuoteReviewSection`
- Integrated in `build_intake_v3_workspace_preview()` → `quote_readiness`, `prequote_review`
- Read-only endpoint: `GET /api/v1/intake-v3/workspaces/{id}/quote-readiness` (no DB writes)

## Frontend

- `IntakeV3PreQuoteReviewPanel` in preview shell
- Command bar: quote readiness status, blocker/warning counts, next action
- Flow stepper: **Pre-Quote Review** (6th step)
- Mandatory copy for blocked / ready preview-only / pricing / handoff / disabled quote button

## Tests

### Backend targeted

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_quote_readiness_gate.py tests/test_intake_v3_finish_variation_summary.py tests/test_intake_v3_finish_assignments.py -q
```

**Result:** 31 passed

### Backend regression (Intake V3)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_production_model_review.py tests/test_intake_v3_svg_upload_analysis.py tests/test_intake_v3_workspace_field_editor.py tests/test_intake_v3_workspace_persistence.py tests/test_intake_v3_preview_endpoint.py tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_volumetric_execution_task_order.py -q
```

**Result:** 93 passed

### Frontend targeted

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
```

**Result:** 69 passed

## Boundary (respected)

- No CostEngine / pricing formulas / TVA / markup
- No Inventory / StockMovement
- No quote / order creation
- No ExecutionPlan / ExecutionTask runtime
- No Employee Mobile / Intake V2
- No DB migration
- No commit / push in this build

## Not implemented (pending builds)

- Real quote creation endpoint and enabled CTA
- Granular pricing per finish group / letter
- Visual SVG click-to-select for assignments
- Per-variation material roll/sheet estimates with quantities

## Open questions

- Should `ReadinessReport.can_create_quote` be aligned to quote gate in UI only, or deprecated when quote build lands?
- `letter_custom` mode: require per-letter confirmation flags in UI (warning only today)?

## Recommended commit message

```
feat(intake-v3): add quote readiness gate and pre-quote review foundation
```
