# Intake V6 UI Surface Inventory Contract

## 1. Purpose

This document is the official UI Surface Inventory Contract for reconstructing the current Intake V6 operator flow through Product System, Form System, and Product Truth.

Intake V6 is the real runtime baseline. It is the factual UI that operators use today for volumetric letters intake, SVG analysis, Review, and Confirmare. However, the current UI must not be treated as the final architecture merely because it exists. Product System + Form System + Product Truth must be able to reproduce the same behavior modularly from explicit contracts.

This contract defines:

- every major Intake V6 UI surface;
- the step where each surface appears;
- the files and product modes each surface applies to;
- current implementation source;
- Product System owner;
- Form System owner;
- expected Product Truth path;
- source/state model;
- readiness dependency;
- commercial boundary;
- downstream boundary.

This contract is based on the final multi-SVG audit:

`docs/qa/intake-v6-multi-svg-e2e/2026-07-04/INTAKE_V6_MULTI_SVG_E2E_FORM_SYSTEM_RECONSTRUCTION_AUDIT_V1.md`

Material consumption, nesting, selected roll width, waste/efficiency, and conditional split/panelization are governed by:

`docs/architecture/product-system/MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`

Concrete Form System fields for these surfaces are mapped by:

`docs/architecture/product-system/FORM_SYSTEM_FIELD_CONTRACT_MAP.md`

This document does not authorize Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB schema, seed, migration, or UI redesign work.

## 2. Scope

In scope:

- Pas 1 / Straturi;
- Pas 2 / Review;
- Pas 3 / Confirmare;
- multi-SVG behavior for the four locked real SVG files;
- UI source/state and Product Truth path expectations;
- Form System reconstruction boundaries;
- commercial preview boundary;
- downstream safety boundary;
- current systemic vs partial vs UI-only status.

Out of scope:

- Pricing formula changes;
- Quote or Order changes;
- Execution or Executie changes;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB schema;
- seed or migration scripts;
- SVG Analyzer implementation changes;
- Intake V6 UI redesign;
- Logo root offerability;
- component root or component quote activation.

## 3. Canonical Test Files

| File | Type | Expected Flow | Expected Template Context | Commercial State |
| --- | --- | --- | --- | --- |
| `gradi-curat.svg` | Full Letters fixture with linked logo/artwork | Pas 1 -> Pas 2 -> Pas 3; 4 Ana/Maria pseudo letter groups plus 2 logo/artwork layers | `TPL-VOLUMETRIC-LETTERS_v2` root with linked `TPL-VOLUMETRIC-LOGO_v1` child segments | Letters commercial preview may be visible, but row/link Product Truth diagnostics remain partial until explicit confirmation policy exists |
| `litere-vol-1-layer.svg` | Generic one-layer Letters file | Pas 1 -> Pas 2 -> Pas 3; one neutral `pseudo fill-*` letter group | `TPL-VOLUMETRIC-LETTERS_v2` root | Letters commercial preview may be visible; generic fill semantics need explicit Product Truth contract |
| `litere-vol-2-layere.svg` | Generic two-layer Letters file | Pas 1 -> Pas 2 -> Pas 3; two neutral `pseudo fill-*` letter groups | `TPL-VOLUMETRIC-LETTERS_v2` root | Letters commercial preview may be visible; generic fill semantics need explicit Product Truth contract |
| `logo.svg` | Logo-only artwork candidate | Pas 1 -> Pas 2 -> Pas 3 as safe candidate/read-only; no Vector Litere rows | `TPL-VOLUMETRIC-LOGO_v1` candidate/read-only, not root offerable | Commercial surface must be guarded/blocked; readiness is `logo_only_candidate_not_offerable` |

## 4. Intake V6 Step Inventory

| Step | UI surface | Purpose | Current source | Owner system | Product Truth impact | Commercial impact | Downstream impact | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pas 1 / Straturi | SVG file upload and preview | Load current source artifact and display analyzer result | `IntakeV6SvgAnalyzerStep`, `IntakeV6LayersFileConfirmPanel`, SVG analyzer client | Intake workspace + SVG Analyzer | Produces source artifact and geometry/layer candidates | None directly | Blocks Review until roles complete | Systemic partial |
| Pas 1 / Straturi | Layer role setup | Operator confirms `face`, `printed_artwork`, `logo`, `ignore`, etc. | `layer_role_setup`, role table, role bridge | Form System SVG/layer role module | Creates layer role truth candidate | Feeds commercial preview only after role confirmation | Blocks downstream when incomplete | Systemic |
| Pas 1 / Straturi | Template candidate hints | Suggest linked Logo or active Letters context from layer roles | layer target helper + linked template contract | Product Template / Component Template capability | Template candidate path, not final root truth | Cannot unlock Logo commercial root | Blocks Logo root offerability | Partial |
| Pas 2 / Review | Header and candidate context | Show active root or candidate/read-only context | `IntakeV6Header`, workspace payload readiness | Product Template root / candidate status | Source context and template candidate display | Must guard non-offerable Logo | No downstream effect by itself | Systemic partial |
| Pas 2 / Review | Finisaje tab | Main technical/commercial review for face, cant, artwork | Review state + finish payload | Form System section grouping | Aggregates finish/cant/artwork Product Truth candidates | Feeds material and commercial previews | May block Confirmare if incomplete | Partial |
| Pas 2 / Review | Vector Litere | Per letter group finish/cant controls | `IntakeV6ReviewLetterGroupsSection`, `letter_group_finishes` | Face, finish, return/cant components | `components.face_finish.letter_groups.*`, `components.return_cant.letter_groups.*` | Used by material/commercial previews | Should block final quote/order until row truth confirmed | Partial/high risk |
| Pas 2 / Review | Vector Atipic / logo | Per artwork/logo surface and cant controls | `IntakeV6ArtworkFinishSection`, `artwork_finishes` | Linked Logo child / finish_artwork | `linked_templates.TPL-VOLUMETRIC-LOGO_v1.segments.*`, `artwork.layers[]` | Used by material/commercial previews if root allows | Suggested binding must not create separate quote/order | Partial |
| Pas 2 / Review | Logo-only candidate guard | Prevent logo-only from looking offerable | readiness `logo_only_candidate_not_offerable`, UI guard | Product Template availability | `template.root_offerability`, `readiness.logo_only` | Blocks commercial surface and adjustments | Blocks draft/quote/order/execution | Systemic guard |
| Pas 2 / Review | Lighting | Configure illumination, LED, PSU, electrical hints | Review lighting section + finish payload + derived helpers | LED/electrical component | `components.lighting.*` | Feeds previews | Should block order/execution when ambiguous | Partial |
| Pas 2 / Review | Mounting/support | Configure mounting system, template, support implications | Review mounting tab + finish payload/defaults | mounting/support components | `components.mounting.*`, `components.support.*` | Feeds previews | Should block order/execution when ambiguous | Partial |
| Pas 2 / Review | Form System Backbone | Read-only diagnostic for root/components/fields/blockers | form contract endpoint + awareness panel | Form System | `form_system_backbone.*` | None directly | Downstream write intent false | Systemic diagnostic |
| Pas 2 / Review | Live calculation | Internal/commercial preview, filters, missing rates | `IntakeV6LiveCalculationSummary`, pricing/material endpoints | Commercial preview layer | Not final Product Truth | Preview only; must be guarded when not offerable | Must not create quote/order/execution | Partial/high risk |
| Pas 2 / Review | Materials/operations/consumables | Breakdown and task/operation preview | material breakdown/task preview endpoints | Component material/operation contracts later | Not final Product Truth today | Preview only | No task materialization | Partial/high risk |
| Pas 2 / Review | Commercial adjustments | Markup/discount/VAT/manual adjustment draft inputs | `IntakeV6PricingInputPanel`, `finish_setup.commercial_inputs` | Commercial preview policy | commercial input candidate | Affects preview; not final offer truth | Must not bypass Product Truth | Partial/high risk |
| Pas 2 / Review | Blockers/warnings | Surface readiness and warnings | header/footer status builders, readiness endpoints | Readiness system | `readiness.blockers[]`, `readiness.warnings[]` | May block preview/handoff | Blocks downstream when severe | Partial |
| Pas 3 / Confirmare | Summary/dashboard | Summarize workspace, SVG, dimensions, material/commercial state | confirm summary builder + endpoints | Product Truth/handoff policy | readiness summary candidate | Can look commercial; must respect readiness | CTAs gated | Partial |
| Pas 3 / Confirmare | Readiness gates/checklist | Operator boundary before handoff | handoff panel + footer confirm state | Handoff boundary | `operator_confirmation.*`, `handoff.*` | Required before write actions | Blocks draft/quote until explicit | Systemic partial |
| Pas 3 / Confirmare | Commercial surface | Offer/dry-run display and priced quote CTA | pricing preview/dry-run + pricing panel | CommercialPriceProposal later | Not final Product Truth | Final-looking only when truth complete | Must not create order/execution | Partial/high risk |
| Pas 3 / Confirmare | Draft/quote handoff | Internal draft/priced quote buttons | backend handoff/write APIs | Quote/Offer layer | Requires complete Product Truth and explicit confirmation | Writes quote/offer when used | Must not create order/execution | Gated |
| Pas 3 / Confirmare | No-order/no-execution guard | State downstream safety | static copy + backend policy | Downstream boundary | downstream intent false | None | Prevents order/execution/task writes | Systemic |

## 5. UI Surface Contract

| Surface ID | Step | Surface name | Applies to | Current UI source | Product System owner | Form System owner | Product Truth path | Source/state model | Readiness dependency | Commercial boundary | Downstream boundary | Current status | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IV6-S1-UPLOAD | Pas 1 | SVG upload / source artifact | all files | `IntakeV6SvgAnalyzerStep`, file input, workspace payload | root product consumes SVG module | `svg.source` field group | `svg.source.file_name`, `svg.source.file_hash` | `svg_analyzer` / `suggested` until persisted | `missing_svg` blocks | no pricing | no downstream writes | systemic | LOW |
| IV6-S1-PREVIEW | Pas 1 | SVG thumbnail / preview | all files | preview source + canvas | Product root visual evidence | SVG diagnostic surface | `svg.preview` | `svg_analyzer` / `suggested` | advisory | no pricing | no downstream writes | systemic | LOW |
| IV6-S1-GEOMETRY | Pas 1 | Geometry metrics | all files | analyzer geometry + quote geometry resolver | geometry component | geometry field group | `geometry.width_mm`, `geometry.height_mm`, `geometry.area`, `geometry.perimeter` | `svg_analyzer` / `suggested` | should block when confidence inadequate | preview input only | no downstream writes | partial | MEDIUM |
| IV6-S1-LAYER-ROLE-SETUP | Pas 1 | Layer role cards/table | all files | `layer_role_setup`, role table, role bridge | root template role vocabulary | SVG/layer roles | `svg.layer_roles[]` | `svg_analyzer` -> `operator_confirmed` | `layer_roles_incomplete` blocks | no direct pricing | blocks Review/downstream until complete | systemic | MEDIUM |
| IV6-S1-TEMPLATE-CANDIDATE | Pas 1 | Template candidate/read-only hint | all files, Logo special | layer target template helper, artwork-only panel | Product Template capability | template candidate field | `template.candidate`, `linked_templates.*` | `analyzer_semantic_expansion` / `candidate_read_only` | Logo root offerability blocks | cannot activate commercial root | no separate quote/order | partial | MEDIUM |
| IV6-S1-WARNINGS | Pas 1 | Analyzer warnings/status | all files | warnings panel/status overlay | Readiness taxonomy | blocker/warning fields | `readiness.warnings[]`, `readiness.blockers[]` | `backend_readiness` / `partial` | severe blockers block | no pricing | no downstream writes | partial | MEDIUM |
| IV6-S2-HEADER | Pas 2 | Header/template context | all files | `IntakeV6Header` | Product Template root/candidate | source context field | `source_context.template_code`, `template.root_offerability` | `payload_persisted` / `confirmed` or `candidate_read_only` | Logo uses not-offerable status | must guard non-offerable root | no downstream writes | systemic partial | LOW/MEDIUM |
| IV6-S2-REVIEW-TABS | Pas 2 | Finisaje / Iluminare / Montaj tabs | all files | `IntakeV6ReviewTabNav` | Product Template section grouping | Form section contract | `form.sections[]` | `UI_only` / `partial` | none by itself | no pricing by itself | no downstream writes | UI-only | MEDIUM |
| IV6-S2-VECTOR-LITERE | Pas 2 | Vector Litere card set | gradi, litere1, litere2 | `IntakeV6ReviewLetterGroupsSection` | Face/finish/return components | letter group field group | `components.face_finish.letter_groups.*`, `components.return_cant.letter_groups.*` | `svg_nearest_color_mapping`, `payload_hydrated_or_prior_state` / `suggested`, `hydrated` | letter readiness endpoint partial until rows confirmed | may feed preview only | should block final quote/order when row partial | partial | HIGH |
| IV6-S2-LETTER-FACE-FINISH | Pas 2 | Face finish controls | letter rows | color registry/selects + payload | face/finish component | face finish field | `components.face_finish.letter_groups.*.face_finish` | nearest mapping or operator input / suggested/confirmed | unconfirmed mapping partial | preview only until confirmed | should block order/execution if ambiguous | partial | HIGH |
| IV6-S2-LETTER-CANT | Pas 2 | Return/cant controls | letter rows | return cant fields + payload | return/cant component | return/cant field | `components.return_cant.letter_groups.*.return_cant` | payload/hydrated/prior state / hydrated | hydrated cant partial | preview only until confirmed | should block order/execution if ambiguous | partial | HIGH |
| IV6-S2-VECTOR-ATIPIC-LOGO | Pas 2 | Vector Atipic / logo cards | gradi linked logo | `IntakeV6ArtworkFinishSection` | linked Logo child template | linked logo segment fields | `linked_templates.TPL-VOLUMETRIC-LOGO_v1.segments.*` | payload + analyzer / confirmed role, suggested binding | linked segment endpoint partial | child-only; no separate commercial root | no separate quote/order/tasks | partial | MEDIUM |
| IV6-S2-LOGO-ONLY-CANDIDATE | Pas 2 | Logo-only safe candidate review | logo | artwork-only panel + Review guard | Logo product candidate | Logo candidate fields | `template.logo_candidate`, `artwork.layers[]` | `backend_readiness` / `candidate_read_only`, `not_offerable` | `logo_only_candidate_not_offerable` | commercial surface guarded/blocked | no quote/order/execution | systemic guard | LOW |
| IV6-S2-LIGHTING | Pas 2 | Lighting/LED/PSU section | all files if illuminated | Review lighting section + derived helpers | LED/shared lighting/profile | lighting field group | `components.lighting.*` | payload/derived/manual / hydrated/partial | lighting truth partial | preview input only | should block execution if ambiguous | partial | MEDIUM |
| IV6-S2-MOUNTING | Pas 2 | Mounting/support section | all files | Review mounting controls + payload | mounting/support components | mounting/support fields | `components.mounting.*`, `components.support.*` | fallback/default/manual / fallback/hydrated | mounting truth partial | preview input only | should block order/execution when ambiguous | partial | MEDIUM |
| IV6-S2-FORM-SYSTEM-BACKBONE | Pas 2 | Form System Backbone awareness | all files | `FormSystemBackboneAwarenessPanel`, form-contract endpoint | Product/Form contracts | Form System backbone | `form_system_backbone.*` | `form_system_backbone` / read-only diagnostic | shows blockers and downstream safety | no pricing | downstream write intent false | systemic diagnostic | LOW |
| IV6-S2-LIVE-CALC | Pas 2 | Live calculation / price spine | letters; logo guarded | `IntakeV6LiveCalculationSummary` | Commercial preview later | commercial preview field set | not final Product Truth | preview endpoints / preview | must be tied to readiness | preview only; not quote snapshot | must not write downstream | partial | HIGH |
| IV6-S2-MATERIALS | Pas 2 | Materials/operations/consumables | letters; logo guarded | `IntakeV6MaterialBreakdownPanel`, preview endpoints | component material/operation contracts | preview diagnostic fields | not final Product Truth | preview endpoints / preview-only | not a truth gate alone | internal/commercial preview only | no task materialization | partial | HIGH |
| IV6-S2-NESTING-PREVIEW | Pas 2 | Nesting preview / `Nesting activ` / nest2 comparison | sheet and roll material candidates | material breakdown nesting rows and technical accordion | material consumption contract | `product_truth.material_consumption.*` | `nesting_preview` / `partial` | partial until real nesting output, selected roll width, and split decisions are connected to Product Truth | preview only; not stock consumption | no stock/task writes | partial | HIGH if treated as real consumption |
| IV6-S2-RIGID-SHEET-NESTING | Pas 2 | Rigid sheet nesting | Plexiglas, Forex, ACM/Bond | material breakdown and sheet quote candidates | rigid sheet component/material contract | `product_truth.material_consumption.rigid_sheets[]` | `nesting_preview` or `fallback_area_estimate` / `partial` | partial until sheet format, nesting output, oversized parts, and split decisions are ready | not quote-ready from area only | no stock/order/execution | partial | HIGH |
| IV6-S2-ROLL-MATERIAL-NESTING | Pas 2 | Roll material nesting | Oracal/vinyl/autocolant, print, laminate | current material rows/warnings; formal UI missing | roll material contract | `product_truth.material_consumption.roll_materials[]` | `fallback_area_estimate` / `partial` today | partial until selected roll width and roll layout exist | not quote-ready from geometry area or cut width | no stock/order/execution | partial | HIGH |
| IV6-S2-ROLL-WIDTH-SELECTION | Pas 2 | Selected roll width | roll materials | partial option contract; future Form System field | finish/material component | `product_truth.material_consumption.roll_materials[].selected_roll_width_mm` | `form_system_roll_width_field` / `suggested` or `confirmed` | quote readiness requires selected and confirmed roll width | commercial consumption uses selected roll width | no downstream writes | partial | HIGH if omitted |
| IV6-S2-MATERIAL-CONSUMPTION-REALITY | Pas 2 | Real material consumption vs geometry area | all material rows | material breakdown/live calculation | material consumption contract | `product_truth.material_consumption.*` | `fallback_area_estimate` or `nesting_preview` / `partial` | quote readiness requires real consumption or explicit override | preview only if area-based | no downstream writes | partial | HIGH |
| IV6-S2-MATERIAL-WASTE-EFFICIENCY | Pas 2 | Waste and efficiency | sheet and roll materials | nesting rows show efficiency where present | material consumption contract | `product_truth.material_consumption.*.waste_area_mm2`, `efficiency_percent` | `nesting_preview` / `partial` | partial until computed and confirmed | preview only | no downstream writes | partial | MEDIUM/HIGH |
| IV6-S2-MATERIAL-SPLIT-PANELIZATION | Pas 2 | Conditional split/panelization | oversized sheet/roll graphics | not formalized today | split/panelization contract | `product_truth.material_consumption.split_plans[]` | `split_plan_generator` / `split_proposed` | blocked/partial until proposed and operator-confirmed | no quote-ready when required and missing | no downstream writes | missing | HIGH |
| IV6-S2-OVERSIZED-MATERIAL-WARNING | Pas 2 | Oversized material warning | parts/graphics exceeding selected format | not formalized today | material consumption contract | `product_truth.material_consumption.*.oversized_parts[]` | `backend_readiness` / `blocked` | must block until split/alternate material/override | no quote-ready if unresolved | no downstream writes | missing | HIGH |
| IV6-S2-COMMERCIAL-ADJUSTMENTS | Pas 2 | Markup/discount/VAT/manual adjustment | letters; logo blocked | `IntakeV6PricingInputPanel`, `finish_setup.commercial_inputs` | commercial policy | commercial input field group | `commercial_inputs.*` | payload draft / hydrated or manual | must require quote-ready truth | affects preview only until handoff | no quote/order by itself | partial | HIGH |
| IV6-S2-BLOCKERS | Pas 2 | Problems/warnings drawer and banners | all files | footer/status overlay + readiness APIs | readiness taxonomy | blocker/warning fields | `readiness.blockers[]`, `readiness.warnings[]` | `backend_readiness` / partial/blocked | blockers must be explicit | may block preview/handoff | must block downstream when severe | partial | MEDIUM |
| IV6-S3-SUMMARY | Pas 3 | Confirmare summary/dashboard | all files | confirm summary builder + endpoints | Product Truth/handoff policy | confirm summary fields | `summary.*`, `readiness.*` | mixed / partial | must reflect row/link readiness | can look commercial; needs guard | no write by itself | partial | MEDIUM |
| IV6-S3-READINESS-GATES | Pas 3 | Handoff/checklist gates | all files | handoff panel + footer confirm state | handoff boundary | operator confirmation fields | `operator_confirmation.*`, `handoff.*` | operator_confirmed only if clicked | required before write actions | gates commercial writes | no order/execution | systemic partial | MEDIUM |
| IV6-S3-COMMERCIAL-SURFACE | Pas 3 | Offer/dry-run/commerce panel | letters; logo guarded | pricing panel + dry-run | CommercialPriceProposal later | commercial preview field set | not final Product Truth | preview/dry-run | only allowed as final-looking when truth complete | not quote snapshot by itself | must not create order/execution | partial | HIGH |
| IV6-S3-MATERIAL-CONSUMPTION-SUMMARY | Pas 3 | Material consumption readiness summary | all quoteable materials | Confirmare summary/pricing sidebar today; formal summary missing | material consumption contract | `product_truth.material_consumption.summary` | `backend_readiness` / `partial` | must block final-looking material cost when consumption is partial | no final material cost if area-only | no stock/order/execution | missing | HIGH |
| IV6-S3-SPLIT-PANELIZATION-SUMMARY | Pas 3 | Split/panelization summary | oversized cases | not formalized today | split/panelization contract | `product_truth.material_consumption.split_plans[]` | `split_proposed` / `partial` or `blocked` | quote readiness requires operator-confirmed split if required | no final offer if split unresolved | no downstream writes | missing | HIGH |
| IV6-S3-DRAFT-HANDOFF | Pas 3 | Internal draft / priced quote CTAs | all files | Confirmare CTAs + backend APIs | Quote/Offer layer | handoff fields | `handoff.quote_candidate`, `quote_snapshot_later` | operator_confirmed + backend-ready | requires all gates | writes quote/offer only if clicked | no order/execution | gated | HIGH |
| IV6-S3-NO-ORDER-NO-EXECUTION | Pas 3 | No-order/no-execution safety copy | all files | Confirmare copy + backend guards | Downstream systems | downstream guard fields | `downstream_write_intent.*` | blocked/safe | always relevant | no pricing effect | prevents ProductAggregate/TaskGraph/ExecutionPlan | systemic | LOW |

## 6. Multi-SVG Behavior Matrix

| File | Pas 1 behavior | Pas 2 behavior | Pas 3 behavior | Expected rows | Template candidate/root | Commercial state | Downstream state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gradi-curat.svg` | 6 layers: 4 `face` pseudo groups, 2 `printed_artwork` logo layers; pending until confirmed | Review has 4 Vector Litere rows and 2 Vector Atipic/logo rows; readiness `ready_for_quote_preview` | Confirmare reachable; draft/quote CTAs gated by checklist | 4 letter rows, 2 artwork rows | Letters root with linked Logo child segments | normal Letters commercial preview visible | no order/execution; CTAs gated |
| `litere-vol-1-layer.svg` | 1 neutral `pseudo fill-00a0e3` face layer; no gradi stale rows | Review has 1 Vector Litere row; readiness `ready_for_quote_preview` | Confirmare reachable; CTAs gated | 1 letter row | Letters root | normal Letters commercial preview visible | no order/execution; CTAs gated |
| `litere-vol-2-layere.svg` | 2 neutral face layers; no gradi stale rows | Review has 2 Vector Litere rows; readiness `ready_for_quote_preview` | Confirmare reachable; CTAs gated | 2 letter rows | Letters root | normal Letters commercial preview visible | no order/execution; CTAs gated |
| `logo.svg` | 1 `printed_artwork` logo layer; Logo candidate visible | Review has no Vector Litere rows; 1 artwork row; readiness `logo_only_candidate_not_offerable` | Confirmare reachable but blocked safe | 0 letter rows, 1 artwork row | `TPL-VOLUMETRIC-LOGO_v1` candidate/read-only | commercial surface guarded/blocked | draft/quote/order/execution disabled |

## 7. Source/State Model

Official source categories:

- `svg_analyzer`: raw analyzer output, layer names, geometry, colors, roles, warnings.
- `svg_nearest_color_mapping`: color-to-registry mapping suggested from SVG paint evidence.
- `analyzer_semantic_expansion`: pseudo layer or semantic expansion generated from analyzer rules.
- `payload_persisted`: value stored in workspace payload.
- `payload_hydrated_or_prior_state`: value carried from prior state or hydration after SVG replacement.
- `operator_confirmed`: value explicitly accepted or changed by operator.
- `fallback_default`: default chosen by UI/service when no operator truth exists.
- `backend_readiness`: derived blocker/readiness state from backend services.
- `form_system_backbone`: read-only contract source from Form System backbone endpoint.
- `UI_only`: local display/navigation/tab/collapse state not yet represented by Form System.

Official state categories:

- `suggested`: proposed by analyzer, mapping, or service; not final Product Truth.
- `hydrated`: persisted or prior value reused; must not be treated as confirmed by itself.
- `fallback`: default value; must remain visibly distinct from operator truth.
- `partial`: enough to display or preview, not enough for final truth.
- `confirmed`: accepted by operator or explicitly validated by a current confirmation rule.
- `blocked`: cannot proceed until resolved.
- `candidate_read_only`: visible candidate only; not offerable/root active.
- `not_offerable`: explicitly blocked from commercial root behavior.

Contract rule:

No field can be considered Product Truth ready without all of the following:

- source;
- state;
- owner;
- Product Truth path;
- readiness state;
- downstream boundary.

Global workspace readiness must not erase row-level or segment-level partial states.

## 8. Product Truth Readiness Rules

Readiness levels:

- Row-level readiness: each letter group, artwork row, linked segment, and component row must expose ready/partial/blocked state.
- Section-level readiness: Vector Litere, Vector Atipic/logo, Lighting, Mounting, Materials, Commercial Preview, and Confirmare must summarize row-level status.
- Workspace-level readiness: may route the operator through steps, but must not hide partial row/segment readiness.
- Commercial readiness: may show preview surfaces only with clear boundary; final-looking quote/offering requires Product Truth completion and explicit handoff gates.
- Downstream readiness: order/execution/ProductAggregate/TaskGraph/ExecutionPlan remain blocked from Intake V6.

Examples:

- Vector Litere row with nearest Oracal mapping: source `svg_nearest_color_mapping`, state `suggested` or `partial` until operator confirmation.
- Cant/return loaded from prior payload: source `payload_hydrated_or_prior_state`, state `hydrated`, partial until confirmed.
- Linked logo binding: source payload binding or inferred segment, state `suggested`, partial until binding confirmation workflow exists.
- Logo-only candidate: source `backend_readiness`, state `candidate_read_only` and `not_offerable`; downstream blocked.

## 9. Commercial Boundary Contract

Rules:

- `Calcul live` is preview, not quote snapshot.
- Material breakdown and operations are preview-only unless a later Product Truth + snapshot boundary authorizes them.
- Letters commercial preview may be visible when workspace readiness permits, but must be tied to Product Truth readiness and should not hide partial row/segment diagnostics.
- Logo-only candidate must never look like final offer, final pricing, or quote-ready product.
- Commercial adjustments must be blocked or guarded when workspace is not quote-ready.
- Confirmare must not show official-looking commercial offer if readiness is `logo_only_candidate_not_offerable` or if required Product Truth remains partial.

| Surface | Allowed when ready? | Allowed when partial? | Allowed for logo-only? | Required guard |
| --- | --- | --- | --- | --- |
| Live calculation | Yes, as preview | Yes only with preview/partial copy | No final-looking calculation; guarded/blocked only | `Preview intern`, `not quote-ready`, source/state warnings |
| Material breakdown | Yes, as preview | Yes only as internal/material preview | Guarded summary only | `not final offer`, no task materialization |
| Commercial adjustments | Yes for Letters preview | Only if clearly draft/preview | No active inputs | `Reglaje comerciale blocate` |
| Confirmare commercial surface | Yes only after readiness gates | No final-looking offer | Guarded/blocked only | `Preview comercial intern blocat`, CTA disabled reason |
| Draft/quote CTA | Yes only after explicit gates | No | No | disabled reason and owner-GO/root-offerability copy |

## 10. Downstream Boundary Contract

Rules:

- Intake V6 cannot create Order.
- Intake V6 cannot trigger Execution.
- Intake V6 cannot create ProductAggregate.
- Intake V6 cannot create TaskGraph.
- Intake V6 cannot create ExecutionPlan.
- Draft/Quote handoff must be explicitly gated by Product Truth readiness, operator confirmation, and backend policy.

| Downstream action | Allowed from Intake V6? | Gate required | Current state | Notes |
| --- | --- | --- | --- | --- |
| Internal draft quote | Conditionally, only via Confirmare | Product Truth and operator checklist gates | gated/disabled until confirmation | Does not create order/execution |
| Priced quote/offer | Conditionally, only via explicit handoff path | backend dry-run, expected hash/total, operator confirmation, no stale snapshot | gated | Must not repair Product Truth |
| Order | No | Quote acceptance and Order Snapshot later | not available from Intake V6 | Confirmare must not create order |
| Execution | No | Order Snapshot + later ProductAggregate/TaskGraph/ExecutionPlan | not available | No direct Intake -> ExecutionPlan |
| ProductAggregate | No | future owner GO after snapshots | not active | must not fill missing Intake truth |
| TaskGraph | No | future owner GO after ProductAggregate | not active | no task materialization from UI/mini-module metadata |
| ExecutionPlan | No | future owner GO after TaskGraph | not active | post-order only |

## 11. What Is Already Systemic

- SVG file isolation across the four real files.
- Analyzer semantic scoping: gradi-specific pseudo names do not leak into generic files.
- Logo-only candidate route and not-offerable readiness.
- Logo-only commercial surface guard.
- Letter group finish readiness backend endpoint.
- Linked logo segment readiness backend endpoint.
- Form System Backbone awareness panel and form-contract endpoint for Letters root.
- Read-only downstream write intent in readiness/backbone services.
- No-order/no-execution guard in Confirmare.

## 12. What Is Still Partial / UI-only / Hydrated

- Vector Litere source/state is not fully surfaced in the primary UI; readiness endpoint is separate.
- Linked logo binding is still `suggested`, not confirmed Product Truth.
- Lighting, mounting, support, PSU, and return/cant values include hydrated/default/manual state that is not always visible.
- Commercial preview for Letters can look stronger than row/segment readiness diagnostics.
- Confirmare global readiness is not fully aligned with row/link readiness diagnostics.
- Product Truth paths are not consistently visible to the operator.
- Form System cannot yet generate all current Intake V6 surfaces from contracts alone.
- Logo candidate has no separate form-contract endpoint (`TPL-VOLUMETRIC-LOGO_v1` returns 404 in the current runtime).

## 13. Required Next Contracts

### 1. Form System Field Contract Map V1

- Purpose: define field-level records for every surface in this inventory.
- Input: this UI surface contract, final multi-SVG audit, current form backbone.
- Output: stable `field_id`, owner, source, state, Product Truth path, required level, blockers.
- Why needed: UI surfaces cannot be generated modularly until fields are enumerable and owned.
- Forbidden scope: no UI rewrite, no Pricing, no Quote/Order, no Execution, no DB.

### 2. Product Truth Confirmation Policy V1

- Purpose: define when suggested/hydrated/fallback/manual values become confirmed Product Truth.
- Input: field contract map, readiness endpoints, operator confirmation rules.
- Output: confirmation states, row-level readiness, section-level readiness, workspace aggregation rules.
- Why needed: current global readiness can overstate row/link finality.
- Forbidden scope: no pricing/quote/order/execution writes.

### 3. Commercial Preview Boundary V1

- Purpose: define how live calculation, material breakdown, commercial inputs, and dry-run totals may display.
- Input: Product Truth readiness policy and existing commercial preview surfaces.
- Output: allowed labels, gates, blocked states, snapshot boundary requirements.
- Why needed: normal Letters preview remains useful but can look final too early.
- Forbidden scope: no Pricing formulas and no quote write behavior changes.

### 4. Confirmare Gate Readiness Alignment V1

- Purpose: align Confirmare summary/checklist/CTA copy with row/link/component readiness diagnostics.
- Input: Product Truth confirmation policy, linked segment readiness, letter group readiness.
- Output: central Confirmare gate model.
- Why needed: Confirmare must not hide partial Product Truth under global readiness.
- Forbidden scope: no Order/Execution/ProductAggregate/TaskGraph/ExecutionPlan.

### 5. Runtime Product Truth Snapshot Contract V1

- Purpose: define the future frozen Product Truth snapshot consumed by ProductDefinition and commercial proposal.
- Input: confirmed field map and readiness policy.
- Output: immutable runtime truth shape and snapshot guard rules.
- Why needed: downstream systems must not consume mutable UI payloads as final truth.
- Forbidden scope: no implementation until owner GO.

## 14. Acceptance Criteria For This Contract

This contract is accepted when:

- it is docs-only;
- it changes no code, UI, backend, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB schema, seeds, or migrations;
- it references the final multi-SVG audit;
- it covers Pas 1, Pas 2, Pas 3;
- it covers all four canonical SVG files;
- it defines stable surface IDs;
- each surface includes owner/source/state/readiness/commercial/downstream boundaries;
- it identifies what is already systemic;
- it identifies what remains partial/UI-only/hydrated;
- it names the next required contracts in order.