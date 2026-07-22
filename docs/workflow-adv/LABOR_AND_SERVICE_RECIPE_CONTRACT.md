# Labor and Service Recipe Contract

## Purpose
Define reusable labor and service recipes that turn confirmed physical production drivers into EIC inputs without placing human-work or external-service rates inside templates.

## Ownership

| Concern | Owner | Rule |
|---|---|---|
| Labor operation identity, rate basis, minimum, and active version | Labor catalog / recipe owner | Reusable catalog resource |
| External service identity, supplier/service basis, and active version | Service catalog / recipe owner | Reusable catalog resource |
| Applicability and physical driver quantity | Product System | Supplies only confirmed quantity inputs |
| Price of purchased physical material | Pricing | Separate from labor/service rates |
| Proposed default | AI | Requires provenance and owner review |

## Invariants
- Labor operations and services are reusable recipes, not hard-coded template price lines.
- Each recipe identifies its resource, version, physical driver, driver unit, cost unit, rate/minimum/setup rule where applicable, applicability condition, active state, source, and provenance.
- The primary driver is physical and operator-auditable: for example linear metres, square metres, number of letters, number of assemblies, or pieces. Time may be retained as a secondary calibration signal, not the sole default cost authority.
- Product System may calculate or expose a declared quantity, but cannot own a hidden labor or service rate.
- A reusable recipe is created JIT when a required production case needs it; speculative labor/service catalog growth is forbidden.
- AI may propose a driver or recipe choice only with provenance. An authorized owner may override it, and that override must be recorded with reason and revision.
- An inactive recipe cannot be newly used. Historic breakdowns retain their original recipe/version.

## Evidence

| Evidence | What it proves |
|---|---|
| `docs/qa/product-price-breakdown-v1/` | Labor uses physical drivers; services appear as explicit breakdown groups |
| `docs/qa/product-system-reference-complete/` | Labor/services are complete reference axes |
| Breakdown commit `a243dd69` | Breakdown preserves groups and avoids parallel total calculation |
| `docs/qa/product-system-reference-complete/DOCUMENTATION_HANDOFF_INPUT_PACKAGE.md` | JIT recipe creation and no template-invented labor rate |

## Limitations
- The broader labor and service catalogs, supplier-service purchasing, and scheduling are not implemented by the reference.
- Calibration hooks may exist but are excluded from total unless an owner-approved recipe explicitly applies them.
- This contract does not establish payroll, time tracking, vendor invoicing, or execution dispatch.

## Do-not-transfer
- Do not transfer one-off template-local labor rates or generic “service adjustment” lines as canonical recipes.
- Do not elevate elapsed time, AI confidence, or a UI estimate to price authority without the governed recipe.
- Do not let AI override owner-confirmed recipe selection or rate basis silently.

## Related docs
- [AI Operational Defaults Contract](AI_OPERATIONAL_DEFAULTS_CONTRACT.md)
- [Operational Process Contract](OPERATIONAL_PROCESS_CONTRACT.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
