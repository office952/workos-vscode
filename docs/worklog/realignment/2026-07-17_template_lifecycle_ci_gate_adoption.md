# 2026-07-17 — Adopt Template Lifecycle Validator as Required CI Gate

## Mini decizie

`GO_ADOPT_TEMPLATE_LIFECYCLE_VALIDATOR_AS_REQUIRED_CI_GATE`

## Verdict

`REAL_CI_PIPELINE_NOT_IDENTIFIED`

Secondary finding (would block green CI even if a pipeline existed):

`EXISTING_ACTIVE_TEMPLATE_BASELINE_BLOCKED` — `TPL-METAL-PREMOUNT-STRUCTURE_v1`

## CI provider search

| Item | Value |
|------|--------|
| CI provider | **none found** |
| Pipeline file | none (no `.github/workflows`, Buildkite, GitLab, Azure, Jenkins) |
| Existing validation job | none |
| Backend command (local) | `backend/.venv/.../python scripts/template_lifecycle_cli.py validate --ci` |
| Frontend command | N/A (validator is backend Product System service) |
| Lifecycle insertion point | prepared: `npm run template-lifecycle:validate` |

Per owner GO: do **not** invent GitHub Actions / other providers.

## What was prepared (not “adopted”)

1. Cross-platform entry: `scripts/template-lifecycle.mjs`
2. Root scripts: `template-lifecycle:validate` (CI summary), `validate:json`, `inspect`
3. CLI `--ci` human-readable summary (same service/rules; exit 2 on required BLOCKED)
4. Docs: validation playbook + architecture CI status + AGENTS.md local gate note

## Baseline validate (local)

```text
Validated: 3
Letters + ACM: OWNER_GATE_REQUIRED (ok for CI policy)
Metal Premount: BLOCKED
  - STEP1_SVG_BINDING_CONTRACT_MISSING
  - PRODUCT_DEFINITION_PREVIEW_NULL
Exit code: 2
```

## Owner-facing label note

Internal role `support_panel` may remain; owner-facing composition label for live ACM is **Panou Alucobond casetat** (Intake composition panel). CI gates template codes/blockers, not label copy.

## Next safe step

**Option 2 — FIX ACTIVE TEMPLATE BASELINE BLOCKERS** (`TPL-METAL-PREMOUNT-STRUCTURE_v1`), then re-attempt CI adoption when a real pipeline file exists (or owner designates the local npm script as the merge gate process).

## Boundary

No Intake / FinishSetup / PD / PA / CPP / tasking / Execution / schema / migration / seed changes.
