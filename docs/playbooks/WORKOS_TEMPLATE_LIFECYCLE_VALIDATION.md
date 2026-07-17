# WORKOS — Template Lifecycle Validation Guide

## Local

```powershell
# All active root-offerable templates
npm run template-lifecycle:validate

# Specific template validate / inspect / impact
.\scripts\template-lifecycle.ps1 validate TPL-VOLUMETRIC-LETTERS_v2
.\scripts\template-lifecycle.ps1 inspect TPL-VOLUMETRIC-LETTERS_v2
.\scripts\template-lifecycle.ps1 impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
```

Backend direct:

```powershell
cd backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe scripts\template_lifecycle_cli.py validate
```

Pytest:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_template_lifecycle_control.py -q
```

## CI integration

No dedicated GitHub Actions / Buildkite pipeline was identified in-repo for Product System.

V1 integrates as:

1. Local command `npm run template-lifecycle:validate`
2. Pytest gate `tests/test_template_lifecycle_control.py`
3. Documented required agent gate before template-affecting work

Diff-aware validation (changed files → affected templates) is **V2** — not claimed in V1.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | validate ok |
| 2 | activation-required BLOCKED on active root-offerable template |
| other | hard runtime error |

## False positive / false negative rules

**False positive (must not claim PASS):** Step 2 missing while SUPPORT_CONTOUR exists without hydrate; PD null; Aggregate null; deprecated new-selection authority.

**False negative (must not BLOCK wrongly):** optional inactive component; CPP correctly `OWNER_GATE_REQUIRED`; task materialization future; candidate logo with owner gate.
