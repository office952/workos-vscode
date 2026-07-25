# Intake V6 — AcmPanel tech status strip (compact)

**Date:** 2026-07-24  
**Scope:** Configurare → Panou / carcasă workbench aside (Previzualizare tehnică + Validare panou)

## Intent

Owner visual ask: less stacked card chrome, less empty air; denser next-gen strip. Badge purge on Configurare is owned separately (`intakeV6OperatorConfigStatusChrome`); this change must not reintroduce Confirmat / L1-C chips.

## Change

- Workbench places blueprint + validation in one full-width shell under the Panou header (`intake-v6-acm-tech-status-strip`) — no side-column empty air.
- Blueprint `chrome="embedded"`: borderless slot, single dense preview row (plain text; no L1-C chip).
- Validation `density="inline"`: clean state is plain text footer; issue lists stay interactive and visible.
- Lab layout keeps separate rail/card slots (slightly tighter clean success text).
- Badge purge remains owned by `intakeV6OperatorConfigStatusChrome` / sibling agent.

## Files

- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelBlueprintPreview.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelValidationRail.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.blueprint.test.tsx`
