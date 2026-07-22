# Test Fixtures

## Purpose
Define the minimum reproducible evidence fixtures for Workflow-ADV production-cost contracts and protect the snapshots that establish historical reconciliation.

## Ownership

| Concern | Owner |
|---|---|
| Fixture intent, expected outcomes, and acceptance | QA / Product System release owner |
| Material identity and selected variant | Inventory plus confirmed Product Truth |
| Price truth used by fixture | Pricing |
| EIC breakdown source inputs | Product System, Operational Processes, recipe owners |
| Snapshot storage and change review | Release owner |

## Invariants
- `vl_letters_demo_v1` is the canonical positive reference fixture for the VL root path.
- Its expected historical evidence is EIC `923.20` and CPP `1061.00`; EIC is the finish line and CPP is reconciliation only.
- The fixture resolves `MAT-LED-PSU-12V-100W`, not the `MAT-LED-PSU-12V` selector.
- Expected totals are assertions over declared fixture input versions. They must not be preserved by rounding away a defect, weakening an assertion, or introducing a second calculator.
- A fixture snapshot is immutable evidence once accepted. A new intended output requires a new version, explicit cause, reviewer, and before/after reconciliation—not in-place mutation.
- Negative fixtures must prove honest blocking/limitation behavior, not merely an error message.

## Fixture matrix

| Fixture | Expected result | Required assertion |
|---|---|---|
| `vl_letters_demo_v1` | EIC `923.20`; CPP `1061.00`; reconciliation passes | Concrete PSU 100W; required lines/provenance; no critical gaps |
| Unresolved PSU selector | No material cost line from generic selector | No raw/generic selector price; readiness blocked until a valid variant is confirmed |
| Missing purchase price | Missing pricing evidence remains visible | No AI market-price fallback; no fabricated EIC line |
| Incompatible/inactive process | Process is ineligible | Process readiness is blocked; version/compatibility shown |
| Missing/invalid recipe driver | Labor/service line cannot be governed | Blocked or accepted limitation, never hidden template rate |
| ACM shell fixture | Bounded EIC evidence and treatments limitation | Null/blocked commercial result remains honest |
| Logo fixture | Preview only | No root-published or root-EIC/CPP completeness claim |

## Evidence

| Evidence | What it proves |
|---|---|
| `docs/qa/product-system-reference-complete/runtime/SUMMARY.json` | `vl_fixture_ok`, EIC `923.2`, CPP `1061.0`, selector and critical checks |
| `docs/qa/product-system-reference-complete/` | Targeted chain reports 13 passing tests |
| `docs/qa/product-price-breakdown-v1/` | VL/ACM/Logo/Volum Aluminiu fixture outcomes and breakdown evidence |
| `docs/qa/active-template-critical-material-fill-v1/` | Concrete 100W resolution preserves reconciliation |
| Commits `a243dd69`, `f67d56a7`, `7bdd9f61` | Breakdown, market provenance, and selector-critical closure chain |

## Limitations
- Fixture totals prove the frozen reference environment and declared inputs, not a future market quotation.
- Test environments may need the documented canonical proof data; an incomplete local database cannot be treated as contradictory evidence without checking fixture/seed state.
- Full CI seeding and a global snapshot-control system are deferred.

## Do-not-transfer
- Do not transfer snapshots by copying them after a behavior change without review.
- Do not weaken totals, bypass negative fixtures, or mark a selector priced to make tests pass.
- Do not treat a passing Lab UI screenshot as sufficient E2E evidence.

## Related docs
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
- [Template Examples](TEMPLATE_EXAMPLES.md)
- [API Contracts](API_CONTRACTS.md)
