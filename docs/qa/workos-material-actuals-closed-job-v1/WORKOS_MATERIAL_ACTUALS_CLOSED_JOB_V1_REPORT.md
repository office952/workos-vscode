# WorkOS Material Actuals + Closed-Job Proof V1

| Field | Value |
|---|---|
| Track | F4 |
| Branch | `feat/material-actuals-closed-job-v1` |
| Base | `10fca478` |
| Migration | `s62_material_actuals_closed_job_v1` |
| Fixture | `880041` |

## Outcome

Canonical ISSUE/RETURN/SCRAP material actuals with freeze-on-movement valuation, closure readiness gates for labor+material, and a controlled closed-job profitability proof.

```text
Closed-job profitability proof = PASS
Platform-wide Profitability Complete = NOT READY
```

## Tests

`pytest tests/test_material_actuals_closed_job_v1.py` → 4 passed.
