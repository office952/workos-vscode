# 2026-07-16 — Gradi-curat dossier + trigger truth audit

## Purpose

Owner-facing read-only audit of remaining dossier/trigger handoff warnings on workspace `11891d68-c4c8-4719-acc5-f8fcb22a44af` after commercial dry-run READY and site-install tariff binding. Proves which codes block which commercial lifecycle stages, and that Aggregate `info` traces are incorrectly treated as accept/convert/production blockers.

## Boundary

- Docs/evidence only
- No product-code, Product System dossier rewrite, severity-mapping implementation
- No pricing/registry/CostEngine changes
- No workspace / DB writes
- No auto-confirm / Step 3 gate changes
- No commit until owner review; no push/PR
- Do not edit Cursor plan file

## Context

Prior commercial path reached dry-run `V6_PRICED_DRY_RUN_READY` (net **3513.56** / VAT **737.85** / gross **4251.41** RON) with montaj + Vector Logo lines. Handoff still showed `operator_confirmation_missing` as the sole fatal, plus five dossier/trigger `review_warnings`. Question: are those warnings quote-blocking, order-blocking, or severity-mapping defects?

## Verdict

| Field | Value |
|-------|-------|
| Classification | `READY_FOR_QUOTE_BUT_NOT_EXECUTION` |
| Can continue | `YES_FOR_QUOTE_ONLY` |
| First coherent friction | `UI_SEVERITY_MAPPING` |
| Proof token | `GRADI_CURAT_DOSSIER_TRIGGER_TRUTH_PROVEN` |

## Live inventory

| Bucket | Codes |
|--------|-------|
| `fatal_blockers` | `operator_confirmation_missing` only |
| `review_warnings` | 2× `TRIGGER_FIELD_MISMATCH`, `DOSSIER_METADATA_ONLY`, `CANONICAL_CONTRACT_AUTHORITY`, `TEMPLATE_IDENTITY` |

## Stage matrix (current runtime)

| Code | Quote draft | Priced offer | Offer accept | Order convert | Execution |
|------|-------------|--------------|--------------|---------------|-----------|
| `operator_confirmation_missing` | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| TRIGGER / dossier info codes | ALLOW* | ALLOW* | BLOCK | BLOCK | BLOCK |

\*After Step 3 operator confirmation.

## Key findings

1. Commercial pricing complete; dossier codes do not invalidate CPP/dry-run.
2. Only legitimate Step 3 quote gate = `operator_confirmation_missing`.
3. After operator confirmation, Quote draft / priced offer create is safe (fatal-only create path).
4. Defect = lift Aggregate `info` (+ TRIGGER diagnostics) into `review_warnings` → `client_order_production_flags_for_quote` clears accept/convert/production.
5. `DOSSIER_METADATA_ONLY` = `INFORMATIONAL_METADATA_WARNING` (root dossier v3/approved); not missing execution body.
6. TRIGGER = legacy alias (`metal_support_required` vs `mounting_system`); equivalent truth exists for this composition.
7. All five review codes are root-level — not per Vector Logo child.

## Direction (locked)

Do not delete warnings — move them to the correct stage. Quote after operator confirm. Order/Execution stay gated where operational truth incomplete; Aggregate `info` must not be that gate. TRIGGER may remain Order/Execution review until Product System link migration or owner equivalent-truth acceptance.

## Files changed (docs)

- `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/plan.md`
- `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/decision-log.md`
- `docs/worklog/realignment/2026-07-16_gradi_curat_dossier_trigger_truth_audit.md`
- `docs/qa/gradi-curat-e2e/dossier-trigger-truth-evidence.json`

## Next steps

1. Owner answers G1–G3 (Quote OK / TRIGGER vs Order-Exec / info visible nonblocking)
2. Docs-only commit after review (no push/PR)
3. Separate GO for severity-mapping correction only
