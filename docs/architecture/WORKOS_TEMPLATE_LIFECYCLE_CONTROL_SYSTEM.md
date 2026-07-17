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
# Local / CI entry
.\scripts\template-lifecycle.ps1 validate
.\scripts\template-lifecycle.ps1 inspect TPL-VOLUMETRIC-LETTERS_v2
.\scripts\template-lifecycle.ps1 impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1

# Direct CLI
cd backend
.\.venv\Scripts\python.exe scripts\template_lifecycle_cli.py inspect TPL-VOLUMETRIC-LETTERS_v2
.\.venv\Scripts\python.exe scripts\template_lifecycle_cli.py validate
```

Root npm alias:

```text
npm run template-lifecycle:validate
```

## API (GET-only)

- `GET /api/v1/product-system/templates/{template_code}/lifecycle-readiness`
- `GET /api/v1/product-system/templates/{template_code}/lifecycle-impact`
- `GET /api/v1/product-system/templates/{template_code}/lifecycle-inspect`
- `GET /api/v1/product-system/template-lifecycle/validate`

## UI

Product System → template detail → tab **Lifecycle** (read-only matrix). No activation buttons.

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
