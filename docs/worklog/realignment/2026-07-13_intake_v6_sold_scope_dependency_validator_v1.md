# Worklog — INTAKE_V6_SOLD_SCOPE_DEPENDENCY_VALIDATOR_V1

**Date:** 2026-07-13  
**Branch:** main  
**HEAD before:** 929c05c  
**Scope:** Hybrid sold-component dependency validation (contract + product bindings + `validate_sold_graph`)

## Delivered

### Backend
- `component_dependency_contract_v1.py` — Slice-1 requirements including `LED_MOUNT_SURFACE` capability on LIGHTING
- `product_dependency_bindings_volumetric_letters_v2.py` — BACK or FACE+RETURN-CANT mount providers
- `sold_scope_dependency_validator_service.py` — permissive default, strict via `OFFER_SCOPE_DEPENDENCY_STRICT`
- Workspace save hook in `intake_v6_workspace_service.py` with `dependency_confirmation_codes`
- Readiness + quote snapshot scope hooks consume `valid_for_confirmation`
- Matrix tests (`test_sold_scope_dependency_matrix.py`) + workspace integration (`test_sold_scope_dependency_workspace.py`)

### Frontend
- `intakeV6OfferScopeDependency.ts` — preview mirror of backend rules
- `IntakeV6OfferScopeDependencyFeedback.tsx` — confirmation UI
- Wired `saveIntakeV6OfferScope`, `useIntakeV6Workspace`, `intakeV6Readiness`, `IntakeV6SvgAnalyzerStep`
- Unit tests: `intakeV6OfferScopeDependency.test.ts`, updated `intakeV6Readiness.test.ts`

## Policy enforced

| Case | Permissive (default) | Strict=1 |
|------|---------------------|----------|
| Empty subset | Block save | Block save |
| LIGHTING without mount | Confirmation required | Block save |
| ELECTRICAL without LIGHTING | Confirmation + warning | Block save |
| full_product | Skip dependency rules | Skip dependency rules |

No silent auto-add of BACK/mount. No SYSTEM_LED bundle UI. No DB migrations.

## Validation

- Backend: `test_sold_scope_dependency_matrix.py`, `test_sold_scope_dependency_workspace.py`
- Frontend: targeted Vitest on dependency + readiness modules
- Frontend build: `npm run build` from `frontend/`
- Runtime QA: Playwright `intake-v6-sold-scope-dependency-validator-v1.spec.ts` on IR-MRI01769

## Next slice

**DEPENDENCY_CONSUMER_ADHESIVE_GATING** — wire dependency confirmations into adhesive/material gating so LIGHTING-only without mount does not silently price mount adhesive rows.

## Direction score

Cat sunt in directia stabilita: **88/100%** — foundation + UI confirmations landed; consumer-side gating (adhesive/BOM) remains the next bounded slice.
