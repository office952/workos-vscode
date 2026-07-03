# Phase 2 Existing Form Answers Audit

**Date:** 2026-07-01  
**Status:** COMPLETE  
**Scope:** READ_ONLY_DOCS_ONLY  
**Runtime anchor:** `gradi-curat.svg` / `IV6-BB8EE3F8` / `IR-MR18L96M`

---

## Why This Was Needed

Owner clarified that most Phase 2 answers should not be invented from zero. Many answers already exist in Intake V6 / Review as form controls, defaults, operator-confirmable fields, or fallback/hydrated values.

This work realigns the owner answer flow so the owner validates existing form policy where the form already answers, and only decides missing policy where the current form does not answer enough for Product Truth.

---

## Sources Read

Docs read:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_DECISION_PACKET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_MODULAR_FORM_COMPONENT_QUESTIONS_INVENTORY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`

Code read-only:

- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLightingSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkOnlyDecisionPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/useTemplateFormContract.ts`
- `frontend/src/lib/intakeV6/intakeV6ReviewFormContract.ts`
- `frontend/src/lib/intakeV6/intakeV4FaceFinishOptions.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/lib/intakeV6/intakeV6BackingMode.ts`
- `frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts`
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts`
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`

---

## Documents Created / Updated

Created:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_EXISTING_FORM_ANSWERS_AUDIT.md`

Updated:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`

Created:

- `docs/worklog/realignment/2026-07-01_phase_2_existing_form_answers_audit.md`

---

## Found In Existing Form

Existing Intake V6 already answers or partially answers:

- Oracal 641 / 651 / 8500 face finish choices;
- Oracal color selection;
- face vinyl roll width;
- print + laminare as current finish/execution mode;
- cant / return depth;
- cant / return finish family;
- RAL paint;
- Oracal 651 wrapped cant;
- Alb / Negru / Auriu / Argintiu return options mapped to aluminum finish types;
- Forex 10 mm backing;
- backing with or without sanfren;
- illuminated toggle;
- LED modules / LED strip;
- light color;
- LED module wattage;
- emblem lighting mode;
- derived LED counts/watts;
- PSU class/select;
- mounting system;
- mounting template enabled/area/material;
- mounting bars/profile;
- printed_artwork / logo / ignore role options;
- artwork confirmation;
- artwork transparency;
- artwork-only confirm/exclude path.

---

## Remains Owner Validation

Owner should validate existing policy instead of answering from zero for:

- hybrid global default plus per-group override model;
- Forex 10 mm backing with/without sanfren;
- cant depth/finish/color allowed set;
- Oracal and roll width policy;
- printed_artwork/logo/ignore policy;
- lighting defaults and PSU class policy;
- mounting system/template/bar profile policy;
- Product Truth / Pricing Registry / CostEngine boundary.

---

## Remains Owner Decision

Owner still needs to decide missing policy for:

- face material and plexiglas thickness;
- explicit finish target model;
- explicit print_required and lamination_required booleans;
- T06 vs T19E applicability and blocker level;
- cable type/length/placement fields;
- PSU placement policy;
- support_required/type/material/position/internal prep;
- installation included vs external;
- site/surface constraints;
- final per-field quote/order/execution taxonomy.

---

## Validation

- Markdown diagnostics for the new audit doc: PASS.
- Markdown diagnostics for the patched owner answer sheet: PASS.
- Final Markdown diagnostics for all three touched docs: PASS.

Tests: NOT_RUN_READ_ONLY_AUDIT  
Build: NOT_RUN_READ_ONLY_AUDIT

---

## Forbidden Scope Confirmation

Confirmed:

- no frontend changes;
- no backend changes;
- no tests changed;
- no tests run;
- no build run;
- no analyzer changes;
- no payload changes;
- no pricing changes;
- no ProductTruth runtime changes;
- no ProductDefinition;
- no ProductAggregate;
- no ExecutionPlan;
- no DB/schema/seeds;
- no materialization;
- no quote/order/execution;
- no Employee Mobile.
