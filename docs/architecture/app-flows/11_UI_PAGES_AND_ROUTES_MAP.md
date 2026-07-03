# UI Pages and Routes Map

**Current status:** PARTIAL

---

## 1. Purpose

Map **frontend routes** to purpose, backend truth, read/write behavior, misleading risks, and required labels (Step 11 target).

---

## 2. Current status

**PARTIAL** — V6 and V2 spine routes exist; labeling policy **NOT_STARTED**; Employee Mobile routes **FROZEN** for V2 lifecycle.

---

## 3. Pages / UI surfaces

See section 4 — this document is the route catalog.

---

## 4. Backend routes

N/A — see per-route backend in flow docs 01–10.

---

## 5. Services / schemas / models

N/A — `frontend/src/App.tsx` is routing source of truth.

---

## 6. Data contract

N/A

---

## 7. Links to previous and next systems

N/A

---

## 8. Source of truth

**Route definitions:** `frontend/src/App.tsx`, standalone roots for `/intake-v6-app/*`, `/employee-app/*`.

---

## 9. What must not happen

- Present preview panels as official offer without label.
- Route volumetric production to legacy `/intake/:id` without V6 workspace.
- Enable Employee Mobile as canonical V2 driver before Faza 10.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Missing preview vs official labels | MEDIUM | Step 11 NOT_STARTED | Operator error | Faza 8 |
| `/inventory/pricing` legacy hub | HIGH | redirects from old paths | Pricing confusion | 7I + labels |
| Demo routes in production nav | LOW | `/demo/*` | — | Dev-only label |

---

## 11. Owner decisions

None currently known (Step 11 label pass needs owner GO).

---

## 12. Verification checklist

```powershell
Select-String -Path frontend\src\App.tsx -Pattern 'Route path='
```

---

## 13. Next safe step

Step 11 label pass (owner GO) — start with Intake V6, Quotes, ExecutionDetail.

---

## Route catalog

> Full responsibilities: [14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md](./14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md).

| Route | Page/Component | Primary role | Secondary roles | Purpose | Current truth | Reads | Writes | Misleading risk | Required label | Status |
| ----- | -------------- | ------------ | --------------- | ------- | ------------- | ----- | ------ | --------------- | -------------- | ------ |
| `/intake` | `WorkIntake` | Sales / coordinator | Intake operator | Intake request list | intake_requests | list API | status, draft | Legacy vs V6 | "Opens V6 for volumetric" | PARTIAL |
| `/intake/:id` | `IntakeLegacyRoute` | — | — | Legacy intake view | intake request | request | limited | DEAD_LEGACY_RISK | "Legacy" | DEAD_LEGACY_RISK |
| `/intake-v6/:id/operator` | `IntakeV6OperatorWorkspaceApp` | Intake operator | Sales | Canonical volumetric workspace | payload_json | workspace APIs | payload, spine | Preview = offer | "Not official until Snapshot V2" | VALIDATED_WITH_GUARDS |
| `/intake-v6-app/*` | `IntakeV6StandaloneRoot` | Intake operator | — | Standalone V6 shell | same as V6 | same | same | same | same | VALIDATED_WITH_GUARDS |
| `/product-system` | Product hub | Configurator | Admin | Template/dossier admin | templates | product APIs | admin CRUD | Not order flow | "Technical library — admin" | PARTIAL |
| `/quotes` | `Quotes` | Sales | Owner | Quote management | quotes entity | quotes API | status, legacy price | `/price` path | "Official = Snapshot V2" | PARTIAL |
| `/quotes/:quoteId` | `Quotes` | Sales | Owner | Quote detail | quote + snapshots | quote | IV6 spine | Preview totals | "Draft may be unpriced" | PARTIAL |
| `/orders` | `Orders` | Sales | Production planner | Order list | orders + snapshot_v2 | orders | PUT guarded | — | "Frozen Snapshot V2" | VALIDATED_WITH_GUARDS |
| `/orders/:orderId` | `Orders` | Sales | Planner | Order detail | snapshot_v2_json | order | immutability guard | — | "Locked commercial fields" | VALIDATED_WITH_GUARDS |
| `/execution` | `ExecutionDashboard` | Production planner | Manager | Execution overview | plan draft | execution API | — | Plan vs runtime | "Draft plan ≠ shop runtime" | PARTIAL |
| `/execution/:order_id` | `ExecutionDetail` | Production planner | Finance | Plan + profitability MVP | plan, profitability | GET | assignment if materialized | actuals null | "Profitability read-only MVP" | PARTIAL |
| `/execution/reality-review` | `OperationalRealityReview` | Manager | Observer | Ops reality review | reports | reports | read | — | "Audit read-only" | IMPLEMENTED_PREVIEW_ONLY |
| `/reports` | `Reports` | Observer | Finance | Reports hub | reports | reports | — | — | — | PARTIAL |
| `/reports/operational` | `OperationalReports` | Manager | Observer | Operational reports | operational APIs | reports | — | — | — | PARTIAL |
| `/employees` | `Employees` | HR admin | — | HR registry | employees | employees | CRUD | Not eligibility | "HR registry only" | PARTIAL |
| `/employees-records/:id` | `EmployeeProfile` | HR admin | — | Employee profile | employee row | profile | edit | — | — | PARTIAL |
| `/utilaje` | `Utilaje` | Admin | Production planner | Machines/utilaje | utilaje registry | utilaje | CRUD | Not plan WC | "Capacity registry" | PARTIAL |
| `/inventory/pricing` | `Pricing` | Admin | Finance | Legacy pricing hub | pricing registry | registry | admin | Hourly/commercial mix | "Not V2 commercial truth" | DEAD_LEGACY_RISK |
| `/settings` | `SettingsPage` | Owner | Admin | App settings | config | settings | settings | CE fallback | "Governance" | PARTIAL |
| `/employee-app/*` | Employee Mobile v1 | Worker | — | Mobile tasks (legacy) | mobile APIs | tasks | sessions future | Looks active | "**Final-final — not V2 canonical**" | FROZEN |
| `/employee-app-v2/*` | Employee Mobile v2 | Worker | — | Mobile v2 | mobile APIs | same | same | same | "**Final-final**" | FROZEN |
| `/demo/commercial-spine` | Demo | Dev | — | Step 8 demo | snapshot APIs | demo | — | Demo as prod | "Dev demo only" | IMPLEMENTED_PREVIEW_ONLY |
| `/operator`, `/tablet/*` | Shop floor UI | Machine operator | Manager | Task queues | operator tasks | tasks | when materialized | Empty if not materialized | "Requires materialized plan" | PARTIAL |
