# Worklog — Intake V6 priced quote critical path performance v1

Date: 2026-08-13  
Task: `WORKOS_INTAKE_V6_PRICED_QUOTE_CRITICAL_PATH_PERFORMANCE_V1`  
Baseline: `c8f27b17`  
Mode: AUDIT FIRST → OPTION B

## Finding

Warm in-process pricedQuote was ~80–100 ms with CPP≈40 ms and EIC≈33 ms; HTTP 1.5–1.9 s under Step 2 fan-out. Material-breakdown + EIC + diagnostic cost-plus were not required for official CPP totals.

## Change

Default dry-run defers internal-cost diagnostics. Write/snapshot opt in.

## Result

SQL 114→61; alone HTTP ~250–360 ms; fan-out pricedQuote ~500–770 ms. Commercial parity preserved. PUSH=NO.
