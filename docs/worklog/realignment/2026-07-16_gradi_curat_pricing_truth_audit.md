# 2026-07-16 — Gradi-curat pricing truth audit

## Purpose

Owner-facing read-only audit of commercial vs internal pricing truth for workspace `11891d68-c4c8-4719-acc5-f8fcb22a44af` (gradi-curat letters+logo composition) on live `:8001`/`:3000`, baseline `99d5c71`.

## Boundary

- PLAN MODE + read-only runtime probes
- Docs/evidence only
- No product-code, pricing registry, Product System, workspace writes
- No Build Locally / implementation
- No commit until owner review

## Context

Prior Step2 UI/runtime closure landed at `99d5c71`. UI showed a commercial RON total beside an EUR internal total; logos appeared in analysis/composition but commercial completeness was doubted. This audit proves the break.

## Verdict

- `GRADI_CURAT_PRICING_FIRST_BLOCKER_FOUND`
- `COMMERCIAL_PARTIAL_NOT_CONFIRMABLE`
- Primary blocker: `COMMERCIAL_RULE` (logo commercial absence)
- Operator Confirmare → Quote: **NO**

## Live totals (authoritative)

| Surface | Value | Source |
|---------|-------|--------|
| Commercial net | 2154.51 RON | priced-quote-dry-run `commercial_totals` |
| VAT 21% | 452.45 RON | same |
| Commercial gross | **2606.96 RON** | same / UI “Valoare estimată cu TVA” |
| Internal MB | **725.16 EUR** | material-breakdown totals |
| Stale 2.587,94 RON | not live | do not mix |

## Key evidence

- CPP lines: 7 priced letter modules + null `ambalare`/`montaj`; **0 logo lines**
- MB: logo plexi/forex/print/lam materials + print/lam/application ops present
- `TPL-VOLUMETRIC-LOGO_v1`: not in template-availability; PD/PA standalone 404; PD linked segments partial
- `contains_missing_prices=true` from informational `led_total_watts` only → false positive

## Files changed (docs)

- `.compound-engineering/gradi-curat-pricing-truth-audit/plan.md`
- `.compound-engineering/gradi-curat-pricing-truth-audit/decision-log.md`
- `docs/worklog/realignment/2026-07-16_gradi_curat_pricing_truth_audit.md`
- `docs/qa/gradi-curat-e2e/pricing-truth-evidence.md`
- Supporting probes: `docs/qa/gradi-curat-e2e/_probe_*.json`

## Commands / probes (read-only)

- `GET .../priced-quote-dry-run`
- material-breakdown
- product-definition / aggregate (letters + logo)
- `GET .../template-availability`
- local summarize script on probe JSON

## Next steps

1. Owner answers G1–G5
2. Docs-only commit after review (no push/PR)
3. If G1=YES: implement logo linked-child commercial pricing truth only
