# Worklog — Intake V6 exhaustive price-input audit V1

**Date:** 2026-08-10  
**Owner GO:** `AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Code changes:** audit runner + evidence only (`PRODUCT_CODE_CHANGES=0` for product/pricing law)

## What was done

1. UI-authoritative `OPERATOR_INPUT_LEDGER.md` (UI → finish-setup → schema → CPP).
2. Dependency-aware OFAT catalog (`scenario_catalog_v1.json`) on gradi-curat + test-bond-litere baselines.
3. Frozen baselines GRADI_EUR_SAFE / BOND_LETTERS_ACM_OPTIONAL / BOND_ACM_INCLUDED.
4. Runner `backend/scripts/run_intake_v6_exhaustive_price_input_audit_v1.py` → `results.jsonl` + captures.
5. Reports: MATRIX, DEFECTS, ROOT_CAUSE_SUMMARY, NOT_EXERCISED, UI_HONESTY, final report.
6. Manual RON special currency audit (no repair).

## Key outcomes

- 46 scenarios audited; **1 P0**, **20 P1** defect rows (grouped in ROOT_CAUSE_SUMMARY).
- Letters GRADI baseline complete_offer EUR coherent (~708.51).
- Bond ACM optional 113.9 vs included 472.4 (sold-scope transition priced).
- Manual RON: accepted, ignored, no FX → EUR-law compatibility **BLOCKED**.
- Next build (single): `WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1`

## Evidence

`docs/qa/workos-intake-v6-exhaustive-price-input-audit-v1/`
