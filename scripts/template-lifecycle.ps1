# Template Lifecycle Control CLI wrapper (repo root)
param(
  [Parameter(Position = 0)]
  [ValidateSet("inspect", "validate", "impact")]
  [string]$Command = "validate",

  [Parameter(Position = 1)]
  [string]$TemplateCode = ""
)

$ErrorActionPreference = "Stop"
$Backend = Join-Path $PSScriptRoot "..\backend"
Set-Location $Backend

$py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  throw "Missing backend/.venv — create venv before running template-lifecycle."
}

$env:APP_ENV = if ($env:APP_ENV) { $env:APP_ENV } else { "development" }
$env:ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "development" }
if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = "sqlite+aiosqlite:///./dev.db"
}
if (-not $env:JWT_SECRET_KEY) {
  $env:JWT_SECRET_KEY = "local-dev-secret-not-for-production"
}

$script = "scripts\template_lifecycle_cli.py"
switch ($Command) {
  "inspect" {
    if (-not $TemplateCode) { throw "inspect requires template code" }
    & $py $script inspect $TemplateCode
  }
  "impact" {
    if (-not $TemplateCode) { throw "impact requires template code" }
    & $py $script impact $TemplateCode
  }
  "validate" {
    if ($TemplateCode) {
      & $py $script validate --template $TemplateCode
    } else {
      & $py $script validate
    }
  }
}
exit $LASTEXITCODE
