# AI Operational Defaults Contract

## Purpose
Constrain AI assistance to evidence-backed operational defaults and proposals. It may reduce operator effort, but it cannot create business truth or a hidden market-price path.

## Ownership

| Concern | Owner | AI role |
|---|---|---|
| Product Truth (PT) | Confirming operator | Propose or explain only |
| Material market price | Pricing | No AI fallback or invented value |
| Material identity and stock | Inventory | May surface a matching candidate, never create authority |
| Process definition/cost basis | Operational Processes | May suggest a compatible process with evidence |
| Labor/service recipe rate basis | Recipe owner | May suggest a reusable recipe or physical driver |

## Invariants
- Every AI default contains provenance: source inputs, model/agent identity, prompt or policy version, timestamp, confidence/uncertainty where available, and the contract version evaluated.
- AI output is classified as `observed`, `proposed`, `default`, or `explanation`; none of these classifications is Product Truth.
- AI cannot write Product Truth, Pricing truth, CostEngine authority, Offer, Order, Execution, or production handoff.
- AI never invents material market prices and never supplies an AI market-price fallback when Pricing evidence is missing.
- AI may recommend a concrete material variant only from allowed, evidence-backed selection rules; the operator confirms the result.
- AI may recommend operational process, labor, or service defaults only when the applicable catalog resource is identified and its compatibility/driver evidence is preserved.
- Owner override is explicit, attributable, and revisioned. It supersedes the proposal for the accepted scope without rewriting the original AI evidence.
- Absence of evidence must produce a question, warning, or blocked readiness axis—not a fabricated default.

## Evidence

| Evidence | What it proves |
|---|---|
| `docs/qa/product-system-reference-complete/` | AI is a frozen assistance boundary; PT remains operator-confirmed |
| `docs/qa/material-market-price-registry-v1/` | AI fallback count is zero and missing purchase price remains visible |
| `docs/qa/product-price-breakdown-v1/` | AI decisions are a distinct breakdown group and do not create a parallel total |
| Market commit `f67d56a7` and breakdown commit `a243dd69` | Accepted evidence chain for no-invention pricing and visible AI contribution |

## Limitations
- The production assistant UX, model evaluation program, and feedback-learning control plane are deferred.
- Provenance schema is contractual; it is not a claim that every historical Lab suggestion has complete prompt-level metadata.
- AI does not replace supplier data, operator confirmation, process engineering, or recipe governance.

## Do-not-transfer
- Do not transfer AI suggestions as automatic confirmation or market-price truth.
- Do not transfer a confidence score as compatibility, cost, or safety authorization.
- Do not use an AI proposal to bypass an inactive resource, an unresolved selector, or a missing required price.

## Related docs
- [Material Price Source Contract](MATERIAL_PRICE_SOURCE_CONTRACT.md)
- [Labor and Service Recipe Contract](LABOR_AND_SERVICE_RECIPE_CONTRACT.md)
- [Inventory and Material Contract](INVENTORY_AND_MATERIAL_CONTRACT.md)
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
