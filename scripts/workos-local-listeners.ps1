# Inventory local WorkOS listeners and probe identity/compatibility.
# Does NOT stop any process. Windows PowerShell helper.
# Usage: npm run diag:local-listeners

$ErrorActionPreference = "Continue"
. "$PSScriptRoot\_workos-dev-contract.ps1"

$Root = Split-Path -Parent $PSScriptRoot
Initialize-WorkOsDevPortContract

$ports = @(3000, 8000, 8001, 8002)
Write-Host "=== WorkOS local listeners (read-only) ===" -ForegroundColor Cyan
Write-Host ("  Repo root        = {0}" -f $Root)
Write-Host ("  Configured BE    = {0}" -f (Get-WorkOsBackendUrl))
Write-Host ("  VITE_API_BASE_URL= {0}" -f ($(if ($env:VITE_API_BASE_URL) { $env:VITE_API_BASE_URL } else { "(unset)" })))
Write-Host ""

function Get-ListenerRows {
    param([int[]] $Ports)
    $rows = @()
    foreach ($port in $Ports) {
        $lines = netstat -ano | Select-String -Pattern "LISTENING" | Select-String -Pattern ":$port\s"
        foreach ($line in $lines) {
            if ($line -match '\s+(\d+)\s*$') {
                $processId = [int]$Matches[1]
                $cmd = Get-WorkOsProcessCommandLine -ProcessId $processId
                $rows += [pscustomobject]@{
                    Port = $port
                    Pid  = $processId
                    Cmd  = $(if ($cmd) { $cmd } else { "(command unavailable - elevated/ghost?)" })
                }
            }
        }
    }
    return $rows
}

$listeners = Get-ListenerRows -Ports $ports
if (-not $listeners.Count) {
    Write-Host "No listeners on 3000/8000/8001/8002." -ForegroundColor Yellow
} else {
    $listeners | Format-Table -AutoSize Port, Pid, Cmd
}

Write-Host "=== Backend probes ===" -ForegroundColor Cyan
foreach ($port in @(8000, 8001, 8002)) {
    $base = "http://127.0.0.1:$port"
    $hasListener = $listeners | Where-Object { $_.Port -eq $port }
    if (-not $hasListener) {
        Write-Host ("  {0}  (no listener)" -f $base) -ForegroundColor DarkGray
        continue
    }
    try {
        $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 3
        $compatStatus = $null
        $compatBody = $null
        try {
            $compatResp = Invoke-WebRequest -Uri "$base/api/v1/system/local-compatibility" -TimeoutSec 3 -UseBasicParsing
            $compatStatus = [int]$compatResp.StatusCode
            $compatBody = $compatResp.Content | ConvertFrom-Json
        } catch {
            if ($_.Exception.Response) {
                $compatStatus = [int]$_.Exception.Response.StatusCode
            } else {
                $compatStatus = "error"
            }
        }
        $openapi = Invoke-RestMethod -Uri "$base/openapi.json" -TimeoutSec 8
        $props = @()
        if ($openapi.components.schemas.IntakeV4FinishSetup.properties) {
            $props = @($openapi.components.schemas.IntakeV4FinishSetup.properties.PSObject.Properties.Name)
        }
        $compatLabel = if ($compatStatus -eq 200 -and $compatBody.service -eq "workos-backend") {
            "COMPATIBLE"
        } elseif ($compatStatus -eq 404) {
            "STALE/INCOMPATIBLE (no local-compatibility)"
        } else {
            "CHECK ($compatStatus)"
        }
        Write-Host ("  {0}" -f $base)
        Write-Host ("    health              = {0}" -f $health.status)
        Write-Host ("    local-compatibility = {0}" -f $compatLabel)
        Write-Host ("    FinishSetup props   = {0} (segmented_background={1})" -f $props.Count, ($props -contains "segmented_background"))
        if ($compatBody.git_commit) {
            Write-Host ("    git_commit          = {0}" -f $compatBody.git_commit)
        }
    } catch {
        Write-Host ("  {0}  PROBE_FAIL: {1}" -f $base, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "No processes were stopped. To free a port, stop the listed PID manually after confirming ownership." -ForegroundColor DarkGray
