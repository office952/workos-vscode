# Dossier Isolation Test Matrix

## Regression tests (this task)

| ID | Scenario | Expected |
|----|----------|----------|
| T1 | Approved dossier extra component | Aggregate uses parent `components_json` only |
| T2 | Approved dossier extra operation mapping | No dossier provenance on materials/ops |
| T3 | Approved dossier extra task rule | Task contract empty / template-only |
| T4 | Intake V6 with dossier variant override | Canonical variants win |
| T5 | Intake V5 template config | `authority: canonical_template_contract` |
| T6 | Output blocks v2 without dossier | Renders from canonical |
| T7 | Canonical behavior without dossier row | Aggregate still builds from parent |
| T8 | Shadowing: dossier + parent disagree | Parent/canonical wins |
| T9 | Retain 44-test isolation suite | All pass |

## Files

- `tests/test_product_aggregate_dossier_gating.py` (updated)
- `tests/test_dossier_true_isolation.py` (new)
- `tests/test_intake_v6_option_contract_dossier_gating.py` (updated if needed)

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_dossier_consumption_policy.py tests/test_product_aggregate_dossier_gating.py tests/test_intake_v6_option_contract_dossier_gating.py tests/test_product_system_identity_boundary.py tests/test_dossier_true_isolation.py -q
```
