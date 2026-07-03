# 14 — App Roles and Page Responsibilities

**Version:** 1.0.0  
**Date:** 2026-06-30  
**Status:** PARTIAL — role taxonomy documented; fine-grained RBAC **NEEDS_VERIFICATION**

---

## 1. Purpose

Define **who uses which surface**, **what each page is allowed to decide**, and **what data it may read/write** — to prevent:

- preview pages looking official;
- legacy paths confused with V2 canonical flow;
- Employee Mobile used before materialization;
- UI implying shop execution when only draft/audit exists;
- operators acting without context (internal vs commercial, planned vs operational).

**Companion docs:** flow details in 01–13; implementation gates in [Doc 21](../realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md).

---

## 2. Role taxonomy

Functional roles (not a new RBAC spec). Mapping to code: **PARTIAL** — `user.role` exists (e.g. admin); page-level enforcement is inconsistent.

| Role | Meaning | Examples in app | Can approve? | Can write? | Can execute? | Status |
| ---- | ------- | --------------- | ------------ | ---------- | ------------ | ------ |
| Owner / Administrator | Business + system owner | Settings, governance, owner-approval gates | **Yes** (owner approval) | **Yes** (admin) | No (not shop floor) | PARTIAL |
| Sales / Offer operator | Quote spine, client comms | Intake V6 handoff, Quotes | No (owner gate) | **Yes** (draft/freeze path) | No | VALIDATED_WITH_GUARDS |
| Intake operator | Capture request + config | Intake V6 workspace | No | **Yes** (workspace) | No | VALIDATED_WITH_GUARDS |
| Product configurator / technical planner | Template/dossier admin | Product-system, dossier UI | No | **Yes** (registry — owner GO) | No | PARTIAL |
| Production planner | Execution plan draft | Execution API (not full UI) | No | **Yes** (plan persist — guarded) | No | VALIDATED_WITH_GUARDS |
| Shop floor manager | Overview, assignment (future) | Execution dashboard, operator | No | Partial (assignment blocked) | No | PARTIAL |
| Machine operator | Run tasks | `/operator`, `/tablet/*` | No | Task actions when materialized | **Execute** (when ready) | PARTIAL |
| Montage / field team | Install (future) | — | No | N/A | BLOCKED | NOT_STARTED |
| Employee / worker | Mobile tasks | Employee Mobile | No | Sessions (future) | FINAL_PHASE | FROZEN |
| HR / employee admin | People registry | `/employees`, attendance | No | **Yes** (HR data) | No | PARTIAL |
| Finance / profitability reviewer | Margin review | ExecutionDetail profitability panel | No | Read-only | No | IMPLEMENTED_PREVIEW_ONLY |
| Read-only observer | Audit/report | Reports, reality-review | No | No | No | PARTIAL |

**Code note:** `canCreateIntakeRequest`, `resolveRole` → viewer fallback — **CONFIRMED_IN_CODE** (partial). No full page×role matrix in backend — **MISSING**.

---

## 3. Application surfaces map

| App / Area | Route | Page/Component | Primary users | Purpose | Reads | Writes | Status | Risk | Required label |
| ---------- | ----- | -------------- | ------------- | ------- | ----- | ------ | ------ | ---- | -------------- |
| Intake V6 operator | `/intake-v6/:id/operator` | `IntakeV6OperatorWorkspaceApp` | Intake operator, Sales | Configure product request | workspace, previews | `payload_json`, spine POSTs | VALIDATED_WITH_GUARDS | Preview ≠ offer | **Workspace — not official offer** |
| Intake list | `/intake` | `WorkIntake` | Sales, Intake operator | List requests | intake_requests | status, draft quote | PARTIAL | Legacy routing | **Opens V6 for volumetric** |
| Legacy intake | `/intake/:id` | `IntakeLegacyRoute` | — | Old intake view | intake request | limited | DEAD_LEGACY_RISK | Parallel path | **Legacy** |
| ProductSystem | `/product-system` | Product hub | Admin, Configurator | Template/dossier admin | templates | admin CRUD | PARTIAL | Not order flow | **Technical library — admin** |
| Quotes | `/quotes`, `/quotes/:id` | `Quotes` | Sales, Owner | Quote records | quotes | status, legacy price | PARTIAL | `/price` | **Official = Snapshot V2** |
| Orders | `/orders`, `/orders/:id` | `Orders` | Sales, Production planner | Frozen orders | orders, snapshot_v2 | PUT guarded | VALIDATED_WITH_GUARDS | — | **Frozen Snapshot V2** |
| Execution hub | `/execution` | `ExecutionDashboard` | Production planner | Plan overview | plans | — | PARTIAL | Draft vs runtime | **Plan draft ≠ shop runtime** |
| Execution detail | `/execution/:order_id` | `ExecutionDetail` | Planner, Finance | Plan + profitability | plan, profitability GET | assignment if materialized | PARTIAL | actuals null | **Profitability MVP read-only** |
| Operational reports | `/reports/operational` | `OperationalReports` | Manager, Observer | Ops metrics | reports API | — | PARTIAL | — | — |
| Employees | `/employees` | `Employees` | HR admin | HR registry | employees | CRUD | PARTIAL | Not task eligibility | **HR registry only** |
| Utilaje | `/utilaje` | `Utilaje` | Admin, Planner | Machines/capacity | utilaje | CRUD | PARTIAL | Not on plan WC | **Capacity registry** |
| Settings | `/settings` | `SettingsPage` | Owner, Admin | Env/config | settings | settings | PARTIAL | CE fallback | **Governance** |
| Pricing registry | `/inventory/pricing` | `Pricing` | Admin, Finance | Registry hub | pricing registry | admin | DEAD_LEGACY_RISK | Hourly mix | **Not V2 commercial truth** |
| Employee Mobile v1/v2 | `/employee-app/*`, `/employee-app-v2/*` | Mobile roots | Worker | Mobile tasks/sessions | mobile APIs | sessions (future) | FROZEN | Too early for V2 | **Final-final — not V2 canonical** |
| Demo | `/demo/commercial-spine` | Demo | Dev | Step 8 demo | snapshot | — | IMPLEMENTED_PREVIEW_ONLY | — | **Dev demo only** |

---

## 4. Page-by-page responsibilities

### `/intake-v6/:id/operator`

| Field | Value |
| ----- | ----- |
| **Primary role** | Intake operator |
| **Secondary roles** | Sales / offer operator |
| **Purpose** | Capture and configure volumetric product request; drive Step 8 commercial spine |
| **Source of truth** | `intake_v6_workspaces.payload_json` |
| **Reads** | workspace, form-contract, CPP/EIC previews, material breakdown, task preview (non-authoritative) |
| **Writes** | workspace fields; draft quote linkage; pricing-review / owner-approval / accept / convert (via spine POSTs) |
| **Allowed** | SVG upload, finish setup, confirm handoff, freeze path triggers (when gates pass) |
| **Forbidden** | Treat live preview as official offer; create execution_plan; materialize tasks; sessions |
| **Status** | VALIDATED_WITH_GUARDS |
| **Required UI label** | “Workspace — preview only until Snapshot V2 freeze” |
| **Risks** | Task dry-run ≠ ExecutionPlan V2; grand_total=0 on draft quote |
| **Next safe step** | Step 11 labels; owner DEC before materialize downstream |

### `/intake`

| Field | Value |
| ----- | ----- |
| **Primary role** | Sales / intake coordinator |
| **Purpose** | List intake requests; entry to V6 for volumetric |
| **Reads** | intake_requests |
| **Writes** | status, optional draft quote |
| **Forbidden** | Treat as product configurator for volumetric (use V6) |
| **Status** | PARTIAL |
| **Required label** | “List — volumetric jobs open in Intake V6” |

### `/product-system`

| Field | Value |
| ----- | ----- |
| **Primary role** | Product configurator / admin |
| **Purpose** | Manage templates, dossier, module links — **technical library**, not runtime task board |
| **Reads** | product_templates, dossier, mini-modules |
| **Writes** | admin CRUD (owner GO for production template changes) |
| **Forbidden** | Mutate frozen snapshots; assign shop tasks |
| **Status** | PARTIAL |

### `/quotes`

| Field | Value |
| ----- | ----- |
| **Primary role** | Sales / offer operator |
| **Secondary roles** | Owner (approval via IV6 spine) |
| **Purpose** | Quote records; linkage to snapshots |
| **Reads** | quotes, snapshot refs |
| **Writes** | V2 path via Intake spine; legacy `/price` **forbidden canonical** |
| **Forbidden** | `/price` as default for new volumetric V2 |
| **Status** | PARTIAL |

### `/orders`

| Field | Value |
| ----- | ----- |
| **Primary role** | Sales, Production planner |
| **Purpose** | View frozen orders; financial fields immutable |
| **Reads** | `snapshot_v2_json` |
| **Writes** | non-financial fields only (Slice 10.1 guard) |
| **Forbidden** | Reprice; mutate accepted commercial total |
| **Status** | VALIDATED_WITH_GUARDS |

### `/execution` and `/execution/:order_id`

| Field | Value |
| ----- | ----- |
| **Primary role** | Production planner |
| **Secondary roles** | Finance (profitability read-only) |
| **Purpose** | View execution plan draft; readiness; profitability MVP |
| **Reads** | execution_plan, profitability GET |
| **Writes** | assignment only when materialized (currently blocked) |
| **Forbidden** | Implies tasks runnable when `operational_tasks[]` empty; start sessions on V2 not materialized |
| **Status** | PARTIAL |
| **Required label** | “Execution plan draft — not shop runtime until materialized” |

### `/employees`, `/utilaje`

| Field | Value |
| ----- | ----- |
| **Primary role** | HR admin / Admin |
| **Purpose** | Registries for people and machines |
| **Forbidden** | Imply task eligibility or assignment (not wired to planned graph) |
| **Status** | PARTIAL |

### Employee Mobile (`/employee-app/*`, `/employee-app-v2/*`)

| Field | Value |
| ----- | ----- |
| **Primary role** | Employee / worker |
| **Purpose** | Mobile task consume + sessions (future) |
| **Status** | **FROZEN** on V2 canonical until Doc 21 Faza 10 |
| **Required label** | “Final-final — not for V2 orders without materialized tasks” |

---

## 5. Decision ownership map

| Decision / Action | Page where it appears | Who may decide | Current implementation | Risk if wrong |
| ----------------- | --------------------- | -------------- | ---------------------- | ------------- |
| Freeze Quote Snapshot V2 | Intake V6 / product-system API | Sales operator | POST freeze — VALIDATED | Skipping freeze |
| Owner approval | Intake V6 | **Owner** | POST owner-approval | Accept without owner |
| Accept quote | Intake V6 | Owner / authorized operator | POST accept + gate | Wrong commercial bind |
| Convert to order | Intake V6 | Sales operator | POST convert | Expect plan auto-created |
| ExecutionPlan preview | API (future 9B UI) | Production planner | POST preview read-only | Treat as runtime |
| Persist plan draft | API | Production planner | POST from-order — VALIDATED | Duplicate plan (idempotent OK) |
| Materialization audit | API GET | Planner / auditor | GET audit | Confuse with POST |
| POST materialize | API | — | **BLOCKED** DEC-009 | Double tasks |
| Assign task | ExecutionDetail | Shop manager | Blocked v2_not_materialized | Assign to planned only |
| Start/stop session | Execution / Mobile | Machine operator | FROZEN Step 11 | False actuals |
| Change template/dossier | Product-system | Admin + owner GO | Admin CRUD | Breaks frozen chain if retroactive |
| Change pricing rules | `/inventory/pricing` | Owner + 7I GO | Registry admin | Hourly commercial |

---

## 6. Write boundaries

| Page | Allowed writes today | Forbidden writes today | Reason |
| ---- | -------------------- | ---------------------- | ------ |
| Intake V6 | workspace, spine gates, draft quote linkage | official price without snapshot; execution_plan | Product truth only |
| Product-system | template/dossier (admin) | frozen snapshot rows | Immutability after accept |
| Quotes (V2 path) | via IV6 spine only | `/price` for new canonical | Dual snapshot model |
| Orders | non-financial updates | commercial total, snapshot_v2 | Slice 10.1 |
| Execution persist API | execution_plan draft | operational_tasks, sessions | Step 9 scope |
| Materialization POST | — | all | DEC-009 blocked |
| Execution UI | — (assignment blocked) | sessions | v2_not_materialized |
| Employee Mobile | legacy paths only | V2 canonical driver | Faza 10 |

---

## 7. Misleading UI risks

| Page | Misleading risk | Required label/copy | Step that fixes it |
| ---- | --------------- | --------------------- | ------------------ |
| Intake V6 pricing panels | preview = official | “Preview — not client offer” | Faza 8 / Step 11 |
| Intake task preview | catalog tasks = order plan | “Dry-run — not order snapshot” | Step 11 |
| Quotes list | grand_total=0 | “Draft unpriced — see Snapshot V2” | Step 11 |
| ExecutionDetail | plan looks runnable | “Draft plan — not materialized” | Faza 1 Step 9B |
| Profitability panel | implies full margin | “MVP — actual margin N/A” | Faza 7 |
| `/inventory/pricing` | registry = client price | “Internal/registry — not CPP” | 7I |
| Employee Mobile nav visible | looks production-ready | “Final-final” | Faza 10 |

---

## 8. Role-to-flow matrix

Legend: **CURRENT** = observed today; **TARGET** = Doc 21; **NEEDS_VERIFICATION** = RBAC unclear.

| Role | Intake | ProductSystem | Quote/Offer | Order | ExecutionPlan | Materialization | Sessions | Profitability | Employee Mobile |
| ---- | ------ | ------------- | ----------- | ----- | ------------- | --------------- | -------- | ------------- | --------------- |
| Owner | APPROVE (CURRENT) | WRITE (admin) | APPROVE | READ | READ | BLOCKED | BLOCKED | READ | FINAL_PHASE |
| Sales / Intake op | WRITE (CURRENT) | READ | WRITE (spine) | READ | READ | BLOCKED | BLOCKED | READ | BLOCKED |
| Configurator | READ | WRITE (CURRENT) | READ | READ | READ | BLOCKED | BLOCKED | N/A | BLOCKED |
| Production planner | READ | READ | READ | READ | WRITE draft (CURRENT) | BLOCKED | BLOCKED (TARGET) | READ | BLOCKED |
| Shop operator | N/A | N/A | N/A | READ | READ | BLOCKED | EXECUTE (TARGET) | N/A | FINAL_PHASE |
| HR admin | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Finance | READ | READ | READ | READ | READ | N/A | N/A | READ (CURRENT) | BLOCKED |

---

## 9. Current gaps

- Full RBAC matrix not encoded in code — **NEEDS_VERIFICATION**
- Employees/skills not on planned task graph — **HIGH**
- Employee Mobile routes exist but unsafe for V2 — **FROZEN**
- Legacy pages callable without labels — **DEAD_LEGACY_RISK**
- Owner decisions (DEC-003+) not surfaced in UI — **PARTIAL**

---

## 10. Next safe step

**Owner decisions DEC-003 / DEC-004 / DEC-005 first** — or **Step 11 UI labels audit** if owner wants page clarity before any materialization discussion.
