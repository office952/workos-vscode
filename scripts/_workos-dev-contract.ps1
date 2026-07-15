# WorkOS local development port contract (canonical source stack).
# Dot-source from dev.ps1, start-dev.ps1, dev-backend.ps1, dev-frontend.ps1

$script:WorkOsDefaultBackendPort = 8001
$script:WorkOsDefaultFrontendPort = 3000
$script:WorkOsDefaultBackendHost = '127.0.0.1'

function Initialize-WorkOsDevPortContract {
    if (-not $env:BACKEND_PORT) {
        $env:BACKEND_PORT = [string]$script:WorkOsDefaultBackendPort
    }
    if (-not $env:VITE_PORT) {
        $env:VITE_PORT = [string]$script:WorkOsDefaultFrontendPort
    }
}

function Get-WorkOsBackendPort {
    Initialize-WorkOsDevPortContract
    return [int]$env:BACKEND_PORT
}

function Get-WorkOsFrontendPort {
    Initialize-WorkOsDevPortContract
    return [int]$env:VITE_PORT
}

function Get-WorkOsBackendUrl {
    $port = Get-WorkOsBackendPort
    return "http://$($script:WorkOsDefaultBackendHost):$port"
}

function Get-WorkOsFrontendUrl {
    $port = Get-WorkOsFrontendPort
    return "http://$($script:WorkOsDefaultBackendHost):$port"
}

function Get-WorkOsViteProxyTarget {
    $port = Get-WorkOsBackendPort
    return "http://$($script:WorkOsDefaultBackendHost):$port"
}

function Clear-WorkOsParityEnv {
    $names = @(
        'PARITY_OBSERVE_ENABLED',
        'COMPETENCE_PARITY_ENABLED',
        'AUTHORIZATION_PARITY_ENABLED',
        'WORKCENTER_PARITY_ENABLED',
        'RESOURCE_PARITY_ENABLED',
        'ELIGIBILITY_PARITY_ENABLED',
        'EXECUTION_SURFACE_PARITY_ENABLED'
    )
    foreach ($name in $names) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
}

function Get-WorkOsProcessCommandLine {
    param([int] $ProcessId)
    if ($ProcessId -le 0) { return $null }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }
    return $proc.CommandLine
}

function Test-WorkOsBackendListenerCanonical {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsBackendPort)
    )
    $cmd = Get-WorkOsProcessCommandLine -ProcessId $ProcessId
    if (-not $cmd) { return $false }
    $rootNorm = ($ProjectRoot -replace '\\', '/').ToLowerInvariant()
    $cmdLower = $cmd.ToLowerInvariant()
    if ($cmdLower -notmatch 'uvicorn') { return $false }
    if ($cmdLower -notmatch "--port\s+$ExpectedPort\b") { return $false }
    if ($cmdLower -notmatch [regex]::Escape($rootNorm)) { return $false }
    return $true
}

function Test-WorkOsFrontendListenerCanonical {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsFrontendPort)
    )
    $cmd = Get-WorkOsProcessCommandLine -ProcessId $ProcessId
    if (-not $cmd) { return $false }
    $rootNorm = ($ProjectRoot -replace '\\', '/').ToLowerInvariant()
    $cmdLower = $cmd.ToLowerInvariant()
    if ($cmdLower -notmatch 'vite') { return $false }
    if ($cmdLower -notmatch "--port\s+$ExpectedPort\b") { return $false }
    if ($cmdLower -notmatch 'frontend') { return $false }
    return $true
}

function Test-WorkOsBackendListenerStale {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsBackendPort)
    )
    $cmd = Get-WorkOsProcessCommandLine -ProcessId $ProcessId
    if (-not $cmd) { return $true }
    if (Test-WorkOsBackendListenerCanonical -ProcessId $ProcessId -ProjectRoot $ProjectRoot -ExpectedPort $ExpectedPort) {
        return $false
    }
    return ($cmd -match 'uvicorn')
}

function Test-WorkOsFrontendListenerStale {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsFrontendPort)
    )
    $cmd = Get-WorkOsProcessCommandLine -ProcessId $ProcessId
    if (-not $cmd) { return $true }
    if (Test-WorkOsFrontendListenerCanonical -ProcessId $ProcessId -ProjectRoot $ProjectRoot -ExpectedPort $ExpectedPort) {
        return $false
    }
    return ($cmd -match 'vite')
}
