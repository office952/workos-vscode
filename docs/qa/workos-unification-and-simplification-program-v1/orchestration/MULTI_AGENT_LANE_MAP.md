# Multi-agent lane map

Nav IA (`SHELL_NAV_SECTIONS`) is **not** system ownership. Lucrări groups Produse with Cereri/Oferte/Comenzi; Product System remains a separate lab/reference system. Payments/Avansuri sit under Management in the sidebar but belong to the HR cost boundary.

Wave 1 already owns page cards for: AppShell chrome, `/dashboard`, `/quotes`, `/shop-floor`. Later lanes **observe** those; they do not re-own them.

---

## LANE_A — COMMERCIAL_SPINE

| Field | Value |
|-------|--------|
| LANE_ID | `A` |
| LANE_NAME | Commercial spine |
| PRIMARY_SCOPE | Request → Intake V6 workspace → Quote (observe Wave 1) → Order; client as commercial counterparty |
| EXCLUDED_SCOPE | Product System lab tree; CostEngine formulas; Execution task graphs; HR money |
| ROUTES_OR_SECTIONS | `/intake`, `/intake/:id`, `/intake-v6/operator`, `/intake-v6/:workspaceId/operator`, `/intake-v6-app/*` (note standalone dark), `/quotes` **observe**, `/quotes/:quoteId` if not covered, `/orders`, `/orders/:orderId`, `/clients`, `/clients/:clientName` (read-only) |
| SYSTEMS_TOUCHED | Intake / Product Truth · CPP display · Quote snapshot · Order snapshot · Clients |
| EXPECTED_EVIDENCE | Page cards, interaction inventory, scroll exhaustion, quote/order handoff edges, 1:1 leak flags (commercial line ≠ task) |
| DEPENDENCIES | Wave 1 `/quotes` card; runtime coordinator for V6 |
| CAN_RUN_IN_PARALLEL_WITH | C, D, E, F (code/docs), G (code/docs) |
| MUST_WAIT_FOR | Runtime slot when capturing; H observes after A page cards exist |
| OUTPUT_ARTIFACTS | `lanes/A/` |

**Primary** on those routes. F and H observe.

---

## LANE_B — PRODUCTION_EXECUTION

| Field | Value |
|-------|--------|
| LANE_ID | `B` |
| LANE_NAME | Production / execution |
| PRIMARY_SCOPE | Planning, machine runs, ops-graph, legacy operator/tablet, employee mobile, execution detail |
| EXCLUDED_SCOPE | Commercial totals; Pricing Registry writes; HR as price input |
| ROUTES_OR_SECTIONS | `/shop-floor` **observe Wave 1**, `/execution`, `/execution/:order_id`, `/execution/reality-review`, `/execution/ops-graph`, `/execution/machine-runs`, `/execution/machine-runs/:machineRunId`, `/operator`, `/tablet` + children, `/employee-app/*`, `/employee-app-v2/*` |
| SYSTEMS_TOUCHED | Execution plan · task graph · actuals · machines-in-run · mobile |
| EXPECTED_EVIDENCE | Page cards; honesty of AUDIT/COMPAT; task vs commercial grain |
| DEPENDENCIES | Wave 1 Atelier card |
| CAN_RUN_IN_PARALLEL_WITH | A, C, D, E (docs); not same browser slot as A |
| MUST_WAIT_FOR | Runtime slot |
| OUTPUT_ARTIFACTS | `lanes/B/` |

---

## LANE_C — PEOPLE_HR

| Field | Value |
|-------|--------|
| LANE_ID | `C` |
| LANE_NAME | People / HR / Pontaj |
| PRIMARY_SCOPE | Employees, attendance, HR records, payments, advances |
| EXCLUDED_SCOPE | Using HR minutes as client tariff; shop-floor task action |
| ROUTES_OR_SECTIONS | `/employees`, `/employees-records`, `/employees-records/:employeeId`, `/attendance`, `/attendance/effects`, `/employee-payments`, `/employee-advances` |
| SYSTEMS_TOUCHED | HR · Pontaj · internal employee cost (not offer) |
| EXPECTED_EVIDENCE | Boundary honesty vs commercial; role visibility |
| DEPENDENCIES | Realignment `12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md` |
| CAN_RUN_IN_PARALLEL_WITH | A, B, D, E |
| MUST_WAIT_FOR | Runtime slot |
| OUTPUT_ARTIFACTS | `lanes/C/` |

---

## LANE_D — PRODUCT_SYSTEM_GOV

| Field | Value |
|-------|--------|
| LANE_ID | `D` |
| LANE_NAME | Product System / modules / governance |
| PRIMARY_SCOPE | Design-time catalog, planned PS sections, modules map, governance, blueprint/reference, volumetric demo |
| EXCLUDED_SCOPE | Treating PS as runtime Product Truth; activating ACM; in-repo parsers |
| ROUTES_OR_SECTIONS | `/product-system/**` (nested structure + planned sections), `/product-system/blueprint-dossier`, `/product-system/output-blocks-preview`, `/modules`, `/governance`, `/demo/volumetric-letter-preview` |
| SYSTEMS_TOUCHED | Product System · ProductDefinition authoring chrome · Governance · Modules |
| EXPECTED_EVIDENCE | Lab vs operator honesty; planned-section placeholders; freeze class |
| DEPENDENCIES | Freeze doc; PS alignment map |
| CAN_RUN_IN_PARALLEL_WITH | A, B, C, E |
| MUST_WAIT_FOR | Runtime slot; **not** Wave 2 (too wide) |
| OUTPUT_ARTIFACTS | `lanes/D/` |

---

## LANE_E — RESOURCES_ADMIN

| Field | Value |
|-------|--------|
| LANE_ID | `E` |
| LANE_NAME | Inventory / pricing / settings / admin support |
| PRIMARY_SCOPE | Inventory, pricing registry, utilaje catalog, settings, colaboratori, documents, reports (incl. operational demo) |
| EXCLUDED_SCOPE | Machine **runs** (lane B); HR payments (lane C); quote totals authority |
| ROUTES_OR_SECTIONS | `/inventory`, `/inventory/pricing`, `/utilaje`, `/settings`, `/colaboratori`, `/documents`, `/reports`, `/reports/operational`, `/demo/commercial-spine` |
| SYSTEMS_TOUCHED | Inventory · Pricing Registry · Machines catalog · Settings · HUB/docs |
| EXPECTED_EVIDENCE | Registry ≠ operator concept; pricing page is catalog not offer hub |
| DEPENDENCIES | Realignment 08, 13, 14, 15, 18 |
| CAN_RUN_IN_PARALLEL_WITH | A, B, C, D |
| MUST_WAIT_FOR | Runtime slot |
| OUTPUT_ARTIFACTS | `lanes/E/` |

---

## LANE_F — UI_SYSTEM (cross-cutting observer)

| Field | Value |
|-------|--------|
| LANE_ID | `F` |
| LANE_NAME | UI system / light-dark / hardcoded UI |
| PRIMARY_SCOPE | None (no page cards) |
| EXCLUDED_SCOPE | Owning a route; redesign tokens |
| ROUTES_OR_SECTIONS | All Wave-active surfaces as **observer** |
| SYSTEMS_TOUCHED | Design system · ThemeContext · terminology |
| EXPECTED_EVIDENCE | Pattern ledger, hardcoded ledger, light/dark matrix rows |
| DEPENDENCIES | Primary lane page cards + screenshots |
| CAN_RUN_IN_PARALLEL_WITH | All (docs from existing shots); live hover/focus needs runtime slot |
| MUST_WAIT_FOR | At least one primary lane’s screenshots for that wave |
| OUTPUT_ARTIFACTS | `lanes/F/` |

---

## LANE_G — LEGACY_DEAD (cross-cutting classify)

| Field | Value |
|-------|--------|
| LANE_ID | `G` |
| LANE_NAME | Legacy / dead / overengineering |
| PRIMARY_SCOPE | Classification only |
| EXCLUDED_SCOPE | Deletion, deprecation switches, refactors |
| ROUTES_OR_SECTIONS | Compat/audit/preview nav; V4 residue; unused components; parallel read models — discovered, not pre-listed as complete |
| SYSTEMS_TOUCHED | All (observer) |
| EXPECTED_EVIDENCE | `REMOVE_CANDIDATE_ONLY` rows with risk; zero-import notes |
| DEPENDENCIES | Policy 19; `docs/workflow-adv/DEAD_AND_LEGACY_PATHS.md` |
| CAN_RUN_IN_PARALLEL_WITH | All (code/docs) |
| MUST_WAIT_FOR | Nothing for static classify; runtime only if a surface must be seen |
| OUTPUT_ARTIFACTS | `lanes/G/` |

---

## LANE_H — NAV_JOURNEYS (cross-cutting observer)

| Field | Value |
|-------|--------|
| LANE_ID | `H` |
| LANE_NAME | Navigation / user journeys / link honesty |
| PRIMARY_SCOPE | None (no page cards). Owns **edge** records, not pages |
| EXCLUDED_SCOPE | Replacing Wave 1 nav graph; inventing journeys |
| ROUTES_OR_SECTIONS | Edges among Wave-active pages; role visibility; dead ends |
| SYSTEMS_TOUCHED | AppShell IA · RBAC · commercial spine |
| EXPECTED_EVIDENCE | Journey graph addenda; honesty mismatches (H1 vs nav) |
| DEPENDENCIES | Primary cards + runtime follow log |
| CAN_RUN_IN_PARALLEL_WITH | F, G |
| MUST_WAIT_FOR | Primary lane cards for the wave |
| OUTPUT_ARTIFACTS | `lanes/H/` |

---

## Control roles (not lanes)

| ID | Name |
|----|------|
| `ORCH` | System orchestrator |
| `REV` | Consistency reviewer |
| `RT` | Runtime / browser coordinator |

`READ_ONLY_LANE_COUNT = 8` (A–H).
