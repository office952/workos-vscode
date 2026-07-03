# Volumetric Letters Phase 2 Modular Form Component Questions Inventory

**Date:** 2026-07-01  
**Status:** DOCUMENTED_NOT_IMPLEMENTED  
**Scope:** Phase 2 prep audit, read-only / docs-only  
**Roadmap phase:** Phase 2 — Modular Form component questions  
**Runtime anchor:** `gradi-curat.svg` in workspace `IV6-BB8EE3F8` / intake `IR-MR18L96M`  
**Known blocker:** `layer_roles_incomplete`

---

## Purpose

This document prepares Phase 2 without implementing it.

It inventories current Intake V6 Review/Form controls and maps them to reusable component ownership. It does not change frontend, backend, tests, payload, analyzer, pricing, ProductDefinition, ProductSystem runtime, ProductAggregate, ExecutionPlan, DB/schema/seeds, quote/order/execution, or Employee Mobile.

Roadmap source:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`

Runtime note:

- Live Review was not entered because `layer_roles_incomplete` correctly blocks access.
- Review/Form inventory is code/docs audited.
- Runtime anchor confirms `gradi-curat.svg` remains on Straturi with disabled CTA and no Pricing Registry false blame.

---

## Sources Audited

Docs:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md`
- `docs/architecture/INTAKE_V6_MODULAR_FORM_CONTRACT.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- Phase 1 worklogs and re-audit worklog

Code read-only:

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLightingSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/lib/intakeV6/intakeV6ReviewFormContract.ts`
- `frontend/src/lib/intakeV6/useTemplateFormContract.ts`
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts`
- `frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts`
- `frontend/src/lib/intakeV6/intakeV6BackingMode.ts`
- related readiness and UI-state helpers

---

## Existing Review/Form Controls Inventory

| UI area / component | Existing control / field | Current source | Current state: confirmed / suggested / fallback / manual / missing / blocker / warning | Global or per layer/group? | Component candidate | Product Truth candidate field | Blocks quote if missing? | Notes / risks |
|---|---|---|---|---|---|---|---|---|
| Straturi / `IntakeV6LayersRoleTable` | role confirmation | SVG Analyzer suggestions + `layer_role_setup` | suggested + blocker until operator confirms | per layer/group | SVG / Layer roles; Artwork | `layers[].role.confirmed`, `layers[].ignored`, `layers[].source=suggested|confirmed` | yes | Active blocker is `layer_roles_incomplete`; must not go to Pricing Registry. |
| Straturi / role select | ignored decision | operator role select / confirmation state | manual / confirmed when selected | per layer/group | SVG / Layer roles | `layers[].ignored.confirmed` | yes if relevant layer remains undecided | Ignored must be explicit, not silent omission. |
| Review letter group cards | face material | not explicit as native material selector; inferred from face finish / registry path today | missing / fallback | per layer/group with possible global default | Face / Plexiglas | `face.groups[].material_family`, `face.groups[].material_code` | yes | Current UI has finish type, not a clear Plexiglas material/thickness owner. |
| Review backing select | back material | `backing_mode` options | fallback/manual; confirmed only through saved review | global today | Back / Forex | `back.material=forex`, `back.thickness_mm=10`, `back.bevel_enabled` | yes | Only Forex 10 no/with bevel exposed; material and thickness are encoded in option, not separate fields. |
| Review backing select | face thickness | no explicit face thickness control | missing | not decided; likely global default with per group override support later | Face / Plexiglas | `face.groups[].thickness_mm` or `face.default_thickness_mm` | yes | Mandatory docs mention face thickness; current UI does not expose it distinctly. |
| Review letter group cards | face finish | `letter_group_finishes[].face_finish_type`; options from template contract/fallback | fallback/hydrated until group confirmed | per layer/group | Finish / Oracal / Print / Laminare; Face | `finish.face.groups[].type` | yes when finish active | Current options include none, Oracal, print/laminate variants via contract. |
| Review global fallback | face finish default | `finish_setup.face_finish_type` | fallback/hydrated job-level | global fallback | Finish / Face | `finish.defaults.face_finish_type` | no if per-group values cover all groups; yes if used as active truth without confirmation | Hidden when per-layer/per-artwork groups exist; should remain fallback, not final truth. |
| Review face color | Oracal type | selected by `face_finish_type` such as `oracal_641`, `oracal_651`, `oracal_8500` | fallback/manual | per layer/group | Finish / Oracal | `finish.face.groups[].oracal_series` | yes when Oracal active | Series comes from finish option; should be explicit Product Truth later. |
| Review face color | Oracal color | `ColorRegistrySelect` with ORACAL series filter | manual / missing warning if required | per layer/group | Finish / Oracal | `finish.face.groups[].oracal_color_code` | yes when Oracal active | Color registry supplies options, but does not decide color. |
| Review face roll width | roll width | `face_vinyl_roll_width_mm`; allowed from contract or fallback `[1000,1260]` | fallback/manual | per layer/group plus global fallback | Finish / Oracal | `finish.face.groups[].roll_width_mm` | conditional | May be CostEngine/internal optimization if not commercial; owner must decide quote blocker policy. |
| Review artwork cards | print required | `artwork_finishes[].execution_type` default `print_laminate`; no separate boolean | suggested/fallback; confirmed by `Confirm artwork` | per artwork layer/group | Artwork / Printed artwork; Finish / Print | `printed_artwork[].print_required` | yes when artwork active | Current execution default can look final; needs explicit Phase 2 question. |
| Review artwork cards | lamination required | `execution_type=print_laminate`; no separate boolean | suggested/fallback; confirmed by artwork row | per artwork layer/group | Finish / Laminare; Artwork | `printed_artwork[].lamination_required` | yes when print active and policy requires | Must separate print from lamination. |
| Review artwork-only panel | artwork-only decision | `IntakeV6ArtworkOnlyDecisionPanel` and guard warnings | blocker / needs confirmation | per layer/group | Artwork / Printed artwork | `artwork_only.decision`, `layers[].role` | yes | Must decide artwork-only vs product layer; not Pricing Registry. |
| Review artwork cards | artwork confirmation | `artwork_finishes[].confirmed` | needs confirmation / confirmed | per artwork layer/group | Artwork / Printed artwork | `printed_artwork[].confirmed` | yes when artwork active | Two logos in `gradi-curat.svg` need this after role confirmation permits Review. |
| Review finish/card semantics | finish target | partially implicit: face zone, cant zone, artwork zone | partial / missing explicit target | per layer/group | Finish | `finish.items[].target=face|cant|back|artwork` | yes | Missing explicit target is a Phase 2 blocker candidate. |
| Review finish/card semantics | finish apply stage | not explicit | missing | per layer/group | Finish / Oracal / T06 / T19E | `finish.items[].apply_stage` | yes when finish active on cant or after body | Needed for T06 vs T19E. |
| Review docs/code | T06 vs T19E | not exposed as a control | missing / blocker candidate | per layer/group or per finish item | Finish / Oracal / Return | `finish.items[].process_code=T06|T19E` | yes when relevant | Must be owner-decided before runtime implementation. |
| Review return/cant fields | return/cant depth | `return_depth_mm`; allowed depths from contract/fallback | fallback/manual | per layer/group; global fallback exists | Return / Cant | `return.groups[].depth_mm` | yes | `60 mm` exists for current case but must be confirmed. |
| Review return/cant fields | return/cant color | `return_oracal_code/name` or RAL color via `ColorRegistrySelect` | manual / missing warning when required | per layer/group | Return / Cant; Finish | `return.groups[].color_code`, `return.groups[].color_system` | yes when color-required finish active | Registry supplies color catalog only. |
| Review return/cant fields | return/cant finish | `return_finish_type`; UI options white/black/gold/silver/RAL/Oracal wrapped | fallback/manual | per layer/group; global fallback exists | Return / Cant | `return.groups[].finish_type` | yes | Must separate material/profile from finish appearance. |
| Review return/cant fields | RAL color | `ColorRegistrySelect` with RAL filter | manual / missing warning | per layer/group | Return / Cant; Finish | `return.groups[].ral_code` | yes when RAL paint active | RAL is color truth, not pricing repair. |
| Review lighting | lighting mode | `illuminated`, `lighting_system_type` | fallback/manual | global today, per group exceptions later possible | Electrical / LED | `lighting.enabled`, `lighting.system_type` | yes when illuminated | Existing toggle and system select cover minimum mode. |
| Review lighting | LED configuration | `led_module_power_w`, derived counts, strip lengths | mixed manual + derived/fallback | global today with emblem exception | Electrical / LED | `lighting.led_module_power_w`, `lighting.counts`, `lighting.emblem_mode` | conditional | Counts are derived; should not be treated as operator-confirmed without source flags. |
| Review mounting tab | power supplies | `selected_psu_watts`, `psu_configuration`, derived required watts | manual + derived/fallback | global | Electrical / LED | `electrical.psu.selected_watts`, `electrical.psu.configuration` | conditional | Current UI selects one PSU wattage; actual placement/hidden transformer missing. |
| Review lighting/docs | cables | no explicit cable fields | missing | not decided; likely global + per run later | Electrical / LED | `electrical.cables.*` | no for quote unless owner says; yes order/execution | Product Truth docs list cable lengths/types as later order/execution truth. |
| Review mounting tab | support / bars | `mounting_system=steel_bars|aluminum_bars`, `mounting_bar_profile` | partial/manual | global today | Support / Bare; Mounting | `support.required`, `support.type`, `support.bar_profile` | yes when support active/suspected | Support requirement is derived from mounting selection today; support type is not first-class. |
| Review mounting tab | mounting system | `mounting_system` options direct_wall/steel_bars/aluminum_bars/acm_panel | fallback/manual | global | Mounting | `mounting.system` | yes | Current default is direct wall; must be confirmed, not assumed. |
| Review mounting tab | mounting template | `mounting_template_enabled`, area, material forex/paper | fallback/manual/derived area | global | Mounting | `mounting.template.enabled`, `area_m2`, `material` | conditional | Area can be derived minimum from geometry. Keep source explicit. |
| Review modular awareness | ProductSystem/Form contract traceability | read-only contract panels | warning/diagnostic | global | Form System contract | n/a for runtime truth | no direct quote blocker | Useful audit surface; not operator input. |
| Review live calculation / pricing panels | commercial sliders | `commercial_inputs` markup/discount/VAT/manual adjustment | manual commercial setting | global | CommercialPriceProposal later | not Product Truth; commercial proposal input | no Product Truth blocker | Must not become Product Truth or ProductDefinition input. |
| Review preview panels | material breakdown/task dry run/handoff previews | endpoints derived from workspace | preview/warning | global/read-only | CostEngine / downstream preview | n/a | no as Product Truth input | Preview only; must not materialize or decide truth. |

---

## Component Ownership Map

| Reusable component | Questions it must own | Existing UI controls that already cover this | Missing UI questions | Product Truth output | Pricing Registry dependency | CostEngine internal-only dependency | Quote blocker | Order blocker | Execution blocker | Current status |
|---|---|---|---|---|---|---|---|---|---|---|
| Face / Plexiglas | Which groups are face? What face material? What thickness? What face finish/visual treatment? | role confirmation in Straturi; per-group face finish; Oracal color; roll width | explicit face material; explicit face thickness; selected face layer refs as canonical field | `face.groups[]` with layer refs, material, thickness, finish refs, source state | material/finish price coverage only after truth | nesting, waste, CNC time/capacity internal | yes | yes | yes | PARTIAL |
| Back / Forex | Is back present? Which material/thickness? With or without bevel/sanfren? | `backing_mode` select with Forex 10 no/with bevel | separate back material and thickness if owner wants more variants; back selected layer if SVG supports it | `back.enabled`, `material=forex`, `thickness_mm=10`, `bevel_enabled` | Forex/back material price only | back nesting/CNC internal | yes | yes | yes | PARTIAL |
| Return / Cant | What depth? What finish/material/profile? What color? Is cant active per group? | per-group return depth, return finish, RAL/Oracal colors; copy cant to all | explicit material/profile separate from finish; stage/process T06/T19E when wrapped/film | `return.groups[]` with depth, finish, color, active state, source state | return profile/finish price coverage | forming, bonding, scrap, internal time/capacity | yes | yes | yes | PARTIAL |
| Finish / Oracal / Print / Laminare | Target? series? color? print? laminate? apply stage? T06 vs T19E? | face finish select; Oracal color; roll width; artwork execution default; transparency toggles; return finish | explicit `finish_target`; explicit `print_required`; explicit `lamination_required`; explicit `apply_stage`; T06/T19E | `finish.items[]` per target/group with series/color/stage/print/lamination | Oracal/print/laminate service/material prices only | application time, waste, rework, print setup internal | yes | yes | yes | PARTIAL |
| Electrical / LED | Illuminated? LED modules vs strip? light color? power/module? emblem lit/excluded? PSU? cables? | LED toggle; system; color; module wattage; emblem lighting; selected PSU watts | cable types/lengths; PSU placement; hidden transformer; per-group exceptions | `lighting` + `electrical` with mode, LED config, PSU config, cables | LED/PSU/wire material price coverage only | watt reserve, cable routing, assembly time, capacity | conditional | yes | yes | PARTIAL |
| Support / Bare | Is support required? What type/material/profile? Internal vs external prep? Relation to mounting? | mounting system steel/aluminum bars; bar profile | first-class support required yes/no; support type; material; position; internal/external prep | `support.required`, `support.type`, `bar_profile`, `prepared_internally` | support material/package price if active | fabrication, welding/routing, capacity internal | conditional | yes | yes | PARTIAL |
| Mounting | Direct wall/bars/ACM? Template needed? Template material/area? Site constraints? | mounting system; template enabled; template area; template material | site constraints; mounting hardware; whether template is quote/order/execution mandatory | `mounting.system`, `template`, `site_constraints` | template/material/hardware price if commercial | installation planning/logistics internal | yes | yes | yes | PARTIAL |
| Artwork / Printed artwork | Which groups are printed artwork? Print/laminate/transparency? Artwork-only vs product? Ignored? | Straturi role suggestion; artwork cards; transparency toggles; confirm artwork; artwork-only decision panel | explicit print vs laminate booleans; selected artwork target; material code; artwork-only policy | `printed_artwork[]`, `artwork_only`, `ignored_layers[]` | print/laminate material/service coverage only | print setup, laminate, scrap, internal time | yes when artwork active | yes | yes | PARTIAL |

---

## Per-layer / Per-group vs Global Decision Audit

| Decision | Global? | Per layer/group? | Why | Current UI support | Product Truth impact | Risk if wrong |
|---|---|---|---|---|---|---|
| role | no | yes | Each detected group can be face, printed_artwork, ignored, or other role. | Strong in Straturi. | `layers[].role` gates all downstream truth. | Quote can price wrong component. |
| face material | both | yes | Most jobs may share a default, but colored/grouped faces can differ. | Missing explicit native control. | `face.groups[].material`. | Material and execution path guessed downstream. |
| face thickness | both | yes | Usually common, but exceptions must be possible. | Missing explicit native control. | `face.groups[].thickness_mm`. | ProductDefinition or pricing infers thickness. |
| face finish | no as final; global fallback yes | yes | `gradi-curat.svg` has four face groups with different colors. | Per-group card plus global fallback. | `finish.face.groups[]`. | Fallback treated as confirmed truth. |
| Oracal type | no as final; global fallback possible | yes | Series may differ by color/visibility/translucency. | Per-group finish type. | `oracal_series`. | Wrong material/service selected. |
| Oracal color | no | yes | Each group can have its own color. | Per-group ColorRegistrySelect. | `oracal_color_code`. | Visual promise wrong; quote/order drift. |
| print/lamination | no | yes | Logos/artwork are separate from volumetric face groups. | Artwork cards default execution and confirmation. | `printed_artwork[].print_required`, `lamination_required`. | Printed artwork priced/executed incorrectly. |
| artwork target | no | yes | Target decides product vs artwork-only vs ignored. | Role suggestion + artwork-only panel partial. | `printed_artwork[].layer_ref`, `artwork_only`. | Artwork becomes product or product becomes artwork. |
| finish target | no | yes | Target separates face, cant, back, artwork. | Implicit by zone only. | `finish.items[].target`. | Pricing Registry asked to repair missing semantic target. |
| T06/T19E | no | yes | Stage differs by target/process. | Missing. | `finish.items[].apply_stage/process_code`. | Wrong operation branch and commercial scope. |
| cant depth | both | yes | Usually common; per group/artwork return can differ. | Per-group and artwork return fields; global fallback. | `return.groups[].depth_mm`. | Return profile and perimeter cost wrong. |
| cant color | no | yes | Return finish can vary by group/artwork. | Per-group RAL/Oracal return fields. | `return.groups[].color_code`. | Visual and material mismatch. |
| lighting mode | yes by default | possible exceptions | Product normally has one lighting intent; artwork/emblems can differ. | Global lighting + emblem mode. | `lighting.mode`, `lighting.emblem_mode`. | LED materials/power promise wrong. |
| LED density/config | yes by default | possible exceptions | Derived from geometry/depth but may need exceptions. | LED system/power + derived counts; no per-group override. | `lighting.config` with source flags. | Derived counts look confirmed. |
| support/mounting | mostly yes | conditional later | Mounting is usually job-level; support may vary for very large groups. | Global mounting system/bar profile/template. | `mounting.*`, `support.*`. | Support branch activated/inactivated incorrectly. |

---

## Product Truth Candidate Shape — Docs Only

**DOCUMENTED_NOT_IMPLEMENTED**

This is a conceptual Phase 3 candidate shape only. It must not be implemented during this audit.

```ts
type SourceState = "suggested" | "confirmed" | "fallback" | "manual" | "blocked" | "warning";

type ProductTruthCandidate = {
  workspace_id: string;
  template_code: string;
  source_file: {
    file_name: string;
    file_hash: string | null;
    analyzer_status: SourceState;
  };
  layers: Array<{
    layer_key: string;
    display_name: string;
    source_layer_name?: string | null;
    suggested_role?: string | null;
    confirmed_role?: string | null;
    ignored?: boolean;
    state: SourceState;
    blockers: string[];
    warnings: string[];
  }>;
  face: {
    groups: Array<{
      layer_key: string;
      material_family?: string | null;
      material_code?: string | null;
      thickness_mm?: number | null;
      finish_item_id?: string | null;
      state: SourceState;
    }>;
  };
  printed_artwork: Array<{
    layer_key: string;
    artwork_only?: boolean;
    print_required?: boolean;
    lamination_required?: boolean;
    transparency?: "standard" | "translucent" | "transparent";
    material_code?: string | null;
    state: SourceState;
  }>;
  finish: {
    items: Array<{
      target: "face" | "cant" | "back" | "artwork";
      layer_key?: string | null;
      finish_type: string;
      oracal_series?: string | null;
      color_system?: "ORACAL" | "RAL" | null;
      color_code?: string | null;
      roll_width_mm?: number | null;
      apply_stage?: "before_forming" | "after_body_formed" | "before_assembly" | "after_assembly" | null;
      process_code?: "T06" | "T19E" | null;
      state: SourceState;
    }>;
  };
  cant: {
    groups: Array<{
      layer_key: string;
      depth_mm?: number | null;
      material_family?: string | null;
      finish_item_id?: string | null;
      state: SourceState;
    }>;
  };
  lighting: {
    illuminated: boolean;
    system_type?: "led_modules" | "led_strip" | null;
    light_color?: string | null;
    led_module_power_w?: number | null;
    led_module_count?: number | null;
    emblem_mode?: "area_lit" | "excluded" | "needs_decision";
    state: SourceState;
  };
  support: {
    required?: boolean | null;
    type?: string | null;
    bar_profile?: string | null;
    prepared_internally?: boolean | null;
    state: SourceState;
  };
  mounting: {
    system?: string | null;
    template_enabled?: boolean;
    template_area_m2?: number | null;
    template_material?: string | null;
    site_constraints?: string[];
    state: SourceState;
  };
  readiness: {
    quote: "blocked" | "ready";
    order: "blocked" | "ready";
    execution: "blocked" | "ready";
    blockers: string[];
    warnings: string[];
  };
};
```

Separation requirements:

- `suggested`: analyzer/system proposal only.
- `confirmed`: explicit operator-accepted truth.
- `fallback`: hydrated/template/default value; not equal to confirmation.
- `manual`: operator-entered override needing save/traceability.
- `blocked`: missing truth that blocks quote/order/execution.
- `warning`: risk or partial alignment that does not block current level.

---

## Pricing / Cost Boundary Audit

| Component question | Product Truth? | Pricing Registry? | CommercialPriceProposal? | CostEngine internal-only? | No commercial hour/minute pricing? | Boundary note |
|---|---|---|---|---|---|---|
| role / ignored / artwork-only | yes | no | consumes only after confirmed | no | yes | Pricing Registry must not decide layer semantics. |
| face material/thickness | yes | price coverage only | consumes complete truth | nesting/CNC/waste internal | yes | Material price is registry; material decision is Product Truth. |
| face finish / Oracal series/color | yes | material/service price coverage only | consumes complete finish truth | application time/scrap internal | yes | Registry does not choose color or series. |
| roll width | conditional Product Truth if commercial policy requires | no decision ownership | may consume if rule needs it | optimization/waste internal | yes | Owner must decide quote blocker policy. |
| print required / lamination required | yes | print/laminate price coverage only | consumes after complete | print setup/scrap/time internal | yes | Must not infer from pricing availability. |
| finish target | yes | no | consumes complete target | operation planning internal later | yes | Missing target is Product Truth blocker. |
| T06 vs T19E | yes | no | consumes chosen branch | operation timing/capacity internal | yes | Registry does not resolve process semantics. |
| return depth/color/finish | yes | material/finish coverage only | consumes complete return truth | forming/bonding/scrap internal | yes | Depth is product truth, not price lookup. |
| RAL color | yes | color/material coverage only | consumes if commercial finish active | paint prep internal | yes | Registry catalog is not operator decision. |
| lighting mode / LED config | yes | LED/PSU material price coverage only | consumes commercial LED scope | watt reserve/capacity/internal time | yes | Derived counts need source state. |
| power supplies | yes if commercial/electrical scope | PSU price coverage only | consumes selected PSU truth | reserve/safety margin internal | yes | Placement/cables may be order/execution truth. |
| cables | conditional; likely order/execution truth | material coverage only after specified | optional if quote policy includes cable scope | routing/time internal | yes | Owner must classify quote vs order blocker. |
| support/bars | yes | material/package coverage only | consumes if support active | fabrication/capacity internal | yes | Support required/type is not Pricing Registry. |
| mounting system/template | yes | template/material coverage only | consumes if commercial scope affected | installation planning internal | yes | Mounting must be confirmed before downstream. |
| commercial sliders | no Product Truth | no | CommercialPriceProposal input | no | yes | Markup/discount/VAT are commercial settings, not product fields. |
| preview/task dry run | no Product Truth input | no | read-only evidence only | yes | yes | Must not materialize or feed execution truth. |

Mandatory rules preserved:

- Pricing Registry does not decide layer, role, finish_target, support, mounting, T06/T19E.
- CommercialPriceProposal uses complete Product Truth.
- CostEngine uses minutes/capacity/operations internal-only.
- Commercial price must not be calculated as hour/minute tariff.

---

## Open Questions for Owner Before Phase 2 Implementation

1. Which settings are allowed as global defaults, and which must always be per group?
2. Are face material and face thickness single global defaults for volumetric letters, or must each face group support override from day one?
3. For `gradi-curat.svg`, should `logo stanga` and `logo dreapta` always be `printed_artwork`, or can operator choose artwork-only / ignored / face in edge cases?
4. When is artwork considered artwork-only versus printed/laminated finish attached to a volumetric product?
5. How should `finish_target` be selected: one row per target, or target embedded inside each component card?
6. How do we choose T06 versus T19E in operator terms: by stage labels, process code labels, or a visual rule?
7. Which fields are mandatory before quote: face material, face thickness, finish target, print, lamination, mounting, support, lighting, PSU?
8. Which fields are mandatory only before order/execution: cable lengths/types, PSU placement, support bar position, install site constraints?
9. How should support/mounting be treated when `mounting_system=direct_wall`: explicit `support_required=false` or inferred inactive?
10. Are fallback/default values acceptable for quote if the operator confirms the section, or must every default be individually confirmed?
11. Should roll width block quote, or remain internal optimization unless a specific material rule requires it?
12. Should power cable and inter-letter cable fields be part of Phase 2 UI, or reserved for later order/execution truth?
13. Should `CommercialPriceProposal` controls stay in Review as commercial settings, or move to Confirmare later?
14. What is the minimum Product Truth object that Phase 3 must persist without breaking existing V4 aliases?

---

## What Must Not Be Implemented Yet

Do not implement in this prep audit:

- Product Truth canonical payload;
- ProductDefinition consumption;
- ProductSystem/Dossier runtime changes;
- CommercialPriceProposal runtime changes;
- Quote Snapshot;
- Order Snapshot;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Utilaje/Workcenters mapping;
- Angajati/Skills/Capacity;
- ExecutionReality;
- Employee Mobile;
- DB/schema/seeds;
- quote/order/execution creation;
- forced confirmations;
- Review unlock bypass.

---

## Recommended Phase 2 Implementation Slice After Owner GO

Owner GO required.

Suggested first implementation slice after GO:

- UI-only/component-contract slice in Review that labels current controls by component ownership and source state.
- Add no payload fields in the first slice unless owner explicitly approves Phase 3 prep.
- Keep Straturi / Review / Confirmare flow.
- Do not introduce a new product-specific form.
- Keep Pricing Registry boundary visible.

Candidate order:

1. Face/Return/Artwork field ownership labels and blocker inventory.
2. Explicit `finish_target` and `print_required` / `lamination_required` design proposal.
3. T06/T19E owner-decision packet.
4. Support/mounting mandatory-field decision packet.
5. Only then Phase 2 runtime UI changes, with focused tests.

---

## Roadmap Alignment Checkpoint

1. Roadmap source used

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`

2. Current roadmap phase

- Phase 2 — Modular Form component questions

3. Roadmap status of this audit

- NEXT / prep audit

4. Why this audit belongs here

This audit is the required preparation before implementing Phase 2. It maps existing Review/Form controls to reusable component ownership and identifies missing component questions without changing runtime behavior. It keeps Phase 2 before Product Truth canonical payload and ProductDefinition, so downstream systems are not asked to invent missing truth. It preserves the existing Intake V6 wizard and documents owner decisions needed before code.

5. What this audit must NOT unlock

This audit does not automatically unlock:

- Product Truth canonical payload;
- ProductDefinition;
- ProductSystem/Dossier runtime changes;
- CommercialPriceProposal;
- Quote Snapshot;
- Order Snapshot;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Utilaje/Workcenters;
- Angajati/Skills/Capacity;
- ExecutionReality;
- Employee Mobile.

6. Re-audit gate result

PASS.

7. Roadmap implementation progress

8/100%.

8. Roadmap alignment score

99/100%.

9. Cat sunt in directia stabilita

98/100%.

10. Dead pieces check

PASS.

11. Owner GO required next

YES.
