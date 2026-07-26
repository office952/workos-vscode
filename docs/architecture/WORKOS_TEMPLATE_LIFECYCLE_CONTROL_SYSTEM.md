# WORKOS — Template Lifecycle Control System V1

**Status:** owner GO `GO_WORKOS_TEMPLATE_LIFECYCLE_CONTROL_SYSTEM_V1`  
**Authority:** Product System contracts (no parallel template registry)  
**Scope:** discover → inspect → readiness → impact → CI validate → read-only API/UI

## Pipeline

```text
Product System contract
→ Template Lifecycle Inspector
→ Readiness Matrix
→ Impact Analyzer
→ CI Validator
→ Owner Gates (reported, not auto-closed)
```

## Status vocabulary

`NOT_APPLICABLE` · `NOT_STARTED` · `DISCOVERED` · `CONFIGURED` · `WIRED` · `VALIDATED` · `PREVIEW_ONLY` · `OWNER_GATE_REQUIRED` · `BLOCKED` · `PASS` · `DEPRECATED`

## Canonical stages (17)

PRODUCT_FAMILY → PRODUCT_TEMPLATE → COMPONENT_TEMPLATES → INTERFACE_CONTRACTS → INTAKE_AVAILABILITY → INTAKE_STEP_1 → INTAKE_STEP_2 → FINISH_SETUP → PRODUCT_DEFINITION → PRODUCT_AGGREGATE → CPP → OFFER → ORDER_SNAPSHOT → TASK_RULES_PROJECTION → TASK_MATERIALIZATION → EXECUTION → RUNTIME_PROOF

## Activation profile (minimum PASS/WIRED)

Product Family, Product Template, Components, Interfaces, Intake, Step 1, Step 2, ProductDefinition, ProductAggregate, Runtime Proof.

Sensitive stages may remain:

- CPP / Snapshot / Task materialization: `OWNER_GATE_REQUIRED` or `PREVIEW_ONLY`
- Execution: `NOT_STARTED`

## Commands

```powershell
# Canonical cross-platform entry (Node → Python CLI → same service as API/UI)
npm run template-lifecycle:validate
npm run template-lifecycle:inspect -- TPL-VOLUMETRIC-LETTERS_v2
node scripts/template-lifecycle.mjs impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
```

Optional Windows wrapper: `.\scripts\template-lifecycle.ps1 validate`

## CI adoption status

**Real CI pipeline files were not found** (no GitHub Actions / Buildkite / GitLab / Azure / Jenkins in-repo).

Required CI gate adoption is **not completed**. Local gate ready:

```text
npm run template-lifecycle:validate   # exit 0 pass / exit 2 required BLOCKED
```

When a real pipeline is introduced, wire that single command — do not duplicate readiness rules in YAML.

Baseline note: `TPL-METAL-PREMOUNT-STRUCTURE_v1` currently fails all-active validate and must be resolved under a separate GO before a required CI gate can stay green.

## API (GET-only)

- `GET /api/v1/product-system/templates/{template_code}/lifecycle-readiness`
- `GET /api/v1/product-system/templates/{template_code}/lifecycle-impact`
- `GET /api/v1/product-system/templates/{template_code}/lifecycle-inspect`
- `GET /api/v1/product-system/template-lifecycle/validate`

## UI

Product System → template detail → tab **Lifecycle** (read-only matrix). No activation buttons.

## Runtime blocker severity (Intake-ready)

A template is **not Intake-ready** if required bindings cannot persist through FinishSetup and be consumed by the next step.

| Class | Examples |
|-------|----------|
| **BLOCKED** | FinishSetup 422 on required support binding; Step 1 cannot complete; Step 2 required consumer missing |
| **OWNER_GATE_REQUIRED** | CPP formula; snapshot activation; task materialization; execution rollout |
| **WARNING** | Contained legacy adapter; optional guarded logo; early association evidence |

Score rules:

- Required stage `BLOCKED` contributes `0` and hard-caps `readiness_score <= 99`
- `activation_eligible=false` when any activation-required stage is `BLOCKED` or carries blockers
- Owner gates may keep a high technical score while `lifecycle_status=OWNER_GATE_REQUIRED`

Step 1 support persistence uses `is_early_svg_component_association` so `SUPPORT_CONTOUR` / Contur suport can save before layer roles are complete, without inventing a fake legacy layer role.

## Non-goals V1

- No parallel registry
- No schema/migration
- No CPP formula changes
- No task materialization
- No Execution rollout
- No scaffold generator (documented as next option)

## Implementation

| Piece | Path |
|-------|------|
| Schemas | `backend/schemas/template_lifecycle_control.py` |
| Service | `backend/services/template_lifecycle_control_service.py` |
| Router | `backend/routers/product_system_template_lifecycle.py` |
| CLI | `backend/scripts/template_lifecycle_cli.py` |
| PS wrapper | `scripts/template-lifecycle-validate.ps1` |
| Tests | `backend/tests/test_template_lifecycle_control.py` |
| UI | `frontend/src/features/product-system/TemplateLifecycleReadinessPanel.tsx` |
