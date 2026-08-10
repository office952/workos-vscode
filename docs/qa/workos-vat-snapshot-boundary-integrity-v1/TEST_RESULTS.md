# TEST_RESULTS

Command (backend venv):

```text
python -m pytest -q \
  tests/test_frozen_commercial_vat_resolver.py \
  tests/test_vat_snapshot_boundary_integrity_v1.py \
  tests/test_intake_v6_snapshot_authoritative_offer.py \
  tests/test_intake_v6_snapshot_authoritative_pricing_review.py \
  --ignore=tests/manual
```

Result: **28 passed**

Coverage highlights:

- Resolver: notes primary, nested fallback, CPP secondary, fail-closed, no amount-as-% guess
- Scenario A: Settings 21 → offer/review @21 → Settings 19 → still 21; notes rate preserved
- Fail-closed offer when provenance stripped
- Existing W4-T01 / W4-T01B offer + pricing-review suites green
