# Worklog — Intake V6 Face Finish Token Fidelity V1

**Date:** 2026-08-11  
**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_FACE_FINISH_TOKEN_FIDELITY_V1`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Baseline:** `27a0cbac`

## Verdict

PASS — Oracal 641/651/8500 series identity preserved through adapter → quote_input → CPP; none / print distinct; no rate/schema/Product Truth changes; local commit only.

## Root cause

1. `_template_face_finish_type` collapsed vinyl family to `oracal_651`.
2. V3 finish map emitted `vinyl` for 641/651 into `quote_input.face_finish_type`.
3. Dry-run enrich did not bridge workspace face identity into `finish_setup` for CPP gates.

## Fix

- `backend/services/intake_v4_pricing_input_service.py` — series-preserving template map + commercial token restore.
- `backend/services/intake_v6_priced_quote_dry_run_service.py` — enrich bridge / overwrite collapsed vinyl.
- Focused tests + evidence under `docs/qa/workos-intake-v6-face-finish-token-fidelity-v1/`.

## Roadmap checkpoint

- Position: Slice 0 after E2E operator-reality audit — **complete**
- Direction alignment: high (bounded fidelity repair only)
- Next recommended (not authorized): `WORKOS_INTAKE_V6_CRITICAL_PATH_GET_DIET_V1`
- Forbidden scope respected: YES
- PUSH: NO

## Dead pieces / overengineering

- No new parallel commercial field.
- V3 `vinyl` retained only for operation-flag compatibility.
- Mixed job-level dominant still setup-driven; per-group identity in handoff/matrix.
