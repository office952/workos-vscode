# Start WorkOS against the Atoms demo DB (detached FE+BE). Never uses dev.db.

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
$StatePath = Join-Path $Root ".workos-demo-detached.json"
$DemoDbPath = Join-Path $BackendDir "demo\workos_demo.db"
$Forbidden = Join-Path $BackendDir "dev.db"

if (-not (Test-Path $DemoDbPath)) {
    Write-Error "Demo DB missing. Run .\scripts\demo-bootstrap.ps1 first."
}

$demoResolved = [System.IO.Path]::GetFullPath($DemoDbPath)
$forbiddenResolved = [System.IO.Path]::GetFullPath($Forbidden)
if ($demoResolved -eq $forbiddenResolved) {
    Write-Error "Refusing start: demo path equals dev.db"
}

$DatabaseUrl = "sqlite+aiosqlite:///" + ($demoResolved -replace "\\", "/")
$LocalJwtSecret = "local-dev-secret-not-for-production"

function Test-HttpOk {
    param([string] $Url, [int] $TimeoutSec = 3)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    } catch { return $false }
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
    param([string] $Name, [scriptblock] $Probe, [int] $MaxAttempts = 60, [int] $DelaySec = 2)
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
    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath)
    $proc = Start-Process -FilePath $psExe `
        -ArgumentList $argList `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdoutLog `
        -RedirectStandardError $StderrLog `
        -PassThru
    Write-Host ('Started {0} as PID {1}' -f $Title, $proc.Id) -ForegroundColor DarkGray
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
$env:ALLOWED_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
$env:VITE_ENABLE_DEV_AUTH = "true"
$env:BACKEND_PORT = [string]$BackendPort
$env:VITE_PORT = [string]$FrontendPort
[void](Sync-WorkOsViteApiBaseUrl)

Write-Host ""
Write-Host "=== WorkOS DEMO detached stack ===" -ForegroundColor Cyan
Write-Host ("  Demo DB     = {0}" -f $demoResolved)
Write-Host ("  Backend URL = {0}" -f $BackendUrl)
Write-Host ("  Frontend    = {0}" -f $FrontendUrl)
Write-Host ""

if ($PreflightOnly) {
    Write-Host "Preflight OK" -ForegroundColor Green
    exit 0
}

$backendListener = Get-PortListener -Port $BackendPort
$frontendListener = Get-PortListener -Port $FrontendPort
$backendHealthy = Test-HttpOk -Url $HealthUrl
$frontendHealthy = Test-HttpOk -Url $FrontendUrl

function Test-DemoWorkspaceServed {
    try {
        $headers = @{ Authorization = "Bearer __DEV_BYPASS_TOKEN__" }
        $probeUrl = "$BackendUrl/api/v1/intake-v6/workspaces/$([uri]::EscapeDataString('d0e10001-0000-4000-8000-000000000001'))"
        $probe = Invoke-WebRequest -Uri $probeUrl -Headers $headers -UseBasicParsing -TimeoutSec 5
        return ($probe.StatusCode -ge 200 -and $probe.StatusCode -lt 300)
    } catch {
        return $false
    }
}

if ($backendHealthy) {
    # Prove the live API is the demo DB (not Owner backend/dev.db or a stale port).
    if (-not (Test-DemoWorkspaceServed)) {
        Write-Host ""
        Write-Host ("BLOCKER: :{0} is healthy but does not serve DEMO-INTAKE-LETTERS-001." -f $BackendPort) -ForegroundColor Red
        Write-Host "Likely Owner/local stack is on backend/dev.db, or a stale non-demo listener." -ForegroundColor Red
        Write-Host "Ask Owner to stop the Owner stack (opreste) if using :8000/:3000, or free the demo ports, then re-run." -ForegroundColor Red
        Write-Host ("Tip: isolated demo ports - `$env:BACKEND_PORT='8010'; `$env:VITE_PORT='3010'; `$env:VITE_API_BASE_URL='http://127.0.0.1:8010'") -ForegroundColor DarkGray
        Write-Host ""
        exit 2
    }
    if ($frontendHealthy) {
        Write-Host "Stack healthy and serves DEMO-INTAKE-LETTERS-001 - reusing." -ForegroundColor Green
        exit 0
    }
}

if ($backendListener -and -not $backendHealthy) {
    Write-Error "Port $BackendPort occupied but unhealthy - do not kill; Owner stop GO required."
}
if ($frontendListener -and -not $frontendHealthy) {
    Write-Error "Port $FrontendPort occupied but unhealthy - do not kill; Owner stop GO required."
}

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backendProc = $null
$frontendProc = $null

if (-not $backendHealthy) {
    $backendProc = Start-DetachedScript `
        -ScriptPath (Join-Path $PSScriptRoot "demo-backend.ps1") `
        -Title "demo-backend" `
        -StdoutLog (Join-Path $LogDir "demo-backend-$stamp.out.log") `
        -StderrLog (Join-Path $LogDir "demo-backend-$stamp.err.log")
}

if (-not $frontendHealthy) {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Push-Location $FrontendDir
        try { npx --yes pnpm@8.10.0 install } finally { Pop-Location }
    }
    $frontendProc = Start-DetachedScript `
        -ScriptPath (Join-Path $PSScriptRoot "dev-frontend.ps1") `
        -Title "frontend" `
        -StdoutLog (Join-Path $LogDir "demo-frontend-$stamp.out.log") `
        -StderrLog (Join-Path $LogDir "demo-frontend-$stamp.err.log")
}

$state = [ordered]@{
    startedAt = (Get-Date).ToString("o")
    mode = "atoms_demo"
    demoDb = $demoResolved
    backendPort = $BackendPort
    frontendPort = $FrontendPort
    backendLauncherPid = if ($backendProc) { $backendProc.Id } else { $null }
    frontendLauncherPid = if ($frontendProc) { $frontendProc.Id } else { $null }
}
$state | ConvertTo-Json | Set-Content -Path $StatePath -Encoding UTF8

if (-not $backendHealthy) {
    if (-not (Wait-ForService -Name "Demo Backend" -Probe { Test-HttpOk -Url $HealthUrl })) {
        Write-Error "Demo backend did not become healthy. Check logs under $LogDir"
    }
}
if (-not $frontendHealthy) {
    if (-not (Wait-ForService -Name "Frontend" -Probe { Test-HttpOk -Url $FrontendUrl })) {
        Write-Error "Frontend did not become healthy. Check logs under $LogDir"
    }
}

Write-Host ""
Write-Host "=== Demo stack READY ===" -ForegroundColor Green
Write-Host ("  Frontend = {0}" -f $FrontendUrl)
Write-Host ("  Backend  = {0}" -f $BackendUrl)
Write-Host ("  Demo DB  = {0}" -f $demoResolved)
Write-Host "  Auth     = development bypass (VITE_ENABLE_DEV_AUTH / __DEV_BYPASS_TOKEN__)"
Write-Host ""
exit 0
