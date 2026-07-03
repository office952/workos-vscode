# QA: Volumetric WorkIntake V2 Migration Boundary Lock

**Build type:** Architecture / documentation only (no business logic changes in this pass)  
**Date:** 2026-06-08

## Scope

- Created architecture lock document.
- Added guard comments on three legacy components.
- No CostEngine, readiness, or V2 logic changes in this pass.

## STEP 0 — Git safety

**Working tree:** DIRTY (not clean at `2935f47`)

| Classification | Files |
|----------------|-------|
| **A — Classic hotfix** | `VolumetricLettersQuoteFlow.tsx`, `intakeReadinessStages.ts` (+test), `volumetricQuoteFlowState.ts` (+test), `BUILD_VOLUMETRIC_CLASSIC_WIZARD_FLOWSTATE_ALIGNMENT.md` |
| **B — V2** | `WorkIntakeV2Flow.tsx`, `WorkIntakeV2.tsx`, `V2ProductionStage.tsx`, `V2QuoteStage.tsx` |
| **C — CostEngine handoff** | `quote_input_line_gate.py`, `seed_build4_templates.py`, `test_volumetric_paint_tube_material.py`, `test_quote_input_line_gate.py`, `volumetricQuoteInput.ts` (+test), `volumetricFrontlitIntake.ts` (+test), `HOTFIX_VOLUMETRIC_COSTENGINE_PAINT_TUBE_APPLICABILITY.md` |
| **D — Unrelated** | None |

Architecture lock proceeded as **docs + comments only** (orthogonal to uncommitted hotfixes).

## Files created/changed (this build)

| File | Change |
|------|--------|
| `docs/architecture/VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md` | **Created** — full boundary |
| `docs/qa/BUILD_VOLUMETRIC_V2_MIGRATION_BOUNDARY.md` | **Created** — this note |
| `VolumetricLettersQuoteFlow.tsx` | Guard comment in file header |
| `Product001IntakeSpecEditor.tsx` | Guard comment |
| `VectorIntakeFastAskPanel.tsx` | Guard comment |

## Verification

| Check | Result |
|-------|--------|
| Business logic changed | No |
| `npm run lint` | Not run (comment-only TS edits; optional) |
| Backend tests | Not run |
| E2E | Not required |

## Operator path locked

```
/intake-v2/:id → V2 stages → Deschide QuoteWizard → /quotes (standalone)
```

Classic `/intake/:id` remains compatibility; do not add new rules there.

## Remaining gaps

See `docs/architecture/VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md` §11.

Uncommitted hotfixes (flowState, paint gate, V2 handoff) should be committed or reverted in a separate approved build before next feature work.

## Commit

Not committed (awaiting approval).
