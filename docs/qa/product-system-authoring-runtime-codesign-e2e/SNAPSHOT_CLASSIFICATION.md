# Snapshot / downstream classification — this build

| Suite / area | Classification | Action |
|--------------|----------------|--------|
| `test_product_truth_job_confirm_v1` | BUILD_OK | Keep; 7 passed with publication suite |
| `test_product_e2e_readiness_v1` | BUILD_OK | Keep; aluminiu inactive → BLOCKED honest |
| Publication publish gate | BUILD_NEW | VL publish 409 when readiness BLOCKED |
| Quote Snapshot V2 freeze gate (`70b2fdf`) | PREEXISTING_FOUNDATION | No weaken; freeze still requires confirmed PT |
| Order provenance | PREEXISTING_FOUNDATION | No change this vertical |
| EP preview PT revision | PREEXISTING_PARTIAL | Out of scope unless build-caused fail |
| Full `test_quote_snapshot_v2` / intake snap suites | PREEXISTING_NOISE | Do not greenwash; classify only |

## Policy

- Fix **build-caused** failures only.
- Never weaken freeze / confirm assertions.
- EIC qty parallel path remains known PARTIAL (foundation worklog).
