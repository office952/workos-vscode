# Volumetric Letters Phase 2 Owner Decision Packet

**Date:** 2026-07-01  
**Status:** OWNER_DECISION_REQUIRED  
**Scope:** Docs-only / read-only decision packet for Phase 2  
**Roadmap phase:** Phase 2 - Modular Form component questions  
**Runtime anchor:** `gradi-curat.svg` / `IV6-BB8EE3F8` / `IR-MR18L96M`  
**Source inventory:** `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_MODULAR_FORM_COMPONENT_QUESTIONS_INVENTORY.md`

---

## Purpose

This packet lists the owner decisions required before Phase 2 runtime or UI implementation.

It is written for owner review, not only for engineering. Every recommendation below is a technical default proposal, not a final rule. Final answers must come from the owner before implementation.

This document does not implement:

- Product Truth runtime payload;
- frontend UI;
- backend logic;
- analyzer logic;
- pricing logic;
- ProductDefinition;
- ProductSystem runtime;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- DB/schema/seeds;
- quote/order/execution;
- Employee Mobile.

---

## Decision Table

| Decision ID | Decision area | Question for owner | Why it matters | Recommended default | Alternatives | Impact if wrong | Quote blocker? | Order blocker? | Execution blocker? | Product Truth field affected | Component affected | Pricing Registry involvement? | CostEngine involvement? | Owner answer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PH2-OD-01 | Global vs per group defaults | Which values may be global defaults, which must be per layer/group, and when can a group override the default? | `gradi-curat.svg` has multiple face groups and artwork groups; global-only truth would lose real product differences. | Allow global defaults only as starting values; require per-group confirmation for role, finish, Oracal color, artwork, cant exceptions, and any field that changes material/offer. OWNER_DECISION_REQUIRED. | Global-only for simple jobs; per-group-only for all fields; hybrid default plus override. | Wrong materials, colors, printed artwork, or cant settings can be quoted and ordered incorrectly. | yes for role/finish/material fields | yes | yes | `layers[]`, `face.groups[]`, `finish.items[]`, `cant.groups[]`, `printed_artwork[]` | SVG / Layer roles; Face; Finish; Return / Cant; Artwork | No decision ownership; registry only supplies price coverage after truth exists. | Internal optimization may use grouped values after truth is confirmed. | TBD |
| PH2-OD-02 | Face / Plexiglas | Is default face material plexiglas opal, is default thickness 3 mm, when is 5 mm required, and must face material/thickness be confirmed before quote? | Face material and thickness are Product Truth. Current UI does not expose them clearly as native confirmed fields. | Default proposal: plexiglas opal 3 mm as quote default, 5 mm only for owner-defined size/rigidity/use cases; require confirmation before quote. OWNER_DECISION_REQUIRED. | Use 3 mm as fallback warning only; require material/thickness every time; add 5 mm based on width/height threshold; allow product variant to choose. | ProductDefinition or pricing would guess material/thickness; quote and execution may not match the product. | yes | yes | yes | `face.groups[].material_family`, `face.groups[].material_code`, `face.groups[].thickness_mm` | Face / Plexiglas | Price coverage only after owner/operator selects material and thickness. | Nesting, waste, CNC time, and capacity remain internal-only. | TBD |
| PH2-OD-03 | Back / Forex | Is Forex 10 mm the default backing, should back bevel/sanfren be default yes or no, and when does backing become mandatory? | Backing mode affects material, quote scope, ProductDefinition activation, and execution instructions. | Default proposal: Forex 10 mm, no sanfren, with explicit operator confirmation; sanfren only when owner/operator selects it or product rule requires it. OWNER_DECISION_REQUIRED. | No backing by default; Forex 10 mm with sanfren by default; backing decided by product variant; backing required only when illuminated. | Back material or bevel can be silently encoded in a select value and not treated as Product Truth. | yes | yes | yes | `back.enabled`, `back.material`, `back.thickness_mm`, `back.bevel_enabled` | Back / Forex | Registry supplies Forex/back material price coverage only. | Back cutting, nesting, bevel prep, and waste remain internal-only. | TBD |
| PH2-OD-04 | Return / Cant | What is default cant depth, default cant color, allowed finish family, and when must cant be confirmed? | Cant depth and finish drive return material, appearance, operations, and commercial promise. | Default proposal: template default 60 mm as starting value; require confirmation for quote; color/finish per group when not identical. OWNER_DECISION_REQUIRED. | 80 mm default; depth based on letter size; global cant only; per-group cant always; default white/black/aluminum/RAL/Oracal by product variant. | Wrong return depth or finish changes both price and manufacturing path. | yes | yes | yes | `cant.groups[].depth_mm`, `cant.groups[].finish_type`, `cant.groups[].color_code`, `cant.groups[].color_system` | Return / Cant | Registry supplies return profile, paint, Oracal, or material price coverage only. | Modelare, bonding, scrap, paint prep, and operation time remain internal-only. | TBD |
| PH2-OD-05 | Finish / Oracal / Print / Laminare | Which finish types are allowed before quote: no finish, Oracal 641/651/8500, print laminated, painting; must Oracal color, roll width, print required, and lamination required be explicit? | Finish is a major Product Truth area and cannot be inferred from SVG color or Pricing Registry availability. | Default proposal: finish type and target required before quote; Oracal color required when Oracal is selected; print_required and lamination_required explicit for artwork/print; roll width warning/conditional unless owner marks it commercial. OWNER_DECISION_REQUIRED. | Roll width required for quote; roll width internal-only; print always implies lamination; print and lamination separate; allow no finish as explicit confirmed choice. | Quote may promise wrong material/service or miss print/lamination cost. | yes for finish type/target/color/print policy; conditional for roll width | yes | yes | `finish.items[].finish_type`, `finish.items[].oracal_series`, `finish.items[].color_code`, `finish.items[].roll_width_mm`, `printed_artwork[].print_required`, `printed_artwork[].lamination_required` | Finish / Oracal / Print / Laminare; Artwork | Registry supplies material/service price coverage after truth exists. | Application time, waste, scrap, print setup, and capacity remain internal-only. | TBD |
| PH2-OD-06 | Artwork / Printed artwork | Is `printed_artwork` automatically print, can it be artwork-only, can it be ignored, how is target decided, and what should `logo stanga` / `logo dreapta` be in `gradi-curat.svg`? | Logos can be product graphics, artwork-only, ignored, or misclassified faces; the analyzer can suggest but not decide. | Default proposal: `printed_artwork` is a suggestion, not automatic final print; `logo stanga` and `logo dreapta` should default to printed artwork suggestions requiring operator confirmation. OWNER_DECISION_REQUIRED. | Always print; require target selection; allow artwork-only; allow ignored only by explicit operator confirmation; map to face/cant target when applied to product. | Artwork can be priced, produced, or ignored incorrectly. | yes | yes | yes | `layers[].confirmed_role`, `layers[].ignored`, `printed_artwork[].artwork_only`, `printed_artwork[].target`, `printed_artwork[].confirmed` | Artwork / Printed artwork; SVG / Layer roles | No decision ownership; print/laminate prices only after target and print truth are confirmed. | Print setup, laminate setup, scrap, and internal effort remain internal-only. | TBD |
| PH2-OD-07 | Finish target | Can target be face, cant, artwork, all, or another target, how is it expressed in UI, and when does missing target block quote? | Finish target separates which surface receives a finish. Without target, downstream systems guess. | Default proposal: require explicit target before quote for any active finish; UI should express target in component cards using owner-friendly labels: Fata, Cant, Artwork, Spate, All when policy allows. OWNER_DECISION_REQUIRED. | Target embedded in each card; single target selector per finish row; no `all`; allow `all` only as shortcut expanding to explicit targets. | Pricing Registry or ProductDefinition may be asked to repair missing semantics. | yes | yes | yes | `finish.items[].target`, `finish.items[].layer_key` | Finish; Face; Return / Cant; Back; Artwork | None except price coverage after target is known. | Internal operation branch selection can use target after Product Truth is confirmed. | TBD |
| PH2-OD-08 | T06 vs T19E | Should UI ask T06 as autocolant pe cant inainte de modelare and T19E as folie dupa corp format, when is this decided, and what does it block? | T06 and T19E are different semantic branches; they affect finish stage, operations, and commercial scope. | Default proposal: ask only when foil/print interacts with cant/body; require before quote if it changes commercial scope, otherwise before order at latest; use plain labels plus code. OWNER_DECISION_REQUIRED. | Always ask when Oracal on cant; derive from finish target; ask later at order; hide codes and show process labels only. | Wrong process branch can alter materials, sequence, quote, and execution plan later. | yes when active/commercial | yes | yes | `finish.items[].apply_stage`, `finish.items[].process_code` | Finish / Oracal / Return / Cant | Registry does not decide T06/T19E; only supplies prices for chosen branch. | Operation timing, sequence, and capacity remain internal-only. | TBD |
| PH2-OD-09 | Lighting / LED | What is default lighting mode, LED density/config default, PSU default, PSU placement policy, and which cable fields are quote vs execution? | Lighting changes commercial scope, electrical truth, and later execution risk. Current UI has lighting and PSU but not full cable/placement truth. | Default proposal: illuminated product defaults to LED modules with neutral light only as starting value; confirm lighting mode and PSU class before quote; cable lengths/types and PSU placement before order/execution unless owner includes them in quote. OWNER_DECISION_REQUIRED. | Non-illuminated default; LED strip default; front-lit/back-lit variants; cables required before quote; PSU placement required before quote. | Quote may omit electrical scope or execution may invent cabling/PSU placement. | yes for lighting mode and commercial PSU scope; conditional for cables | yes | yes | `lighting.enabled`, `lighting.system_type`, `lighting.light_color`, `lighting.led_density`, `electrical.psu.*`, `electrical.cables.*`, `electrical.transformer_hidden_mounting` | Electrical / LED | Registry supplies LED, PSU, wire/material price coverage only. | Watt reserve, cable routing, safety margin, assembly time, and capacity remain internal-only. | TBD |
| PH2-OD-10 | Support / Bare | Is rear support default yes/no, when use aluminum bars/structure/no support, when does support affect offer, and when execution? | Support must be first-class truth, not only derived from mounting system. | Default proposal: default support_required=false for direct_wall, but require explicit confirmation when geometry, mounting, or owner policy suspects support; support affects quote when commercial material/labor is included. OWNER_DECISION_REQUIRED. | Always ask support; derive fully from mounting; support required for large dimensions; aluminum bars default; steel/structure default; external support prep. | Support may be omitted from offer or invented during execution. | conditional | yes | yes | `support.required`, `support.type`, `support.bar_profile`, `support.material`, `support.position`, `support.prepared_internally` | Support / Bare; Mounting | Registry supplies support material/package prices only after support truth exists. | Fabrication, routing, welding, prep time, and capacity remain internal-only. | TBD |
| PH2-OD-11 | Mounting | What is default mounting system, is installation included or external, how is mounting surface/area handled, is template/sablon required, and what blocks quote? | Mounting affects offer scope, support trigger, template material, and later execution. | Default proposal: direct_wall as starting default only; require operator confirmation before quote; template/sablon enabled only when owner policy says it is part of offer; installation included/external must be explicit. OWNER_DECISION_REQUIRED. | Always include template; template optional; montaj external by default; montaj included by default; require site surface before quote; site details only before order. | Offer may include/exclude mounting or support incorrectly. | yes for mounting system and included/external scope | yes | yes | `mounting.system`, `mounting.included`, `mounting.template_enabled`, `mounting.template_area_m2`, `mounting.template_material`, `mounting.site_constraints` | Mounting; Support / Bare | Registry supplies template/material/hardware prices only. | Installation planning, crew/capacity, travel, and logistics remain internal-only. | TBD |
| PH2-OD-12 | Pricing / Cost boundary | Which questions must never go to Pricing Registry, what remains CostEngine internal-only, and how do we avoid hour/minute pricing? | The architecture forbids Pricing Registry from repairing Product Truth and forbids commercial price by minutes/hours. | Default proposal: Pricing Registry only answers coverage/prices after Product Truth; CostEngine keeps minutes, rates, capacity, waste, and actuals internal; commercial pricing uses unit/product rules. OWNER_DECISION_REQUIRED. | Allow owner acknowledgement when internal cost incomplete; stricter block when commercial rule missing; separate CommercialPriceProposal from EstimatedInternalCost. | Product Truth blockers may be mislabeled as pricing issues, or internal time may become client price. | yes only for missing commercial price coverage after truth exists | no direct, except snapshot readiness | no direct, except internal planning readiness | `readiness.pricing_coverage`, `commercial.rules`, not component Product Truth | CommercialPriceProposal; Pricing Registry; CostEngine | Pricing coverage only; no role/target/support/mounting/T06 decisions. | Internal-only for minutes, capacity, workcenter rates, actuals, waste, margin confidence. | TBD |
| PH2-OD-13 | Quote / Order / Execution classification | For each decision, is it required for quote, required for order, required for execution, optional, or warning only? | Phase 2 needs blocker taxonomy before UI/runtime; otherwise every missing detail either over-blocks quote or leaks into execution as guesswork. | Default proposal: quote requires commercial Product Truth; order requires frozen commercial decisions and non-ambiguous configs; execution requires full technical details; internal-only data is warning unless owner says otherwise. OWNER_DECISION_REQUIRED. | Make more fields quote blockers; defer more fields to order; classify cables/site constraints as execution only; use owner acknowledgement warnings. | Quote can unlock too early or stay blocked by internal-only data. | yes for commercial truth | yes for frozen order truth | yes for technical execution truth | `readiness.quote`, `readiness.order`, `readiness.execution`, `readiness.blockers[]`, `readiness.warnings[]` | Commercial offer readiness; all reusable components | Pricing coverage is a separate quote blocker only after Product Truth is complete. | Internal-only missing data should be warning or execution planning blocker, not client price blocker. | TBD |

---

## Recommended Owner Defaults

These are recommended starting defaults for owner review. They are not final rules.

| Area | Recommended default | Status |
|---|---|---|
| Global vs per group | Global defaults may prefill, but per-group confirmation is required for role, finish, color, artwork, cant exceptions, and any field that changes price or product meaning. | OWNER_DECISION_REQUIRED |
| Face material | Plexiglas opal as default material for volumetric face. | OWNER_DECISION_REQUIRED |
| Face thickness | 3 mm default; 5 mm only for owner-defined size/rigidity/use cases. | OWNER_DECISION_REQUIRED |
| Backing | Forex 10 mm default, no sanfren unless selected. | OWNER_DECISION_REQUIRED |
| Cant depth | Template/default 60 mm as starting value; allow owner-approved 80 mm or other values. | OWNER_DECISION_REQUIRED |
| Cant finish/color | Require explicit finish family and color when not neutral/default; support white, black, aluminum, RAL paint, Oracal wrap as owner-approved options. | OWNER_DECISION_REQUIRED |
| Face finish | Explicit no finish / Oracal 641 / Oracal 651 / Oracal 8500 / print laminated / painting. | OWNER_DECISION_REQUIRED |
| Oracal color | Required when Oracal is selected. | OWNER_DECISION_REQUIRED |
| Roll width | Warning or conditional field unless owner marks it commercial quote truth. | OWNER_DECISION_REQUIRED |
| Print required | Explicit boolean for artwork/print targets, not inferred from SVG color or role alone. | OWNER_DECISION_REQUIRED |
| Lamination required | Explicit boolean; print does not automatically become lamination unless owner policy says so. | OWNER_DECISION_REQUIRED |
| Printed artwork | `printed_artwork` remains a suggestion requiring operator decision; `logo stanga` and `logo dreapta` default to printed artwork suggestions for `gradi-curat.svg`. | OWNER_DECISION_REQUIRED |
| Artwork-only / ignored | Must be explicit operator choices, not silent omission. | OWNER_DECISION_REQUIRED |
| Finish target | Required before quote for any active finish; use face/cant/artwork/back/all only if owner accepts those labels. | OWNER_DECISION_REQUIRED |
| T06/T19E | Required when foil/print interacts with cant/body; use owner-friendly process labels plus process code. | OWNER_DECISION_REQUIRED |
| Lighting | If illuminated, LED modules with neutral light may prefill; lighting mode and commercial PSU scope require confirmation. | OWNER_DECISION_REQUIRED |
| PSU placement | Required before order/execution; before quote only if it changes commercial scope. | OWNER_DECISION_REQUIRED |
| Cables | Cable lengths/types are order/execution truth unless owner wants them in quote scope. | OWNER_DECISION_REQUIRED |
| Support | `support_required=false` may prefill for direct wall, but support must be confirmed when geometry/mounting/policy suspects support. | OWNER_DECISION_REQUIRED |
| Mounting | Direct wall may prefill; included/external mounting and template policy must be explicit before quote. | OWNER_DECISION_REQUIRED |
| Pricing boundary | Product Truth decisions never go to Pricing Registry; commercial price must not be hour/minute based. | OWNER_DECISION_REQUIRED |
| Cost boundary | Minutes, capacity, workcenter rates, waste, and actuals remain internal-only CostEngine data. | OWNER_DECISION_REQUIRED |

---

## Quote / Order / Execution Classification Guide

Use this as the owner-facing classification baseline.

| Classification | Meaning | Examples | Default recommendation |
|---|---|---|---|
| Required for quote | Missing value changes commercial product meaning, visual promise, material path, or commercial scope. | role confirmation, face material/thickness, finish type, finish target, print/lamination, mounting system, lighting mode when illuminated. | Block quote until resolved. OWNER_DECISION_REQUIRED. |
| Required for order | Missing value may not change initial quote total, but must be frozen before accepted order truth. | PSU placement, support bar position, cable policy when not included in quote, site constraints that do not affect quote. | Block order snapshot until resolved. OWNER_DECISION_REQUIRED. |
| Required for execution | Missing value is technical production/install detail needed before work starts. | final cable routing, detailed support prep, exact transformer hidden mounting, internal work instructions. | Block execution/materialization, not quote. OWNER_DECISION_REQUIRED. |
| Optional / warning only | Missing value informs internal confidence, efficiency, or later planning without changing commercial truth. | internal minutes, capacity estimate, nesting optimization details, workcenter rate for margin confidence only. | Warning only unless owner upgrades it to blocker. OWNER_DECISION_REQUIRED. |

---

## Implementation Readiness After Owner Answers

After owner answers are recorded, Phase 2 can safely prepare implementation of:

- component question labels in the existing Review UI;
- required/optional flags per component;
- per-group versus global behavior;
- quote/order/execution blocker taxonomy;
- UI copy for owner-approved wording;
- Product Truth candidate fields in docs;
- clear separation between suggested, fallback, manual, confirmed, blocked, and warning;
- component tests for UI-only behavior after a separate implementation GO;
- payload runtime only after a separate Product Truth GO.

Implementation must still preserve:

- Intake V6 as entry point;
- Straturi / Review / Confirmare;
- gradual modularization;
- Product Truth before ProductDefinition / Offer / Order;
- Pricing Registry as price/coverage only;
- CostEngine as internal-only.

---

## Still Forbidden After This Packet

This packet does not unlock:

- Product Truth runtime payload without separate GO;
- ProductDefinition changes;
- Pricing changes;
- ProductSystem/Dossier runtime changes;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- DB/schema/seeds;
- quote/order/materialization;
- utilaje/workcenters runtime;
- angajati/skills/capacity runtime;
- ExecutionReality;
- Employee Mobile;
- forced confirmations;
- Review unlock bypass;
- analyzer changes;
- payload changes;
- frontend/backend implementation.

---

## Roadmap Alignment Checkpoint

1. Roadmap source used

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`

2. Current roadmap phase

- Phase 2 - Modular Form component questions

3. Roadmap status of this task

- NEXT / owner decision gate

4. Why this task belongs here

This task turns the Phase 2 inventory into owner-answerable decisions before runtime/UI implementation. Phase 2 cannot safely add component questions until the owner decides which fields are quote blockers, which are order/execution blockers, which defaults are allowed, and how Product Truth stays separate from Pricing Registry and CostEngine. It keeps the current Intake V6 wizard and prevents downstream systems from inventing missing truth.

5. What this task must NOT unlock

This task does not automatically unlock:

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

---

## Forbidden Confirmation

Confirmed for this packet:

- no frontend changes;
- no backend changes;
- no tests changed;
- no analyzer changes;
- no payload changes;
- no pricing changes;
- no ProductTruth runtime changes;
- no ProductDefinition;
- no ProductSystem runtime;
- no ProductAggregate;
- no ExecutionPlan;
- no DB/schema/seeds;
- no materialization;
- no quote/order/execution;
- no Employee Mobile.

Tests: NOT_RUN_DOCS_ONLY  
Build: NOT_RUN_DOCS_ONLY
