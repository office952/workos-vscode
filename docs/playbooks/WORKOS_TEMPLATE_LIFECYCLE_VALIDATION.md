# WORKOS — Template Lifecycle Validation Guide

## Status (2026-07-17)

**Real CI pipeline:** **not identified** in this repository (no GitHub Actions / Buildkite / GitLab / Azure / Jenkins files).

Therefore required CI gate adoption is **blocked** with verdict `REAL_CI_PIPELINE_NOT_IDENTIFIED`.

Local / agent gate is ready and must be used until a real pipeline exists.

## Local command (canonical)

Cross-platform (Node → Python CLI → same lifecycle service as API/UI):

```powershell
# Repo root — human-readable CI summary + exit code
npm run template-lifecycle:validate

# JSON payload
npm run template-lifecycle:validate:json

# Inspect / impact
npm run template-lifecycle:inspect -- TPL-VOLUMETRIC-LETTERS_v2
node scripts/template-lifecycle.mjs impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
```

Direct Python:

```powershell
cd backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe scripts\template_lifecycle_cli.py validate --ci
```

## Validation profile (V1)

**Active root-offerable templates** (`active_only=true`):

Fails (exit **2**) when an **ACTIVE** root-offerable template has an activation-required stage `BLOCKED`.

Does **not** fail for:

- CPP / snapshot / task materialization / Execution `OWNER_GATE_REQUIRED` or preview
- optional inactive components
- guarded logo candidate
- read-only legacy compatibility warnings

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | required lifecycle gates passed (owner gates may remain) |
| 2 | activation-required BLOCKED on active root-offerable template |
| other | hard runtime error |

## Baseline snapshot (local, 2026-07-17)

Validated: **3** active root-offerable codes in `dev.db`

| Template | Status | Notes |
|----------|--------|-------|
| TPL-VOLUMETRIC-LETTERS_v2 | OWNER_GATE_REQUIRED | score 100; no required blockers |
| TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 | OWNER_GATE_REQUIRED | score 100; no required blockers |
| TPL-METAL-PREMOUNT-STRUCTURE_v1 | **BLOCKED** | `STEP1_SVG_BINDING_CONTRACT_MISSING`, `PRODUCT_DEFINITION_PREVIEW_NULL` |

⇒ `npm run template-lifecycle:validate` currently exits **2** because of Metal Premount.

Before wiring any future CI job: either fix Metal Premount readiness under a dedicated GO, or owner must explicitly redefine its activation profile. **Do not** hide with a broad allowlist.

## When a real CI pipeline appears

1. Add a job that runs from repo root: `npm run template-lifecycle:validate`
2. Require `backend/.venv` (or `WORKOS_PYTHON`) + `DATABASE_URL` pointing at seeded/dev DB used for availability reads
3. Fail the job on exit code ≠ 0
4. Do not duplicate rules in YAML — only invoke the CLI
5. Keep all-active validation (diff-aware summary is V2)

## Owner-facing labels

Internal composition role code may remain `support_panel`. Owner-facing UI must show **Panou Alucobond casetat** for live ACM support (already mapped in Intake composition panel). CI validates template codes / stage blockers, not Romanian labels.

## Pytest

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_template_lifecycle_control_system_v1.py tests/test_early_svg_support_finish_setup_v1.py -q
```

## False positive / false negative

**Must not PASS:** required Step 1 persist blocker; Step 2 hydrate missing for SUPPORT_CONTOUR; PD null; Aggregate null; deprecated new-selection authority as active path.

**Must not FAIL:** optional inactive ACP; CPP owner gate; task materialization future; candidate logo with owner gate.
