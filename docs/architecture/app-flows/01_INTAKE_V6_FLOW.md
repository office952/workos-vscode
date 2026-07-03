# Intake V6 Flow

**Current status:** VALIDATED_WITH_GUARDS

---

## 1. Purpose

Capture **client product request** (geometry, finishes, SVG, commercial operator inputs) as durable workspace truth. Start the canonical V2 chain. **Does not** create official priced offer or execution tasks.

---

## 2. Current status

**VALIDATED_WITH_GUARDS** — pilot `TPL-VOLUMETRIC-LETTERS_v2`; Step 8 commercial spine validated on fixture; parallel legacy intakes remain.

---

## 3. Pages / UI surfaces

> Page responsibilities detail: [14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md](./14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md).

| Route/Page | Component/File | Primary role | Secondary roles | Role of page | Reads | Writes | Status | Risk |
| ---------- | -------------- | ------------ | --------------- | ------------ | ----- | ------ | ------ | ---- |
| `/intake-v6/:workspaceId/operator` | `IntakeV6OperatorWorkspaceApp` | Intake operator | Sales / offer operator | **Product request configurator** — starts order lifecycle | workspace, form-contract, CPP/EIC previews | `payload_json`, spine POSTs | VALIDATED_WITH_GUARDS | Preview ≠ official |
| `/intake-v6/operator` | Same | Intake operator | Sales | New volumetric workspace | — | create workspace | VALIDATED_WITH_GUARDS | — |
| `/intake-v6-app/*` | `IntakeV6StandaloneRoot` | Intake operator | — | Standalone V6 shell | same | same | VALIDATED_WITH_GUARDS | — |
| `/intake` | `WorkIntake.tsx` | Sales / coordinator | Intake operator | **Intake list / router** to V6 | intake_requests | status, draft quote | PARTIAL | Legacy parallel |
| `/intake/:id` | `IntakeLegacyRoute` | — | — | **Legacy** intake view | intake request | limited | DEAD_LEGACY_RISK | Not V2 canonical |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| POST | `/api/v1/intake-v6/workspaces` | `intake_v6_workspaces.py` | Create workspace | — | `intake_v6_workspaces` | VALIDATED | — |
| GET | `/api/v1/intake-v6/workspaces/{id}` | same | Load workspace | `payload_json` | — | VALIDATED | — |
| PUT | `.../finish-setup`, `layer-roles`, `analysis-bundle` | same | Mutate config | workspace | `payload_json` | VALIDATED | — |
| POST | `.../svg` | same | SVG upload | — | payload + storage | VALIDATED | — |
| GET | `.../pricing-input-preview` | same | Ephemeral pricing inputs | workspace | — | IMPLEMENTED_PREVIEW_ONLY | MISLEADING_UI |
| GET | `.../task-preview`, task dry-run | same | Task preview (V4 path) | workspace | — | PARTIAL | Not order snapshot truth |
| POST | `.../create-draft-quote` | same | Draft quote linkage | workspace | `quotes.notes` linkage | VALIDATED_WITH_GUARDS | `grand_total=0` |
| POST | `/quotes/{id}/complete-pricing-review` | same | Commercial spine | snapshot V2 totals | quote notes JSON | VALIDATED_WITH_GUARDS | — |
| POST | `.../owner-approval`, `accept`, `convert-to-order` | `intake_v6_quote_to_order_service` | Step 8 chain | quote, snapshot | quote/order | VALIDATED_WITH_GUARDS | — |

**Parallel (legacy):** `intake_v3_workspaces`, `intake_v4_workspaces`, `intake_v5`, `intake_requests` — not canonical V2.

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `models/intake_v6_workspace.py` | Persistence | — | ORM row | VALIDATED | `payload_json` Text |
| `schemas/intake_v6.py` | API contracts | — | DTOs | VALIDATED | — |
| `services/intake_v6_workspace_service.py` | CRUD + previews | workspace_id | payload | VALIDATED | — |
| `services/intake_v6_quote_to_order_service.py` | Commercial spine | quote_id | accept/convert | VALIDATED_WITH_GUARDS | Delegates snapshot convert |
| `services/intake_v6_task_generation_dry_run_service.py` | Task dry-run | workspace | V4 catalog tasks | PARTIAL | ≠ Step 9 path |

---

## 6. Data contract

**DB:** `intake_v6_workspaces.payload_json` (JSON text)

**Key paths (typical volumetric):**

| Path | Role |
| ---- | ---- |
| `template_code` | ProductSystem binding |
| `client.*` | width_mm, height_mm, client_name |
| `svg_source.*` | file_name, analysis refs |
| `quote_geometry.*` | letter_count, areas, perimeter |
| `finish_setup.*` | finishes, LED, mounting, backing |
| `commercial_inputs.*` | markup/discount — operator input, not commercial truth |

**Outputs (not stored as official price):** preview panels, draft quote linkage in `quotes.notes` (`intake_v6_linkage_v1`).

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Intake request (`/intake`) | `ensure-for-intake-request` | Intake V6 workspace | workspace_id | MEDIUM | Legacy list parallel |
| — | — | Form System | `template_code` | STRONG | Pilot only |
| Intake V6 | `payload_json` + workspace_id | ProductDefinition | builder reads workspace | STRONG | Missing fields → blockers |
| Intake V6 | commercial spine | Quote/Order | draft quote → snapshot | STRONG | Preview ≠ official |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Product request config | **`intake_v6_workspaces.payload_json`** |
| Official commercial price | **NOT Intake** — Quote Snapshot V2 after freeze |
| Execution tasks | **NOT Intake** — Order snapshot → ExecutionPlan |

---

## 9. What must not happen

- Treat Intake live calculation / pricing preview as official client offer.
- Create execution_plan or materialize tasks from Intake endpoints.
- Use Intake task dry-run as production task truth (use Order snapshot path).
- Reprice accepted quote from Intake workspace changes.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| V3/V4/V5 parallel intakes | MEDIUM | Multiple routers/models | Single product truth | Step 12 classify; route all volumetric to V6 |
| Task preview ≠ ExecutionPlan V2 | MEDIUM | `intake_v6_task_generation_dry_run` → V4 | Operator confusion | Label preview; Step 11 |
| Live preview vs draft quote total | MEDIUM | draft `grand_total=0` | MISLEADING_UI | Step 11 labels |
| Non-volumetric templates | HIGH | Only v2 pilot wired | Scale | Owner GO per template |

---

## 11. Owner decisions

None currently known specific to Intake V6 entry (execution decisions DEC-003+ are downstream).

---

## 12. Verification checklist

```powershell
# Read-only
Select-String -Path backend\routers\intake_v6_workspaces.py -Pattern "@router"
Get-Content frontend\src\lib\volumetricIntakeRoute.ts
# Prior worklog: Step 8 live accept/convert on IV6 quote
```

---

## 13. Next safe step

Route new volumetric jobs through `/intake-v6/.../operator` only; label all Intake previews as non-official until Step 11.
