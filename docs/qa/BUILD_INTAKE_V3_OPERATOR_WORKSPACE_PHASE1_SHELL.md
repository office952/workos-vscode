# BUILD: Intake V3 Operator Workspace — Phase 1 Shell

**Date:** 2026-06-19  
**Build:** `INTAKE_V3_OPERATOR_WORKSPACE_PHASE1_SHELL`  
**Status:** PASS (frontend-only)

---

## Pre-flight

| Field | Before | After |
|-------|--------|-------|
| Branch | `local/integration-pr4-plus-svg-path` | same |
| HEAD | `b4d8500495f42cf2b8f5cebcc99571a37c9932e6` | _(updated at commit)_ |

Initial git status: untracked docs/tmp only — no tracked off-scope modifications.

---

## Scope

- New Operator Workspace page (UI from zero — not polish on `IntakeV3App`)
- Route `/intake-v3/:workspaceId/operator`
- Legacy technical route `/intake-v3/:workspaceId/technical` (wraps existing `IntakeV3App`)
- Sticky header, 10 real tabs, operator-facing layer cards
- Reuse existing V3 API clients (`lib/intakeV3/api.ts`) and panels
- Frontend Vitest for route/tabs/safety

## Non-scope (confirmed not implemented)

- No backend / schema / migrations / `backend/dev.db`
- No CostEngine, inventory mutation, ExecutionTask/Plan, PO
- No native `layer_finish_assignments[]`
- No policromie backend (Phase 4)
- No LED/PSU persistence (Phase 5 placeholder only)
- No ColorRegistry port (Phase 2)

---

## What was implemented

1. **`IntakeV3OperatorWorkspaceApp`** — new page with tabbed shell
2. **`operator-workspace/` components** — header, tabs, per-tab panels
3. **`useIntakeV3OperatorWorkspace`** — workspace/preview/quote/production data hook
4. **`operatorWorkspaceHelpers`** — header derivation, layer evidence/status helpers
5. **Routes in `App.tsx`**
6. **`IntakeV3TechnicalRoute`** — legacy view with link back to operator
7. **`IntakeV3App` props** — optional `fixedWorkspaceId` + `variant="technical"`

### Tabs (Phase 1)

| Tab | Content |
|-----|---------|
| SVG & Layers | Upload, saved filename, production model, operator layer role cards |
| Geometry | Confirmed letters headline, dimensions, geometry metrics (technical collapsed) |
| Finishes | Global finish summary + existing FinishAssignment API; Phase 3 notice |
| Production Setup | FieldEditor controlled fields |
| Lighting & PSU | Read-only/placeholder; Phase 5 notice |
| Readiness | Readiness panel + repair links |
| Quote Preview | Confirmed setup summary + guarded draft quote |
| Materials | Read-only material breakdown / availability / procurement when API available |
| Production Preview | Grouped read-only `ProductionPreviewPanel` |
| Advanced | Collapsed guard stack, flow stepper, legacy link |

### UX rules enforced

- Layer name = evidence; operator-confirmed role = production truth
- Confirmed letters headline (not holes)
- No unsafe action buttons
- Materials read-only banner

---

## Intentionally deferred

| Phase | Content |
|-------|---------|
| 2 | ColorRegistry, V2 finish UX, repair jump polish |
| 3 | Native `layer_finish_assignments[]` |
| 4 | Policromie / printed artwork |
| 5 | Full LED/PSU planning + persistence |
| 6 | E2E multi-layer stress fixtures |

---

## Files changed (frontend)

```text
frontend/src/pages/IntakeV3OperatorWorkspaceApp.tsx
frontend/src/pages/IntakeV3OperatorWorkspaceApp.test.tsx
frontend/src/pages/IntakeV3TechnicalRoute.tsx
frontend/src/pages/IntakeV3App.tsx (props only)
frontend/src/App.tsx (routes)
frontend/src/lib/intakeV3/operatorWorkspaceTabs.ts
frontend/src/lib/intakeV3/operatorWorkspaceHelpers.ts
frontend/src/lib/intakeV3/useIntakeV3OperatorWorkspace.ts
frontend/src/components/workos/intake-v3/operator-workspace/*.tsx (13 files)
docs/qa/BUILD_INTAKE_V3_OPERATOR_WORKSPACE_PHASE1_SHELL.md
```

---

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx
```

**Result:** 10/10 PASS

---

## Boundary confirmations

- [x] no backend changes
- [x] no schema/migration
- [x] no backend/dev.db
- [x] no CostEngine
- [x] no inventory mutation
- [x] no ExecutionTask/ExecutionPlan creation UI
- [x] no PurchaseOrder/SupplierOrder actions
- [x] legacy technical view kept at `/intake-v3/:workspaceId/technical`
- [x] no push

---

## PASS/FAIL

**PASS** — Phase 1 operator shell meets roadmap boundaries and test gate.
