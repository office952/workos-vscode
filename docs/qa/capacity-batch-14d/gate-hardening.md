# Capacity Batch 14D — Track C: Gate Hardening / Process Patch

- **Date:** 2026-07-29
- **Scope:** Stale-runtime detection before future controlled materialize execute
- **Non-goals:** No materialize POST redesign · no DEC-009 business-rule change · no execute unlock

## Gap (14C)

Controlled materialize / execute work could be aimed at a **healthy but stale** backend process that never loaded OD3 (`enforce_dec009_materialize_gate` from PR #29 / merge `a1b759c8`).

Symptoms of that class of failure:

| Observation | Meaning |
|-------------|---------|
| Backend answers health/version | Process is up — **not** proof of OD3 |
| POST materialize does not return `DEC009_MATERIALIZE_BLOCKED` | Likely pre-OD3 code path (or unexpected unlock) |
| `GET /api/v1/system/local-compatibility` 404 | Ghost/stale process (pre local-compat) |
| Compat 200 but no `execution.dec009_od3_gate` / no `od3_dec009_gate` | Compat-era but **pre-14D identity** / pre-OD3 stamp |

OD3 land reference: [PR #29](https://github.com/office952/workos-vscode/pull/29) → merge commit `a1b759c81355124f285b83425b93a9422f0e891e`.

## Smallest useful guard (landed)

Reuse the existing stale-backend identity surface (`GET /api/v1/system/local-compatibility`):

1. Capability: `execution.dec009_od3_gate`
2. Field: `od3_dec009_gate` ← `build_od3_runtime_identity()` in `services/dec009_materialize_gate.py`

Identity payload (read-only, no DB, not an execute path):

| Field | Expected (post-OD3 / 14D) |
|-------|---------------------------|
| `identity_version` | `capacity-batch-14d/v1` |
| `gate_module` | `services.dec009_materialize_gate` |
| `gate_landed` | `true` |
| `min_merge_commit` | `a1b759c81355124f285b83425b93a9422f0e891e` |
| `live_dec009` | `A` |
| `scoped_b_stamp` | `SCOPED_B_STAMPED` |
| `batch_execute_materialize_authorized` | `false` until Owner 14C GO |

Also expose `git_commit` on the same response when `WORKOS_GIT_COMMIT` / release manifest provides it. Prefer the OD3 stamp over SHA alone — SHA may be null in some local runs.

## Agent preflight — prove fresh OD3 runtime before future execute

**Mandatory before any controlled materialize POST / Batch 14C execute attempt:**

```bash
# 1) Identity (fail if missing / wrong)
curl -sS "$API_BASE/api/v1/system/local-compatibility" | jq '{
  git_commit,
  capabilities,
  od3_dec009_gate
}'
```

Pass criteria (all required):

1. HTTP **200** on `/api/v1/system/local-compatibility`
2. `capabilities` contains `execution.dec009_od3_gate`
3. `od3_dec009_gate.gate_landed == true`
4. `od3_dec009_gate.identity_version == "capacity-batch-14d/v1"`
5. `od3_dec009_gate.min_merge_commit` starts with `a1b759c8`
6. `od3_dec009_gate.live_dec009 == "A"` and `batch_execute_materialize_authorized == false` unless Owner has explicitly authorized execute in that build
7. Optional: if `git_commit` is non-null, confirm it is on a revision that **contains** `a1b759c8` (`git merge-base --is-ancestor a1b759c8 <git_commit>`)

**Reject / restart runtime if:**

- Compat 404, or
- Capability / `od3_dec009_gate` absent, or
- `gate_landed` not true, or
- Identity version mismatch

Then restart the backend from a checkout ≥ `a1b759c8` (prefer current `origin/main`), re-run preflight, and only then proceed to Owner-authorized execute steps.

## Negative proof (stale)

A pre-OD3 or wrong-port process must **not** be treated as OD3-live. Minimum agent evidence of stale:

```text
FAIL: missing capabilities includes execution.dec009_od3_gate
  OR missing field od3_dec009_gate
  OR HTTP 404 on local-compatibility
```

Do **not** infer OD3 from dashboard copy, release label alone, or a green `/health`.

## Tests

```bash
cd backend
pytest tests/test_dec009_materialize_gate.py::test_od3_runtime_identity_stamp_for_preflight \
       tests/test_system_local_compatibility.py::SystemLocalCompatibilityTest::test_endpoint_exposes_od3_runtime_identity \
       -q
```

## Explicit non-changes

- No change to `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED` default
- No change to materialize write path beyond existing OD3 hard reject
- No live DEC-009=B invention
- Frontend `LOCAL_COMPAT_REQUIRED_CAPABILITIES` intentionally **not** expanded (agent/process guard only; avoids unrelated DEV banner churn)
