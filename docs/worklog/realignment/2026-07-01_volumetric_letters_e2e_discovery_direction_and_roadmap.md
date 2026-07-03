# 2026-07-01 — Volumetric Letters E2E Discovery Direction and Roadmap

**Status:** DONE_DOCS_ONLY  
**Primary artifact:** `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`  
**Implementation:** none

---

## Scope

Created the docs-only strategic reconciliation and roadmap for Volumetric Letters E2E implementation order.

The work reconciles:

- Intake V6 Product Truth direction;
- reusable volumetric component contracts;
- Modular Form readiness boundary;
- Modular Form UI state contract;
- `gradi-curat.svg` runtime findings;
- old ProductDefinition, ProductAggregate, Pricing Registry, Commercial/Internal Cost, and volumetric current-state docs;
- the latest operator-friendly labels/state-badges micro-slice.

No code or runtime behavior was changed.

---

## Documents Read / Reconciled

- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md`
- `docs/architecture/INTAKE_V6_MODULAR_FORM_CONTRACT.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md`
- `docs/architecture/realignment/03_PRODUCT_DEFINITION_COMPILER.md`
- `docs/architecture/realignment/04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md`
- `docs/architecture/realignment/08_PRICING_REGISTRY_SEPARATION.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_docs_reconciliation.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_product_truth_contract.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_intake_v6_reusable_components_contract.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_intake_v6_modular_form_readiness_boundary.md`
- `docs/worklog/realignment/2026-07-01_volumetric_letters_intake_v6_modular_form_ui_state_contract.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_operator_friendly_labels_state_badges.md`

Missing/flagged during reconciliation:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_EXISTING_FORM_TO_MODULAR_FORM_UI_CONTRACT.md` was not found as a separate file in this export; its content direction appears folded into the UI State Contract.
- `docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md` was not found in this export.

---

## Conclusions

Official direction:

- keep the existing Intake V6 UI as the base;
- modularize gradually;
- Intake V6 produces Product Truth;
- SVG Analyzer suggests, it does not decide;
- Form System asks missing component inputs;
- operator confirmation converts suggestions/fallbacks into accepted truth;
- ProductDefinition consumes Product Truth;
- ProductSystem/Dossier holds component contracts and allowed variants;
- Pricing Registry resolves price/configuration coverage, not missing Product Truth;
- CommercialPriceProposal computes client commercial proposal, not hourly/minute pricing;
- CostEngine remains internal-only;
- ProductAggregate comes after Order Snapshot;
- ExecutionPlan comes after ProductAggregate/Order/Task Graph;
- machines/workcenters and employees/skills/capacity are execution/capacity concerns, not commercial hourly tariff;
- Employee Mobile is final-final.

Mandatory `gradi-curat.svg` conclusion:

`Pricing Registry este pregatit; blockerul real este Product Truth incomplet / layer_roles_incomplete.`

---

## Roadmap Summary

The roadmap defines 16 ordered phases:

- Phase 0 — Preserve and document current Intake V6 truth: NOW.
- Phase 1 — Operator-friendly layer/group truth: NOW / partially implemented.
- Phase 2 — Modular Form component questions: NEXT.
- Phase 3 — Product Truth canonical output: NEXT.
- Phase 4 — ProductDefinition consumes Product Truth: LATER.
- Phase 5 — ProductSystem / Dossier modular contract: LATER.
- Phase 6 — CommercialPriceProposal / Offer: LATER.
- Phase 7 — Quote Snapshot: LATER.
- Phase 8 — Order Snapshot: LATER.
- Phase 9 — ProductAggregate: LATER / FORBIDDEN_NOW.
- Phase 10 — Task Graph / Operations: LATER / FORBIDDEN_NOW.
- Phase 11 — ExecutionPlan: LATER / FORBIDDEN_NOW.
- Phase 12 — Utilaje / Workcenters: LATER.
- Phase 13 — Angajati / Skills / Capacity: LATER.
- Phase 14 — ExecutionReality: LATER.
- Phase 15 — Employee Mobile: FINAL-FINAL.

Every phase has an explicit verification method and re-audit gate.

---

## Re-audit Points

Re-audit gates were defined for:

- after UI labels/state badges;
- before and after component form implementation;
- before and after Product Truth canonical payload;
- before ProductDefinition;
- before ProductSystem/Dossier changes;
- before CommercialPriceProposal changes;
- before Quote Snapshot;
- before Order Snapshot;
- before ProductAggregate;
- before Task Graph;
- before ExecutionPlan;
- before utilaje/workcenters;
- before angajati/skills/capacity;
- before ExecutionReality;
- before Employee Mobile.

The key stop rule is that ProductAggregate, Task Graph, ExecutionPlan, machines, employees, and Employee Mobile must not begin while Product Truth or snapshots are unstable.

---

## What Remains Unimplemented

No implementation was performed in this slice.

Known remaining implementation areas include:

- component-owned Review/Form questions;
- canonical Product Truth payload shape/runtime output;
- ProductDefinition consumption of canonical Product Truth;
- ProductSystem/Dossier alignment to reusable components;
- CommercialPriceProposal after complete Product Truth;
- Quote Snapshot and Order Snapshot;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Workcenters / Utilaje;
- Employees / Skills / Capacity;
- ExecutionReality;
- Employee Mobile.

---

## Explicit Non-Changes

This slice did not change:

- frontend code;
- backend code;
- tests;
- analyzer logic;
- payload structure;
- readiness logic;
- pricing logic;
- ProductDefinition;
- ProductAggregate;
- ExecutionPlan;
- database schema;
- seeds;
- quote/order/session/materialization behavior.

No ProductAggregate, no ExecutionPlan, no CommercialPriceProposal, no CostEngine, no Pricing Registry changes, and no hourly commercial pricing were introduced.

---

## Recommended Next Safe Slice

Recommended next safe slice:

**UI-only micro-slice: apply the same badge vocabulary to artwork finish cards and the readiness summary panel.**

Why:

- starts from Intake V6;
- preserves the existing UI;
- improves operator clarity;
- stays display-only;
- does not change analyzer/payload/readiness/pricing/backend;
- keeps ProductAggregate and ExecutionPlan out of scope;
- can be verified against `gradi-curat.svg`.

---

## Validation

- docs-only artifact created: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- worklog created: `docs/worklog/realignment/2026-07-01_volumetric_letters_e2e_discovery_direction_and_roadmap.md`
- tests: NOT_RUN_DOCS_ONLY
- code changes: NONE
- materialization: NONE
