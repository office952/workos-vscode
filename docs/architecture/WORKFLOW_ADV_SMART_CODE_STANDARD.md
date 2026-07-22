# Workflow-ADV Smart Code Standard

## Status

Mandatory pre-read for Workflow-ADV implementation work.

| Evidence | Value |
|---|---|
| Owner-accepted evidence HEAD | `9769bbe8` |
| Documentation tip | `fd2532e1` |
| Canonical navigation | [`docs/workflow-adv/README.md`](../workflow-adv/README.md) |

This is the single implementation standard for Workflow-ADV. Do not create a parallel standard; propose an amendment through version governance.

## 1. Simplicity

- Build the smallest complete module that satisfies a frozen contract and acceptance test.
- Prefer explicit data flow, named states, and ordinary language over magic, hidden defaults, and clever abstractions.
- Do not introduce speculative frameworks, generic engines, or extension points without an approved demonstrated need.
- One business rule has one declared owner.
- Do not use a UI workaround to hide an unresolved domain decision.

## 2. Readability

- Use names that reflect domain meaning, ownership, state, and units.
- Keep functions and modules focused on one responsibility; extract only when ownership becomes clearer.
- Put imports at module top; do not use inline imports without a documented circular-dependency exception.
- Prefer direct control flow and typed results to implicit mutation and broad catch-all behavior.
- Comment decisions and constraints, not restatements of code.

## 3. Typing

- Type public API payloads, domain commands/results, persistence boundaries, and UI state explicitly.
- Represent lifecycle/authority states with closed unions/enums and exhaustive handling.
- Validate untrusted inputs at the boundary before domain use.
- Include units in names/types for measurements and money/cost semantics where ambiguity is possible.
- Do not use `any`, untyped dictionaries, or stringly typed status values to bypass a contract.

## 4. Module ownership

- Each module declares what it owns, consumes, produces, and must not decide.
- Product System owns design-time templates/composition; it does not own runtime Product Truth.
- Form System owns reusable field composition, validation/confirmation requirements, and valid choices.
- Product Truth owns confirmed runtime facts with provenance.
- Catalog modules own resource identity/rates; templates reference them and do not invent them.
- Quantity/EIC domain modules own calculation evidence; UI does not.

## 5. Dependency direction

```text
UI / transport adapters -> application commands -> domain modules -> ports
                                                <- infrastructure adapters
```

- Dependencies point toward stable domain contracts, never from domain to UI/framework/infrastructure.
- Avoid god services that coordinate unrelated templates, pricing, UI, persistence, and integration logic.
- Cross-module access goes through a typed contract, not private-table or component reach-through.
- Circular dependencies indicate unclear ownership; resolve rather than hide them.

## 6. API boundaries

- Version external and public contracts; reject unsupported versions clearly.
- APIs validate identity, authorization, shape, units, state, and provenance before command execution.
- Commands are explicit about actor, target version, expected state, and idempotency where needed.
- Return structured errors: stable code, human message, affected field/scope, and valid recovery action.
- Never expose an undocumented endpoint as business authority.

## 7. UI architecture

- Platform UI is desktop-first and role-specific: Operator, Admin, and Dev.
- Lab diagnostic/badge-heavy UI is not the Platform design baseline.
- Show source state, confirmation state, blockers, warnings, and valid actions at the decision point.
- Use badges as compact supporting state, never as the main information architecture.
- Preserve entered values on validation failure; do not make the operator rediscover context.
- UI may format and guide; it must not invent business fields, rules, or calculations.

## 8. Form System

- Compose forms from reusable field contracts, template/component requirements, and explicit overrides.
- Every field declares source, destination, unit, visibility, validation, confirmation need, and formula impact.
- Present only valid choices and explain why a field is blocked or required.
- “Save draft” and “confirm Product Truth” are separate explicit actions.
- Do not clone a template-specific form page as the scaling strategy.

## 9. Product System

- Templates own what may exist; runtime requests own what was actually confirmed.
- Parent/child composition has one owner per technical input, material, process, and quantity.
- A child does not become an offerable root or operationally active merely because it exists in catalog/seed data.
- Product Definition is intent/derived draft; Product Truth is operator-confirmed authority.
- Do not mutate accepted snapshots or frozen truth from a mutable template.

## 10. Catalog-backed resources

- Materials, variants, processes, labor, services, consumables, and packaging use canonical catalog identity.
- `VARIANT_SELECTOR` is not a priced SKU; resolve a concrete variant before a price/cost is used.
- Templates and UI never invent local materials, selector prices, process rates, or labor rates.
- Catalog changes are versioned/audited according to their operational impact.

## 11. Operational processes

- Treat CNC, laser, print, lamination, edge, painting, and related work as first-class process resources.
- Templates reference process contracts and quantities; catalogs/recipes own rates and classifications.
- Do not flatten operational processes into anonymous price lines.
- EIC is the current reference finish line; CPP remains reconciliation evidence, not an offer/Execution shortcut.

## 12. Error handling

- Fail closed on unsupported version, missing provenance, invalid lifecycle transition, unauthorized action, or invalid required truth.
- Distinguish error, blocker, warning, and informational evidence.
- Error messages identify what failed, where, why, and the next valid action without leaking secrets.
- Do not silently coerce a proposal into confirmed truth or replace an operator correction.
- Log recoverable integration failure with correlation/record/version identifiers.

## 13. Testing

- Write targeted unit/domain tests for rules, boundary tests for contracts, and UI tests for operator-visible decisions.
- Include happy path, invalid input, authorization, lifecycle, provenance, and regression fixtures.
- Preserve assertions when moving laboratory evidence; do not greenwash tests by weakening them.
- Runtime verification supplements automated tests; it does not replace them.
- Each promotion package links fixtures and evidence to the contract version under test.

## 14. Security

- Enforce authorization server-side for Operator, Admin, Dev, and Owner actions.
- Treat uploads and Analyzer payloads as untrusted input; validate type, size/shape, schema, provenance, and version.
- Never allow Analyzer, AI, frontend, seed, or automation to bypass confirmation, Freeze, or audit.
- Protect secrets, personal data, source files, and audit records by least privilege.
- Owner-only unfreeze is exceptional, explicit, and fully audited.

## 15. Observability

- Emit structured events for validation failure, confirmation, correction, promotion, freeze, unfreeze request, and integration rejection.
- Correlate events with actor, request/record, version, contract version, and Analyzer run/source hash when relevant.
- Make operational metrics and diagnostics observable without making Dev diagnostics the operator workflow.
- Do not log raw secrets or unnecessary source-file content.

## 16. Dependency policy

- Prefer existing approved project dependencies and platform primitives.
- Add a dependency only for a concrete module requirement, documented owner, security review, and removal/upgrade path.
- Do not add libraries to compensate for unclear domain design or to create speculative architecture.
- Keep framework code at edges; domain contracts remain portable and testable.

## 17. Legacy policy

- Do not extend WorkIntake V1, hardcoded template pages, duplicate calculators, ghost runtime assumptions, or badge-heavy Lab UI.
- Extract transferable contracts, fixtures, tests, and evidence; rewrite Platform implementation under this standard.
- In-repo SVG/DXF/DWG analysis is legacy/external-app-owned. Do not extend or delete without owner GO.
- Retire legacy only after reference/import checks and explicit owner approval.

## 18. Analyzer separation

- Workflow-ADV Analyzer is a separate desktop application that owns SVG/DXF/DWG and related file intelligence.
- Analyzer output uses `workflow_adv_analyzer_io_contract_v1`, carries provenance, and is only `observed` or `proposed`.
- Platform validates/consumes/reviews; the operator confirms; confirmed facts become Product Truth.
- Analyzer owns no Product Truth, templates, pricing, EIC/CPP, central database writes, or Platform parser.
- Platform must not implement parsers, geometry inference, auto-grouping, or file-to-Product-Truth conversion.

## 19. Dev Mode

- Dev Mode exists only on a new draft/version and is visibly non-operational.
- Use it for diagnostics, warnings, formula evidence, fixtures, and experiments.
- Never mutate a frozen operational version in place.
- Move work through `DEV_ONLY → READY_FOR_REVIEW → CONTRACT_FROZEN → READY_FOR_IMPLEMENTATION → IMPLEMENTED → RUNTIME_VERIFIED → ACCEPTED`.

## 20. Freeze

- FREEZE ON means immutable accepted operational truth, not a display label.
- Evolve only through `Frozen v1 → DEV v2 → validate → promote → FREEZE ON`.
- Freeze records scope, immutable identity/hash, dependencies, evidence, owner, and audit data.
- Only an Owner may authorize an exceptional unfreeze; default resolution is a successor draft/version.
- No seed, agent, admin endpoint, or UI control may silently alter frozen content/history.

## 21. Final compliance checklist

Before implementation completes, confirm:

- [ ] The relevant Workflow-ADV docs and contract version were read and cited.
- [ ] Ownership, source of truth, valid lifecycle, and dependency direction are explicit.
- [ ] No frontend business-truth/EIC calculation, duplicated calculator, or invented catalog price exists.
- [ ] Operator confirmation is required before Product Truth changes.
- [ ] Analyzer separation and versioned observed/proposed I/O are preserved.
- [ ] UI is role-specific, desktop-first, accessible, and not copied from Lab chrome.
- [ ] Dev work is on a new version; frozen operational content was not mutated.
- [ ] Errors, audit, authorization, observability, fixtures, and tests cover the changed behavior.
- [ ] Evidence supports the claimed promotion/runtime stage.
