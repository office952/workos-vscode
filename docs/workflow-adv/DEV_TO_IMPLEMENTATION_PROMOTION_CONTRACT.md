# Workflow-ADV Dev-to-implementation promotion contract

## Purpose

This contract makes experimental work reviewable and prevents a lab finding, prototype screen, or code branch from becoming operational truth by implication. A promotion concerns a named, versioned contract and its evidence; it does not transfer the Lab UI or authorize unrelated product expansion.

## Lifecycle stages

```text
DEV_ONLY
  -> READY_FOR_REVIEW
  -> CONTRACT_FROZEN
  -> READY_FOR_IMPLEMENTATION
  -> IMPLEMENTED
  -> RUNTIME_VERIFIED
  -> ACCEPTED
```

Stages are ordered. A record does not skip a stage without an explicit owner decision recorded in its audit evidence.

| Stage | Meaning | Minimum entry criteria | Exit / accountable decision |
|---|---|---|---|
| `DEV_ONLY` | Draft exploration, experiment, or proposed change | New draft/version exists; scope and non-goals declared | Author requests review with evidence |
| `READY_FOR_REVIEW` | Coherent proposal ready for human review | Contract prose/types, fixtures, tests, known limits, and open decisions assembled | Reviewer accepts, returns, or rejects proposal |
| `CONTRACT_FROZEN` | Semantics and boundary accepted for a defined version | Owner accepts scope, vocabulary, authority, exclusions, and evidence | Implementation owner accepts an implementation package |
| `READY_FOR_IMPLEMENTATION` | A frozen contract has sufficient build instructions | API/UI/domain boundaries, acceptance tests, dependencies, migration decision, and delivery scope are explicit | Implementer begins work against the pinned package |
| `IMPLEMENTED` | Scoped implementation exists | Code/config/docs match the frozen contract; targeted tests pass | Runtime verification is scheduled or performed |
| `RUNTIME_VERIFIED` | Intended behavior is proven in a relevant runtime | Runtime proof, fixtures, validation/error proof, and observability evidence captured | Owner evaluates operational acceptance |
| `ACCEPTED` | Operationally accepted result | Required verification complete; limits and rollback/next-version path stated | Freeze accepted operational truth or create successor work |

`CONTRACT_FROZEN` freezes the contract semantics for implementation. It does not mean that an operational version is already frozen; operational immutability is governed by [Freeze and version governance](./FREEZE_AND_VERSION_GOVERNANCE.md).

## DEV MODE rules

- DEV MODE exists only on a **new draft/version**.
- DEV MODE may use experimental diagnostics and fixtures, but it remains visibly non-operational.
- DEV MODE never mutates an accepted frozen operational version in place.
- A Dev change that affects a contract creates a new version and traces its predecessor.
- A bug fix may be implemented against a frozen contract only when it preserves that contract's semantics; a semantic change still requires a successor version.

## Promotion package checklist

Every request to move from `READY_FOR_REVIEW` through `READY_FOR_IMPLEMENTATION` includes a complete package:

### Identity and scope

- [ ] Stable contract/module name, version, owner, and predecessor/successor relation.
- [ ] Problem statement, intended operational outcome, and explicit non-goals.
- [ ] Named four-system boundary: Current WorkOS lab, Workflow-ADV Lab, Workflow-ADV Platform, and Analyzer desktop where relevant.
- [ ] Evidence pins: owner-accepted evidence HEAD `9769bbe8` and documentation tip `fd2532e1`, or a documented approved successor.

### Contract and authority

- [ ] Domain terms and state transitions defined.
- [ ] Source-of-truth and confirmation owner identified.
- [ ] Product Truth, EIC, template, catalog, and pricing boundaries named where relevant.
- [ ] API/input/output contract versioned; compatibility and rejection behavior stated.
- [ ] Analyzer inputs, if present, use `workflow_adv_analyzer_io_contract_v1` and remain observed/proposed until operator confirmation.

### UX and operations

- [ ] Operator, Admin, and Dev mode impact identified.
- [ ] Valid choices, blockers, errors, accessibility needs, and audit events specified.
- [ ] Freeze/version behavior defined.
- [ ] Observability events, operational dashboard/log needs, and failure ownership identified.

### Verification

- [ ] Representative happy-path, boundary, invalid-input, and regression fixtures.
- [ ] Automated tests at the appropriate domain/API/UI layers.
- [ ] Runtime verification plan with environment and evidence capture.
- [ ] Security/authorization expectations and negative tests.
- [ ] Explicit acceptance criteria and owner approver.

### Delivery boundaries

- [ ] Implementation module ownership and dependency direction are named.
- [ ] Migration/data impact is assessed; no implicit schema change.
- [ ] Transfer list contains contracts, fixtures, tests, and evidence only unless separately approved.
- [ ] Exclusion list confirms no Lab UI, legacy routes, duplicated calculators, offer/Execution expansion, in-repo parser, or hardcoded template pages are being transferred.

## Evidence by transition

| Transition | Required proof |
|---|---|
| `DEV_ONLY` → `READY_FOR_REVIEW` | Draft contract, fixtures, test intent, known risks and unresolved choices |
| `READY_FOR_REVIEW` → `CONTRACT_FROZEN` | Owner review record, complete boundary/authority decision, pinned evidence |
| `CONTRACT_FROZEN` → `READY_FOR_IMPLEMENTATION` | Implementation design, API/schema decisions, acceptance tests, UI/role impacts |
| `READY_FOR_IMPLEMENTATION` → `IMPLEMENTED` | Scoped change set, code review, targeted automated tests |
| `IMPLEMENTED` → `RUNTIME_VERIFIED` | Runtime traces/screenshots/API proof, error-path proof, observability evidence |
| `RUNTIME_VERIFIED` → `ACCEPTED` | Owner acceptance, operational limitations, Freeze decision or successor plan |

## Promotion blockers

Do not promote when any of these are true:

- Analyzer data is treated as confirmed without an operator.
- A frontend calculation becomes a business-truth authority.
- A frozen version would need mutation in place.
- A proposal relies on an invented selector price, template-local resource, undocumented endpoint, or hidden default.
- The work transfers a Lab visual surface instead of its contract/evidence.
- Runtime verification is asserted without actual runtime evidence.
- A stage is used to conceal a missing owner decision.

## Audit record

Each transition records the subject/version, prior and new stage, actor, timestamp, rationale, evidence links/hashes, reviewer/owner decision, and any exception. Rejection or rollback records the reason and returns to a new or existing draft without altering a frozen accepted version.
