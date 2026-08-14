# S4 — Technical-model leak research

| Field | Value |
|-------|--------|
| Task | `S4_TECHNICAL_MODEL_LEAK_REDUCTION_V1` |
| Phase | ROOT-CAUSE RESEARCH ONLY |
| Date | 2026-08-14 |
| HEAD | `9ab027787d1c078fc771c9065c2eab6b25160614` |
| Implementation | NO |
| Commit | NO |

Principle: factory facts (material, machine, dimensions, sequence, employee, state) are not leaks. Leaks are developer/system language in everyday chrome.

---

## Compact inventory (non-cosmetic)

| SURFACE | VISIBLE_ITEM | CURRENT_TEXT/VALUE | SOURCE | CLASSIFICATION | WHY | UC | OV | RISK | SHARE | FIX | PRI |
|---------|--------------|--------------------|--------|----------------|-----|----|----|------|-------|-----|-----|
| Atelier | Breadcrumb | `Shop Floor` vs H1 `Atelier` | `FlowBreadcrumb.tsx:164-168` | INTERNAL_LEAK | English product name on operator home | 2 | 0 | 0 | 2 | COPY_ONLY | P1 |
| Atelier | WC card title | live `CNC_ROUTING`, `METAL_FAB`, `LETTER_FORMING`, `LASER_CUTTING`, `VINYL_APPLICATION` | `useShopFloorData.ts:61-128` fallback `cleanCode` | INTERNAL_LEAK | Registry codes as station names; `useMachinesData` has a richer map unused here | 3 | 1 | 1 | 3 | LABEL_TRANSLATION | P1 |
| Atelier | Queue / blocked primary id | `JOB-*` / `ORD-{id}` | `useShopFloorData.ts:105,171` | KEEP_BUT_DEMOTE | Synthetic id; `order_code` exists on tasks | 2 | 2 | 1 | 2 | FORMAT_IDENTIFIER | P1 |
| Atelier | Section chrome | `Blocked Jobs`, `Machine State`, `tick #N`, `1 active` | `ShopFloor.tsx` | INTERNAL_LEAK | English/dev chrome, not graph model | 2 | 1 | 0 | 1 | COPY_ONLY | P2 |
| Atelier | Status chips | `Running` / `Blocked` | `SharedComponents.tsx` JobStatusBadge | INTERNAL_LEAK | English enum labels | 2 | 2 | 1 | 3 | LABEL_TRANSLATION | P2 |
| Planificare `/execution` | Capacity strip | `IMPLEMENTED_INACTIVE`, `NEEDS ASSIGNMENT TRUTH`, `DEC-009` | `ExecutionDashboard.tsx:198-235` | AUDIT_ONLY on primary | Compiler/capacity lab on manager list | 3 | 0 | 1 | 1 | MOVE_TO_AUDIT_DETAILS | P1 |
| Planificare | Plan strip | `EXECUTION PLAN` / `Draft Plan` / `Operational Plan · blocked` | `ExecutionPlanStatesStrip` + `productTemplateModulesVocabulary.ts:60-65` | INTERNAL_LEAK | English compiler lifecycle as primary | 2 | 1 | 1 | 2 | LABEL_TRANSLATION | P1 |
| `/execution/:id` | V2 truth panel | `order_id`, `AUDIT_ONLY`, `task_key`, `MISSING_WORKCENTER` | `ExecutionPlanV2TruthPanel` above fold | AUDIT_ONLY on primary | Manager handoff lands in compiler audit | 3 | 1 | 2 | 2 | MOVE_TO_AUDIT_DETAILS | P1 |
| `/execution/:id` | Assignment footer | `PATCH /api/v1/execution/plan/...` | `AssignmentReadinessPanel.tsx:177-190` | INTERNAL_LEAK | API contract on manager page | 3 | 0 | 0 | 1 | MOVE_TO_AUDIT_DETAILS | P1 |
| Machine-run detail | Participant subline | full `task_key` mono | `MachineRunDetailPage.tsx:490-492` | INTERNAL_LEAK | Graph key always visible | 3 | 0 | 1 | 1 | HIDE_FROM_PRIMARY_VIEW | P1 |
| `/operator` | Primary label fallback | `identity.task_id` e.g. `node:root_product:…` | `operatorTaskPresentation.ts:76-79` | INTERNAL_LEAK | Graph id as headline when `display_label` missing | 3 | 0 | 1 | 3 | FORMAT_IDENTIFIER | P0 |
| `/operator` | Role badge | `root product` | `componentRoleBadgeLabel` `:69-74` | INTERNAL_LEAK | Raw role; RO map already exists unused | 3 | 0 | 1 | 3 | LABEL_TRANSLATION | P1 |
| `/operator` | Policy line | `ORDER AND PLAN ALLOWED TASK START BLOCKED` (underscores→spaces) | `OperatorProductionReleaseSummary.tsx:59-60` | INTERNAL_LEAK | Explanation below is already RO | 3 | 0 | 0 | 2 | HIDE_FROM_PRIMARY_VIEW | P1 |
| `/operator` | Chrome | `Operator View`, `Input Dependencies`, `Next Tasks` | `OperatorView.tsx` | INTERNAL_LEAK | English chrome | 2 | 0 | 0 | 1 | COPY_ONLY | P2 |
| `/operator` | Detalii tehnice | TPL / parent graph ids | `OperatorTaskIdentityPresentation.tsx:171-218` | AUDIT_VALID | Collapsed; keep | 0 | 2 | 0 | 3 | KEEP_AS_IS | P3 |
| `/tablet` | Routing line | `Operație cnc_routing → stație cnc` | `tabletLiveBridge.ts:131-133` | INTERNAL_LEAK | Raw process + station id | 3 | 0 | 1 | 2 | COPY_ONLY | P1 |
| `/tablet` | Order code | `ORD-*` from `JOB-*` | `tabletLiveBridge.ts:113` | KEEP_BUT_DEMOTE | Ignores API `order_code` | 2 | 1 | 1 | 2 | FORMAT_IDENTIFIER | P1 |
| `/tablet` | Actions footer | `/api/v1/operator/task-action` | `TabletMode.tsx:1047` | INTERNAL_LEAK | Dev path | 2 | 0 | 0 | 1 | HIDE_FROM_PRIMARY_VIEW | P2 |
| Orders handoff | Dispatch copy | “Operator, Shop Floor și Tablet” | `Orders.tsx:501-508` | INTERNAL_LEAK | English route names | 1 | 0 | 0 | 1 | COPY_ONLY | P3 |
| Orders handoff | Snapshot / CTAs | Snapshot acceptat, Generează taskuri | `Orders.tsx` | OPERATIONALLY_REQUIRED | Not a leak | 0 | 3 | 0 | 1 | KEEP_AS_IS | — |
| Intake V6 | Header template fallback | raw `template_code` if no label | `IntakeV6Header.tsx:41-47` | INTERNAL_LEAK | TPL as product name | 2 | 0 | 1 | 2 | LABEL_TRANSLATION (`humanTemplateName`) | P1 |
| Intake V6 | “Product Truth” | banners / pricing empty | V6 blocker helpers | EXPECTED_OPERATOR_TECHNICAL_DETAIL | Owner domain language, not compiler | 1 | 2 | 1 | 2 | KEEP_AS_IS | P3 |

Runtime 2026-08-14: operator `/shop-floor` showed `Shop Floor`, `tick #2`, `CNC_ROUTING` / `METAL_FAB` / `LETTER_FORMING`. Manager `/execution` showed `EXECUTION PLAN`, `Capacity Stage 1 · IMPLEMENTED_INACTIVE`, `DEC-009`.

---

## Synthesis

```text
ATELIER_MODEL_LEAK_STATUS = CONFIRMED
ATELIER_P0_P1_COUNT = 3
OPERATOR_MODEL_LEAK_STATUS = CONFIRMED
OPERATOR_P0_P1_COUNT = 3
TABLET_MODEL_LEAK_STATUS = CONFIRMED
TABLET_P0_P1_COUNT = 2
TASK_DETAIL_MODEL_LEAK_STATUS = CONFIRMED
TASK_DETAIL_P0_P1_COUNT = 2
PLANNING_MODEL_LEAK_STATUS = CONFIRMED
PLANNING_P0_P1_COUNT = 3
ORDER_EXECUTION_HANDOFF_LEAK_STATUS = MOSTLY_CLEAN
ORDER_EXECUTION_HANDOFF_P0_P1_COUNT = 1
INTAKE_V6_MODEL_LEAK_STATUS = SPOT_ONLY
INTAKE_V6_P0_P1_COUNT = 1
TOTAL_P0 = 1
TOTAL_P1 = 13
TOTAL_P2 = 6
TOTAL_P3 = 3
```

P0 is only the operator primary-label fallback to raw `task_id`. Everything else high-value is P1. English chrome on Atelier (`Blocked Jobs`, badges) is P2 — language, not model.

```text
SHARED_LEAK_SOURCES =
  FlowBreadcrumb.shopFloorBreadcrumb
  useShopFloorData.wcNameMap (incomplete vs useMachinesData)
  operatorTaskPresentation.taskPrimaryLabel / componentRoleBadgeLabel
  tabletLiveBridge.routingExplanation + orderCode
  productTemplateModulesVocabulary EXECUTION_PLAN_* labels
  SharedComponents JobStatusBadge (P2)

PAGE_LOCAL_LEAK_SOURCES =
  ShopFloor.tsx English sections / tick
  ExecutionDashboard capacity strip
  ExecutionPlanV2TruthPanel on ExecutionDetail
  AssignmentReadinessPanel API footer
  MachineRunDetailPage task_key line
  OperatorProductionReleaseSummary policy underscored string
  IntakeV6Header template_code fallback

AUDIT_VALID_INTERNAL_DETAIL =
  Ops-Graph, Reality Review, OperatorTaskIdentityPresentation “Detalii tehnice” (collapsed),
  TechnicalDetails <details>, V6 diagnostic drawer

OPERATOR_INVALID_INTERNAL_DETAIL =
  WC_* as Atelier titles, Shop Floor crumb, node:task_id as headline,
  root product badge, raw production policy, tablet process_type routing line,
  ExecutionPlan V2 / capacity lab on everyday planning
```

```text
OWNER_DECISION_REQUIRED = YES
DECISION = How far does S4 go beyond the two GS-15 acceptance lines?
OPTIONS =
  A. GS-15 only: Shop Floor → Atelier + WC titles (plus the P0 task_id fallback — safety)
  B. A + demote planning compiler chrome (capacity strip + V2 panel default-collapsed)
  C. Full English chrome pass on Atelier/operator/tablet
RECOMMENDED = B
TRADEOFF = A is smallest; C becomes an i18n project. B matches “what the user needs” without a new view-model.
```

```text
RECOMMENDED_S4_IMPLEMENTATION_BOUNDARY =
  Display-only. Reuse existing helpers. No new OperatorViewModel / Graph API / DTO.
  IN:
    1. shopFloorBreadcrumb Shop Floor → Atelier
    2. Atelier WC titles via existing/extended name map (not enum rename)
    3. taskPrimaryLabel never returns raw task_id
    4. componentRoleBadgeLabel uses COMPONENT_ROLE_LABEL_FALLBACK or hides
    5. Hide raw production policy string (keep RO explanation)
    6. tablet routingExplanation without raw process/station ids
    7. Collapse or demote ExecutionPlanV2TruthPanel + capacity strip (if OD = B)
    8. Hide machine-run task_key from default row
  OUT:
    English badge/section i18n (P2 later)
    V6 redesign / Product Truth vocabulary
    JOB-* identity rewrite unless order_code is already on the payload
    Pagination, RBAC, routes, backend, execution logic
EXPECTED_PRODUCT_CODE_FILES =
  FlowBreadcrumb.tsx
  useShopFloorData.ts
  operatorTaskPresentation.ts
  OperatorProductionReleaseSummary.tsx
  tabletLiveBridge.ts
  ExecutionDashboard.tsx (if OD B)
  ExecutionDetail.tsx or ExecutionPlanV2TruthPanel.tsx (if OD B)
  MachineRunDetailPage.tsx
EXPECTED_BACKEND_CHANGE = NO
EXPECTED_ROUTE_CHANGE = NO
EXPECTED_RBAC_CHANGE = NO
EXPECTED_DB_CHANGE = NO
EXPECTED_EXECUTION_LOGIC_CHANGE = NO
```

No stop-condition: all listed P0/P1 are presentation. Do not touch ProductAggregate, task generation, or pricing to “fix” these.

---

## Roadmap

```text
Roadmap awareness = 9/10
Where is S4 in the complete simplification program? = Wave 4 of S1–S8 (GS-15)
Cât sunt în direcția stabilită = 85%
Does technical-model leak reduction still provide meaningful owner/operator value after S1-S3? = YES
Dead Pieces Check = none
Overengineering Check = would fail if we invent a TechnicalTruthFramework
Forbidden Scope respected = YES
Next recommended step according to roadmap = S4 implementation after Owner picks A or B — not authorized here
```
