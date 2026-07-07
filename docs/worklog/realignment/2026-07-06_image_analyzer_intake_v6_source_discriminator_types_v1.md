# Image Analyzer Intake V6 Source Discriminator Types V1

Date: 2026-07-06
HEAD before work: bbcece2

## Files changed

- frontend/src/lib/intakeV6/intakeV6AnalysisSourceTypes.ts
- frontend/src/lib/intakeV6/intakeV6AnalysisSourceTypes.test.ts
- frontend/src/components/workos/NewIntakeDialog.tsx
- docs/worklog/realignment/2026-07-06_image_analyzer_intake_v6_source_discriminator_types_v1.md

## What changed

- Added a small Intake V6 analysis source type model for `svg` and future `image` analyzer sources.
- Centralized source metadata in a frontend-only registry with explicit status and `canCreateWorkspace` flags.
- Kept SVG as the only active source that can create an Intake V6 workspace.
- Kept Image Analyzer as preview-only and non-submittable.
- Updated `NewIntakeDialog` to read the source registry instead of local scattered method constants.

## Tests run

- `pnpm.cmd --dir frontend exec vitest run src/lib/intakeV6/intakeV6AnalysisSourceTypes.test.ts src/components/workos/NewIntakeDialog.test.ts --reporter=verbose`
- `git diff --check`

## Runtime impact

- No backend source added.
- No API route added.
- No adapter added.
- No Image Analyzer workspace creation enabled.
- No external Image Analyzer integration added.

## Forbidden scope confirmation

- No Pricing changes.
- No Quote/Order changes.
- No Execution changes.
- No ProductAggregate changes.
- No TaskGraph changes.
- No ExecutionPlan changes.
- No DB, seed, or migration changes.
- No Logo offerability changes.
- No component root or component quote activation.
- No Product Truth finalization from image.
- No ProductDefinition finalization from image.

## Next recommended slice

- IMAGE_ANALYZER_PAYLOAD_ADAPTER_AUDIT_V1