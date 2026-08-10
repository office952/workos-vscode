# QA — Intake V6 Exhaustive Price-Input Audit V1

**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1`  
**Report:** [WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1_REPORT.md](./WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1_REPORT.md)

## Run

```powershell
cd C:\w\psiso\backend
.\.venv\Scripts\python.exe scripts\run_intake_v6_exhaustive_price_input_audit_v1.py
.\.venv\Scripts\python.exe scripts\_write_intake_v6_price_audit_reports_v1.py
```

Requires live API `:8000` with dev bypass.

## Index

| Artifact | Role |
|----------|------|
| OPERATOR_INPUT_LEDGER.md | UI→CPP reconcile |
| scenario_catalog_v1.json | OFAT catalog |
| results.jsonl | machine results |
| INPUT_PRICE_MATRIX.md | human matrix |
| DEFECTS.md | P0/P1/P2 rows |
| ROOT_CAUSE_SUMMARY.md | grouped causes |
| UI_HONESTY.md | P0 + sample P1 |
| NOT_EXERCISED.md | out of scope |
| baselines/ · captures/ | frozen + per-scenario |
| manual_ron_audit.json | EUR/RON special |
