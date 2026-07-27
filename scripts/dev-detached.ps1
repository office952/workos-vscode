# WorkOS detached local stack (Windows).
# Starts backend (:8000) + frontend (:3000) as independent OS processes that
# SURVIVE the parent PowerShell / Cursor agent session ending.
#
# Prefer this for agents and any unattended start. Owner interactive streaming:
#   .\scripts\dev.ps1
#
# This script does NOT kill listeners. If a port is occupied but unhealthy,
# it exits with a blocker - Owner may then run .\scripts\stop-dev.ps1.
#
# Usage:
#   .\scripts\dev-detached.ps1
#   .\scripts\dev-detached.ps1 -PreflightOnly

param(
    [switch] $PreflightOnly
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"
. "$PSScriptRoot\_workos-python.ps1"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$LogDir = Join-Path $Root ".workos-dev-logs"
$StatePath = Join-Path $Root ".workos-dev-detached.json"
$DevDbPath = Join-Path $BackendDir "dev.db"
$DatabaseUrl = "sqlite+aiosqlite:///" + ($DevDbPath -replace "\\", "/")
$LocalJwtSecret = "local-dev-secret-not-for-production"
$AllowedOrigins = "http://localhost:3000,http://127.0.0.1:3000"

function Test-HttpOk {
    param(
        [string] $Url,
        [int] $TimeoutSec = 3
    )
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    } catch {
        return $false
    }
}

function Get-PortListener {
    param([int] $Port)
    $conns = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($conns.Count -eq 0) { return $null }
    $listenerPid = $conns[0].OwningProcess
    $proc = Get-Process -Id $listenerPid -ErrorAction SilentlyContinue
    return [PSCustomObject]@{
        Port = $Port
        PID = $listenerPid
        ProcessName = if ($proc) { $proc.ProcessName } else { "unknown" }
    }
}

function Wait-ForService {
    param(
        [string] $Name,
        [scriptblock] $Probe,
        [int] $MaxAttempts = 60,
        [int] $DelaySec = 2
    )
    foreach ($i in 1..$MaxAttempts) {
        if (& $Probe) {
            Write-Host "$Name ready after $($i * $DelaySec)s" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds $DelaySec
    }
    return $false
}

function Start-DetachedScript {
    param(
        [Parameter(Mandatory = $true)][string] $ScriptPath,
        [Parameter(Mandatory = $true)][string] $Title,
        [Parameter(Mandatory = $true)][string] $StdoutLog,
        [Parameter(Mandatory = $true)][string] $StderrLog
    )

    $psExe = (Get-Command powershell.exe -ErrorAction Stop).Source
    $argList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ScriptPath
    )
    # Hidden + redirects: independent process tree; no console tied to the agent shell.
    $proc = Start-Process -FilePath $psExe `
        -ArgumentList $argList `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdoutLog `
        -RedirectStandardError $StderrLog `
        -PassThru
    Write-Host ('Started {0} as PID {1} - detached; logs: {2}' -f $Title, $proc.Id, $StdoutLog) -ForegroundColor DarkGray
    return $proc
}

Initialize-WorkOsDevPortContract
Clear-WorkOsParityEnv
$BackendPort = Get-WorkOsBackendPort
$FrontendPort = Get-WorkOsFrontendPort
$BackendUrl = Get-WorkOsBackendUrl
$FrontendUrl = Get-WorkOsFrontendUrl
$HealthUrl = "$BackendUrl/health"

$env:APP_ENV = "development"
$env:ENVIRONMENT = "development"
Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
$env:DATABASE_URL = $DatabaseUrl
$env:JWT_SECRET_KEY = $LocalJwtSecret
$env:DEBUG = "true"
$env:ALLOWED_ORIGINS = $AllowedOrigins
$env:VITE_ENABLE_DEV_AUTH = "true"
$env:BACKEND_PORT = [string]$BackendPort
[void](Sync-WorkOsViteApiBaseUrl)

if (-not (Test-Path $BackendDir -PathType Container)) {
    Write-Error "Missing backend directory: $BackendDir"
}
if (-not (Test-Path $FrontendDir -PathType Container)) {
    Write-Error "Missing frontend directory: $FrontendDir"
}

$null = Get-WorkOsBackendVenvPython -BackendDir $BackendDir

Write-Host ""
Write-Host "=== WorkOS detached dev ===" -ForegroundColor Cyan
Write-Host ('  Root          = {0}' -f $Root)
Write-Host ('  Backend URL   = {0}' -f $BackendUrl)
Write-Host ('  Frontend URL  = {0}' -f $FrontendUrl)
Write-Host '  Mode          = detached OS processes - survives agent session end'
Write-Host '  Stop          = Owner only via .\scripts\stop-dev.ps1'
Write-Host ""

if ($PreflightOnly) {
    Write-Host 'Preflight OK - exiting without starting servers (-PreflightOnly).' -ForegroundColor Green
    exit 0
}

$backendListener = Get-PortListener -Port $BackendPort
$frontendListener = Get-PortListener -Port $FrontendPort
$backendHealthy = Test-HttpOk -Url $HealthUrl
$frontendHealthy = Test-HttpOk -Url $FrontendUrl

if ($backendHealthy -and $frontendHealthy) {
    Write-Host 'Stack already healthy - reusing existing listeners. No kill, no restart.' -ForegroundColor Green
    if ($backendListener) {
        Write-Host ('  Backend  :{0} PID={1}' -f $BackendPort, $backendListener.PID) -ForegroundColor DarkGray
    }
    if ($frontendListener) {
        Write-Host ('  Frontend :{0} PID={1}' -f $FrontendPort, $frontendListener.PID) -ForegroundColor DarkGray
    }
    exit 0
}

if ($backendListener -and -not $backendHealthy) {
    Write-Host ""
    Write-Host ('BLOCKER: Port {0} is occupied but /health is not OK - PID={1}, {2}.' -f $BackendPort, $backendListener.PID, $backendListener.ProcessName) -ForegroundColor Red
    Write-Host '  Agents must NOT kill this process. Ask Owner to run .\scripts\stop-dev.ps1, then retry.' -ForegroundColor Red
    Write-Host ""
    exit 1
}

if ($frontendListener -and -not $frontendHealthy) {
    Write-Host ""
    Write-Host ('BLOCKER: Port {0} is occupied but frontend is not OK - PID={1}, {2}.' -f $FrontendPort, $frontendListener.PID, $frontendListener.ProcessName) -ForegroundColor Red
    Write-Host '  Agents must NOT kill this process. Ask Owner to run .\scripts\stop-dev.ps1, then retry.' -ForegroundColor Red
    Write-Host ""
    exit 1
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backendProc = $null
$frontendProc = $null

if (-not $backendHealthy) {
    Install-WorkOsBackendRequirements -BackendDir $BackendDir
    $backendProc = Start-DetachedScript `
        -ScriptPath (Join-Path $PSScriptRoot "dev-backend.ps1") `
        -Title "backend" `
        -StdoutLog (Join-Path $LogDir "backend-$stamp.out.log") `
        -StderrLog (Join-Path $LogDir "backend-$stamp.err.log")
}

if (-not $frontendHealthy) {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Push-Location $FrontendDir
        try {
            npx --yes pnpm@8.10.0 install
        } finally {
            Pop-Location
        }
    }
    $frontendProc = Start-DetachedScript `
        -ScriptPath (Join-Path $PSScriptRoot "dev-frontend.ps1") `
        -Title "frontend" `
        -StdoutLog (Join-Path $LogDir "frontend-$stamp.out.log") `
        -StderrLog (Join-Path $LogDir "frontend-$stamp.err.log")
}

$state = [ordered]@{
    startedAt = (Get-Date).ToString("o")
    root = $Root
    backendPort = $BackendPort
    frontendPort = $FrontendPort
    backendLauncherPid = if ($backendProc) { $backendProc.Id } else { $null }
    frontendLauncherPid = if ($frontendProc) { $frontendProc.Id } else { $null }
    note = "Detached launchers. Stop only with Owner GO via stop-dev.ps1 - port-based."
}
$state | ConvertTo-Json | Set-Content -Path $StatePath -Encoding UTF8

if (-not $backendHealthy) {
    $backendOk = Wait-ForService -Name "Backend" -Probe { Test-HttpOk -Url $HealthUrl }
    if (-not $backendOk) {
        Write-Host "Backend did not become healthy. Check logs under $LogDir" -ForegroundColor Red
        exit 1
    }
}

if (-not $frontendHealthy) {
    $frontendOk = Wait-ForService -Name "Frontend" -Probe { Test-HttpOk -Url $FrontendUrl }
    if (-not $frontendOk) {
        Write-Host "Frontend did not become healthy. Check logs under $LogDir" -ForegroundColor Red
        Write-Host 'Backend was left running - detached. Owner may stop with .\scripts\stop-dev.ps1' -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "=== Detached stack READY ===" -ForegroundColor Green
Write-Host ('  Frontend = {0}' -f $FrontendUrl)
Write-Host ('  Backend  = {0}' -f $BackendUrl)
Write-Host ('  Health   = {0}' -f $HealthUrl)
Write-Host ('  Logs     = {0}' -f $LogDir)
Write-Host '  Survives Cursor/agent shell end. Owner stops manually with .\scripts\stop-dev.ps1'
Write-Host ""
exit 0
