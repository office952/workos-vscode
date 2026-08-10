# WorkOS demo backend - uses backend/demo/workos_demo.db only (never dev.db).

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"
. "$PSScriptRoot\_workos-python.ps1"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$DemoDbPath = Join-Path $BackendDir "demo\workos_demo.db"
$Forbidden = Join-Path $BackendDir "dev.db"

$demoResolvedExisting = Resolve-Path -LiteralPath $DemoDbPath -ErrorAction SilentlyContinue
$forbiddenResolvedExisting = Resolve-Path -LiteralPath $Forbidden -ErrorAction SilentlyContinue
if ($demoResolvedExisting -and $forbiddenResolvedExisting) {
    if ($demoResolvedExisting.Path -eq $forbiddenResolvedExisting.Path) {
        Write-Error "Demo DB path resolves to forbidden dev.db"
    }
}
if (-not (Test-Path $DemoDbPath)) {
    Write-Error "Demo DB missing: $DemoDbPath - run .\scripts\demo-bootstrap.ps1 first"
}

$DatabaseUrl = "sqlite+aiosqlite:///" + ($DemoDbPath -replace "\\", "/")
$env:APP_ENV = "development"
$env:ENVIRONMENT = "development"
Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
$env:DATABASE_URL = $DatabaseUrl
Set-WorkOsJwtEnv
$env:DEBUG = "true"
$env:VITE_ENABLE_DEV_AUTH = "true"

Initialize-WorkOsDevPortContract
Clear-WorkOsParityEnv
$BackendPort = Get-WorkOsBackendPort
$FrontendPort = Get-WorkOsFrontendPort
$env:ALLOWED_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
Write-Host "=== WorkOS DEMO backend ===" -ForegroundColor Cyan
Write-Host ("  DATABASE_URL = {0}" -f $DatabaseUrl)
Write-Host ("  Backend URL  = {0}" -f (Get-WorkOsBackendUrl))

Set-Location $BackendDir
& $venvPython -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --reload
