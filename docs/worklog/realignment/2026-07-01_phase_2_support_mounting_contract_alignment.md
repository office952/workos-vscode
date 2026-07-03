# Phase 2 Support / Mounting Contract Alignment

## Verdict

PASS.

## What was audited

Audited Support / Bare / Structura suport versus Mounting / Montaj across:

- Phase 2 roadmap and owner-answer docs;
- Product Truth, reusable component, readiness, and pricing boundary contracts;
- previous Phase 2 UI/display worklogs;
- Intake V6 Review/Form UI and display helpers;
- SVG analyzer role vocabulary for `support_panel` / `frame`;
- ProductSystem linkage UI and tests;
- backend registry, seed, ProductDefinition, ProductAggregate, commercial proposal, internal cost, and quote-input bridge code.

## Source inventory summary

Main findings:

- `finish_setup.mounting_system` is the current Intake V6 mounting field.
- `metal_support_required` is the ProductSystem / quote bridge trigger for support structure.
- `structura_suport` is the support/premount module.
- current runtime bridges derive support activation from `mounting_system` values such as `steel_bars` / `aluminum_bars`.
- `direct_wall` currently makes `structura_suport` inactive in several preview/commercial/internal-cost paths.
- SVG can suggest support-like roles (`support_panel`, `frame`) but must not confirm support truth.
- `TRIGGER_FIELD_MISMATCH` is intentionally visible and should remain until a future ProductSystem/support payload bridge is designed.

Detailed inventory is documented in:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md`

## Mismatch verdict

The mismatch is real.

`metal_support_required` and `finish_setup.mounting_system` are not the same concept. Current code uses a transitional bridge, but canonical Product Truth must separate:

- Mounting / Montaj: scope, system, surface, template.
- Support / Bare: support required, support type, source, quote relevance.

## UI changes

UI display-only changes were made.

Changed existing labels only:

- Support chips now state `metal_support_required means Support/Bare, not mounting method`.
- Support chips now state `Support and mounting are separate decisions`.
- Mounting chips now state `mounting_system is Mounting, not Support truth`.
- Existing ProductSystem downstream linkage warning now adds a short owner-friendly explanation for `structura_suport` mismatch.

No controls were added. No values changed. No readiness or payload logic changed.

## Files changed

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md`
- `docs/worklog/realignment/2026-07-01_phase_2_support_mounting_contract_alignment.md`
- `frontend/src/lib/intakeV6/intakeV6ComponentQuestionDisplay.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ComponentQuestionBadges.test.tsx`
- `frontend/src/features/product-system/TemplateDownstreamLinkagePanel.tsx`
- `frontend/src/features/product-system/TemplateDownstreamLinkagePanel.test.tsx`

## Tests run

Focused Vitest:

```text
pnpm.cmd vitest run src/components/workos/intake-v6/IntakeV6ComponentQuestionBadges.test.tsx src/lib/intakeV6/intakeV6ComponentQuestionDisplay.test.ts src/features/product-system/TemplateDownstreamLinkagePanel.test.tsx
```

Result:

```text
Test Files  3 passed (3)
Tests       8 passed (8)
```

Diagnostics:

- TypeScript/TSX diagnostics: PASS for touched frontend files.
- Markdown diagnostics: PASS for the architecture document before worklog creation.

Build status: NOT_RUN_NARROW_UI_DOC_SLICE.

## Runtime visual check

Route checked read-only:

```text
http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator
```

Observed:

- `LIVE / DB` visible.
- Workspace `IV6-BB8EE3F8` visible.
- Review is accessible after legitimate layer confirmation.
- Confirmare remains blocked by final confirmation steps; `Creează draft intern V6` remains disabled.
- `Verificări sistem` shows canonical `TRIGGER_FIELD_MISMATCH` for `structura_suport link=metal_support_required intake=finish_setup.mounting_system`.
- Review / Montaj tab shows Product Truth candidate chips.
- Mounting chip says `mounting_system is Mounting, not Support truth`.
- Support chip says `metal_support_required means Support/Bare, not mounting method` and `Support and mounting are separate decisions`.
- No false Pricing Registry blame observed.
- No commercial hour/minute pricing copy observed in changed chip surfaces.
- No confirmations were clicked.
- No state-changing controls were used.

## Target semantic contract summary

Target future fields, docs-only:

- `mounting_scope`: `no_mounting`, `mounting_included`, `mounting_external`, `to_be_decided`.
- `mounting_system`: `direct_wall`, `spacer`, `rail`, `template`, `other`.
- `mounting_surface`: optional/order/execution.
- `mounting_template_required`: boolean / conditional.
- `support_required`: `yes`, `no`, `suggested`, `unknown`.
- `support_type`: `none`, `aluminum_bars`, `metal_frame`, `rear_support`, `other`.
- `support_source`: `detected_svg`, `operator_selected`, `owner_default`, `product_rule`.
- `support_quote_relevant`: boolean / conditional.

Status: DOCUMENTED_NOT_IMPLEMENTED.

## Next safe step

Recommended final state: `UI_DISPLAY_PASS_NEXT_PAYLOAD_DESIGN`.

Next safe slice:

- Product Truth payload design docs for `support` and `mounting` branches only.
- No runtime payload implementation without owner GO.
- Later ProductSystem contract migration plan for `metal_support_required -> support_required`.

## Roadmap alignment checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`.
2. Current roadmap phase: Phase 2 - Modular Form component questions.
3. Roadmap status of this task: NEXT / support-mounting contract alignment.
4. Why this task belongs here: support/mounting are Phase 2 component-owned questions; current mismatch blocks clean Product Truth payload design; Intake V6 remains the source; this does not jump to ProductDefinition/ProductAggregate/ExecutionPlan.
5. What this task must NOT unlock: Product Truth canonical payload, ProductDefinition, ProductSystem/Dossier runtime changes, CommercialPriceProposal, Quote Snapshot, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate result: PASS.
7. Roadmap implementation progress: 11/100%.
8. Roadmap alignment score: 100/100%.
9. Cat sunt in directia stabilita: 100/100%.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.

## Forbidden confirmation

Confirmed:

- no new form;
- no duplicate controls;
- no new wizard;
- no backend changes;
- no DB/schema/seeds;
- no API changes;
- no payload shape changes;
- no ProductTruth runtime canonical payload;
- no readiness logic changes;
- no analyzer changes;
- no pricing changes;
- no ProductDefinition;
- no ProductSystem runtime;
- no ProductAggregate;
- no Task Graph;
- no ExecutionPlan;
- no materialization;
- no quote/order/execution;
- no forced confirmations;
- no Review artificial unlock;
- no Employee Mobile.