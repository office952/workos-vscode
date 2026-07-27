# Stop WorkOS local listeners on canonical ports (:8000 backend, :3000 frontend).
#
# OWNER GATE — agents may run this ONLY when the Owner explicitly says
# "oprește" / "stop server" / "kill stack" / "restart" (or clear equivalent).
# Starting the app is NEVER a reason to run this script.
#
# Usage (Owner or agent-with-explicit-GO only):
#   .\scripts\stop-dev.ps1
#   .\scripts\stop-dev.ps1 -WhatIf

param(
    [switch] $WhatIf
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-dev-contract.ps1"

Initialize-WorkOsDevPortContract
$BackendPort = Get-WorkOsBackendPort
$FrontendPort = Get-WorkOsFrontendPort
$Root = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $Root ".workos-dev-detached.json"

Write-Host ""
Write-Host '=== WorkOS stop-dev - Owner-gated ===' -ForegroundColor Yellow
Write-Host '  Agents: run only after explicit Owner stop/kill/restart request.'
Write-Host ('  Targets = listeners on :{0} backend and :{1} frontend' -f $BackendPort, $FrontendPort)
Write-Host ""

function Get-ListenPids {
    param([int] $Port)
    $conns = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    $pids = @($conns | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique)
    return $pids
}

function Stop-PortListeners {
    param([int] $Port)
    $pids = @(Get-ListenPids -Port $Port)
    if ($pids.Count -eq 0) {
        Write-Host ('  :{0} - no Listen process' -f $Port) -ForegroundColor DarkGray
        return
    }
    foreach ($procId in $pids) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.ProcessName } else { "unknown" }
        if ($WhatIf) {
            Write-Host ("  WhatIf: would Stop-Process -Id {0} ({1}) on :{2}" -f $procId, $name, $Port) -ForegroundColor Cyan
            continue
        }
        Write-Host ("  Stopping PID {0} ({1}) on :{2}" -f $procId, $name, $Port) -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}

Stop-PortListeners -Port $FrontendPort
Stop-PortListeners -Port $BackendPort

if (-not $WhatIf) {
    foreach ($port in @($FrontendPort, $BackendPort)) {
        foreach ($i in 1..20) {
            if (@(Get-ListenPids -Port $port).Count -eq 0) { break }
            Start-Sleep -Milliseconds 250
        }
        $left = @(Get-ListenPids -Port $port)
        if ($left.Count -gt 0) {
            Write-Host ("  WARN: :{0} still has Listen PID(s): {1}" -f $port, ($left -join ", ")) -ForegroundColor Red
        } else {
            Write-Host ("  :{0} released" -f $port) -ForegroundColor Green
        }
    }
    if (Test-Path $StatePath) {
        Remove-Item $StatePath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host 'Done. Start again with .\scripts\dev-detached.ps1 for agents, or .\scripts\dev.ps1 for Owner interactive.' -ForegroundColor DarkGray
Write-Host ""
