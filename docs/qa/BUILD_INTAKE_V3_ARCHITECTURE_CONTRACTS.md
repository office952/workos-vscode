# BUILD — INTAKE_V3_ARCHITECTURE_CONTRACTS

**Date:** 2026-06-17  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `4e43299`  
**Verdict:** PASS (pending owner commit decision)

---

## Purpose

First real Intake V3 build: versioned architecture contracts, readiness skeleton, frontend types only, documentation and targeted pytest — **no UI, no DB migration, no commercial/production runtime changes**.

---

## Context

- Atoms V6 accepted as `DESIGN_REFERENCE_ACCEPTED_WITH_WARNINGS`
- Owner operational rules documented as future execution gap, not implemented now

---

## Files changed / created

| Path | Action |
|------|--------|
| `backend/data_models/intake_v3_contracts.py` | **created** — version constants, blocker codes, owner rules |
| `backend/schemas/intake_v3.py` | **created** — Pydantic contracts + `IntakeV3Workspace` |
| `backend/services/intake_v3_readiness_service.py` | **created** — in-memory `ReadinessReport` evaluator |
| `backend/tests/test_intake_v3_architecture_contracts.py` | **created** — contract + readiness tests |
| `frontend/src/lib/intakeV3/contracts.ts` | **created** — TypeScript type mirrors |
| `docs/architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md` | **created** — architecture reference |
| `docs/qa/BUILD_INTAKE_V3_ARCHITECTURE_CONTRACTS.md` | **created** — this QA log |

---

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_architecture_contracts.py -q
# 15 passed, 2 warnings in 0.08s

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
# 22 passed, 2 warnings in 0.08s
```

Frontend: types-only file added; full `validate:frontend` not run (known TS debt out of scope).

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| 13 contracts defined in backend | ✅ |
| Readiness skeleton with required blockers | ✅ |
| Frontend types only (no UI/routes) | ✅ |
| `MaterialIntent.inventory_mutation_allowed` locked false | ✅ |
| `ProductionHandoff.preview_only` locked true | ✅ |
| `EmployeePreviewSeed.non_executable` locked true | ✅ |
| Owner rules documented in constants + arch doc | ✅ |
| No DB migration | ✅ |
| No CostEngine / ExecutionPlan changes | ✅ |
| Targeted pytest green | ✅ 15 + 22 passed |

---

## Boundary

**In scope:** contracts, readiness skeleton, types, docs, tests  
**Out of scope:** UI, SVG parser, execution fix, electrical runtime, CostEngine, inventory, migrations, commit, push

---

## What remains separate

- `INTAKE_V3_VECTOR_AND_LETTER_MODEL`
- `INTAKE_V3_PRICING_INPUT_ADAPTER`
- `INTAKE_V3_PRODUCTION_HANDOFF_ADAPTER`
- `AUDIT/FIX — Volumetric execution task order and electrical source handling`
- `INTAKE_V3_UI_SHELL`
- Persistence / `intake_schema_version=3` (owner decision)

---

## Next steps

1. Owner reviews report and decides local commit
2. Next build: `INTAKE_V3_VECTOR_AND_LETTER_MODEL` or pricing adapter per owner priority
