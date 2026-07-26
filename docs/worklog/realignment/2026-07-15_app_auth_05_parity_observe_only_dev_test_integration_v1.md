# APP-AUTH-05 — Parity observe-only dev/test integration v1

**Date:** 2026-07-15  
**Task:** APP-AUTH-05-PARITY-OBSERVE-ONLY-DEV-TEST-INTEGRATION-V1  
**Starting HEAD:** `f4a8769`  
**Verdict:** `APP_AUTH_05_OBSERVE_ONLY_DEV_TEST_PASS_COMMITTED`  
**Gate:** I2 PASS (observe-only wiring, no source switch)

## Summary

Connected the isolated `backend/parity/` foundation to two approved operational consumers via a thin adapter package `backend/services/parity_observe/`. Operational responses and status codes remain unchanged; parity runs only after operational results are finalized, behind feature flags defaulting false, with production/staging forced off.

## Architecture

```text
operational service/router
  → parity_observe adapter (flags, batch reads, error isolation)
    → backend/parity pure comparators + contracts
  → unchanged operational response
```

## Wired consumers (2)

1. **Employee Mobile available** — `list_available_tasks()` tail hook  
2. **Eligibility endpoint** — `GET /api/v1/operational-registry/operation-mappings/{code}/eligible-employees`

## Sandu

In-memory observe report helper (`build_sandu_observe_report`, employee_id=4). No request-path wiring; no mutations; `CONFIRMATION_REQUIRED`.

## Feature flags

16 flags remain default false. Activation requires `parity_observe_enabled` plus domain subflags. `get_effective_parity_flags()` uses `model_construct()` outside local/development/test. Startup adds `PARITY_RUNTIME_FLAGS_GUARD`.

## Tests

- Focused parity + integration: **65 PASS**
- Regression bundle (mobile, eligibility, assignment, operator, execution reality, attendance, health): **119 PASS**
- Runtime probe on `:8001` with in-process flags-on supplement: PASS

## Evidence

`docs/qa/product-system-active-path-isolation-v1/app_auth_05/*.json`

## Forbidden scope respected

No source switch · no DB writes · no migrations · no new endpoints/UI · no eligibility enforcement · PROD-ARCH-01/MOBILE-INT-02/MODULE-RUNTIME-01 not opened.

## Next

**APP-AUTH-06-PARITY-OBSERVATION-PILOT** — controlled dev/test observation period; still no production activation or persistence.

## Authority debt

Gate I1 (foundation) + Gate I2 (observe-only wiring) **PASS**. Enforcement, persistence, and source switch remain **NOT AUTHORIZED**.
