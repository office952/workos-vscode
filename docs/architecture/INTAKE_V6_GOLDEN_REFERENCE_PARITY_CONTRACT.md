# Intake V6 — Golden Reference Parity Contract

**Status:** Architecture contract (no implementation)  
**Date:** 2026-07-17  
**Authority plan:** `docs/plans/2026-07-17_intake_v6_golden_reference_modular_reproduction_alignment.md`

## Purpose

Define what “full-product parity” means before modular reproduction changes how Intake is composed.

## Golden input

| Item | Value |
|------|--------|
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Reference workspace (read-only) | `4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1` / `IV6-C8066690` |
| SVG | `gradi-curat.svg` (Desktop `fisiere-teste-svg`) |
| Mode | Full product (explicit or legacy equivalent) |

## Parity law

```text
Same golden SVG + same operator choices
→ same SVG facts (layers, IDs, colors, geometry)
→ same candidate roles + operator approvals
→ same visible fields
→ same persisted values
→ same ProductDefinition technical truth
→ same ProductAggregate outputs
→ same quantities and formulas
→ same materials and operations
→ same CPP commercial result (exact)
→ same readiness and Review
```

## SVG parity rows

| Layer | Requirement |
|-------|-------------|
| SVG facts / layer identity / colors | exact |
| Geometry / quantities | exact (document any tolerance) |
| Candidate roles | equivalent |
| Operator layer/component approvals | equivalent |
| Formulas | exact |
| CPP / price totals | **exact** |
| Persistence | no loss of SVG attachment, analysis, approvals |
| Provenance | same or improved |

## Analyzer boundary

SVG Analyzer proposes; operator confirms. Analyzer does not own sold modules, active scope, CPP, or Execution.

## Allowed differences

| Layer | Allowed |
|-------|---------|
| Payload | Additive provenance / owner metadata only |
| PD / Aggregate | Equivalent truth with clearer provenance |
| CPP | **None** — exact commercial match |
| UI | Zero functional difference for full product |

## Forbidden under parity

- Formula changes  
- Tariff / commercial rule changes  
- Silent qty changes  
- Dropping golden materials/ops that full product emits today  
- Losing layer IDs, colors, geometry, roles, operator confirmation  
- Declaring ACM on `gradi-curat.svg` without proof  
- Historical workspace or snapshot mutation  

## Money boundary

Intake does not own money. CPP + `commercial_rules_volumetric_v2` remain commercial authority. SVG feeds quantities only through frozen formula path (`quote_geometry`).

## Evidence baseline

Disposable UI proof (same day): workspace `4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1`, evidence under `docs/audits/_evidence/2026-07-17_intake_v6_gradi_curat/`.

## Exit criteria (future Build 1–2)

Automated or documented harness proves golden disposable workspace matches reference outputs **including SVG facts** layer-by-layer before subset isolation ships.
