# Test results — C3 Owner Review

## Backend (targeted)

```text
command: python -m pytest tests/test_f6_multi_type_actual_cost_pilot.py tests/test_actual_cost_coverage_v1.py tests/test_material_actuals_closed_job_v1.py tests/test_profitability_actual_read_model.py tests/test_post_job_truth.py tests/test_closure_readiness_operator_v1.py -q --tb=line -W error::RuntimeWarning
passed: 23
failed: 0
skipped: 0
duration: ~11.8s (wall ~14.9s)
warnings: Starlette/httpx TestClient deprecation; Pydantic V2 config deprecation (preexisting deps)
failure ownership: n/a
```

## Frontend (targeted)

```text
command: npm test -- --run src/components/execution-result src/lib/executionClosureUi.test.ts
passed: 4
failed: 0
skipped: 0
duration: ~1.06s
warnings: none material
```

## Not run / not claimed

```text
full backend suite — NOT RUN
full frontend suite — NOT RUN
Pricing.badges — NOT RUN / not green-claimed
```
