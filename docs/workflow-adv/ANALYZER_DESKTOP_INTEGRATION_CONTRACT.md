# Workflow-ADV Analyzer desktop integration contract

## Status and scope

| Field | Value |
|---|---|
| Status | Canonical integration boundary |
| Contract version | `workflow_adv_analyzer_io_contract_v1` |
| Evidence HEAD | `9769bbe8` |
| Documentation tip | `fd2532e1` |
| Applies to | SVG, DXF, DWG, and other supported graphic/CAD files |

This contract governs only the integration between Workflow-ADV Platform and Workflow-ADV Analyzer. It does not prescribe Analyzer internals, transport, pricing, template authoring, or central database schema.

## Ownership

| System | Owns | Must not own |
|---|---|---|
| Workflow-ADV Analyzer (desktop) | File import; parsing; geometry; entities; layers; groups; measurements; classification; observed facts; proposed mappings | Product Truth, product templates, catalog authority, pricing/EIC/CPP, offer, execution, central Platform DB writes |
| Workflow-ADV Platform | Contract validation; provenance capture; review UI; operator confirmation; confirmed Product Truth; downstream governed workflow | SVG/DXF/DWG parsing, geometry intelligence, auto-grouping, analyzer inference |
| Operator | Acceptance, rejection, correction, and explicit mapping decisions | Silent automation or confirmation bypass |

No component of the central application may introduce or extend a parser, geometry analyzer, automatic grouping engine, or file-to-Product-Truth conversion path.

## Authority model

```text
Analyzer observation or proposal
  != Product Truth
Operator confirmation
  => Product Truth candidate accepted with provenance
```

| Inbound state | Meaning | Platform treatment |
|---|---|---|
| `observed` | A file-derived observation such as dimension, area, perimeter, entity count, or layer | Display and validate; require confirmation when the field affects truth |
| `proposed` | An Analyzer suggestion such as grouping, role, material mapping, or complexity | Display as a suggestion; never apply as truth without an operator action |
| `confirmed` | Not valid as Analyzer authority | Reject or coerce to unconfirmed input; only the Platform's operator-confirmation flow can create confirmed truth |

AI assistance follows the same limitation: it may explain, propose, or ask, but may not write Product Truth or commercial authority.

## Versioned I/O envelope

Every payload must contain:

```json
{
  "contract_version": "workflow_adv_analyzer_io_contract_v1",
  "analysis_id": "stable-run-id",
  "analysis_version": "desktop-build-or-model-version",
  "producer": {
    "app": "workflow-adv-analyzer",
    "version": "..."
  },
  "document_id": "platform-or-shared-document-id",
  "file_id": "stable-file-id",
  "source_file": {
    "name": "artwork.svg",
    "kind": "svg",
    "hash": "content-hash"
  },
  "produced_at": "ISO-8601 timestamp",
  "observations": [],
  "proposals": []
}
```

The exact transport is deliberately open: file exchange, folder sync, local bridge, or authenticated API can satisfy this contract. A transport choice must preserve schema version, source hash, run identity, and auditability; it must not turn the Analyzer into a Platform database writer.

## Minimum payload semantics

The contract supports the following categories. Individual template contracts decide which accepted fields are required.

| Category | Examples | State |
|---|---|---|
| File provenance | document/file IDs, kind, source hash, Analyzer build | `observed` |
| Measurements | unit, width/height, bounding box, filled area, perimeter, cut path | `observed` |
| Structure | element, contour, hole, and group counts | `observed` |
| Manufacturability signals | minimum feature size and warnings | `observed` |
| Interpretations | complexity class, suggested groups, roles, materials | `proposed` |
| Extensible fields | field-ID keyed observations/proposals | matching source state |

Measurements used by quantities or EIC must have explicit unit handling and an operator-confirmed source path. Unsupported units, non-positive required measurements, missing IDs, unsupported contract versions, invalid hashes, or malformed payloads are clear errors, not silent fallbacks.

## Grouping rule

For an initial grouping proposal, the operator chooses one declared mode:

- `by_layer`, or
- `by_color`.

The Analyzer must not silently mix grouping methods. Layer/color names and fixture labels are observations, not domain identity. A proposed group records its mode and is reviewed before use.

## Platform consumption sequence

1. Receive an external payload without granting it business authority.
2. Validate contract version, envelope, IDs, hash, source type, field shape, units, and provenance.
3. Store/refer to the source and run provenance required for an audit.
4. Show observed facts, proposals, confidence where supplied, errors, and warnings distinctly.
5. Let the operator accept, reject, correct, or defer each truth-relevant item.
6. Persist only confirmed facts and their source entity/run provenance as Product Truth.
7. Allow Product Definition, quantities, catalog-backed resources, and EIC to consume confirmed truth only.
8. At a later snapshot/freeze, preserve the accepted truth revision and Analyzer reference/hash; do not re-read a mutable Analyzer result to alter frozen truth.

## Validation and rejection rules

The Platform integration validates the **consumed payload**, not geometric correctness of the Analyzer implementation.

| Check | Required outcome |
|---|---|
| Unsupported `contract_version` | Reject with actionable compatibility error |
| Missing analysis/file/document identity | Reject |
| Missing or invalid source hash/type | Reject |
| Required numeric measurement non-positive | Reject the affected payload/field per contract |
| Unit needs conversion but conversion is unavailable | Block confirmation with clear error |
| Inbound `confirmed` binding | Reject or downgrade to unconfirmed; audit the event |
| Proposed mapping sets price/cost | Reject |
| Grouping mixes `by_layer` and `by_color` | Reject proposal or require explicit operator correction |
| Low confidence / manufacturability warning | Keep visible as warning; do not auto-block unless the template policy says it is a blocker |

Validation errors identify the field, rule, source file/run, and next operator or Analyzer action. They must not masquerade as product readiness or pricing results.

## Explicit exclusions

The Analyzer must not:

- create, mutate, or confirm Product Truth;
- choose a template, product, finish, mounting, electrical, or other operational truth;
- create or update catalog resources;
- calculate EIC, CPP, markup, commercial prices, offers, orders, or Execution;
- write to a central Platform database;
- bypass required fields, readiness gates, or the operator.

The Platform must not:

- parse SVG/DXF/DWG or implement CAD/vector intelligence;
- infer geometry from a source file;
- add auto-grouping, visual recognition, or file mapping engines;
- treat a complete-looking external payload as confirmed truth.

## Audit record and evidence

A confirmation record links the accepted fact to: `analysis_id`, `analysis_version`, contract version, producer identity/version, source file hash/kind/name, source entity IDs where applicable, operator identity, timestamp, prior value, accepted/corrected value, and reason when overridden.

Required integration evidence for promotion includes representative valid/invalid fixtures, schema validation results, review/confirmation tests, and a proof that no Analyzer path writes truth or pricing directly.
