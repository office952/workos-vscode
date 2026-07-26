# Product Truth contract

## Purpose
Define Product Truth (PT) as the confirmed, auditable authority for quantity compilation and production cost.

## Ownership
The operator confirms PT. Workflow-ADV persists provenance, revision, hash, and confirmation event. Templates and formulas consume PT; Analyzer never owns it.

## Confirmation contract
| Input state | Can enter PD | Can enter PT |
|---|---|---|
| OPERATOR | yes | after operator confirmation |
| ANALYZER_OBSERVED | yes | only through required confirmation |
| ANALYZER_PROPOSED | yes | only through explicit confirmation |
| AI_DEFAULT | yes | only through explicit confirmation |
| OWNER_DEFAULT / CATALOG | yes | after compatibility/selection confirmation |
| DERIVED | yes | when derivation is declared and accepted |

Minimum PT metadata: `product_definition_revision`, `template_code`, template/schema version, confirmed field set, field-level provenance, confirmer, confirmation timestamp, revision number, immutable hash, and supersession reference.

## Invariants
- PT is distinct from PD and cannot be silently overwritten.
- No Analyzer, AI, seed, agent, migration, generic admin action, or frontend can write PT without operator confirmation.
- Quantities and formulas consume confirmed PT only.
- PT stores a concrete PSU variant selection; `MAT-LED-PSU-12V` cannot be recorded as a priced generic SKU.
- A frozen operational version is immutable. Change occurs through a new DEV version/revision.

## Evidence sources
- `GET .../analyzer-io-contract`
- `GET .../form-field-ownership-map`
- `GET .../reference-finish-line/contract`
- `docs/qa/product-system-reference-complete/runtime/reference_complete.json`

## Limitations
Full audit UI polish and storage hardening for revisions/hashes remain implementation work. The contract, not the current Lab UI, is authoritative.

## Do-not-transfer
Do not transfer direct Analyzer-to-PT writes, auto-confirmed proposals, mutable frozen truth, or UI state as PT authority.

## Related docs
- [Product Definition contract](PRODUCT_DEFINITION_CONTRACT.md)
- [Form Schema contract](FORM_SCHEMA_CONTRACT.md)
- [Quantity and Formula contract](QUANTITY_AND_FORMULA_CONTRACT.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
