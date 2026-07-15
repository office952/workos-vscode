# Start WorkOS backend only (uvicorn :8001 by default) with local SQLite defaults.
# Windows helper invoked by: npm run dev:backend
#
# Injects env vars into this process — does NOT load backend/.env automatically.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"
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
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"

Initialize-WorkOsDevPortContract
Clear-WorkOsParityEnv
$BackendPort = Get-WorkOsBackendPort

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
Install-WorkOsBackendRequirements -BackendDir $BackendDir

Set-Location $BackendDir
& $venvPython -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --reload
