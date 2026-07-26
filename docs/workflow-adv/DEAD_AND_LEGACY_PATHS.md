# Workflow-ADV dead and legacy paths

## Purpose

This inventory prevents Current WorkOS laboratory behavior from being mistaken for Workflow-ADV Platform authority. “Legacy” does not authorize deletion; it means the path is not a Platform baseline. Delete only after a zero-reference check and owner GO.

## Disposition vocabulary

| Disposition | Meaning |
|---|---|
| Do not transfer | Exclude from Platform architecture and implementation |
| Quarantine | May remain in Current WorkOS, clearly non-authoritative; do not extend |
| Rewrite | Preserve the business contract/evidence but rebuild the implementation |
| Retire with owner GO | Remove only after dependency/reference and operational checks |

## Inventory

| Path or pattern | Reason | Risk if reused | Disposition | Transfer decision |
|---|---|---|---|---|
| WorkIntake V1 | Parallel legacy intake route, not the canonical modular Workflow-ADV form/confirmation path | Duplicate runtime truth and route confusion; breaks a controlled migration | Quarantine; retire only with owner GO | Do not transfer route/code; transfer only relevant request-context evidence if explicitly mapped |
| Hardcoded volumetric-letters (VL) pages | Template-code page copies encode pilot-specific UI behavior | One page/form/calculator per template; blocks reusable Form/Product System | Rewrite | Transfer field/validation/fixture contracts, not page components |
| Badge-heavy Lab UI | Diagnostic/lab visualization, not production operator IA | Users mistake badges for workflow, authority, or actionable errors | Do not transfer | Transfer badge semantics/status vocabulary only; rebuild Platform UI |
| Ghost `:8000` backend assumptions | Local port/env habits can differ from actual proof/dev runtime and hide missing configuration | False runtime verification and accidental coupling to stale services | Quarantine | Transfer documented environment contracts only; rebuild Platform startup/runtime configuration |
| Invented selector prices | A `VARIANT_SELECTOR` is not a priced SKU; price belongs to resolved concrete variant/catalog owner | Incorrect EIC/commercial results and false material truth | Do not transfer | Transfer selector policy and concrete-variant fixture evidence |
| Offer-as-finish-line | Reference laboratory stops at EIC; CPP is reconciliation only | Premature commercial/order/execution work masks missing production-cost truth | Do not transfer | Transfer EIC boundary and CPP reconciliation evidence, not offer/Execution behavior |
| Duplicate calculators | Competing frontend/backend/template calculations create divergent business truth | Inconsistent cost/quantity totals and untraceable corrections | Retire with owner GO / do not extend | Transfer one declared domain formula contract and tests; no calculator implementation copy |
| Frontend business calculation | UI has no authority to calculate or reconcile Product Truth/EIC independently | Client-side drift, hidden rules, bypassed audit | Do not transfer | Platform FE renders server/domain evidence and validates UX only |
| In-repo SVG/DXF/DWG parser/analyzer | Graphic-file intelligence is owned by Workflow-ADV Analyzer desktop | Central Platform becomes a second Analyzer; ownership and security drift | Quarantine; do not extend | Transfer only versioned I/O consumer contract and fixtures |
| In-repo geometry/grouping/auto-binding logic | Same external Analyzer ownership boundary | Silent inferred truth, non-reproducible mapping, hidden product decisions | Quarantine; do not extend | Transfer observed/proposed semantics and review requirements only |
| Analyzer direct central DB write | Analyzer must not own central persistence or Product Truth | Bypasses Platform validation, confirmation, authorization, and audit | Do not transfer | Use versioned payload intake/reference only |
| Analyzer pricing/template ownership | Analyzer observes/proposes; Platform owns governed template/catalog/EIC logic | File heuristics become commercial/product authority | Do not transfer | Transfer provenance and proposal review contract only |
| Automatic Analyzer confirmation | External result cannot declare truth confirmed | Unreviewed geometric/semantic mistakes enter Product Truth | Do not transfer | Require explicit operator confirmation UI and audit |
| Mixed `by_layer` + `by_color` grouping | Initial grouping has one operator-declared mode | Unclear group meaning and non-repeatable results | Do not transfer | Transfer explicit grouping-mode constraint |
| Template-local invented materials/resources | Catalog is the source of resource identity and rates | Unpriced/duplicate resources, invalid EIC and procurement semantics | Do not transfer | Transfer catalog-backed reference rules and fixture IDs |
| Hardcoded process/labor rates in templates | Operational processes/labor/services are catalog/recipe-owned | Price/cost rules spread across templates | Rewrite | Transfer ownership contract; implement catalog lookup |
| Undocumented ad-hoc endpoints | Authority cannot be reviewed or versioned | Integration drift and untested operational writes | Retire with owner GO | Transfer documented versioned API contracts only |
| Seed/agent/admin mutation of frozen v1 | FREEZE ON makes accepted operational truth immutable | Audit breach and changed historical output | Do not transfer | Transfer Freeze policy and successor-version workflow |
| DEV tools on frozen operational records | Dev Mode is draft/version only | Experimental changes alter live truth | Do not transfer | Transfer draft-only Dev Mode rule and diagnostics intent |
| “Latest” mutable configuration reads | Frozen/snapshotted work must resolve pinned versions | Historical records change when templates/catalogs evolve | Rewrite | Transfer immutable version/reference requirements |
| Product Definition treated as Product Truth | PD is draft/configuration intent; PT is confirmed fact | Pricing/quantities consume guesses or incomplete input | Do not transfer | Transfer PD/PT distinction and confirmation tests |
| AI silent writes | AI may propose/ask but cannot own truth or commercial actions | Non-auditable and unsafe automation | Do not transfer | Transfer proposal provenance and operator-confirmation rules |
| Legacy WorkIntake V2 shell copies | Existing shell is transitional and not an automatic Platform design | Platform inherits narrow pilot coupling and inconsistent IA | Rewrite | Transfer useful workflow contracts, not shell implementation |
| Current WorkOS parser-related tests as feature mandate | Tests may document legacy behavior after ownership moved | Reintroduces central parser scope through “regression” work | Quarantine/reclassify | Keep as historical/legacy evidence; new Platform tests target Analyzer I/O |
| Global freeze implementation assumptions | Existing lab has Freeze governance as a contract, not an active global control plane | Pretending a feature exists creates unsafe operational guarantees | Rewrite | Transfer governance contract; implement first-class control plane |
| Generic Form Builder implied by VL pilot | A complete VL field map is not a generic builder | Over-generalized framework before validated requirements | Defer | Transfer reusable field contract; build generic tooling only by separate promotion |
| Future template activation from seeds | Seed presence does not equal operational readiness/offerability | Unsupported products exposed to operators | Quarantine | Transfer readiness/lifecycle rules; no activation by migration default |

## Rules for dealing with legacy

1. Do not extend a legacy path to satisfy a new Workflow-ADV requirement.
2. Do not delete it merely because it is listed here.
3. Classify imports/references before retirement; preserve necessary historical evidence.
4. If behavior is valuable, extract its contract, fixtures, and tests, then rewrite under Platform ownership.
5. A legacy UI screenshot demonstrates evidence at most; it never sets the Platform UX specification.
6. A current runtime behavior that conflicts with these contracts is a migration risk to resolve explicitly, not precedent to copy.

## Required review question

For every proposed reuse, ask: “Does this transfer an accepted contract/evidence, or does it import a legacy implementation/authority?” Only the former is eligible for Workflow-ADV transfer without a separate exception.
