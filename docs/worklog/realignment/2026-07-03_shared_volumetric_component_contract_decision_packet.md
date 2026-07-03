# 2026-07-03 — Shared Volumetric Component Contract Decision Packet

## Status

`DONE_DOCS_ONLY`

## Scope

Created the owner decision packet:

`docs/architecture/product-system/SHARED_VOLUMETRIC_COMPONENT_CONTRACT_DECISION_PACKET.md`

The packet defines the proposed shared volumetric component contract direction for `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1`.

This work is docs-only. It does not implement runtime shared components and does not change template links.

## Evidence

Sources verified:

- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/seeds/seed_tpl_volumetric_logo_v1.py`
- `backend/services/product_template_availability_service.py`
- `backend/schemas/product_template_availability.py`
- `backend/models/product_template_module_links.py`
- `backend/services/template_architecture_scope.py`
- `backend/tests/test_product_template_availability.py`
- `backend/tests/test_seed_tpl_volumetric_logo_v1.py`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.test.tsx`
- `frontend/src/features/product-system/templateWorkflow.ts`
- `docs/architecture/MINI_MODULE_CONTRACT_REGISTRY.md`
- `docs/architecture/app-flows/16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md`
- `docs/worklog/realignment/2026-07-01_product_system_logo_module_reuse_blueprint_order.md`

## Key Decisions Proposed

- Use shared volumetric component contracts with template-specific profiles/configs.
- Do not replace Logo child templates directly with Letters child templates.
- Do not duplicate identical technical logic long-term.
- Keep Logo as `candidate_product` until separate owner GO.
- Keep Letters as `offerable_product`.
- Keep Work Intake based on `quote_offerable=true`.
- Treat `volumetric_lighting` as a partial shared candidate that needs more owner/electrical audit.
- Keep `electrica_logo` as future/reserved; do not activate now.

## Explicit Non-Changes

Not modified:

- backend logic;
- frontend logic;
- DB;
- seed/migration;
- pricing;
- Pricing Registry;
- CommercialPriceProposal;
- CostEngine;
- Work Intake;
- ProductDefinition;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Employee Mobile.

No template links were changed.
No runtime behavior was changed.
No Logo offerability was introduced.

## Validation

- Docs created: yes.
- Tests run: pending at creation time; see final task report for command results.
- Code changes: none.
- Commit: not done.
- Push: not done.
