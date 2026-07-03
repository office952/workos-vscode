# Start WorkOS backend only (uvicorn :8000) with local SQLite defaults.
# Windows helper invoked by: npm run dev:backend
#
# Injects env vars into this process — does NOT load backend/.env automatically.

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
$env:JWT_SECRET_KEY = "local-dev-secret-not-for-production"
$env:DEBUG = "true"
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
Install-WorkOsBackendRequirements -BackendDir $BackendDir

Set-Location $BackendDir
& $venvPython -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
