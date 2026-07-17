# WORKOS — Product Template Creation & E2E Wiring Playbook

**Companion:** `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md`  
**Lifecycle control:** `docs/architecture/WORKOS_TEMPLATE_LIFECYCLE_CONTROL_SYSTEM.md`

## Agent gate (required)

Any task that modifies a Product Template / Component Template / Intake template wiring **must start with**:

```powershell
.\scripts\template-lifecycle.ps1 inspect <TEMPLATE_CODE>
```

Report before coding:

1. current readiness score + lifecycle_status
2. missing / BLOCKED stages
3. affected systems (impact)
4. owner gates
5. legacy conflicts
6. proposed scope

If inspect cannot run → **STOP**.

## Create / extend checklist

1. Product Family + Product Template in Product System (authority)
2. Component composition + interface contracts (`svg_bindable_components` when SVG-bound)
3. Intake availability exposure (offerable / candidate / component-only)
4. Step 1 geometry / role / composition
5. Step 2 configuration consumers (no hardcoded dimensions for SVG-bound support)
6. FinishSetup persistence fields
7. ProductDefinition preview
8. ProductAggregate projection
9. Runtime proof (route + tests + worklog)
10. CPP / snapshot / task materialization remain owner-gated unless separate GO

## Validate before claiming active

```powershell
.\scripts\template-lifecycle.ps1 validate <TEMPLATE_CODE>
npm run template-lifecycle:validate
```

CI fails when an **active root-offerable** template has an activation-required stage `BLOCKED`.

## Do not

- Create a second template registry for lifecycle
- Auto-close owner gates
- Auto-activate CPP, task materialization, or Execution
- Treat documentation alone as PASS
