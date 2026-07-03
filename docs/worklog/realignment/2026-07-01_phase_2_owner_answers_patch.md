# Phase 2 Owner Answers Patch

**Date:** 2026-07-01  
**Status:** COMPLETE  
**Scope:** DOCS_ONLY  
**Roadmap status:** NEXT / owner answers patch

---

## Why This Was Needed

Owner provided approved answers for the real Phase 2 policy gaps remaining after the Existing Form Answers Audit. This patch applies those answers to the owner answer sheet without implementing runtime behavior.

---

## Files Created / Modified

Modified:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_OWNER_ANSWER_SHEET.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_EXISTING_FORM_ANSWERS_AUDIT.md`

Created:

- `docs/worklog/realignment/2026-07-01_phase_2_owner_answers_patch.md`

---

## Owner Answers Applied

Applied owner-approved answers for:

- PH2-OD-01 Global vs per group defaults: hybrid model approved; global defaults/prefill require operator confirmation and per-group overrides when groups differ.
- PH2-OD-02 Face / Plexiglas: plexiglas opal 3 mm remains operational default; 5 mm remains later exception; visible operator confirmation required.
- PH2-OD-03 Back / Forex: Forex 10 mm without sanfren is default; sanfren selectable; visible operator confirmation required.
- PH2-OD-04 Return / Cant: existing return/cant fields are approved; defaults may come from template/form but must be visible, confirmable, and per-group overrideable.
- PH2-OD-05 Finish / Oracal / Print / Laminare: existing Oracal/color/roll width/print/lamination/target options are sufficient for offer when selected and confirmed; print_required and lamination_required remain separate.
- PH2-OD-06 Artwork / Printed artwork: printed_artwork remains suggestion only; logo stanga/logo dreapta require operator confirmation as print/applied, artwork-only, or ignored.
- PH2-OD-07 Finish target: finish target must be explicit and visible per layer/group, including different face and cant finishes on the same group.
- PH2-OD-08 T06 / T19E: not a main commercial offer question now; task activation belongs later to Task Graph / ExecutionPlan; Phase 2 keeps finish/target only.
- PH2-OD-09 Lighting / LED / Cabluri / Surse: default included commercial cables are 1 m 2 x 0.75 for letters and 5 m 2 x 1.5 for final 220V feed; special electrical/site requirements are clarified later or in offer when requested.
- PH2-OD-10 Support / Bare: support/bars are optional; detected support/bars should be suggested and confirmed; otherwise manually selectable.
- PH2-OD-11 Mounting: offer must explicitly classify mounting as no mounting, included, external, or to decide.
- PH2-OD-12 Pricing / Cost boundary: Pricing Registry does not decide Product Truth; CommercialPriceProposal uses confirmed Product Truth and commercial rules; CostEngine remains internal-only.
- PH2-OD-13 Quote / Order / Execution classification: owner-approved blocker rules applied; commercial price is not hour/minute based.

---

## Decisions Still Open

None. PH2-OD-01 through PH2-OD-13 now have owner answers captured in the answer sheet.

---

## Runtime Impact

None.

This patch does not implement form fields, payload fields, analyzer behavior, pricing behavior, Product Truth runtime behavior, ProductDefinition, ProductSystem runtime changes, ProductAggregate, Task Graph, ExecutionPlan, quote/order/execution creation, or Employee Mobile.

---

## Recommended Next Step

Use the owner-approved answer sheet as the Phase 2 policy source for the next docs/design micro-slice: define exact Modular Form component question copy, owner-approved defaults, and readiness/blocker labels for the approved answers while keeping runtime implementation behind a separate GO.

---

## Validation

Markdown diagnostics: PASS for all three touched docs.

Tests: NOT_RUN_DOCS_ONLY  
Build: NOT_RUN_DOCS_ONLY

---

## Roadmap Alignment Checkpoint

1. Roadmap source used

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`

2. Current roadmap phase

- Phase 2 - Modular Form component questions

3. Roadmap status of this task

- NEXT / owner answers patch

4. Why this task belongs here

Owner answers close policy gaps for Phase 2 component questions. This task does not implement runtime behavior. It keeps Intake V6 and Product Truth as the source path and does not jump to ProductDefinition, ProductAggregate, Task Graph, or ExecutionPlan.

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
