# Run backend pytest with local SQLite env defaults.
# Windows helper invoked by: npm run test:backend
#
# Ensures requirements-dev.txt (pytest) is installed in backend/.venv.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-python.ps1"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$DevDbPath = Join-Path $BackendDir "dev.db"
$DatabaseUrl = "sqlite+aiosqlite:///" + ($DevDbPath -replace "\\", "/")

$env:APP_ENV = "development"
$env:ENVIRONMENT = "development"
Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
$env:DATABASE_URL = $DatabaseUrl
Set-WorkOsJwtEnv
$env:DEBUG = "true"

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
Install-WorkOsBackendRequirements -BackendDir $BackendDir -IncludeDev

Set-Location $BackendDir
& $venvPython -m pytest tests/ -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
