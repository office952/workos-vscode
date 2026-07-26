# Start WorkOS frontend only (Vite :3000) with canonical BACKEND_PORT proxy default.
# Windows helper invoked by: npm run dev:frontend

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"

Initialize-WorkOsDevPortContract
Clear-WorkOsParityEnv
$env:VITE_ENABLE_DEV_AUTH = "true"
$viteApiBase = Sync-WorkOsViteApiBaseUrl

$frontendPort = Get-WorkOsFrontendPort
$proxyTarget = Get-WorkOsViteProxyTarget

Write-Host "=== WorkOS frontend dev ===" -ForegroundColor Cyan
Write-Host ("  Frontend URL        = {0}" -f (Get-WorkOsFrontendUrl))
Write-Host ("  Vite proxy          = /api -> {0}" -f $proxyTarget)
Write-Host ("  BACKEND_PORT        = {0}" -f $env:BACKEND_PORT)
Write-Host ("  VITE_API_BASE_URL   = {0}" -f $viteApiBase)
Write-Host ("  Compat probe        = {0}/api/v1/system/local-compatibility" -f $viteApiBase)
Write-Host ""

Set-Location $FrontendDir
if (-not (Test-Path "node_modules")) {
    npx --yes pnpm@8.10.0 install
}

npx --yes pnpm@8.10.0 run dev --host 127.0.0.1 --port $frontendPort
