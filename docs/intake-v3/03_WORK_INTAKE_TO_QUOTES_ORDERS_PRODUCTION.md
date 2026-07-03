# Work Intake → Quotes → Orders → Production

**Strat:** boundary comercial și producție  
**Boundary:** Intake V3 nu creează execution plan real

---

## Lanțul de handoff

```text
┌─────────────────┐
│  Intake V3      │  confirmă realitatea lucrării
│  (workspace)    │  ReadinessReport, MaterialIntent, FinishAssignment
└────────┬────────┘
         │ PricingInput adapter ✅ in-memory
         ▼
┌─────────────────┐
│ QuoteWizard /   │  quote_input, CostEngine simulate, commercial gate
│ Quotes          │
└────────┬────────┘
         │ accept / convert
         ▼
┌─────────────────┐
│ Order           │  snapshot înghețat
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ExecutionPlan   │  taskuri REALE, dependențe, minute
│ Service         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Employee Mobile │  taskuri executabile, work sessions
└─────────────────┘
```

---

## Clarificări obligatorii

| Afirmație | Adevăr |
|-----------|--------|
| Intake creează execution plan | **NU** |
| ProductionHandoff în Intake | preview / seed / readiness |
| Taskuri reale în atelier | după Order → ExecutionPlanService |
| Employee Mobile din Intake preview | **NU** — doar `EmployeePreviewSeed` non-executable |
| Inventory consum | după producție reală, nu din Intake |

---

## ProductionHandoff vs Execution Plan

| | ProductionHandoff (Intake) | Execution Plan (Order) |
|--|---------------------------|------------------------|
| `preview_only` | `true` | N/A — plan real |
| execution_plan id | absent | creat |
| execution_reality | absent | posibil după start task |
| StockMovement | absent | posibil la consum real |
| Operator poate Start Task | **NU** | DA (Mobile) |

---

## Ce urmează

- Adapter pricing: `templates/TPL-VOLUMETRIC-LETTERS/09_PRICING_INPUT_ADAPTER.md`
- Adapter handoff: `templates/TPL-VOLUMETRIC-LETTERS/10_PRODUCTION_HANDOFF_ADAPTER.md`

---

## Workspace preview composition (E2E foundation)

`intake_v3_workspace_preview_service.build_intake_v3_workspace_preview()` compune:

```text
IntakeV3Workspace
  → finish variation summary (preview notes)
  → quote readiness gate / pre-quote review
  → quote creation dry-run (GET, no quote created)
  → quote creation guard policy (disabled-by-default; real quote blocked)
  → commercial quote bridge preview (GET, mapping only — no quote created)
  → quote creation enablement + final blocker check (GET, owner approval required — no quote created)
  → real quote creation enablement readiness (GET, owner decision + snapshot policy — no quote created)
  → guarded draft quote creation (POST, owner approval + snapshot in notes — draft Quote only)
  → draft quote review + pricing handoff (GET, read-only — no CostEngine/order/execution/inventory)
  → pricing review completion (POST manual priced draft — quote stays draft, no CostEngine/order/execution/inventory)
  → accept/convert readiness audit (GET read-only)
  → guarded accept (POST — draft→priced→accepted, no order/execution/inventory)
  → guarded convert to order (POST — accepted→Order locked, no execution/inventory)
  → order production readiness audit (GET — handoff preview, no execution/inventory)
  → material quantity / geometry / material cost breakdown (GET — materials-only informative)
  → production task generation dry-run (GET — candidate tasks/groups/deps preview only)
  → evaluate_intake_v3_readiness
  → validate_confirmed_production_model / validate_finish_assignment
  → derive_material_intent
  → build_pricing_input_candidate
  → build_production_handoff_preview
  → IntakeV3WorkspacePreview + IntakeV3BoundaryFlags (preview_only=true)
```

**Boundary shell:** `quote_creation_allowed=false` în preview UI — distinct de `can_create_quote` din readiness general **și** de quote readiness gate (`can_create_quote` mereu false până la build dedicat de creare ofertă).

Frontend: `/intake-v3` consumă preview read-only și **persistă draft workspace** via `POST/PATCH /api/v1/intake-v3/workspaces`. Fără quote/order/plan/inventory.
