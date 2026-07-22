# Readiness and Lifecycle

## Purpose
Define a transparent lifecycle for Workflow-ADV templates and resources. Lifecycle state communicates governance maturity; readiness axes communicate whether a specific scope can safely produce a governed EIC result.

## Ownership

| Concern | Owner |
|---|---|
| Template lifecycle transition and publication decision | Authorized Product System owner |
| Material identity/stock readiness | Inventory |
| Purchase-price readiness | Pricing |
| Process and recipe readiness | Operational Processes and recipe owners |
| PT confirmation readiness | Confirming operator |
| Evidence verification | QA / release owner |

## Invariants
- Lifecycle and readiness are separate: a `PUBLISHED` template may be constrained by a declared unsupported capability; a `DRAFT` template is never production-ready merely because one calculation succeeds.
- Every transition records actor, timestamp, source revision, evidence links, reason, and resulting version.
- Accepted immutable versions are not edited in place. Change creates a successor draft/version.
- A selector is not an unresolved critical material if a confirmed configuration resolves it to a concrete eligible variant.
- A readiness result is scoped to a template, version, configuration/fixture, and requested outcome (for example EIC). It must not be generalized to unrelated templates or an offer path.

## Lifecycle states

| State | Meaning | Entry criteria | Allowed next states |
|---|---|---|---|
| `DRAFT` | Authoring or change work; truth is not accepted | Version exists with identified owner | `VALIDATED`, `DEPRECATED`, `ARCHIVED` |
| `VALIDATED` | Contract and scoped automated/manual evidence pass | Required axes evaluated; limitations recorded | `E2E_CHECKED`, `DRAFT`, `DEPRECATED` |
| `E2E_CHECKED` | A governed end-to-end fixture proves the intended path | Validated version plus reproducible E2E/fixture evidence | `PUBLISHED`, `DRAFT`, `DEPRECATED` |
| `PUBLISHED` | Approved for the explicitly declared operational scope | Owner approval; current evidence; limitations visible | `DEPRECATED`, `ARCHIVED` |
| `DEPRECATED` | Not for new adoption; retained for historical reads/migration | Successor or removal rationale recorded | `ARCHIVED` |
| `ARCHIVED` | Retained immutable history; unavailable for new use | Retention and access policy satisfied | none |

`DRAFT → VALIDATED → E2E_CHECKED → PUBLISHED` is the normal promotion route. Emergency withdrawal may move a published version to `DEPRECATED` with recorded reason; it must not rewrite historical evidence.

## Readiness axes

| Axis | Ready means | Not-ready handling |
|---|---|---|
| Scope and composition | Root/child ownership and applicability are explicit | Block the claimed scope |
| Form, PD, and PT | Required inputs validate and PT is operator-confirmed | Request confirmation or mark blocked |
| Material identity | Every required physical material resolves to Inventory | Record missing identity; do not invent local material |
| Material price | Required concrete material has eligible Pricing evidence | Expose missing price; no AI fallback |
| Selector resolution | Selector resolves to an allowed concrete variant | Block priced/EIC material line |
| Process | Compatible active process/version exists | Block process line or scope |
| Labor/service recipe | Active reusable recipe with a physical driver exists | Block or state accepted limitation |
| Quantity/formula | Declared owner and unit-bearing result exist | Block calculation |
| EIC | All required governed line inputs can be aggregated and explained | No production-cost finish-line claim |
| Evidence and snapshots | Tests/fixtures reconcile and protected snapshots remain unchanged | Fail validation |
| Limitations | Every supported boundary is visibly declared | Do not publish ambiguous readiness |

## Evidence

| Evidence | Lifecycle/readiness result |
|---|---|
| `docs/qa/product-system-reference-complete/` | VL reference path is `READY_FOR_DOCUMENTATION_HANDOFF`; critical list is empty |
| `docs/qa/product-price-breakdown-v1/` | VL published evidence; ACM shell constrained; Logo not root-ready |
| Critical-fill commit `7bdd9f61` | Selector closure removes false critical blocker |
| `docs/qa/product-system-reference-finish-line-v1/` | Freeze/DEV contract and reference finish-line evidence |

## Limitations
- This is the canonical Workflow-ADV state model; a global lifecycle/freeze control plane is deferred.
- It does not define offer readiness, order readiness, production dispatch, or stock reservation.
- `PUBLISHED` must always be qualified by its supported scope; it is not a blanket quality claim.

## Do-not-transfer
- Do not transfer Lab badges or current activation UI as the state machine implementation.
- Do not publish based on a false selector blocker, stale screenshot, or a green test that weakens assertions.
- Do not mutate frozen/published historical data to simulate a lifecycle transition.

## Related docs
- [Test Fixtures](TEST_FIXTURES.md)
- [Template Examples](TEMPLATE_EXAMPLES.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [API Contracts](API_CONTRACTS.md)
