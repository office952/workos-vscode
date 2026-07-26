# INTAKE V6 Configuration Defaults, Readiness & Confirmation Audit V1

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_CONFIGURATION_DEFAULTS_READINESS_CONFIRMATION_AUDIT_V1` |
| Verdict | **PARALLEL_TRUTH_CONFIRMED** |
| Accepted HEAD (audit baseline) | `58370b1` |
| Repo HEAD at audit time | `5208f05` (2-step simplification — flagged as owner-direction regression) |
| Runtime workspace | `22ef834d-f2d0-453b-a7a7-118928c98a39` / `IV6-189D2F12` |
| Live API | Backend `:8000` unavailable (503); read-only capture used |
| Application code changed | **NO** |

## Artifacts

| Path | Purpose |
|------|---------|
| `captures/workspace_field_summary.json` | Extracted persisted field truth for fixture workspace |
| `scripts/extract_workspace_summary.py` | Read-only extractor from FHA audit captures |
| `../worklog/realignment/2026-07-10_intake_v6_configuration_defaults_readiness_confirmation_audit_v1.md` | Full audit report |

## Source captures (read-only, pre-existing)

- `docs/qa/intake-v6-functional-handoff-audit-v1/captures/workspace.json`
- `docs/qa/intake-v6-functional-handoff-audit-v1/captures/quote_handoff.json`
- `docs/qa/intake-v6-functional-handoff-audit-v1/captures/product_definition.json`

## Tests run (read-only)

| Command | Passed | Failed | Exit |
|---------|--------|--------|------|
| `pytest tests/test_intake_v4_internal_draft_quote_confirmation_policy.py tests/test_return_cant_product_truth_bridge.py -q` | 27 | 0 | 0 |
| `vitest run …returnCantTruthFieldsReadonlyMapper.test.ts …intakeV6QuoteHandoffReadiness.test.ts …intakeV6FinishHydration.test.ts …IntakeV6ConfirmStep.test.tsx` | 29 | 2 | 1 |

Frontend failures are stale copy expectations in `intakeV6QuoteHandoffReadiness.test.ts` (not audit regressions).
