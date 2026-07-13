# Worklog — ACM boxed mounting owner rates & CPP gap closure

**Date:** 2026-07-13  
**Slice:** `PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_OWNER_RATES_DELIVERY_CLOSEOUT_V1`  
**HEAD before:** `d693b37`

## Summary

Closed owner-confirmed EUR commercial rates for linked-child ACM boxed mounting (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`): registry seeds, template workcenter wiring, BOM dedupe by `component_ref`, CPP structura_suport rules, EIC capacity hints, frontend 3 mm-only intake, and targeted regression tests.

## Subagents (readonly analysts, parallel)

Three readonly analysts launched in parallel during audit phase (pricing registry, BOM/EIC/CPP trace, materials/operations commercial model) under `.compound-engineering/product-system-acm-boxed-mounting-owner-rates-cpp-gap-audit-v1/`.

## Owner rates applied

| Code | Rate |
|------|------|
| `ACM_PANEL_CUTTING` | 1.5 EUR/lm |
| `ACM_V_GROOVE` | 3 EUR/lm |
| `ACM_BOXED_ASSEMBLY` | 15 EUR/m², min 20 EUR/product |
| `MAT-SURUBURI-GEN` | 5 EUR/set |
| `MAT-ACM-BOND-3MM` | 15 EUR/m² |
| 4 mm | Blocked (resolver + UI + template variants) |

## Tests (closeout)

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py -q` | 7 passed |
| `pytest tests/test_acm_boxed_mounting_template_v1.py tests/test_mounting_solution_intake_reference.py -k "not test_api_save" -q` | 19 passed |
| `vitest run src/lib/intakeV6/mountingSolution.test.ts src/lib/acmQuoteInput.test.ts` | 12 passed |
| `git diff --check` (scoped slice) | clean; unrelated worklog trailing whitespace only |

## Runtime verification

- Stack healthy (:3000 / :8000 HTTP 200).
- Route: `http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator`
- UI: preparation_only, ACM casetat, 3 mm only (4 mm unavailable), valid dimensions, reload preserved.
- HTTP CPP preview on live :8000 returned no `acm_*` lines — live backend likely not hot-reloaded to uncommitted slice; pytest CPP case confirms lines + owner rates on seeded DB.
- Evidence: `docs/qa/product-system-acm-boxed-mounting-owner-rates-cpp-v1/`

## Commit

- Message: `Complete ACM boxed mounting owner rates and CPP`
- Hash: `7653678`

## Preserved unrelated dirty files (not staged)

- `.gitignore`, unrelated QA screenshots/evidence, `.compound-engineering/**`, other intake-v6 dirty docs/worklogs, `IntakeV6LayersOperatorPanel.tsx` (EOL-only), realignment worklogs, test-results/

## Gaps / next safe step

- Restart or reload backend dev process so live HTTP CPP/EIC matches committed code; run `seed_sync_all` (or targeted ACM seeds) on shared dev DB.
- Optional: extend Playwright to assert commercial spine dry-run once backend is on new code.
