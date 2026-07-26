# Product Definition contract

## Purpose
Define Product Definition (PD) as the versioned configuration-intent boundary before confirmation.

## Ownership
Workflow-ADV owns PD. Form Schema supplies typed inputs; operators own confirmation decisions; Analyzer supplies only versioned observations and proposals.

## PD content matrix
| Content | Accepted in PD | PT consequence |
|---|---|---|
| Operator input | yes | eligible for confirmation |
| Analyzer observation | yes, with provenance/confidence | confirm before truth if required |
| Analyzer proposal | yes, explicitly proposed | never automatically becomes truth |
| AI default | yes, with provenance | operator confirms or replaces |
| Owner default / catalog reference | yes, versioned | validate compatibility before confirmation |
| Derived candidate | yes, declaration required | confirm when it changes production truth |

Minimum PD metadata: `template_code`, template/schema version, field values, field provenance, source document/file identifiers when relevant, candidate/proposal status, author, timestamp, and revision.

## Invariants
- PD is configuration intent, not Product Truth.
- PD may be revised; confirmation creates a separate PT revision/snapshot.
- Analyzer cannot write PD values without provenance and cannot write PT at all.
- PD is bound to a Product Template and Form Schema version.
- PD cannot use a generic price for `MAT-LED-PSU-12V`; it must select a concrete priced variant before cost.

## Evidence sources
- `GET .../form-field-ownership-map`
- `GET .../analyzer-io-contract`
- `GET .../reference-finish-line/contract`
- `docs/qa/product-system-reference-complete/`

## Limitations
The reference provides partial Lab surfaces, not the future PD versioning UX. Analyzer desktop implementation and Form Builder are deferred.

## Do-not-transfer
Do not treat a saved Intake form, an Analyzer payload, or a UI preview as confirmed truth. Do not hide provenance while promoting PD values.

## Related docs
- [Form Schema contract](FORM_SCHEMA_CONTRACT.md)
- [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
- [Child composition](CHILD_TEMPLATE_COMPOSITION.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
