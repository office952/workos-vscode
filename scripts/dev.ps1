# WorkOS Dev Mode - canonical local launcher (Windows only).
# Sets script-scoped dev env (incl. dev auth flags), verifies layout, then starts the stack.
# Does NOT hardcode dev auth in Python source - env vars only.
#
# Usage:
#   .\scripts\dev.ps1              Start or reuse backend :8001 + frontend :3000
#   .\scripts\dev.ps1 -PreflightOnly   Validate layout/env only (no servers)
#
# Stop: Ctrl+C when frontend logs are streaming; or stop PIDs on ports 8001 / 3000.

param(
    [switch] $PreflightOnly
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$DevDbPath = Join-Path $BackendDir "dev.db"
$DatabaseUrl = "sqlite+aiosqlite:///" + ($DevDbPath -replace "\\", "/")

$LocalJwtSecret = "local-dev-secret-not-for-production"
Initialize-WorkOsDevPortContract
Clear-WorkOsParityEnv
$BackendUrl = Get-WorkOsBackendUrl
$FrontendUrl = Get-WorkOsFrontendUrl
$HealthUrl = "$BackendUrl/health"
$AllowedOrigins = "http://localhost:3000,http://127.0.0.1:3000"

function Set-WorkOsDevModeEnv {
    $env:APP_ENV = "development"
    $env:ENVIRONMENT = "development"
    Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
    $env:DATABASE_URL = $DatabaseUrl
    $env:JWT_SECRET_KEY = $LocalJwtSecret
    $env:DEBUG = "true"
    $env:ALLOWED_ORIGINS = $AllowedOrigins
    # Frontend dev auth (Vite build-time / runtime import.meta.env)
    $env:VITE_ENABLE_DEV_AUTH = "true"
    $env:BACKEND_PORT = [string](Get-WorkOsBackendPort)
    [void](Sync-WorkOsViteApiBaseUrl)
}

function Show-WorkOsDevModeReport {
    $backendDevAuth = ($env:APP_ENV -in @("local", "development", "test"))
    $frontendDevAuth = ($env:VITE_ENABLE_DEV_AUTH -eq "true")
    $impersonation = $env:WORKOS_DEV_AUTH_USER_ID
    if (-not $impersonation) { $impersonation = "(unset - synthetic Dev Admin)" }

    Write-Host ""
    Write-Host "=== WorkOS Dev Mode ===" -ForegroundColor Cyan
    Write-Host ("  Root                     = {0}" -f $Root)
    Write-Host ("  Backend URL              = {0}" -f $BackendUrl)
    Write-Host ("  Frontend URL             = {0}" -f $FrontendUrl)
    Write-Host ("  Health                   = {0}" -f $HealthUrl)
    Write-Host ("  Vite proxy (/api)        = {0}" -f (Get-WorkOsViteProxyTarget))
    Write-Host ("  BACKEND_PORT             = {0}" -f $env:BACKEND_PORT)
    Write-Host ("  VITE_API_BASE_URL        = {0}" -f $env:VITE_API_BASE_URL)
    Write-Host ("  Local compat             = {0}/api/v1/system/local-compatibility" -f $BackendUrl)
    Write-Host ("  Backend dev auth         = {0} (APP_ENV={1}, dev_auth_allowed)" -f $(if ($backendDevAuth) { "ENABLED" } else { "DISABLED" }), $env:APP_ENV)
    Write-Host ("  Frontend dev auth        = {0} (VITE_ENABLE_DEV_AUTH={1})" -f $(if ($frontendDevAuth) { "ENABLED" } else { "DISABLED" }), $env:VITE_ENABLE_DEV_AUTH)
    Write-Host ("  Impersonation            = {0}" -f $impersonation)
    Write-Host "  DATABASE_URL             = sqlite+aiosqlite:///<backend>/dev.db"
    Write-Host "  JWT_SECRET_KEY           = [local placeholder, not for deploy]"
    Write-Host ("  ALLOWED_ORIGINS          = {0}" -f $env:ALLOWED_ORIGINS)
    Write-Host ""
    Write-Host "Stop: Ctrl+C while this script streams frontend logs, or end the processes listening on ports 8001 and 3000." -ForegroundColor DarkGray
    Write-Host ""
}

function Require-RepoLayout {
    if (-not (Test-Path $BackendDir -PathType Container)) {
        Write-Error "Missing backend directory: $BackendDir"
    }
    if (-not (Test-Path $FrontendDir -PathType Container)) {
        Write-Error "Missing frontend directory: $FrontendDir"
    }
}

Set-WorkOsDevModeEnv
Require-RepoLayout

. "$PSScriptRoot\_workos-python.ps1"
$null = Get-WorkOsBackendVenvPython -BackendDir $BackendDir

Show-WorkOsDevModeReport

if ($PreflightOnly) {
    Write-Host "Preflight OK - exiting without starting servers (-PreflightOnly)." -ForegroundColor Green
    exit 0
}

& "$PSScriptRoot\start-dev.ps1"
