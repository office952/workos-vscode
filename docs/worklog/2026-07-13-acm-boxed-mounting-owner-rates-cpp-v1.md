# Worklog — ACM boxed mounting owner rates & CPP gap closure

**Date:** 2026-07-13  
**Slice:** `PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_OWNER_RATES_DELIVERY_CLOSEOUT_V1`  
**HEAD before:** `d693b37`

## Summary

Closed owner-confirmed EUR commercial rates for linked-child ACM boxed mounting (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`): registry seeds, template workcenter wiring, BOM dedupe by `component_ref`, CPP structura_suport rules, EIC capacity hints, frontend 3 mm-only intake, explicit 4 mm block (no silent coerce), and targeted regression tests.

## Check 9 (diff reviewer)

- **Before:** `normalize_acm_mounting_configuration` forced `acm_thickness_mm = 3` for all inputs (silent 4 mm → 3 mm).
- **After:** Supported 3 mm only in UI; normalization preserves unsupported thickness (e.g. 4 mm) so `resolve_acm_bond_panel_material_rate` blocks explicitly.

## Owner rates applied

| Code | Rate |
|------|------|
| `ACM_PANEL_CUTTING` | 1.5 EUR/lm |
| `ACM_V_GROOVE` | 3 EUR/lm |
| `ACM_BOXED_ASSEMBLY` | 15 EUR/m², min 20 EUR/product |
| `MAT-SURUBURI-GEN` | 5 EUR/set |
| `MAT-ACM-BOND-3MM` | 15 EUR/m² |
| 4 mm | Blocked (resolver + UI + normalization preserve) |

## Tests (closeout)

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py -q` | 7 passed |
| `pytest tests/test_acm_boxed_mounting_template_v1.py tests/test_mounting_solution_intake_reference.py -k "not test_api_save and not test_seed_creates" -q` | 20 passed |
| `vitest run src/lib/intakeV6/mountingSolution.test.ts src/lib/acmQuoteInput.test.ts` | 13 passed |
| **Total targeted** | **40 passed** |

## Runtime verification

- Stack healthy (:3000 / :8002 HTTP 200; stale :8000 process noted — restart recommended).
- Route: `http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator`
- UI: preparation_only, ACM casetat, 3 mm only, panel 400×300 mm, reload preserved.
- CPP HTTP (400×300): 6 `acm_*` lines; `acm_boxed_assembly` subtotal 20 EUR (min charge).
- Evidence: `docs/qa/product-system-acm-boxed-mounting-owner-rates-cpp-v1/` — **verdict PASS**

## Commits

- `9ba73f3` — Complete ACM boxed mounting owner rates and CPP (initial slice)
- Closeout commit — check 9 fix + runtime evidence refresh

## Preserved unrelated dirty files (not staged)

- `.gitignore`, unrelated QA screenshots/evidence, `.compound-engineering/**`, other intake-v6 dirty docs/worklogs, `IntakeV6LayersOperatorPanel.tsx`, test-results/

## Gaps / next safe step

- Restart backend on :8000 so live stack matches committed code (stale process may omit `acm_*` CPP lines).
- Optional: wire frontend `VITE_API_BASE_URL` to reloaded backend after restart.
