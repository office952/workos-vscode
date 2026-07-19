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

# Best-effort identity for /api/v1/system/version + local-compatibility (no secrets).
try {
    $shortSha = (& git -C $Root rev-parse --short HEAD 2>$null)
    if ($shortSha) { $env:WORKOS_GIT_COMMIT = [string]$shortSha.Trim() }
} catch { }

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
Install-WorkOsBackendRequirements -BackendDir $BackendDir

Write-Host "=== WorkOS backend dev ===" -ForegroundColor Cyan
Write-Host ("  Backend URL     = {0}" -f (Get-WorkOsBackendUrl))
Write-Host ("  Local compat    = {0}/api/v1/system/local-compatibility" -f (Get-WorkOsBackendUrl))
if ($env:WORKOS_GIT_COMMIT) {
    Write-Host ("  git_commit      = {0}" -f $env:WORKOS_GIT_COMMIT)
}
Write-Host ""

Set-Location $BackendDir
& $venvPython -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --reload
