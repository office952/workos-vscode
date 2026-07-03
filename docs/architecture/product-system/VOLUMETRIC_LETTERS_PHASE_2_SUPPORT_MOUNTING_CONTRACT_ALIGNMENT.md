# Volumetric Letters Phase 2 Support / Mounting Contract Alignment

**Date:** 2026-07-01  
**Status:** DOCUMENTED_NOT_IMPLEMENTED  
**Scope:** Phase 2 support vs mounting contract audit, docs-first, no payload runtime  
**Runtime anchor:** `gradi-curat.svg` / `IV6-BB8EE3F8` / `IR-MR18L96M`

---

## 1. Purpose

Clarify the contract boundary between Mounting / Montaj and Support / Bare / Structura suport before canonical Product Truth payload design.

This document aligns:

- existing Intake V6 form fields;
- Phase 2 owner-approved answers;
- Product Truth candidate semantics;
- ProductSystem / Dossier module triggers;
- Pricing and CostEngine boundaries;
- future Order / Execution needs.

This document does not implement payload, backend, DB/schema, pricing, ProductDefinition, ProductAggregate, Task Graph, ExecutionPlan, materialization, quote/order/execution creation, or Employee Mobile behavior.

---

## 2. Current Mismatch

Observed canonical warning:

```text
TRIGGER_FIELD_MISMATCH:
structura_suport link=metal_support_required
intake=finish_setup.mounting_system

Module link trigger_field 'metal_support_required' may not match Intake V6 field 'mounting_system' used in commercial quote flow.
```

Verdict: real contract mismatch.

Current code and docs use a transitional bridge:

- ProductSystem module link still points to `metal_support_required` for `structura_suport`;
- Intake V6 Review currently exposes `finish_setup.mounting_system` as the operator-facing control;
- several runtime preview/cost/commercial paths derive `structura_suport` or `metal_support_required` from mounting values such as `steel_bars` / `aluminum_bars`;
- this is acceptable as a documented transitional warning, but it is not clean Product Truth.

The risk is semantic collapse: mounting system may be treated as support truth, even though mounting and support are separate Phase 2 component questions.

---

## 3. Source Inventory

| Source file | Symbol / field / copy | Category | Current meaning | Used by | Risk | Recommended action |
|---|---|---|---|---|---|---|
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md` | Phase 2 component questions, Product Truth before downstream | MIXED | roadmap says support/mounting belong in Phase 2 and downstream must not invent missing truth | Docs only | low | Keep as roadmap source. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md` | PH2-OD-10 Support / Bare | SUPPORT | support/bars optional; detected support/bars suggested and confirmed; otherwise manually selectable | Docs only | medium if not made first-class later | Use as owner-approved policy. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md` | PH2-OD-11 Mounting | MOUNTING | offer must classify mounting as no mounting / included / external / to decide | Docs only | medium because current UI only has `mounting_system` | Use for future `mounting_scope`. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_EXISTING_FORM_ANSWERS_AUDIT.md` | `mounting_system`, bar profile, support truth missing | MIXED | current form has bars via mounting, not first-class support truth | Docs only | high if mistaken as complete support truth | Mark `NEEDS_BRIDGE`. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_MODULAR_FORM_COMPONENT_QUESTIONS_INVENTORY.md` | `support.required`, `support.type`, `mounting.system`, `template` | MIXED | conceptual docs-only Product Truth candidate shape separates support and mounting | Docs only | low | Preserve separation. |
| `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md` | support truth, mounting truth, `metal_support_required`, `mounting_system` | MIXED | support missing type/position/prep; mounting has native trigger alignment debt | Docs only | high if ProductSystem repairs missing Product Truth | Use as canonical warning. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md` | `rear_support` and `mounting` reusable components | MIXED | `rear_support` and `mounting` are separate components with separate outputs | Docs only | low | Continue using component separation. |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md` | `SUPPORT_TYPE_MISSING`, `MOUNTING_SYSTEM_MISSING` | MIXED | support type and mounting system are separate blockers | Readiness docs only | medium | Keep separate blocker taxonomy. |
| `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` | mounting/template commercial vs internal cost | MOUNTING | mounting/template may be commercial lines; minutes remain internal-only | Pricing docs | medium if support cost leaks into hourly pricing | Keep pricing boundary. |
| `docs/architecture/INTAKE_V6_MODULAR_FORM_CONTRACT.md` | TRIGGER_FIELD_MISMATCH resolution | MIXED | older contract says DB link uses `metal_support_required`; Intake V6 uses `finish_setup.mounting_system` | Docs only | high because it suggests future DB trigger migration | Supersede with explicit support/mounting bridge design later. |
| `frontend/src/lib/intakeV6/intakeV6ComponentQuestionDisplay.ts` | `supportBars` chips | SUPPORT | display-only Support component labels and missing UI gap | Intake V6 UI | low | Add explicit separation warning only. |
| `frontend/src/lib/intakeV6/intakeV6ComponentQuestionDisplay.ts` | `mountingScope` chips | MOUNTING | display-only Mounting component labels and missing commercial scope gap | Intake V6 UI | low | Add label that `mounting_system` is not support truth. |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | mounting tab, support/mounting/pricing badge stack | MIXED | existing Review insertion point for Mounting, Support, Pricing boundary chips | Intake V6 UI | low if kept display-only | Reuse, do not add controls. |
| `frontend/src/lib/intakeV6/intakeV6ModuleActivationPreview.ts` | `BAR_MOUNTING`, `resolveStructuraSuportState`, `triggerMismatchNote` | MIXED | derives `structura_suport` active from `mounting_system` values | Review preview | high semantic bridge debt | Document as bridge; do not treat as canonical support truth. |
| `frontend/src/components/workos/intake-v6/IntakeV6ModularFormAwarenessPanel.tsx` | `structura_suport` display state | SUPPORT | displays selected/active structure module; currently driven by preview state | Intake V6 UI | medium because UI can imply support is solved | Add display-only explanation if touched. |
| `frontend/src/features/product-system/TemplateDownstreamLinkagePanel.tsx` | trigger DB `<-` Intake linkage display | MIXED | displays `metal_support_required <- finish_setup.mounting_system` alignment warning | ProductSystem UI | medium | Add owner-friendly explanation near existing warning. |
| `frontend/src/features/product-system/TemplateDownstreamLinkagePanel.test.tsx` | `module_link_trigger_field`, `canonical_intake_field` | MIXED | test fixture for mismatch display | Tests | low | Extend if UI copy changes. |
| `frontend/src/lib/intakeV6/useTemplateFormContract.ts` | `mounting_system`, values `direct_wall`, `steel_bars`, `aluminum_bars`, `acm_panel` | MOUNTING | Intake V6 contract options for mounting system | Intake V6 UI | medium because `steel_bars`/`aluminum_bars` mix support type into mounting enum | Future payload split needed. |
| `frontend/src/lib/intakeV6/intakeV6ReviewFormContract.ts` | default mounting system `direct_wall` | MOUNTING | default/prefill for Review adapter | Intake V6 UI | low if displayed as fallback only | Keep visible/confirmable. |
| `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts` | `support_panel`, `frame`, `reference` roles | SUPPORT | SVG/layer role candidates for support-related layers | SVG / Intake V6 UI | medium because detection is suggestion only | Map to `support_source=detected_svg` later. |
| `frontend/src/lib/svgAnalyzer/analyzer/guessLayerAutoRole.ts` | `support_panel` keyword suggestion | SUPPORT | analyzer can suggest support panel role | SVG Analyzer | medium | Keep suggestion-only. |
| `frontend/src/lib/svgAnalyzer/analyzer/layerRoleTypes.ts` | role `support_panel` | SUPPORT | layer role vocabulary | SVG Analyzer / UI | medium | Future bridge to support candidate only after operator confirmation. |
| `frontend/src/lib/intakeV6/mapAnalyzerReportToModuleDetectionResult.ts` | `support_panel` / `frame` mapping | SUPPORT | maps detected layers into module hints | SVG Analyzer / Review preview | medium | Keep as suggestion, not activation truth. |
| `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts` | skips `support_panel` / `bond_panel` from quote geometry | SUPPORT | support panels are not counted as main letter geometry | Review preview / geometry | low | Keep. |
| `frontend/src/lib/volumetricQuoteFlowState.ts` | `METAL_SUPPORT_MOUNTING_SYSTEMS`, `metal_support_required` | MIXED | legacy quote flow derives metal support from bar mounting | Pricing / quote flow | high | Document as legacy bridge; payload design later. |
| `backend/data/mini_module_registry_volumetric_v2.py` | `structura_suport`, consumed fields, `trigger_field='metal_support_required'`, TRIGGER_FIELD_MISMATCH | MIXED | ProductSystem registry knows mismatch and exposes warning | ProductSystem template / Dossier | high | Keep warning; later migrate to explicit support bridge. |
| `backend/seeds/seed_tpl_volumetric_letters_v2.py` | module link `trigger_field='metal_support_required'` | SUPPORT | seeded ProductSystem link trigger | ProductSystem template | high | PRODUCTSYSTEM_CONTRACT_LATER, not now. |
| `backend/schemas/intake_v6_modular_form.py` | warning code default `TRIGGER_FIELD_MISMATCH` | MIXED | contract schema carries mismatch alignment warning | Form contract API | medium | Keep docs-only warning. |
| `backend/services/intake_v6_pilot_contract_seed.py` | `canonical_intake_field=finish_setup.mounting_system`, derived key `metal_support_required` | MIXED | pilot contract documents DB trigger mismatch and quote adapter derivation | ProductSystem / form contract | high | Future bridge design. |
| `backend/services/product_definition_builder_service.py` | `_derive_metal_support_required(mounting_system)` | MIXED | ProductDefinition preview derives support boolean from mounting | ProductDefinition | high because hidden inference | PAYLOAD_RUNTIME_LATER must replace with explicit support truth. |
| `backend/services/product_aggregate_service.py` | `TRIGGER_FIELD_MISMATCHES = {'metal_support_required': 'mounting_system'}` | MIXED | Aggregate warning maps ProductSystem link trigger to Intake field | ProductAggregate | medium warning only | Do not remove until contract migrated. |
| `backend/services/aggregate_cost_bom_adapter.py` | `MODULE_GEOMETRY_KEYS['structura_suport']=['mounting_system']`; active if bar mounting | MIXED | cost BOM bridge activates support cost from mounting | Pricing / CostEngine | high if support inferred silently | Later consume explicit `support_required`. |
| `backend/services/commercial_price_proposal_service.py` | active modules add/discard `structura_suport` based on mounting | MIXED | commercial proposal bridge uses mounting to include/exclude support | Pricing | high | Later require support truth before priced support line. |
| `backend/services/estimated_internal_cost_service.py` | same active module bridge pattern | MIXED | internal estimate bridge uses mounting | CostEngine | medium | Later use explicit support truth. |
| `backend/services/quote4_workspace_quote_input_mapper.py` | `structura_suport inactive for direct_wall` provenance | MIXED | quote input mapper treats direct wall as no support structure | Review preview / quote bridge | medium | Keep informational, not canonical support truth. |
| `backend/services/intake_v4_commercial_quote_service.py` | `metal_support_required` legacy quote input | SUPPORT | legacy V4 quote path uses metal support trigger | Pricing legacy | medium | Legacy only; do not use as Product Truth model. |
| `backend/services/intake_v6_commercial_quote_service.py` | `quote_input['metal_support_required'] = True` | SUPPORT | V6 commercial bridge can set metal support flag | Pricing bridge | high | Replace later with explicit support fields. |
| `backend/scripts/step7e_report.json` | exact TRIGGER_FIELD_MISMATCH copy | MIXED | generated historical report with current mismatch | Docs/audit artifact | low | Evidence only. |
| `backend/tests/test_intake_v6_modular_form.py` | asserts trigger alignment mismatch | MIXED | backend test locks current warning | Tests | low | Keep until contract migration. |
| `backend/tests/test_product_aggregate_volumetric_v2.py` | asserts aggregate mismatch warning | MIXED | backend test locks warning | Tests | low | Keep until ProductSystem contract migration. |

---

## 4. Support / Mounting Mismatch Explanation

`metal_support_required` means the product needs a metal support / bars / rear structural support branch. It is Support truth. It should answer: do we need support, what kind of support, why, and is it quote-relevant?

`finish_setup.mounting_system` means the currently selected mounting method in the existing Intake V6 Review form. It is Mounting truth. It answers how the product is intended to be mounted, not whether a separate support structure is truly required.

Using `mounting_system` as the trigger for metal support can be wrong because:

- some mounting methods imply no separate support;
- some direct-wall jobs may still require rear bars because of size, span, substrate, or owner/operator decision;
- some external-installation jobs may require no support from P-Media;
- an SVG may contain a separate support layer/group that should become a suggestion requiring confirmation, not a silent activation.

Mounting can imply support only when the contract explicitly says the chosen mounting method includes a support structure. Current bridge examples are `steel_bars` and `aluminum_bars`, but those values mix mounting method and support type in one enum.

Mounting does not imply support when it only describes installation responsibility or surface approach, such as direct wall or external installation with no P-Media support structure.

ProductSystem should not repair missing Product Truth. ProductSystem may describe modules and allowed links, but it must not decide `support_required` from incomplete Intake V6 truth. Product Truth must be completed in Intake V6/Form/Operator Review first.

Examples:

| Example | Mounting value | Support value | Meaning |
|---|---|---|---|
| 1 | `mounting_system = direct_wall` | `support_required = false` | Direct wall mounting with no separate rear support. |
| 2 | `mounting_system = direct_wall` | `support_required = true` | Direct wall mounting, but large letters need rear bars or stabilizing structure. |
| 3 | `mounting_scope = mounting_external` | `support_required = false` | Installation is externalized; no support structure is included by P-Media unless separately selected. |
| 4 | SVG layer role `support_panel` / `frame` detected | `support_required = suggested` | Analyzer suggests support evidence; operator must confirm support truth. |

---

## 5. Target Semantic Contract - Support vs Mounting

**DOCUMENTED_NOT_IMPLEMENTED**

Future Product Truth candidate fields should separate mounting and support.

### Mounting Fields

| Field | Values | Current implementation status |
|---|---|---|
| `mounting_scope` | `no_mounting`, `mounting_included`, `mounting_external`, `to_be_decided` | DOCUMENTED_NOT_IMPLEMENTED |
| `mounting_system` | `direct_wall`, `spacer`, `rail`, `template`, `other` | PARTIAL today via existing `direct_wall`, `steel_bars`, `aluminum_bars`, `acm_panel`; values need cleanup later |
| `mounting_surface` | free/enum later | optional/order/execution; DOCUMENTED_NOT_IMPLEMENTED |
| `mounting_template_required` | boolean / conditional | PARTIAL today via `mounting_template_enabled` |

### Support Fields

| Field | Values | Current implementation status |
|---|---|---|
| `support_required` | `yes`, `no`, `suggested`, `unknown` | DOCUMENTED_NOT_IMPLEMENTED |
| `support_type` | `none`, `aluminum_bars`, `metal_frame`, `rear_support`, `other` | PARTIAL today through bar mounting labels only |
| `support_source` | `detected_svg`, `operator_selected`, `owner_default`, `product_rule` | DOCUMENTED_NOT_IMPLEMENTED |
| `support_quote_relevant` | boolean / conditional | DOCUMENTED_NOT_IMPLEMENTED |

Rule: `mounting_system` may contribute to a support suggestion or bridge only through an explicit mapping object, not by silent inference.

---

## 6. Current-to-Target Mapping

| Current field | Current location | Current meaning | Target field | Mapping status | Quote impact | Order impact | Execution impact | Recommended next implementation type |
|---|---|---|---|---|---|---|---|---|
| `finish_setup.mounting_system` | Intake V6 Review / payload bridge | mounting method enum; today includes bar choices | `mounting_system` | PARTIAL | required when mounting affects offer | required | required | PAYLOAD_DESIGN_LATER |
| `metal_support_required` | ProductSystem module link / quote input bridge | support module trigger boolean | `support_required` | NEEDS_BRIDGE | quote-relevant when support affects offer | required if active | required if active | PRODUCTSYSTEM_CONTRACT_LATER + PAYLOAD_RUNTIME_LATER |
| `structura_suport` | ProductSystem module code | support/premount structure module | `support_type` + `support_required` | NEEDS_BRIDGE | priced only if support active | frozen if active | task branch later | PRODUCTSYSTEM_CONTRACT_LATER |
| `mounting_system = direct_wall` | existing Review/form contract | direct wall mounting method | `mounting_system` only | EXACT for mounting; WRONG as support truth | can mean no support, but not proof by itself | order needs explicit support false/yes later | execution needs support truth later | UI_DISPLAY_ONLY + PAYLOAD_DESIGN_LATER |
| `support_panel` / `frame` detected from SVG | SVG Analyzer / layer roles | support evidence suggestion | `support_source=detected_svg`, `support_required=suggested` | NEEDS_BRIDGE | conditional quote blocker after confirmation policy | required if support selected | required if support selected | PAYLOAD_DESIGN_LATER |
| `steel_bars` / `aluminum_bars` inside `mounting_system` | existing Review/form contract | bar mounting option; mixes mounting and support type | `mounting_system` + `support_type` | PARTIAL | quote-relevant if support affects offer | required | required | PAYLOAD_DESIGN_LATER |
| mounting included/external | owner answer sheet; not first-class UI today | commercial installation scope | `mounting_scope` | NEEDS_BRIDGE | required before quote | required | method details later | PAYLOAD_DESIGN_LATER |
| `mounting_template_enabled` | Intake V6 Review / form contract | template/sablon required flag | `mounting_template_required` or `mounting_system=template` | PARTIAL | conditional quote line | order snapshot if active | execution prep later | PAYLOAD_DESIGN_LATER |
| `mounting_template_area_m2` | Intake V6 Review / derived fallback | template area | mounting template detail | PARTIAL | quote relevant if template priced | required if active | required if produced | PAYLOAD_RUNTIME_LATER |
| `mounting_bar_profile` | Intake V6 Review / template contract | bar profile for premount | `support_type` detail / support material/profile | NEEDS_BRIDGE | quote relevant if support active | required if active | required | PAYLOAD_DESIGN_LATER |
| ProductAggregate mismatch mapping | `product_aggregate_service.py` | warning-only bridge from `metal_support_required` to `mounting_system` | explicit bridge warning | NEEDS_BRIDGE | warning only now | warning only now | warning only now | DOC_ONLY now, PRODUCTSYSTEM_CONTRACT_LATER |
| Commercial/Cost active module bridge | commercial/cost services | include/exclude `structura_suport` from bar mounting | explicit support activation | NEEDS_BRIDGE | can affect preview line | can affect snapshot later | later task branch | PAYLOAD_RUNTIME_LATER |
| ProductDefinition `_derive_metal_support_required` | ProductDefinition builder service | derives support boolean from mounting | explicit support truth | REMOVE_AS_TRIGGER later | current preview bridge only | later must consume support truth | later must consume support truth | PAYLOAD_RUNTIME_LATER |

---

## 7. Current UI Display Recommendation - No Payload Runtime

No new form, duplicate controls, or wizard should be created now.

Mounting section may show:

- `Component: Mounting`;
- `Product Truth candidate`;
- `Mounting scope must be explicit`;
- `Required for quote when included/external`;
- `Site/method details order/execution`;
- `mounting_system is mounting, not support truth`.

Support section may show:

- `Component: Support`;
- `Product Truth candidate when support affects offer/order/execution`;
- `Optional unless detected/suggested`;
- `If not detected in SVG, ask/select in form later`;
- `If detected in SVG, show suggested and require confirmation`;
- `metal_support_required means Support/Bare, not mounting method`.

Current mismatch warning may show, only near existing linkage/boundary surfaces:

```text
Support and mounting are separate decisions. Current template link uses mounting_system as support trigger; contract needs alignment before Product Truth payload.
```

This warning should not be a global banner and must not change readiness.

---

## 8. Pricing / Cost Boundary

Pricing Registry does not decide support or mounting truth.

Rules:

- support requirement is Product Truth, not pricing coverage;
- mounting scope/system is Product Truth, not CostEngine output;
- Pricing Registry may provide prices only after truth exists;
- CommercialPriceProposal may price support/mounting only from accepted truth and commercial rules;
- CostEngine may estimate bars, prep, welding, mounting effort, and capacity internally;
- client commercial pricing must not be hour/minute based.

Missing support truth must not be repaired by Pricing Registry, workcenter rates, ProductAggregate, or ExecutionPlan.

---

## 9. Product Truth Payload Impact Later

**DOCUMENTED_NOT_IMPLEMENTED**

Later payload design should introduce explicit support and mounting branches, for example:

```ts
type MountingTruthCandidate = {
  mounting_scope: "no_mounting" | "mounting_included" | "mounting_external" | "to_be_decided";
  mounting_system: "direct_wall" | "spacer" | "rail" | "template" | "other";
  mounting_surface?: string | null;
  mounting_template_required?: boolean | null;
  state: "suggested" | "confirmed" | "fallback" | "manual" | "blocked" | "warning";
};

type SupportTruthCandidate = {
  support_required: "yes" | "no" | "suggested" | "unknown";
  support_type: "none" | "aluminum_bars" | "metal_frame" | "rear_support" | "other";
  support_source: "detected_svg" | "operator_selected" | "owner_default" | "product_rule";
  support_quote_relevant?: boolean | null;
  state: "suggested" | "confirmed" | "fallback" | "manual" | "blocked" | "warning";
};
```

Future migration must preserve source state: suggested support from SVG is not confirmed support truth; fallback mounting is not confirmed mounting truth.

---

## 10. ProductSystem / Dossier Impact Later

**DOCUMENTED_NOT_IMPLEMENTED**

Future ProductSystem work should replace the ambiguous trigger bridge with an explicit contract:

- module `structura_suport` activates from `support_required=yes`, not raw `mounting_system`;
- `mounting_system` may create a support suggestion only through a documented bridge rule;
- `metal_support_required` should either be retired or aliased to canonical `support_required` in a controlled DB migration;
- ProductSystem / Dossier must expose component vocabulary and allowed options, not repair missing Intake V6 truth.

Until that migration, `TRIGGER_FIELD_MISMATCH` should remain visible as a warning.

---

## 11. Execution / TaskGraph Impact Later

**DOCUMENTED_NOT_IMPLEMENTED**

Execution and Task Graph must wait for frozen quote/order truth.

Later rules:

- mounting scope and support truth must be frozen before execution tasks are derived;
- `support_type=aluminum_bars` or `metal_frame` may activate support preparation tasks after order truth exists;
- `mounting_template_required=true` may activate template preparation tasks;
- `mounting_surface` and site constraints belong at order/execution level if they do not change quote;
- ExecutionPlan must not infer support from `mounting_system` if Intake V6 did not confirm support truth.

---

## 12. What Remains Forbidden Now

Forbidden in this slice:

- new form;
- duplicate controls;
- new wizard;
- backend changes;
- DB/schema/seeds;
- API changes;
- payload shape changes;
- Product Truth runtime canonical payload;
- readiness/gating logic changes;
- analyzer changes;
- pricing changes;
- ProductDefinition changes;
- ProductSystem runtime changes;
- ProductAggregate changes;
- Task Graph;
- ExecutionPlan;
- materialization;
- quote/order/execution creation;
- forced confirmations;
- Review artificial unlock;
- Employee Mobile.

---

## 13. Recommended Next Slice

Recommendation: `UI_DISPLAY_PASS_NEXT_PAYLOAD_DESIGN`.

Next safe slice after this document:

1. Product Truth payload design docs for `support` and `mounting` branches only.
2. No runtime payload implementation until owner GO.
3. Later ProductSystem contract migration plan for `metal_support_required -> support_required` bridge.

---

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`.
2. Current roadmap phase: Phase 2 - Modular Form component questions.
3. Roadmap status of this task: NEXT / support-mounting contract alignment.
4. Why this task belongs here: support and mounting are Phase 2 component-owned questions; the current mismatch blocks clean Product Truth payload design; it keeps Intake V6 as the source; it does not jump to ProductDefinition, ProductAggregate, or ExecutionPlan.
5. What this task must NOT unlock: Product Truth canonical payload, ProductDefinition, ProductSystem/Dossier runtime changes, CommercialPriceProposal, Quote Snapshot, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, or Employee Mobile.
6. Re-audit gate result: PASS.
7. Roadmap implementation progress: 11/100%.
8. Roadmap alignment score: 100/100%.
9. Cat sunt in directia stabilita: 100/100%.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.