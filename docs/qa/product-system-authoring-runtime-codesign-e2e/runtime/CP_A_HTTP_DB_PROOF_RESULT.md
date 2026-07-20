# CP-A — HTTP/DB Product Truth Proof RESULT

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Agent | A |
| HEAD | `705a701a6e48f2bee1f638e44031f32f6d19d751` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Verdict | **PASS** |
| BE used | `http://127.0.0.1:8000` |
| DB | `C:\w\psiso\backend\dev.db` |

## Routes + auth

- Confirm: `POST /api/v1/intake-v6/workspaces/{id}/product-truth/confirm-job`
- Status: `GET /api/v1/intake-v6/workspaces/{id}/product-truth/job-status`
- Auth: router-level `Depends(get_current_user)` + per-route dependency; live proof used `Authorization: Bearer __DEV_BYPASS_TOKEN__` (dev bypass → admin `dev-admin-user-00000000`)

## Fixture

- Created via HTTP: workspace_id `720a53ce-adc7-4173-8be5-86db85a438c8` / `IV6-66C427F7`
- `template_code`: `TPL-VOLUMETRIC-LETTERS_v2`
- SVG/layer prereqs cloned from existing VL fixture for finish-setup gate only (not aluminiu)

## Proof outcomes

| Case | Result |
|------|--------|
| Confirm → DB `payload_json.product_truth.confirmed_snapshot_v1` | PASS (`write_performed=true`) |
| Fresh sqlite session 1 + 2 reload | PASS (same revision/hash/state) |
| Service re-read via GET job-status | PASS (`has_job_revision=true`, freeze allowed) |
| Idempotent reconfirm | PASS (`idempotent_noop=true`, `write_performed=false`, revision stays 1) |
| Stale after finish-setup edit | PASS (`stale_after_edit`, pin retained, freeze blocked) |
| 409 `revision_mismatch` | PASS |
| 409 `draft_hash_mismatch` | PASS |
| 409 `content_hash_mismatch` | PASS |

## revision / hash

- `revision_id`: **1**
- `content_hash`: `sha256:7c0f5855584b988f3ddd7df6a475e7f4705150020194ddd8350461cecdf5b090`

## Tests

```text
pytest tests/test_product_truth_job_confirm_v1.py -q
10 passed in 0.77s
```

First Agent-A run (pre parallel WT edits): `7 passed`. Current WT adds 3 tests (content_hash 409, pinned-bag drift, order provenance) — **not authored by Agent A**; file is allowlisted; no foreign conflict stop (additions are separable / additive).

## Code fixes (Agent A)

None required — persist path already commits via `_persist_payload_json_raw_for_product_truth_writer`.

## Evidence paths

- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/cp_a_product_truth_http_db_proof.py`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/cp_a_http_db_proof_latest.json`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/cp_a_http_db_proof_20260720_223343.json`
- Failed first attempt (seed 422 before prereq clone): `cp_a_http_db_proof_20260720_223238.json`
