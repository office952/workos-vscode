# BUILD — INTAKE_V3_FINISH_VARIATION_MATERIAL_AND_PRICING_PREVIEW_SUMMARY

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `e431173` — finish assignment per letter/group foundation  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Derive preview-safe finish variation summaries from existing payload assignments (global / group / letter). Expose material and operation notes plus pricing/handoff preview notes — **no CostEngine, no formulas, no runtime tasks**.

## Why CostEngine was not touched

Finish variations are already persisted in workspace payload. This build only **reads** effective finishes via `resolve_effective_finish_for_letter` and composes human/operator-facing summaries. Commercial pricing, unit costs, VAT, and markup remain out of scope.

## Summary model

`IntakeV3FinishVariationSummary` (top-level on `IntakeV3WorkspacePreview`):

| Field | Purpose |
|-------|---------|
| `has_variations` | True when enabled group/letter overrides exist |
| `variations[]` | Buckets by winning source (global / group / letter) |
| `material_notes[]` | Affected materials + letter counts (no m²/ml) |
| `operation_notes[]` | Face vinyl / wrapping / painting / backing flags |
| `pricing_preview_notes[]` | Grouped review messaging |
| `handoff_preview_notes[]` | Operator visibility messaging |

**Precedence:** letter override → group → global (same as assignment build).

## Pricing preview integration

`PricingInputCandidate` extended (notes only):

- `finish_variation_notes`
- `requires_grouped_finish_review`
- `finish_variation_count`

No changes to `quote_input_payload` price keys or operation formula handlers.

## Handoff preview integration

`ProductionHandoffPreview` extended (notes only):

- `finish_variation_handoff_notes`
- `requires_letter_group_visibility`
- `group_labels`
- `letter_override_count`

`non_executable` and `preview_only` remain enforced.

## Backend service

`backend/services/intake_v3_finish_variation_summary_service.py`

- `build_finish_variation_summary`
- `group_letters_by_effective_finish`
- `summarize_finish_material_variations`
- `summarize_finish_operation_variations`
- `build_finish_variation_pricing_notes`
- `build_finish_variation_handoff_notes`

## Frontend

- `IntakeV3FinishVariationSummaryPanel` in preview shell
- Pricing/handoff sections show variation notes when present
- Wording: preview summary only — not final price

## Tests

### Backend targeted

```powershell
pytest tests/test_intake_v3_finish_variation_summary.py tests/test_intake_v3_finish_assignments.py tests/test_intake_v3_production_model_review.py -q
```

**Result:** 28 passed

### Backend regression

```powershell
pytest tests/test_intake_v3_svg_upload_analysis.py tests/test_intake_v3_workspace_field_editor.py tests/test_intake_v3_workspace_persistence.py tests/test_intake_v3_preview_endpoint.py tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_volumetric_execution_task_order.py -q
```

**Result:** 84 passed

### Frontend targeted

```powershell
vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
```

**Result:** 61 passed

## Boundary

| Area | Touched? |
|------|----------|
| CostEngine / pricing formulas | ❌ |
| Inventory / quote / order / execution runtime | ❌ |
| Intake V2 / Employee Mobile | ❌ |
| DB migration | ❌ |
| SVG visual selection | ❌ |
| Commit / push | ❌ |

## Pending (separate builds)

- Granular pricing per finish group (quantities, labor splits)
- Visual SVG letter selection for assignments
- Per-variation material intent roll/sheet estimates

## Recommended commit message

```
feat(intake-v3): add finish variation material and pricing preview summary
```
