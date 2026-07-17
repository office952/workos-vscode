# 2026-07-17 — Close ACP Step 1 persistence, Step 2 dimensions, lifecycle truth

## Mini decizie

`GO_CLOSE_ACP_PERSISTENCE_STEP2_WIRING_AND_LIFECYCLE_TRUTH`

## Root cause 422

| Item | Value |
|------|--------|
| URL | `PUT /api/v1/intake-v6/workspaces/{id}/finish-setup` |
| Error | `422 {"error":"layer_roles_incomplete"}` |
| Validator | `save_finish_setup_for_intake_v6_workspace` required `layer_role_setup.confirmation_status == "complete"` |
| Secondary gate | `assert_v6_analysis_boundary_or_raise` also listed `layer_roles_incomplete` |
| Effect | Contur suport / `SUPPORT_CONTOUR` → ACM could not persist before all layer roles confirmed |

## Fix

- `is_early_svg_component_association`: allow unconfirmed FinishSetup patches that carry `SUPPORT_CONTOUR` bindings and/or `ALUCOBOND_CASED_PANEL` selection
- Skip full analysis-boundary layer-role completeness for that early path; keep lightweight SVG + layer_role_setup existence checks
- Non-support FinishSetup while roles incomplete still returns `layer_roles_incomplete`
- Confirmed FinishSetup still requires complete layer roles
- Lifecycle: missing early association → **BLOCKED** (`STEP1_SUPPORT_BINDING_PERSIST_GATE`); with association → Step 1 WIRED + warning evidence
- Score hard-cap: any required BLOCKED ⇒ `readiness_score <= 99`; `activation_eligible=false` when required blockers exist

## Runtime proof (workspace `f07058e2-…`)

| Element | Before | After |
|---------|--------|-------|
| FinishSetup HTTP | 422 | 200 |
| Error | layer_roles_incomplete | — |
| Support binding | no | yes (1) |
| Composition | letters+logo | letters+logo+support_panel |
| Panel W×H | — | 2000×700 |
| Lifecycle Step 1 | warning persist gate | WIRED + early association enabled |
| activation_eligible | true with false truth | true only without required blockers |

## Tests

- `tests/test_early_svg_support_finish_setup_v1.py` — 6 passed
- `tests/test_template_lifecycle_control_system_v1.py` — 8 passed, 1 skipped
- FE: mountingSolution / associatePrimarySupportContour / ProductCompositionPanel — 18 passed

## Boundary

No schema/migration/seed · no CPP · no tasking · no Execution · CI required-gate deferred (Option 1 after owner review).
