# WorkOS local dev (Windows) - LOCAL ONLY defaults; do not use for staging/production deploy.
# Requires: Node.js 20+, Python 3.11+ on PATH, pnpm (or use npx pnpm@8.10.0)
#
# Idempotent startup:
#   - Detects port 8001 / 3000 occupancy before launching
#   - Reuses processes that already serve WorkOS health endpoints
#   - Refuses to start when ports are held by unknown/unhealthy processes
#   - Waits for backend /health and frontend before reporting ready

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"
. "$PSScriptRoot\_workos-dev-backend-freshness.ps1"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$DevDbPath = Join-Path $BackendDir "dev.db"
$DatabaseUrl = "sqlite+aiosqlite:///" + ($DevDbPath -replace "\\", "/")

$LocalJwtSecret = "local-dev-secret-not-for-production"
$ProductSystemPath = "/product-system"
$PricingPath = "/inventory/pricing"

function Set-WorkOsLocalDevEnv {
    param([string] $ProjectRoot)
    Initialize-WorkOsDevPortContract
    Clear-WorkOsParityEnv
    $env:APP_ENV = "development"
    $env:ENVIRONMENT = "development"
    Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
    $env:DATABASE_URL = $DatabaseUrl
    Set-WorkOsJwtEnv
    $env:DEBUG = "true"
    $env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
    $env:VITE_ENABLE_DEV_AUTH = "true"
    $env:BACKEND_PORT = [string](Get-WorkOsBackendPort)
    [void](Sync-WorkOsViteApiBaseUrl)
}

function Show-WorkOsLocalDevSummary {
    $backendUrl = Get-WorkOsBackendUrl
    $frontendUrl = Get-WorkOsFrontendUrl
    Write-Host ""
    Write-Host "=== Local dev configuration (safe summary) ===" -ForegroundColor Cyan
    Write-Host ("  APP_ENV                  = {0}" -f $env:APP_ENV)
    Write-Host ("  ENVIRONMENT              = {0}" -f $env:ENVIRONMENT)
    Write-Host "  DEPLOYMENT_ENVIRONMENT   = (unset)"
    Write-Host "  DATABASE_URL             = sqlite+aiosqlite:///<backend>/dev.db"
    Write-Host "  JWT_SECRET_KEY           = [local placeholder, not for deploy]"
    Write-Host ("  JWT_ALGORITHM            = {0}" -f $env:JWT_ALGORITHM)
    Write-Host ("  JWT_EXPIRE_MINUTES       = {0}" -f $env:JWT_EXPIRE_MINUTES)
    Write-Host ("  DEBUG                    = {0}" -f $env:DEBUG)
    Write-Host ("  VITE_ENABLE_DEV_AUTH     = {0}" -f $env:VITE_ENABLE_DEV_AUTH)
    Write-Host ("  BACKEND_PORT             = {0}" -f $env:BACKEND_PORT)
    Write-Host ("  VITE_API_BASE_URL        = {0}" -f $env:VITE_API_BASE_URL)
    Write-Host ("  Vite proxy (/api)        = {0}" -f (Get-WorkOsViteProxyTarget))
    Write-Host ("  Backend                  = {0}" -f $backendUrl)
    Write-Host ("  Frontend                 = {0}" -f $frontendUrl)
    Write-Host ("  Health                   = {0}/health" -f $backendUrl)
    Write-Host ("  Local compat             = {0}/api/v1/system/local-compatibility" -f $backendUrl)
    Write-Host ("  ProductSystem            = {0}{1}" -f $frontendUrl, $ProductSystemPath)
    Write-Host ("  Pricing                  = {0}{1}" -f $frontendUrl, $PricingPath)
    Write-Host ""
}

function Require-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Missing required command: $name. Install it and ensure it is on PATH."
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

function Wait-ForService {
    param(
        [string] $Name,
        [scriptblock] $Probe,
        [int] $MaxAttempts = 45,
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

function Show-FinalStatus {
    param(
        [bool] $BackendReady,
        [bool] $FrontendReady,
        [bool] $ProductSystemReady,
        [bool] $PricingReady
    )
    Write-Host ""
    Write-Host "=== WorkOS dev stack status ===" -ForegroundColor Cyan
    Write-Host ("  Backend /health     : {0}" -f ($(if ($BackendReady) { "READY" } else { "NOT READY" })))
    Write-Host ("  Frontend            : {0}" -f ($(if ($FrontendReady) { "READY" } else { "NOT READY" })))
    Write-Host ("  ProductSystem       : {0}" -f ($(if ($ProductSystemReady) { "REACHABLE" } else { "NOT REACHABLE" })))
    Write-Host ("  Pricing             : {0}" -f ($(if ($PricingReady) { "REACHABLE" } else { "NOT REACHABLE" })))
    Write-Host ""
}

function Test-IntakeV3OperatorWorkspaceRoutesOk {
    param(
        [string] $BaseUrl = $(Get-WorkOsBackendUrl),
        [string] $ProjectRoot = $(Split-Path -Parent $PSScriptRoot)
    )
    $evaluation = Test-WorkOsBackendDevReadyEvaluation -ProjectRoot $ProjectRoot -ScriptsRoot $PSScriptRoot
    return $evaluation.Ready
}

function Write-BackendDevReadyDiagnostics {
    param(
        [string] $BaseUrl = $(Get-WorkOsBackendUrl),
        [string] $ProjectRoot = $(Split-Path -Parent $PSScriptRoot)
    )

    $evaluation = Test-WorkOsBackendDevReadyEvaluation -ProjectRoot $ProjectRoot -ScriptsRoot $PSScriptRoot
    Write-WorkOsBackendFreshnessDiagnostics -Evaluation $evaluation
}

function Test-BackendDevReady {
    param([string] $ProjectRoot = $(Split-Path -Parent $PSScriptRoot))
    return (Test-WorkOsBackendDevReady -ProjectRoot $ProjectRoot -ScriptsRoot $PSScriptRoot)
}

function Resolve-WorkOsBackendPortService {
    param(
        [int] $Port,
        [string] $ProjectRoot
    )

    $evaluation = Get-WorkOsBackendFreshnessClassification -ProjectRoot $ProjectRoot -Port $Port -ScriptsRoot $PSScriptRoot

    if ($evaluation.Classification -eq "backend_absent") {
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $false
            Ready = $false
            Listener = $null
            Freshness = $evaluation
        }
    }

    if ($evaluation.Ready) {
        $listenerPid = if ($evaluation.Listeners.Count -gt 0) { $evaluation.Listeners[0].OwningProcess } else { 0 }
        Write-Host "Backend already running on port $Port (freshness=$($evaluation.Classification), PID=$listenerPid)" -ForegroundColor DarkGray
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $true
            Ready = $true
            Listener = [PSCustomObject]@{
                Port = $Port
                PID = $listenerPid
                ProcessName = "uvicorn"
            }
            Freshness = $evaluation
        }
    }

    if ($evaluation.RecommendedAction -eq "controlled_stop") {
        Write-Host ""
        Write-Host "Backend on port $Port failed freshness guard ($($evaluation.Classification))." -ForegroundColor Yellow
        Write-WorkOsBackendFreshnessDiagnostics -Evaluation $evaluation
        $tree = Get-WorkOsBackendProcessTreeSnapshot -Port $Port -ProjectRoot $ProjectRoot -ExpectedPort $Port
        $stopIds = if ($evaluation.StopProcessIds.Count -gt 0) { $evaluation.StopProcessIds } else { @(Get-WorkOsBackendStopTargetProcessIds -Tree $tree) }
        Write-Host "  Action       = Controlled stop of same-worktree stale backend process tree"
        Write-Host ("  Stop targets = {0}" -f ($stopIds -join ", "))
        Write-Host ""
        $stopResult = Stop-WorkOsBackendProcessTreeControlled -Tree $tree -ProcessIds $stopIds -Port $Port
        if (-not $stopResult.PortReleased) {
            Write-Host ""
            Write-Host "BLOCKER: Port $Port remained occupied after controlled stale-backend stop." -ForegroundColor Red
            foreach ($remaining in @($stopResult.RemainingListeners)) {
                Write-Host ("  Remaining PID = {0} alive={1}" -f $remaining.OwningProcess, $remaining.ProcessAlive)
            }
            Write-Host "  Action       = Stop remaining listeners manually, then re-run .\scripts\start-dev.ps1" -ForegroundColor Red
            Write-Host ""
            exit 1
        }
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $false
            Ready = $false
            Listener = $null
            Freshness = $evaluation
        }
    }

    Write-Host ""
    Write-Host "BLOCKER: Port $Port backend failed freshness guard ($($evaluation.Classification))." -ForegroundColor Red
    Write-WorkOsBackendFreshnessDiagnostics -Evaluation $evaluation
    Write-Host "  Action       = Resolve the reported process ownership manually; foreign/other-worktree processes are never stopped automatically." -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Resolve-PortService {
    param(
        [int] $Port,
        [string] $ServiceName,
        [scriptblock] $HealthProbe,
        [string] $ProjectRoot
    )
    $listener = Get-PortListener -Port $Port
    if (-not $listener) {
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $false
            Ready = $false
            Listener = $null
        }
    }
    $ready = & $HealthProbe
    if ($ready) {
        Write-Host "$ServiceName already running on port $Port (PID=$($listener.PID), $($listener.ProcessName))" -ForegroundColor DarkGray
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $true
            Ready = $true
            Listener = $listener
        }
    }

    $isStale = $false
    if ($ServiceName -eq "Backend") {
        $isStale = Test-WorkOsBackendListenerStale -ProcessId $listener.PID -ProjectRoot $ProjectRoot -ExpectedPort $Port
    } elseif ($ServiceName -eq "Frontend") {
        $isStale = Test-WorkOsFrontendListenerStale -ProcessId $listener.PID -ProjectRoot $ProjectRoot -ExpectedPort $Port
    }

    if ($isStale) {
        Write-Host ""
        Write-Host "$ServiceName on port $Port is occupied by a stale WorkOS listener." -ForegroundColor Yellow
        Write-Host ("  PID          = {0}" -f $listener.PID)
        Write-Host ("  Process      = {0}" -f $listener.ProcessName)
        Write-Host "  Action       = Stopping stale listener so canonical stack can start."
        Write-Host ""
        Stop-Process -Id $listener.PID -Force -ErrorAction SilentlyContinue
        foreach ($i in 1..20) {
            Start-Sleep -Milliseconds 250
            if (-not (Get-PortListener -Port $Port)) {
                break
            }
        }
        if (Get-PortListener -Port $Port) {
            Write-Host ""
            Write-Host "BLOCKER: Port $Port remained occupied after stopping stale $ServiceName." -ForegroundColor Red
            Write-Host "  Action       = Stop the remaining listener manually, then re-run .\scripts\start-dev.ps1" -ForegroundColor Red
            Write-Host ""
            exit 1
        }
        return [PSCustomObject]@{
            Port = $Port
            Occupied = $false
            Ready = $false
            Listener = $null
        }
    }

    Write-Host ""
    Write-Host "BLOCKER: Port $Port is occupied but $ServiceName is not healthy and process could not be classified as stale WorkOS." -ForegroundColor Red
    Write-Host ("  PID          = {0}" -f $listener.PID)
    Write-Host ("  Process      = {0}" -f $listener.ProcessName)
    Write-Host ("  CommandLine  = {0}" -f (Get-WorkOsProcessCommandLine -ProcessId $listener.PID))
    Write-Host "  Action       = Stop that process manually, then re-run .\scripts\start-dev.ps1"
    Write-Host ""
    exit 1
}

. "$PSScriptRoot\_workos-python.ps1"

Set-WorkOsLocalDevEnv -ProjectRoot $Root
Require-Command node

Write-Host "=== WorkOS dev ===" -ForegroundColor Cyan
Write-Host "Root: $Root"
Show-WorkOsLocalDevSummary

$BackendPort = Get-WorkOsBackendPort
$FrontendPort = Get-WorkOsFrontendPort
$BackendUrl = Get-WorkOsBackendUrl
$FrontendUrl = Get-WorkOsFrontendUrl
$HealthUrl = "$BackendUrl/health"
$ProductSystemUrl = "$FrontendUrl$ProductSystemPath"
$PricingUrl = "$FrontendUrl$PricingPath"

$backendState = Resolve-WorkOsBackendPortService -Port $BackendPort -ProjectRoot $Root
$frontendState = Resolve-PortService -Port $FrontendPort -ServiceName "Frontend" -HealthProbe { Test-HttpOk -Url $FrontendUrl } -ProjectRoot $Root

$PSNativeCommandUseErrorActionPreference = $false

$ProgressPreference = "SilentlyContinue"

function Get-JobTail {
    param(
        [Parameter(Mandatory = $true)] $Job,
        [int] $Last = 40
    )
    try {
        $output = @(Receive-Job $Job -Keep -ErrorAction Continue 2>&1)
        if ($output.Count -gt 0) {
            $output | Select-Object -Last $Last
        }
    } catch {
        Write-Host ("(failed to receive job output: {0})" -f $_) -ForegroundColor DarkGray
    }
}

$backendJob = $null
if (-not $backendState.Ready) {
    $BackendVenvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir
    Install-WorkOsBackendRequirements -BackendDir $BackendDir

    $backendJob = Start-Job -ScriptBlock {
        param($BackendDir, $DatabaseUrl, $LocalJwtSecret, $AllowedOrigins, $BackendPort)
        Set-Location $BackendDir
        $env:APP_ENV = "development"
        $env:ENVIRONMENT = "development"
        Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
        $env:DATABASE_URL = $DatabaseUrl
        $env:JWT_SECRET_KEY = $LocalJwtSecret
        $env:JWT_ALGORITHM = "HS256"
        $env:JWT_EXPIRE_MINUTES = "60"
        $env:DEBUG = "true"
        $env:ALLOWED_ORIGINS = $AllowedOrigins
        & .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --reload 2>&1
    } -ArgumentList $BackendDir, $DatabaseUrl, $LocalJwtSecret, $env:ALLOWED_ORIGINS, $BackendPort

    Write-Host "Backend job started (id=$($backendJob.Id)). Waiting for backend freshness..." -ForegroundColor DarkGray
    $backendReady = Wait-ForService -Name "Backend" -Probe { Test-BackendDevReady -ProjectRoot $Root }
    if (-not $backendReady) {
        Write-Host "Backend health check did not pass - recent job output:" -ForegroundColor Yellow
        Write-BackendDevReadyDiagnostics -BaseUrl $BackendUrl -ProjectRoot $Root
        Get-JobTail -Job $backendJob -Last 40
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    $backendReady = $true
}

if ($backendState.Ready -and $frontendState.Ready) {
    $productSystemReady = Test-HttpOk -Url $ProductSystemUrl -TimeoutSec 5
    $pricingReady = Test-HttpOk -Url $PricingUrl -TimeoutSec 5
    Show-FinalStatus -BackendReady $true -FrontendReady $true -ProductSystemReady $productSystemReady -PricingReady $pricingReady
    Write-Host "All services already running - no duplicate processes started." -ForegroundColor Green
    exit 0
}

if ($frontendState.Ready) {
    $productSystemReady = Test-HttpOk -Url $ProductSystemUrl -TimeoutSec 5
    $pricingReady = Test-HttpOk -Url $PricingUrl -TimeoutSec 5
    Show-FinalStatus -BackendReady $backendReady -FrontendReady $true -ProductSystemReady $productSystemReady -PricingReady $pricingReady
    Write-Host "Frontend was already running. Backend started or reused. Exiting without duplicate frontend." -ForegroundColor Green
    if ($backendJob) {
        Write-Host "Backend job id=$($backendJob.Id) continues in background." -ForegroundColor DarkGray
    }
    exit 0
}

Set-Location $FrontendDir
if (-not (Test-Path "node_modules")) {
    npx --yes pnpm@8.10.0 install
}
Write-Host "Starting frontend (Ctrl+C stops frontend; backend job will be stopped if started here)..." -ForegroundColor Green

$viteApiBaseForJob = Sync-WorkOsViteApiBaseUrl
$frontendJob = Start-Job -ScriptBlock {
    param($FrontendDir, $BackendPort, $FrontendPort, $ViteApiBaseUrl)
    Set-Location $FrontendDir
    $env:BACKEND_PORT = [string]$BackendPort
    $env:VITE_ENABLE_DEV_AUTH = "true"
    if ($ViteApiBaseUrl) {
        $env:VITE_API_BASE_URL = [string]$ViteApiBaseUrl
    }
    npx --yes pnpm@8.10.0 run dev --host 127.0.0.1 --port $FrontendPort
} -ArgumentList $FrontendDir, $BackendPort, $FrontendPort, $viteApiBaseForJob

$frontendReady = Wait-ForService -Name "Frontend" -Probe { Test-HttpOk -Url $FrontendUrl }
if (-not $frontendReady) {
    Write-Host "Frontend did not become reachable on $FrontendUrl" -ForegroundColor Red
    Receive-Job $frontendJob -Keep | Select-Object -Last 30
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    exit 1
}

$productSystemReady = Test-HttpOk -Url $ProductSystemUrl -TimeoutSec 5
$pricingReady = Test-HttpOk -Url $PricingUrl -TimeoutSec 5
Show-FinalStatus -BackendReady $backendReady -FrontendReady $frontendReady -ProductSystemReady $productSystemReady -PricingReady $pricingReady

Write-Host "Streaming frontend logs (Ctrl+C stops frontend + backend job if started here)..." -ForegroundColor DarkGray
try {
    while ($true) {
        # Same stderr-handling rule as backend: do not treat normal native output as terminating errors.
        Receive-Job $frontendJob -Keep -ErrorAction Continue 2>&1 | ForEach-Object { Write-Host $_ }
        if ($frontendJob.State -eq "Completed" -or $frontendJob.State -eq "Failed") {
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
}
