# 2026-07-16 — Gradi-curat readiness severity channel split

## Purpose

Implement owner-approved readiness channel split so Aggregate `info` diagnostics no longer clear `accept_allowed` / Order / Execution flags, while `TRIGGER_FIELD_MISMATCH` remains Order/Execution-sensitive and `operator_confirmation_missing` stays the Step 3 quote fatal.

## Boundary

- Readiness classification only (`intake_v6_canonical_readiness_service` + handoff schema/UI surfacing)
- No pricing / registry / CostEngine
- No Quote/Order creation
- No auto-confirm / Step 3 gate removal
- No diagnostic deletion
- No global “all warnings nonblocking”
- No PD/PA emit changes (codes still produced; channel split on lift)

## Owner gates (locked)

| Gate | Answer |
|------|--------|
| G1 | YES — Quote after Step 3 confirm if no other fatals |
| G2 | TRIGGER remains Order/Execution-sensitive; not Quote-blocking |
| G3 | Three info codes visible, nonblocking for Quote/accept/Order/Execution |

## Changes

| Area | Change |
|------|--------|
| `intake_v6_canonical_readiness_service.py` | `partition_canonical_unresolved_warnings`; `diagnostic_warnings` on findings + merge |
| `schemas/intake_v4.py` | `diagnostic_warnings` on handoff preview |
| `intake_v6_commercial_quote_service.py` | Pass diagnostics through handoff preview |
| Confirm handoff card | Separate “Detalii tehnice (nu blochează)” section |
| Tests | `test_intake_v6_readiness_severity_channel_split.py` |

## Validation

```text
backend/.venv/Scripts/python.exe -m pytest tests/test_intake_v6_readiness_severity_channel_split.py tests/test_intake_v6_canonical_readiness_spine.py -q
# 15 passed
```

## Verdict

`GRADI_CURAT_READINESS_CHANNEL_SPLIT_COMPLETE`

## Related audit artifacts

- `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/`
- `docs/qa/gradi-curat-e2e/dossier-trigger-truth-evidence.json`
