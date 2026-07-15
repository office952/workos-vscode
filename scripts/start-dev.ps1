# WorkOS local dev (Windows) - LOCAL ONLY defaults; do not use for staging/production deploy.
# Requires: Node.js 20+, Python 3.11+ on PATH, pnpm (or use npx pnpm@8.10.0)
#
# Idempotent startup:
#   - Detects port 8000 / 3000 occupancy before launching
#   - Reuses processes that already serve WorkOS health endpoints
#   - Refuses to start when ports are held by unknown/unhealthy processes
#   - Waits for backend /health and frontend before reporting ready

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$DevDbPath = Join-Path $BackendDir "dev.db"
$DatabaseUrl = "sqlite+aiosqlite:///" + ($DevDbPath -replace "\\", "/")

$LocalJwtSecret = "local-dev-secret-not-for-production"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:3000"
$HealthUrl = "$BackendUrl/health"
$ProductSystemUrl = "$FrontendUrl/product-system"
$PricingUrl = "$FrontendUrl/inventory/pricing"

function Set-WorkOsLocalDevEnv {
    param([string] $ProjectRoot)
    $env:APP_ENV = "development"
    $env:ENVIRONMENT = "development"
    Remove-Item Env:DEPLOYMENT_ENVIRONMENT -ErrorAction SilentlyContinue
    $env:DATABASE_URL = $DatabaseUrl
    Set-WorkOsJwtEnv
    $env:DEBUG = "true"
    $env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
    $env:VITE_ENABLE_DEV_AUTH = "true"
}

function Show-WorkOsLocalDevSummary {
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
    Write-Host "  Backend                  = $BackendUrl"
    Write-Host "  Frontend                 = $FrontendUrl"
    Write-Host "  Health                   = $HealthUrl"
    Write-Host "  ProductSystem            = $ProductSystemUrl"
    Write-Host "  Pricing                  = $PricingUrl"
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
    param([string] $BaseUrl = $BackendUrl)
    $required = @()
    try {
        $schema = Invoke-RestMethod -Uri "$BaseUrl/openapi.json" -TimeoutSec 5
        $paths = @($schema.paths.PSObject.Properties | ForEach-Object { $_.Name })
        foreach ($path in $required) {
            if ($paths -notcontains $path) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

function Write-BackendDevReadyDiagnostics {
    param([string] $BaseUrl = $BackendUrl)

    $healthOk = Test-HttpOk -Url $HealthUrl
    $openapiUrl = "$BaseUrl/openapi.json"
    $required = @()

    Write-Host ""
    Write-Host "=== Backend dev readiness diagnostics (no semantics change) ===" -ForegroundColor Yellow
    Write-Host ("  health_ok     = {0}" -f $healthOk)
    Write-Host ("  health_url    = {0}" -f $HealthUrl)
    Write-Host ("  openapi_url   = {0}" -f $openapiUrl)

    try {
        $schema = Invoke-RestMethod -Uri $openapiUrl -TimeoutSec 5
        $paths = @($schema.paths.PSObject.Properties | ForEach-Object { $_.Name })
        $missing = @($required | Where-Object { $paths -notcontains $_ })
        if ($missing.Count -eq 0) {
            Write-Host "  openapi_parse = ok"
            Write-Host "  missing_paths = (none)"
        } else {
            Write-Host "  openapi_parse = ok"
            Write-Host ("  missing_paths = {0}" -f ($missing -join ", "))
        }
    } catch {
        Write-Host ("  openapi_parse = failed: {0}" -f $_.Exception.Message)
        Write-Host "  missing_paths = (unknown - OpenAPI fetch/parse failed)"
    }
    Write-Host ""
}

function Test-BackendDevReady {
    if (-not (Test-HttpOk -Url $HealthUrl)) {
        return $false
    }
    return (Test-IntakeV3OperatorWorkspaceRoutesOk)
}

function Resolve-PortService {
    param(
        [int] $Port,
        [string] $ServiceName,
        [scriptblock] $HealthProbe
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
    if (-not $ready) {
        if ($listener -and $ServiceName -eq "Backend" -and (Test-HttpOk -Url $HealthUrl)) {
            Write-Host ""
            Write-Host "Backend on port $Port responds to /health but is missing Intake V3 operator routes (stale process)." -ForegroundColor Yellow
            Write-BackendDevReadyDiagnostics -BaseUrl $BackendUrl
            Write-Host ("  PID          = {0}" -f $listener.PID)
            Write-Host ("  Process      = {0}" -f $listener.ProcessName)
            Write-Host "  Action       = Stopping stale backend so current code can start."
            Write-Host ""
            Stop-Process -Id $listener.PID -Force -ErrorAction SilentlyContinue
            # Wait for the port to actually be released.
            foreach ($i in 1..20) {
                Start-Sleep -Milliseconds 250
                if (-not (Get-PortListener -Port $Port)) {
                    break
                }
            }
            if (Get-PortListener -Port $Port) {
                Write-Host ""
                Write-Host "BLOCKER: Port $Port remained occupied after stopping stale backend." -ForegroundColor Red
                Write-Host "  Action       = Stop the remaining listener manually, then re-run .\\scripts\\start-dev.ps1" -ForegroundColor Red
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
        Write-Host "BLOCKER: Port $Port is occupied but $ServiceName is not healthy." -ForegroundColor Red
        Write-Host ("  PID          = {0}" -f $listener.PID)
        Write-Host ("  Process      = {0}" -f $listener.ProcessName)
        Write-Host "  Action       = Stop that process manually, then re-run .\scripts\start-dev.ps1"
        Write-Host ""
        exit 1
    }
    Write-Host "$ServiceName already running on port $Port (PID=$($listener.PID), $($listener.ProcessName))" -ForegroundColor DarkGray
    return [PSCustomObject]@{
        Port = $Port
        Occupied = $true
        Ready = $true
        Listener = $listener
    }
}

. "$PSScriptRoot\_workos-python.ps1"

Set-WorkOsLocalDevEnv -ProjectRoot $Root
Require-Command node

Write-Host "=== WorkOS dev ===" -ForegroundColor Cyan
Write-Host "Root: $Root"
Show-WorkOsLocalDevSummary

$backendState = Resolve-PortService -Port 8000 -ServiceName "Backend" -HealthProbe { Test-BackendDevReady }
$frontendState = Resolve-PortService -Port 3000 -ServiceName "Frontend" -HealthProbe { Test-HttpOk -Url $FrontendUrl }

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
        param($BackendDir, $DatabaseUrl, $LocalJwtSecret, $AllowedOrigins)
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
        # Uvicorn logs to stderr by default; merge streams so callers don't treat normal INFO as NativeCommandError.
        & .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload 2>&1
    } -ArgumentList $BackendDir, $DatabaseUrl, $LocalJwtSecret, $env:ALLOWED_ORIGINS

    Write-Host "Backend job started (id=$($backendJob.Id)). Waiting for /health..." -ForegroundColor DarkGray
    $backendReady = Wait-ForService -Name "Backend" -Probe { Test-BackendDevReady }
    if (-not $backendReady) {
        Write-Host "Backend health check did not pass - recent job output:" -ForegroundColor Yellow
        Write-BackendDevReadyDiagnostics -BaseUrl $BackendUrl
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

$frontendJob = Start-Job -ScriptBlock {
    param($FrontendDir)
    Set-Location $FrontendDir
    npx --yes pnpm@8.10.0 run dev --host 127.0.0.1 --port 3000
} -ArgumentList $FrontendDir

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
