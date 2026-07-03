# Volumetric Letters Full E2E Product Truth to Execution Alignment

**Date:** 2026-07-01  
**Status:** AUDIT_CONTRACT_IMPLEMENTATION_PLAN_ONLY  
**Runtime anchor:** `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`  
**Workspace:** `IV6-BB8EE3F8`  
**Intake:** `IR-MR18L96M`  
**SVG:** `gradi-curat.svg`  
**Template:** `TPL-VOLUMETRIC-LETTERS_v2`

Tags used: `CONFIRMED_IN_CODE`, `CONFIRMED_IN_DOCS`, `OBSERVED_RUNTIME`, `DOCUMENTED_NOT_IMPLEMENTED`, `DISPLAY_ONLY`, `FORBIDDEN_NOW`, `OWNER_GO_REQUIRED`, `RISK`.

---

## Purpose

This document aligns the full WorkOS volumetric letters process from Work Intake through Employee Mobile later.

It is not a runtime implementation. It is an audit, contract, gap matrix, and implementation map.

Hard boundary:

- Intake V6 remains the source workspace.
- The existing Intake V6 form remains the base.
- No new form, duplicate controls, or new wizard.
- SVG Analyzer suggests; it does not decide Product Truth.
- Operator Review/Form confirmations create Product Truth.
- ProductDefinition, ProductSystem, CommercialPriceProposal, Quote Snapshot, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, workcenters, employees, ExecutionReality, and Employee Mobile must not repair missing Product Truth.

---

## Sources Read

### Required docs

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_EXISTING_FORM_ANSWERS_AUDIT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_MODULAR_FORM_COMPONENT_QUESTIONS_INVENTORY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`

### Required worklogs

- `docs/worklog/realignment/2026-07-01_phase_2_component_question_labels_ui_only.md`
- `docs/worklog/realignment/2026-07-01_phase_2_product_truth_candidate_visibility_ui_only.md`
- `docs/worklog/realignment/2026-07-01_phase_2_gap_closure_existing_form_ui_only.md`
- `docs/worklog/realignment/2026-07-01_phase_2_support_mounting_contract_alignment.md`
- `docs/worklog/realignment/2026-07-01_phase_2_owner_answers_patch.md`
- `docs/worklog/realignment/2026-07-01_phase_2_existing_form_answers_audit.md`

### Code areas inspected

- `frontend/src/components/workos/intake-v6/`
- `frontend/src/lib/intakeV6/`
- `frontend/src/lib/svgAnalyzer/`
- `frontend/src/features/product-system/`
- `backend/services/`
- `backend/data/`
- `backend/routers/`

---

## Current Process Truth Audit

| Stage | Current status | Source of truth today | Main files / docs | What is real | What is fallback/hydrated | What is suggested | What is confirmed | What is not implemented | Risk if used too early |
|---|---|---|---|---|---|---|---|---|---|
| Work Intake | PARTIAL | Existing Work Intake and Intake V6 entry bridge | roadmap; `frontend/src/components/workos/intake-v6/`; backend intake routers | Request can reach Intake V6 workspace. | Some old V4/V6 aliases remain in payload paths. | Product family/template hints may be inferred from route/template. | Workspace exists for `IR-MR18L96M`. | Clean V6-native handoff into canonical Product Truth. | A downstream quote path may treat request intent as full product truth. |
| Intake V6 workspace | IMPLEMENTED | Intake V6 workspace live payload and UI | `IntakeV6OperatorWorkspace.tsx`; `useIntakeV6Workspace`; Product Truth docs | `IV6-BB8EE3F8` is live; Straturi/Review/Confirmare flow exists. | Finish, geometry, lighting, mounting, backing values can be hydrated. | UI badges show candidates and warnings. | Layer roles and several review confirmations are currently confirmed in runtime. | Canonical Product Truth payload branch. | Hydrated values can look quote-safe without source state. |
| SVG Analyzer | IMPLEMENTED | SVG analysis report | `frontend/src/lib/svgAnalyzer/`; analyzer docs | SVG parsed; geometry, colors, groups, warnings exist. | Previous report may hydrate workspace. | Role, geometry confidence, support/artwork hints. | Geometry accepted only after operator/system readiness conditions. | Analyzer cannot produce final commercial truth. | Analyzer suggestions may be mistaken for confirmed truth. |
| Layer/group detection | IMPLEMENTED | Analyzer grouped layer report | `layerRoleTypes.ts`; `IntakeV6LayersRoleTable.tsx`; roadmap | Six operational groups for `gradi-curat.svg`. | Pseudo groups are technical identity. | Detected groups suggest face/artwork. | Runtime now shows Review accessible after legitimate confirmation. | Durable canonical layer refs in Product Truth branch. | Pseudo or detected group identity may leak as final production target without confirmation metadata. |
| Layer role suggestion | IMPLEMENTED | Analyzer auto-role candidates | `layerRoleTypes.ts`; `guessLayerAutoRole.ts`; `mapAnalyzerReportToModuleDetectionResult.ts` | Roles include `face`, `printed_artwork`, `support_panel`, `frame`, `ignore`, `unknown`. | Prior role selections can hydrate UI. | Suggested face/artwork/support-like roles. | Current logos show `SUGGESTED` and `CONFIRMED` in Review. | Native Product Truth status history for suggested vs confirmed. | Suggested support or artwork could trigger modules too early. |
| Operator confirmation | IMPLEMENTED | Intake V6 UI confirmation state | `IntakeV6LayersOperatorPanel.tsx`; `IntakeV6LayersRoleTable.tsx`; readiness docs | Confirm-all/per-layer role flow exists. | Confirmations may be loaded from workspace. | System can propose all roles. | Runtime shows Straturi complete and Review accessible. | Canonical audit object under `product_truth.audit`. | Bypassing confirmation would invalidate quote/order/execution. |
| Review/Form component questions | PARTIAL | Existing Intake V6 Review form | `IntakeV6ReviewStep.tsx`; component question docs | Existing form has face finish, return/cant, backing, lighting, mounting, template, PSU, artwork cards. | Defaults and saved payload hydrate many fields. | Product Truth chips show candidate status. | Some artwork/Review items are confirmed in runtime. | Separate canonical fields for face material/thickness, print_required, lamination_required, support_required, mounting_scope, site details. | Existing values can be mistaken for complete Product Truth. |
| Product Truth candidates | DISPLAY_ONLY | Display helper and UI badges | `intakeV6ComponentQuestionDisplay.ts`; `IntakeV6ComponentQuestionBadges.tsx`; recent worklogs | Chips are visible in Review, including support/mounting separation. | Chips can describe hydrated/fallback state. | Candidate labels identify future Product Truth branches. | Runtime shows chips for Face/Finish/Cant/Artwork/Mounting/Support/Pricing boundary. | Runtime canonical payload. | UI labels could be overread as readiness logic if not kept display-only. |
| Product Truth canonical payload | DOCS_ONLY | Architecture contracts | `INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`; this document | Product Truth is canonical direction. | Existing V6 payload carries transitional fields. | Candidate shape exists in docs. | No runtime canonical payload confirmed. | `product_truth` top-level payload branch. | Downstream systems may repair missing fields. |
| ProductDefinition | PARTIAL | Read-only builder from workspace payload and contract seed | `product_definition_builder_service.py`; Product Truth docs | Preview builder exists; no pricing; no DB writes. | Uses workspace payload and canonical value bridges. | Module states and validation warnings. | ProductDefinition preview can classify modules. | Consumption of confirmed canonical Product Truth only. | It currently derives `metal_support_required` from `mounting_system`; hidden inference risk. |
| ProductSystem / Dossier / modules | PARTIAL | Template/dossier/module registry | `mini_module_registry_volumetric_v2.py`; ProductSystem UI; support/mounting doc | Modules exist; `structura_suport` trigger mismatch is explicitly exposed. | Dossier mappings can act as template contract. | Module linkage panels warn about alignment. | ProductSystem template `TPL-VOLUMETRIC-LETTERS_v2` visible. | Runtime contract migration to explicit support/mounting fields. | ProductSystem could be misused as runtime truth override. |
| CommercialPriceProposal / Offer | PARTIAL | Commercial preview service and Review panel | `commercial_price_proposal_service.py`; pricing/cost contract | Unit-based commercial preview exists; runtime shows preview only. | Payload coalesces quote_input and workspace values. | Preview/dry-run can propose commercial total. | Runtime labels official offer after Quote Snapshot V2. | Official offer flow from frozen Product Truth/Quote Snapshot. | Preview can be mistaken for final offer; support bridge may affect lines. |
| Quote Snapshot | PARTIAL | Snapshot candidate services/routers | `quote_output_snapshots.py`; quote snapshot services | Candidate snapshot router exists and says no Quote/Order mutation. | Composition preview can feed snapshot candidate. | Snapshot status workflow exists. | No official volumetric E2E quote snapshot from canonical Product Truth observed. | Quote Snapshot freezing Product Truth and commercial proposal. | Live mutable Intake values could drift after offer. |
| Order Snapshot | PARTIAL | Order snapshot services exist elsewhere | `order_snapshot_service.py`; order routers; roadmap | Order snapshot infrastructure exists. | Older quote/order conversion paths may hydrate from legacy quote input. | Readiness panels can preview order-bound tasks. | No canonical volumetric Order Snapshot from Product Truth observed. | Order Snapshot after accepted Quote Snapshot. | Order may recompute from mutable Intake/ProductDefinition. |
| ProductAggregate | FORBIDDEN_NOW | ProductSystem/ProductAggregate read-only builder | `product_aggregate_service.py`; roadmap | Aggregate builder exists for templates; warning mapping exists. | Dossier/module mappings hydrate aggregate shape. | Conflicts/warnings expose trigger mismatch. | Template aggregate can be built. | Creation from frozen Order Snapshot for this flow. | Aggregate could repair missing Intake truth or start technical graph too early. |
| Task Graph | FORBIDDEN_NOW | Existing task/dry-run/task services | task dry-run services; task dependency services; roadmap | Task preview/dry-run infrastructure exists. | Dry-run can derive from current workspace paths. | Task candidates may be suggested. | No canonical task graph from ProductAggregate for this E2E slice. | DAG from ProductAggregate after Order Snapshot. | Task catalog may diverge from accepted product truth. |
| ExecutionPlan | FORBIDDEN_NOW | Execution plan services/routers exist | `execution_plan_service.py`; `execution_plan_v2.py`; roadmap | Execution plan infrastructure exists elsewhere. | Plans may hydrate from orders/tasks. | Preview/gates can suggest readiness. | Not part of current volumetric Product Truth slice. | Plan after Task Graph and frozen order. | Premature materialization from incomplete truth. |
| Workcenters / Utilaje | FORBIDDEN_NOW | Machines/workcenter services and routers | `machines_read_service.py`; `workcenter_rates_service.py`; `foundation_workcenters.py`; pricing/cost contract | Utilaje and rates exist as internal resources. | Rates can hydrate internal estimates. | Capacity warnings can be suggested. | Not confirmed as commercial truth. | Operation-to-workcenter mapping after ExecutionPlan. | Machine rates may leak into client hourly pricing. |
| Employees / Skills / Capacity | FORBIDDEN_NOW | Employee and workforce services | `employees.py`; employee mobile identity/tasks; execution workforce services | Employee/attendance/task assignment infrastructure exists. | HR and assignments can hydrate execution context. | Skills/capacity can be suggested later. | Not part of Product Truth/Quote. | Skills/capacity after plan shape exists. | Employees may become quote tariff or premature resource constraint. |
| ExecutionReality | FORBIDDEN_NOW | Execution reality services | `execution_reality_service.py`; `execution_reality_workforce.py`; pricing/cost contract | Actuals infrastructure exists. | Actuals hydrate profitability/reality later. | Actual variance can warn later. | Not applicable before order/execution. | Actuals after production. | Actuals could rewrite accepted commercial price. |
| Employee Mobile | FORBIDDEN_NOW | Employee mobile services/routers | `employee_mobile_tasks_service.py`; `employee_mobile_tasks.py`; roadmap | Mobile task domain exists elsewhere. | Employee/task identity can hydrate mobile. | Mobile can later show assigned tasks. | Not connected to this Product Truth slice. | Final-final after stable ExecutionPlan/Reality. | Mobile would capture bad model if upstream truth is unstable. |

---

## Existing Intake V6 Form Source Map

| UI area | Existing field/control | Component owner | Product Truth candidate? | Current source | Confirmation required? | Quote blocker? | Order blocker? | Execution blocker? | Payload status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Face card | face material | Face | yes | owner-approved default + missing explicit UI | yes | yes | yes | yes | missing canonical field | Default is plexiglas opal 3 mm, visible/displayed but not first-class runtime field. |
| Face card | face thickness | Face | yes | owner-approved default + missing explicit UI | yes | yes | yes | yes | missing canonical field | 3 mm default; 5 mm later exception. |
| Finish face | Oracal series | Finish | yes | existing form value | yes | yes | yes | yes | existing runtime field/encoded option | Existing options include 641, 651, 8500. |
| Finish face | Oracal color | Finish | yes | existing form value | yes | yes when Oracal active | yes | yes | existing runtime field | Per group colors visible for `maria`, `soare`, `ana`, `gradinita`. |
| Finish face | roll width | Finish | conditional | fallback/hydrated + existing form value | conditional | conditional | conditional | conditional | existing runtime field | May be commercial or internal optimization depending owner policy. |
| Finish/artwork | print required | Finish / Artwork | yes | existing form value + fallback/hydrated | yes | yes when print active | yes | yes | missing canonical field | Currently encoded in `print_laminate` / execution type; needs explicit boolean later. |
| Finish/artwork | lamination required | Finish / Artwork | yes | existing form value + fallback/hydrated | yes | conditional | yes | yes | missing canonical field | Must remain separate from print_required. |
| Finish | finish target | Finish | yes | existing UI zone + missing explicit canonical field | yes | yes | yes | yes | missing canonical field | UI zones imply face/cant/artwork, but Product Truth needs explicit target. |
| Return/cant | return/cant depth | Return / Cant | yes | existing form value + fallback/hydrated | yes | yes | yes | yes | existing runtime field | Runtime shows 60 mm. |
| Return/cant | return/cant color/RAL/finish | Return / Cant | yes | existing form value | yes | yes when finish active | yes | yes | existing runtime field | RAL/Oracal/white/black/gold/silver/vopsit options exist. |
| Backing | backing / Forex | Back | yes | existing form value + owner default | yes | yes | yes | yes | existing runtime field | `forex_10_no_bevel` / `forex_10_with_bevel`. |
| Backing | sanfren | Back | yes | existing form value | yes | conditional | yes | yes | existing runtime field | Derived from backing mode as `back_bevel_enabled`. |
| Lighting | lighting mode | Lighting | yes | existing form value + fallback/hydrated | yes when illuminated | yes when illuminated | yes | yes | existing runtime field | Runtime shows LED modules. |
| Lighting | LED settings | Lighting / Electrical | yes | existing form value + derived | yes | conditional | yes | yes | existing runtime field | Counts/watts can be derived; source state must be explicit later. |
| Electrical | cable defaults | Electrical | yes/conditional | owner-approved default | yes when commercial exception | conditional | yes | yes | future field | Defaults: 1 m 2x0.75 letters, 5 m 2x1.5 final feed. |
| Electrical | extra cable/site details | Electrical | conditional | missing / future field | yes when requested | conditional | yes | yes | future field | Order/execution blocker unless commercial scope changes offer. |
| Electrical | PSU placement | Electrical | yes/conditional | missing / future field | yes before order | conditional | yes | yes | future field | Selected PSU watts exists; placement does not. |
| Artwork | printed_artwork | Artwork | yes | analyzer suggestion + operator confirmed | yes | yes | yes | yes | existing runtime + missing canonical field | Runtime shows `SUGGESTED` and `CONFIRMED`; suggestion is not automatic print. |
| Artwork | artwork-only | Artwork | yes | existing form/control partial | yes when relevant | yes | yes | yes | existing runtime/display partial | Must be explicit when artwork is not produced as product. |
| Artwork | ignored | Artwork / Layer roles | yes | operator confirmed | yes | yes if relevant | yes | yes | existing runtime field | Ignored must be explicit, not silent omission. |
| Support | support required | Support | yes | missing canonical field; current bridge from mounting | yes when support active/suggested | conditional | yes | yes | missing canonical field | Must not be inferred silently from mounting. |
| Support | support type | Support | yes | partial via `steel_bars` / `aluminum_bars` in mounting enum | yes when support active | conditional | yes | yes | missing canonical field | Needs separate support branch. |
| Support | support source | Support | yes | analyzer suggestion / operator / owner default later | yes when suggested | conditional | yes | yes | future field | SVG roles `support_panel` / `frame` become suggestions only. |
| Mounting | mounting scope | Mounting | yes | owner-approved docs + missing UI control | yes | yes when commercial scope changes offer | yes | yes | missing canonical field | Values: no mounting, included, external, to decide. |
| Mounting | mounting system | Mounting | yes | existing form value + fallback/hydrated | yes | yes | yes | yes | existing runtime field | Runtime shows Direct perete. |
| Mounting | mounting template required | Mounting | yes | existing form value | yes | conditional | yes | yes | existing runtime field/target canonical future | Runtime shows template enabled. |
| Mounting | mounting surface | Mounting | conditional | missing / future field | yes before order/execution | conditional | yes | yes | future field | Site/method details later unless commercial impact exists. |
| Pricing area | commercial preview | Pricing boundary | no | preview/dry-run | no as Product Truth | no Product Truth blocker | no | no | not Product Truth | Pricing Registry follows truth; CostEngine internal-only. |

---

## Product Truth Canonical Payload Design - DOCUMENTED_NOT_IMPLEMENTED

**DOCUMENTED_NOT_IMPLEMENTED**

This is the future payload design only. It must not be implemented without owner GO.

```yaml
product_truth:
  metadata: {}
  source_svg: {}
  layers: []
  groups: []
  components:
    face: {}
    back: {}
    return_cant: {}
    finish: {}
    artwork: {}
    lighting: {}
    electrical: {}
    support: {}
    mounting: {}
    pricing_boundary: {}
  readiness: {}
  blockers: []
  warnings: []
  audit: []
```

### State model

| State | Meaning | Rule |
|---|---|---|
| `suggested` | Analyzer/system proposal | Never final truth alone. |
| `confirmed` | Explicit operator-confirmed truth | Can feed downstream if blockers clear. |
| `fallback` | Template/default value | Must be visible; not final silently. |
| `hydrated` | Loaded saved/transitional value | Must show provenance. |
| `manual` | Operator-entered override | Needs audit trail and save state. |
| `blocked` | Missing truth that blocks a gate | Must be action-oriented. |
| `warning` | Risk/debt that does not block current gate | Must not hide blockers. |
| `not_applicable` | Component does not apply | Not a missing-field blocker. |

### Top-level fields

| Field | Type | Source | Status model | Confirmation owner | Relevance | Default behavior | Blocker behavior | Notes |
|---|---|---|---|---|---|---|---|---|
| `metadata.workspace_id` | string | Intake V6 | confirmed/hydrated | system | all | hydrate from workspace | block if missing | Links truth to workspace. |
| `metadata.intake_id` | string | route/workspace | confirmed/hydrated | system | all | hydrate | block if missing | `IR-MR18L96M`. |
| `metadata.template_code` | string | ProductSystem binding | confirmed/hydrated | operator/system | quote/order/execution | hydrate template | block if ambiguous | `TPL-VOLUMETRIC-LETTERS_v2`. |
| `source_svg.file_name` | string | SVG upload/analyzer | confirmed/hydrated | operator/system | quote/order/execution | hydrate existing SVG | block if SVG path required and missing | `gradi-curat.svg`. |
| `source_svg.analysis_status` | enum | analyzer | suggested/confirmed/warning/blocked | system/operator | review readiness | suggested after parse | block if unusable | SVG analysis alone is not Product Truth. |
| `layers[]` | array | analyzer + operator | suggested/confirmed/manual/ignored | operator | quote/order/execution | analyzer prefill | block unresolved production layers | Holds role, source layer, display name, confirmation state. |
| `groups[]` | array | analyzer + operator | suggested/confirmed/manual | operator | quote/order/execution | analyzer prefill | block unresolved groups | Detected group identity and relationship to layers. |

### Component fields

| Component | Field | Type | Source | Status model | Confirmation owner | Quote/order/execution relevance | Default behavior | Blocker behavior | Notes |
|---|---|---|---|---|---|---|---|---|---|
| face | `material_family` | enum/string | owner default + form | fallback/confirmed/manual | operator | quote/order/execution | plexiglas opal default | block quote until confirmed | `CONFIRMED_IN_DOCS`; not explicit runtime field. |
| face | `thickness_mm` | number | owner default + form | fallback/confirmed/manual | operator | quote/order/execution | 3 mm default | block quote until confirmed | 5 mm later exception. |
| face | `group_refs[]` | array | analyzer/operator | suggested/confirmed | operator | quote/order/execution | analyzer groups | block if face target unresolved | Must map to detected groups. |
| back | `material` | enum/string | existing form | fallback/hydrated/confirmed | operator | quote/order/execution | Forex 10 mm | block if missing when back active | Encoded today in `backing_mode`. |
| back | `bevel_enabled` | boolean | existing form | fallback/confirmed | operator | conditional quote/order/execution | false default | block if policy active | `sanfren`. |
| return_cant | `depth_mm` | number | existing form | fallback/hydrated/confirmed/manual | operator | quote/order/execution | 60 mm default | block when return active | Runtime visible. |
| return_cant | `finish_type` | enum/string | existing form | fallback/confirmed/manual | operator | quote/order/execution | template/default | block if active and missing | RAL/Oracal/white/black/etc. |
| return_cant | `color_code` | string/null | existing form | manual/confirmed/blocked | operator | quote/order/execution | null | block if finish requires color | RAL/Oracal code. |
| finish | `finish_target` | enum | UI zone now; future field | suggested/confirmed/manual/blocked | operator | quote/order/execution | none | block if active finish has no target | face/cant/back/artwork/all policy later. |
| finish | `oracal_series` | enum | existing finish option | fallback/confirmed/manual | operator | quote/order/execution | none unless selected | block if Oracal active and missing | 641/651/8500. |
| finish | `oracal_color` | string | existing form | manual/confirmed/blocked | operator | quote/order/execution | null | block if Oracal active | Registry supplies options only. |
| finish | `roll_width_mm` | number/null | existing form | fallback/manual/warning | operator/policy | conditional | 1000/1260 fallback | warning or blocker by owner policy | Can be internal optimization. |
| finish | `print_required` | boolean/null | future explicit field | suggested/confirmed/manual/blocked | operator | quote/order/execution when print active | no silent default | block for artwork/print path | Separate from lamination. |
| finish | `lamination_required` | boolean/null | future explicit field | suggested/confirmed/manual/blocked | operator | conditional quote/order/execution | no silent default | block if policy requires | Separate from print. |
| finish | `apply_stage` | enum/null | future field | manual/confirmed/blocked | operator/process owner | conditional quote/order/execution | null | block when stage changes commercial/process path | T06/T19E detail later. |
| artwork | `printed_artwork[]` | array | analyzer + form | suggested/confirmed/manual | operator | quote/order/execution | analyzer suggests | block until confirmed/ignored/artwork-only | `printed_artwork` is suggestion, not final print. |
| artwork | `artwork_only` | boolean/null | form/operator | manual/confirmed/blocked | operator | quote/order/execution | null | block when guard triggers | Avoid producing/quoting accidental artwork. |
| lighting | `lighting_mode` | enum/bool | existing form | fallback/confirmed/manual | operator | quote/order/execution if lit | default lit in current path | block if illuminated and missing | LED modules/strip. |
| lighting | `led_settings` | object | form + derived | hydrated/confirmed/warning | operator/system | conditional | derive counts | warning/block depending field | Counts must keep source flags. |
| electrical | `psu_selected_watts` | number | existing form | fallback/confirmed/manual | operator | conditional quote/order/execution | contract default | block if lit and policy needs | Runtime selected 100W. |
| electrical | `cable_defaults` | object | owner-approved default | fallback/confirmed | operator/policy | conditional quote/order/execution | 1 m 2x0.75 + 5 m 2x1.5 | block only if special scope | Commercial default. |
| electrical | `psu_placement` | enum/string/null | future form | manual/confirmed/blocked | operator | order/execution; quote if commercial | null | block before order/execution | Hidden transformer/site detail. |
| support | `support_required` | `yes/no/suggested/unknown` | form/operator/analyzer/product rule | suggested/confirmed/manual/blocked/warning | operator | conditional quote; order/execution if active | unknown unless explicit | block when support active/suspected | Separate from mounting. |
| support | `support_type` | enum | form/operator | suggested/confirmed/manual/blocked | operator | conditional quote; order/execution if active | none only if support_required=no | block if support_required=yes and missing | `aluminum_bars`, `metal_frame`, etc. |
| support | `support_source` | enum | analyzer/operator/default/rule | suggested/confirmed/manual | operator/system | audit/order/execution | null | warning if unclear | `detected_svg`, `operator_selected`, `owner_default`, `product_rule`. |
| support | `support_quote_relevant` | boolean/null | policy/operator | confirmed/manual/warning | operator/policy | quote | null | warning/block by policy | Determines commercial line. |
| support | `status` | state enum | product_truth | all states | operator/system | all | blocked/unknown | block as needed | Must not be derived silently from `mounting_system`. |
| mounting | `mounting_scope` | enum | future form | confirmed/manual/blocked | operator | quote/order/execution | `to_be_decided` until chosen | block quote when commercial mounting scope matters | no mounting/included/external/to decide. |
| mounting | `mounting_system` | enum | existing form | fallback/hydrated/confirmed/manual | operator | quote/order/execution | direct_wall fallback | block if missing | Mounting truth only. |
| mounting | `mounting_surface` | enum/string/null | future form | manual/confirmed/warning/blocked | operator | order/execution; quote if commercial | null | block later | Site/method detail. |
| mounting | `mounting_template_required` | boolean | existing form/future canonical | fallback/confirmed/manual | operator | conditional quote/order/execution | current template flag | block if template line active and missing | Current `mounting_template_enabled`. |
| mounting | `status` | state enum | product_truth | all states | operator/system | all | fallback/blocked | block as needed | Must not activate support silently. |
| pricing_boundary | `commercial_preview_status` | enum | preview service | warning/not_applicable | system/owner | quote only after truth | preview only | must not repair Product Truth | Pricing Registry coverage after truth. |

### Blockers, warnings, readiness, audit

| Field | Type | Source | Status model | Confirmation owner | Relevance | Default behavior | Blocker behavior | Notes |
|---|---|---|---|---|---|---|---|---|
| `readiness.ready_for_review` | boolean | analyzer/operator | blocked/confirmed | system/operator | Review | false until layer role minimum | blocks Review | Already exists as flow concept. |
| `readiness.ready_for_internal_draft` | boolean | Intake V6 | blocked/confirmed/warning | operator/system | internal draft | false until confirmations | blocks draft CTA | Runtime has draft-ready state but still preview-only. |
| `readiness.ready_for_commercial_proposal` | boolean | Product Truth + pricing coverage | blocked/confirmed/warning | system/owner | offer | false | block official offer | Design only. |
| `readiness.ready_for_quote_snapshot` | boolean | Product Truth + CommercialPriceProposal | blocked/confirmed | owner/system | quote snapshot | false | block snapshot | Design only. |
| `readiness.ready_for_order_snapshot` | boolean | accepted quote snapshot | blocked/confirmed | owner/system | order | false | block order | Design only. |
| `readiness.ready_for_product_aggregate` | boolean | frozen order/product truth | blocked/confirmed | system | aggregate | false | block aggregate | Forbidden now. |
| `readiness.ready_for_execution_plan` | boolean | aggregate/task graph | blocked/confirmed | system/production | execution | false | block execution | Forbidden now. |
| `blockers[]` | array | all components | blocked | system/operator | all gates | empty only when clean | blocks according to severity | Product Truth blockers, not pricing repair. |
| `warnings[]` | array | all components | warning | system/operator | all gates | empty | no gate unless escalated | Includes trigger mismatch. |
| `audit[]` | array | system/operator | all states | operator/system | all | append-only | missing audit blocks trust | Tracks who/when/source/status. |

---

## Product Truth Readiness Rules - Design Only

**DOCUMENTED_NOT_IMPLEMENTED**

| Readiness flag | Entry rule | Exit / unlock target | Must stay blocked by | Must not depend on |
|---|---|---|---|---|
| `ready_for_review` | SVG analysis exists and role confirmation route can be evaluated | Review step access | missing/invalid SVG analysis or unresolved layer role gate | pricing coverage, CostEngine, ProductAggregate |
| `ready_for_internal_draft` | Review component values and required confirmations are complete enough for internal draft | internal draft CTA | unresolved Review confirmations, draft limit confirmations, Product Truth blockers surfaced for internal draft | quote/order/materialization |
| `ready_for_commercial_proposal` | Product Truth complete for quote plus commercial coverage exists | CommercialPriceProposal official proposal | layer roles incomplete, finish target missing, support/mounting ambiguity, active component missing truth, commercial pricing coverage missing after truth | CostEngine minutes, workcenter hourly rate, employees |
| `ready_for_quote_snapshot` | complete Product Truth + approved CommercialPriceProposal | Quote Snapshot freeze | unapproved commercial preview, missing accepted truth, unresolved owner commercial blocker | mutable Intake live values after freeze |
| `ready_for_order_snapshot` | accepted Quote Snapshot and accepted product/commercial configuration | Order Snapshot | quote not accepted, revision pending, live mutable form drift | recomputation from ProductDefinition without revision |
| `ready_for_product_aggregate` | frozen Order Snapshot exists with product truth and accepted modules | ProductAggregate | incomplete order/product snapshot | live Intake form |
| `ready_for_execution_plan` | ProductAggregate and Task Graph are stable | ExecutionPlan | missing task DAG, unresolved workcenter dependency | employee mobile, actuals |

Rules:

- SVG analysis alone is not Product Truth.
- Analyzer suggestions are not confirmed truth.
- Owner-approved defaults are prefill/default, not final truth until confirmed where required.
- Fallback/hydrated values are not final truth silently.
- Product Truth must be complete before CommercialPriceProposal or Quote Snapshot.
- Pricing Registry must not repair Product Truth.
- CostEngine internal data must not block quote unless owner policy marks it commercial.
- Support and mounting must be separate.
- `T06` / `T19E` is execution process sequencing later, not the main quote question unless commercial impact exists.

---

## ProductDefinition Boundary

**CONFIRMED_IN_DOCS** and **CONFIRMED_IN_CODE** as partial/read-only preview today.

ProductDefinition may:

- consume confirmed Product Truth;
- map product variant;
- select compatible ProductSystem template/module set;
- prepare product definition output;
- emit validation, blockers, warnings, and deterministic module activation state.

ProductDefinition must not:

- guess layer roles;
- decide artwork ignored/printed;
- infer support from mounting silently;
- decide finish target;
- decide `print_required` / `lamination_required`;
- repair missing Product Truth;
- calculate commercial price;
- create tasks;
- create ExecutionPlan;
- write Product Truth or mutate DB in the preview path.

Current code risk:

- `product_definition_builder_service.py` derives `metal_support_required` from `mounting_system` for transitional canonical values. This must be replaced later by explicit `support.support_required` after payload runtime exists.

---

## ProductSystem / Dossier / Module Boundary

**CONFIRMED_IN_CODE**, **CONFIRMED_IN_DOCS**, **PRODUCTSYSTEM_CONTRACT_LATER**, **PAYLOAD_RUNTIME_LATER**.

Template/dossier should know:

- product family and compatible templates;
- module vocabulary;
- always-on, optional, and conditional module definitions;
- allowed fields/options and component contracts;
- downstream destination hints for ProductDefinition, Aggregate, cost, quote, order, and task preview.

Module triggers should receive:

- confirmed Product Truth fields;
- explicit module-compatible values;
- not raw ambiguous UI fallback values.

Trigger classification:

| Module/trigger | Current status | Target rule |
|---|---|---|
| `geometry_svg` | always_on/required when SVG exists | uses `source_svg` and geometry truth. |
| `debitare_fata` | always_on after analysis for volumetric letters | uses face Product Truth. |
| `modelare_cant` | required linked module | uses return/cant Product Truth. |
| `debitare_spate` | always_on/required when back active | uses back Product Truth. |
| `sistem_led` | conditional on lighting truth | uses lighting/electrical Product Truth. |
| `finisaje` | always/conditional depending finish/template | uses finish Product Truth. |
| `structura_suport -> metal_support_required` | current mismatch | later uses `support.support_required`, not raw `mounting_system`. |

Current mismatch:

```text
structura_suport -> metal_support_required
finish_setup.mounting_system
TRIGGER_FIELD_MISMATCH
```

Target rule:

- mounting module uses mounting fields;
- support module uses support fields;
- no module should use `mounting_system` as silent support truth;
- bridge may exist only as explicit migration logic with warning and source state.

Runtime fixes are later only:

- `PRODUCTSYSTEM_CONTRACT_LATER`
- `PAYLOAD_RUNTIME_LATER`

---

## CommercialPriceProposal / Offer Boundary

**CONFIRMED_IN_CODE**, **CONFIRMED_IN_DOCS**, partial runtime preview today.

Rules:

- CommercialPriceProposal consumes complete Product Truth.
- It may produce internal preview / dry-run.
- Official offer must come after Quote Snapshot rules.
- Pricing Registry checks commercial coverage after truth exists.
- It must not decide Product Truth.
- It must not calculate final client price by hour/minute.
- CostEngine remains internal-only for time/minute/capacity/actuals.
- Current Intake V6 preview is not final quote.
- Current preview/dry-run does not create order or tasks.
- Owner approval is required for reprice.

Runtime observation:

- Review shows commercial preview total and explicitly says official offer exists only after Quote Snapshot V2.
- Confirmare says draft internal only, no client offer, no order, no production, no stock movement.

Current code risk:

- `commercial_price_proposal_service.py` still includes/excludes `structura_suport` from `mounting_system` in a bridge path. Later runtime must consume explicit support truth.

---

## Quote Snapshot / Order Snapshot Boundary

**DOCUMENTED_NOT_IMPLEMENTED** for this volumetric E2E chain.

Target rules:

- Quote Snapshot freezes CommercialPriceProposal and Product Truth used for offer.
- Quote Snapshot must include the Product Truth source version, component statuses, blockers cleared, warnings accepted, and commercial proposal version.
- Order Snapshot freezes accepted commercial/product configuration.
- Order must not depend on live mutable Intake V6 form values.
- Order must not recompute from changing ProductDefinition without explicit revision.
- Order Snapshot comes before ProductAggregate.

Current code status:

- Quote output snapshot candidate router exists and says it does not mutate Quote, Order, send email, or create final contract.
- Order snapshot services exist, but this task does not use or change them.

---

## ProductAggregate Boundary

**FORBIDDEN_NOW** for implementation in this slice.

ProductAggregate is after Order Snapshot.

It composes the accepted product into a manufacturable aggregate. It must:

- consume frozen order/product snapshot;
- preserve accepted modules/components/material/operation structure;
- expose warnings/conflicts without repairing Product Truth;
- prepare structured product components for Task Graph.

It must not:

- be created from incomplete Intake V6;
- repair missing Product Truth;
- activate support from mounting silently;
- change accepted commercial truth;
- create tasks or ExecutionPlan.

Current code status:

- `product_aggregate_service.py` can build read-only aggregate from ProductSystem/dossier/template links.
- It carries `TRIGGER_FIELD_MISMATCHES = {'metal_support_required': 'mounting_system'}` as warning debt.

Status: `FORBIDDEN_NOW until Product Truth + Quote Snapshot + Order Snapshot are stable`.

---

## Task Graph / ExecutionPlan Boundary

**FORBIDDEN_NOW**.

Rules:

- Task Graph comes after ProductAggregate.
- ExecutionPlan comes after Task Graph.
- Tasks must derive from active modules/components, not from a parallel catalog.
- ExecutionPlan schedules tasks, workcenters, dependencies, and resources after order/product truth is frozen.

T06/T19E sequencing belongs here later:

- `T19E`: foil application after body formed/assembled;
- task blocked until operator confirms previous assembly/body task;
- `T06`: foil/cant application before modeling if process requires.

Workcenters/utilaje and employees/skills/capacity come later.

Employee Mobile is final-final.

Current code status:

- ExecutionPlan, task, workcenter, machine, employee, execution reality, and mobile services exist in the repo.
- They are not the next implementation layer for this volumetric letters Product Truth work.

---

## Gap Matrix

| Gap ID | Area | Description | Current source | Required target | Risk | Phase | Recommended next slice | Owner GO required? | Status |
|---|---|---|---|---|---|---|---|---|---|
| E2E-G01 | Face | Face material canonical field missing | owner default/display chip | `product_truth.components.face.material_family/material_code` | ProductDefinition/pricing guesses face material | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G02 | Face | Face thickness canonical field missing | owner default/display chip | `face.thickness_mm` | wrong material/execution/quote | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G03 | Finish | Finish target canonical field missing | UI zones | `finish.items[].target` | Pricing/ProductDefinition repairs target | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G04 | Finish | `print_required` not explicit | execution type `print_laminate` | explicit boolean | print auto-assumed | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G05 | Finish | `lamination_required` not explicit | execution type `print_laminate` | explicit boolean separate from print | lamination auto-assumed | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G06 | Support/Mounting | Support vs mounting split not runtime canonical | `mounting_system`, `metal_support_required` bridge | separate `support` and `mounting` branches | support silently inferred from mounting | Phase 3/5 | Product Truth payload design then ProductSystem contract migration | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G07 | Support | Support source from SVG missing | `support_panel`/`frame` suggestions | `support.support_source=detected_svg` with status suggested | SVG suggestion activates support | Phase 3 | Product Truth payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G08 | Support | `support_required` missing | derived `metal_support_required` | `support.support_required` | module activation wrong | Phase 3 | Payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G09 | Mounting | `mounting_scope` missing | owner docs/display chip | no mounting/included/external/to decide | commercial scope unclear | Phase 3 | Payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G10 | Mounting | mounting template required needs canonical naming | `mounting_template_enabled` | `mounting.mounting_template_required` | template quote/order drift | Phase 3 | Payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G11 | Electrical | Cable defaults vs extra details not canonical | owner answers/display chip | cable defaults + site extras branch | cable scope ambiguous | Phase 3 | Payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G12 | Electrical | PSU placement missing | PSU watts only | `electrical.psu_placement` | order/execution detail guessed | Phase 3/Order | Payload design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G13 | Readiness | Product Truth readiness flags not runtime canonical | readiness docs/UI | typed readiness object | quote unlock too early or too late | Phase 3 | readiness design | YES | NEEDS_PAYLOAD_DESIGN |
| E2E-G14 | ProductDefinition | Consumes transitional payload and derives support | builder service | consume canonical Product Truth only | hidden inference | Phase 4 | ProductDefinition consumption design | YES | NEEDS_PAYLOAD_RUNTIME |
| E2E-G15 | ProductSystem | Module trigger mismatch | registry warning | `structura_suport` uses support fields | support/mounting semantic collapse | Phase 5 | ProductSystem contract alignment | YES | NEEDS_CONTRACT_FIX |
| E2E-G16 | CommercialPriceProposal | Preview uses bridge active modules | commercial service | price only from complete Product Truth | offer line wrong | Phase 6 | Commercial boundary runtime after Product Truth | YES | FORBIDDEN_NOW |
| E2E-G17 | Quote Snapshot | Frozen Product Truth/offer snapshot missing for this flow | snapshot candidate infra | official Quote Snapshot from Product Truth | mutable Intake drift | Phase 7 | Quote Snapshot design/runtime | YES | FORBIDDEN_NOW |
| E2E-G18 | Order Snapshot | Accepted order freeze missing for this flow | order snapshot infra | Order Snapshot from accepted Quote Snapshot | order recomputes from live values | Phase 8 | Order Snapshot design/runtime | YES | FORBIDDEN_NOW |
| E2E-G19 | ProductAggregate | Aggregate can exist before frozen Product Truth/order | aggregate service | aggregate after Order Snapshot | aggregate repairs Intake | Phase 9 | Aggregate contract later | YES | FORBIDDEN_NOW |
| E2E-G20 | Task Graph | Task graph not derived from frozen aggregate in this chain | dry-runs/task services | DAG from ProductAggregate | parallel task catalog | Phase 10 | Task Graph later | YES | FORBIDDEN_NOW |
| E2E-G21 | ExecutionPlan | ExecutionPlan before Task Graph forbidden | execution services | plan after DAG | premature materialization | Phase 11 | ExecutionPlan later | YES | FORBIDDEN_NOW |
| E2E-G22 | Employee Mobile | Mobile exists but must be final-final | employee mobile services | mobile after stable execution model | bad task capture | Phase 12+ | Employee Mobile later | YES | FORBIDDEN_NOW |

---

## Implementation Roadmap From Here

| Phase | Goal | Entry criteria | Exit criteria | Forbidden shortcuts | Tests required | Runtime check required |
|---|---|---|---|---|---|---|
| Phase 2 completion | UI-only gaps complete; Product Truth payload design docs complete; readiness design complete | current Phase 2 docs/worklogs pass | owner accepts payload/readiness design docs | no runtime payload, no new form | docs diagnostics; focused UI tests only if labels change | Intake V6 read-only visual audit |
| Phase 3 | Product Truth canonical payload runtime, small slice; no ProductDefinition yet | final payload design doc approved | `product_truth` branch written/read with source states for one narrow component slice | no ProductDefinition, no pricing, no aggregate | payload unit tests, migration compatibility tests, readiness tests | existing workspace shows source states without quote/order mutation |
| Phase 4 | ProductDefinition consumes Product Truth | Phase 3 stable payload | ProductDefinition reads confirmed truth and emits module state without guessing | no pricing, no tasks | builder tests for missing/confirmed/fallback truth | ProductDefinition preview shows no hidden support-from-mounting truth |
| Phase 5 | ProductSystem/Dossier module contract alignment | ProductDefinition source stable | triggers consume Product Truth fields; `structura_suport` bridge migrated or explicit | no DB/schema without approved migration | module registry/contract tests | ProductSystem warning changes only after bridge is explicit |
| Phase 6 | CommercialPriceProposal / Offer uses Product Truth | complete Product Truth + ProductDefinition | commercial preview/offer reads truth only; no hourly client price | no quote/order snapshot materialization unless phase starts | commercial rule tests, no-hourly-token tests | Intake V6 preview labels remain preview-only |
| Phase 7 | Quote Snapshot | approved commercial proposal | Quote Snapshot freezes Product Truth + commercial proposal | no Order Snapshot | snapshot immutability tests | quote snapshot does not read live Intake after freeze |
| Phase 8 | Order Snapshot | accepted Quote Snapshot | Order Snapshot freezes accepted product/commercial config | no ProductAggregate yet | quote-to-order preservation tests | order snapshot survives Intake form changes |
| Phase 9 | ProductAggregate | stable Order Snapshot | Aggregate from frozen order/product truth | no Intake repair, no task graph shortcuts | aggregate provenance tests | aggregate warnings do not mutate truth |
| Phase 10 | Task Graph | ProductAggregate stable | task DAG from active modules/components | no parallel task catalog | DAG/dependency tests, T06/T19E sequencing tests | dry-run only until owner GO |
| Phase 11 | ExecutionPlan | task graph stable | scheduled execution plan with workcenter/resource hooks | no mobile, no actuals rewrite | execution plan gate tests | plan generated only from accepted order/task graph |
| Phase 12+ | Utilaje / Angajati / ExecutionReality / Employee Mobile later | ExecutionPlan stable | capacity, skills, actuals, mobile integrated downstream | no client hourly pricing, no retroactive repricing | resource/capacity/actuals/mobile tests | mobile only after stable execution runtime |

---

## Runtime Observation - Read Only

**OBSERVED_RUNTIME** on `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`.

Observed:

- Current stage: Review after read-only navigation from Confirmare; Confirmare was accessible.
- Data source: `LIVE / DB`.
- Workspace: `IV6-BB8EE3F8`.
- SVG: `gradi-curat.svg`.
- Layer confirmation status: Straturi step checked; Review accessible after legitimate confirmation.
- Review accessibility: yes.
- Product Truth chips visible: yes for Face, Finish, Return/Cant, Artwork, Mounting, Support, Pricing boundary.
- Support/mounting warning visible: yes. Runtime shows `mounting_system is Mounting, not Support truth`, `metal_support_required means Support/Bare, not mounting method`, and `Support and mounting are separate decisions`.
- Preview/dry-run visible: yes, commercial/internal preview visible and labeled preview/internal.
- CTA status: Confirmare was reachable and showed `Creeaza draft intern V6`; no CTA was clicked.
- Blocker/warning: system checks show `TRIGGER_FIELD_MISMATCH: structura_suport link=metal_support_required intake=finish_setup.mounting_system`.
- No false Pricing Registry blame observed.
- No commercial hour/minute pricing observed in changed Product Truth chip surfaces; cost shown as internal estimate.
- No forced confirmations, draft, order, production, stock movement, or materialization were triggered.

---

## Final Recommendation

Recommendation: `A. PHASE_3_PRODUCT_TRUTH_PAYLOAD_DESIGN_DOCS`.

Why:

- Phase 2 UI-only labels and gap closure are sufficient for payload design.
- Support/mounting split is documented and visible.
- The next risk is designing canonical payload shape deeply enough before runtime.
- No additional UI-only gap blocks payload design.

---

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`.
2. Current roadmap phase: Phase 2 transitioning toward Phase 3 design.
3. Roadmap status of this task: NEXT / full E2E alignment map before Product Truth payload.
4. Why this task belongs here: it consolidates Phase 2 outputs, defines the Product Truth payload target before runtime, prevents downstream systems from repairing missing truth, and keeps the roadmap order.
5. What this task must not unlock automatically: Product Truth runtime payload, ProductDefinition, ProductSystem/Dossier runtime changes, CommercialPriceProposal runtime, Quote Snapshot, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate result: PASS.
7. Roadmap implementation progress: 12/100%.
8. Roadmap alignment score: 100/100%.
9. Cat sunt in directia stabilita: 100/100%.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.

---

## Forbidden Confirmation

Confirmed:

- no new form;
- no duplicate controls;
- no new wizard;
- no backend runtime changes;
- no DB/schema/seeds;
- no API changes;
- no payload runtime changes;
- no ProductTruth runtime canonical payload implementation;
- no readiness/gating runtime changes;
- no analyzer runtime changes;
- no pricing runtime changes;
- no ProductDefinition runtime changes;
- no ProductSystem runtime changes;
- no ProductAggregate implementation;
- no Task Graph implementation;
- no ExecutionPlan implementation;
- no quote/order/execution materialization;
- no forced confirmations;
- no Employee Mobile.