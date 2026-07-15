# WorkOS canonical backend freshness guard (RUNTIME-FRESHNESS-04A).
# Dot-source from start-dev.ps1 after _workos-dev-contract.ps1

$script:WorkOsFreshnessDefaultOpenApiRetries = 3
$script:WorkOsFreshnessDefaultOpenApiRetryDelayMs = 500
$script:WorkOsFreshnessDefaultPortReleaseAttempts = 20
$script:WorkOsFreshnessDefaultPortReleaseDelayMs = 250

function Get-WorkOsCanonicalOpenApiManifestPath {
    param([string] $ScriptsRoot = $PSScriptRoot)
    return Join-Path $ScriptsRoot "workos-canonical-openapi-paths.json"
}

function Get-WorkOsCanonicalOpenApiManifest {
    param([string] $ScriptsRoot = $PSScriptRoot)

    $manifestPath = Get-WorkOsCanonicalOpenApiManifestPath -ScriptsRoot $ScriptsRoot
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        return [PSCustomObject]@{
            Valid = $false
            Error = "manifest_missing"
            Message = "Canonical OpenAPI manifest not found: $manifestPath"
            ManifestVersion = $null
            RequiredPaths = @()
            ManifestPath = $manifestPath
        }
    }

    try {
        $raw = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8
        $parsed = $raw | ConvertFrom-Json
    } catch {
        return [PSCustomObject]@{
            Valid = $false
            Error = "manifest_malformed"
            Message = "Failed to parse canonical OpenAPI manifest: $($_.Exception.Message)"
            ManifestVersion = $null
            RequiredPaths = @()
            ManifestPath = $manifestPath
        }
    }

    $version = $parsed.manifest_version
    $paths = @($parsed.required_paths | ForEach-Object { [string]$_ })
    $unique = @($paths | Select-Object -Unique)

    if ($null -eq $version -or [string]::IsNullOrWhiteSpace([string]$version)) {
        return [PSCustomObject]@{
            Valid = $false
            Error = "manifest_version_missing"
            Message = "Canonical OpenAPI manifest missing manifest_version"
            ManifestVersion = $null
            RequiredPaths = $paths
            ManifestPath = $manifestPath
        }
    }

    if ($paths.Count -eq 0) {
        return [PSCustomObject]@{
            Valid = $false
            Error = "manifest_empty"
            Message = "Canonical OpenAPI manifest required_paths is empty (fail closed)"
            ManifestVersion = $version
            RequiredPaths = @()
            ManifestPath = $manifestPath
        }
    }

    if ($unique.Count -ne $paths.Count) {
        return [PSCustomObject]@{
            Valid = $false
            Error = "manifest_duplicate_paths"
            Message = "Canonical OpenAPI manifest contains duplicate required_paths"
            ManifestVersion = $version
            RequiredPaths = $paths
            ManifestPath = $manifestPath
        }
    }

    return [PSCustomObject]@{
        Valid = $true
        Error = $null
        Message = $null
        ManifestVersion = $version
        RequiredPaths = $unique
        ManifestPath = $manifestPath
    }
}

function Get-WorkOsBackendPortListeners {
    param(
        [int] $Port,
        [string] $ExpectedHost = '127.0.0.1'
    )

    $rows = @()
    $seen = @{}
    $conns = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    foreach ($conn in $conns) {
        if ($ExpectedHost -and $conn.LocalAddress -ne $ExpectedHost) {
            continue
        }
        $procId = [int]$conn.OwningProcess
        $key = "$($conn.LocalAddress):${Port}:$procId"
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        $cmd = Get-WorkOsProcessCommandLine -ProcessId $procId
        $rows += [PSCustomObject]@{
            LocalAddress = $conn.LocalAddress
            LocalPort = $Port
            OwningProcess = $procId
            ProcessAlive = [bool]$proc
            ProcessName = if ($proc) { $proc.ProcessName } else { "unknown" }
            CommandLine = $cmd
        }
    }
    return $rows
}

function Get-WorkOsProcessExecutablePath {
    param([int] $ProcessId)
    if ($ProcessId -le 0) { return $null }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }
    return $proc.Path
}

function Test-WorkOsPathUnderProjectRoot {
    param(
        [string] $CandidatePath,
        [string] $ProjectRoot
    )
    if ([string]::IsNullOrWhiteSpace($CandidatePath)) { return $false }
    $rootNorm = (Resolve-Path -LiteralPath $ProjectRoot -ErrorAction SilentlyContinue).Path
    if (-not $rootNorm) {
        $rootNorm = $ProjectRoot
    }
    $candidateNorm = $CandidatePath
    try {
        if (Test-Path -LiteralPath $CandidatePath) {
            $candidateNorm = (Resolve-Path -LiteralPath $CandidatePath).Path
        }
    } catch {
        $candidateNorm = $CandidatePath
    }
    $rootPrefix = ($rootNorm.TrimEnd('\') + '\').ToLowerInvariant()
    return $candidateNorm.ToLowerInvariant().StartsWith($rootPrefix)
}

function Test-WorkOsBackendCommandLineReferencesProjectVenv {
    param(
        [string] $CommandLine,
        [string] $ProjectRoot
    )
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { return $false }
    $backendDirNorm = ((Join-Path $ProjectRoot "backend") -replace '\\', '/').ToLowerInvariant()
    $cmdNorm = ($CommandLine -replace '\\', '/').ToLowerInvariant()
    return $cmdNorm.Contains("$backendDirNorm/.venv/scripts/python.exe")
}

function Test-WorkOsBackendProcessParentLineageProof {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $MaxDepth = 10
    )

    $rootNorm = ($ProjectRoot -replace '\\', '/').ToLowerInvariant()
    $current = $ProcessId
    for ($depth = 0; $depth -lt $MaxDepth; $depth++) {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$current" -ErrorAction SilentlyContinue
        if (-not $proc) { return $false }
        $parentId = [int]$proc.ParentProcessId
        if ($parentId -le 0 -or $parentId -eq $current) { return $false }
        $parentProc = Get-CimInstance Win32_Process -Filter "ProcessId=$parentId" -ErrorAction SilentlyContinue
        if (-not $parentProc) { return $false }
        $parentCmd = [string]$parentProc.CommandLine
        if (Test-WorkOsBackendCommandLineReferencesProjectVenv -CommandLine $parentCmd -ProjectRoot $ProjectRoot) {
            return $true
        }
        if (-not [string]::IsNullOrWhiteSpace($parentCmd)) {
            $parentCmdNorm = ($parentCmd -replace '\\', '/').ToLowerInvariant()
            if ($parentCmdNorm.Contains($rootNorm) -and (
                $parentCmdNorm -match 'dev-backend\.ps1' -or
                $parentCmdNorm -match 'start-dev\.ps1' -or
                $parentCmdNorm -match 'scripts/dev\.ps1'
            )) {
                return $true
            }
        }
        $current = $parentId
    }
    return $false
}

function Get-WorkOsSpawnWorkerParentProcessIdFromCommandLine {
    param([string] $CommandLine)
    if (-not $CommandLine) { return $null }
    if ($CommandLine -match 'spawn_main\(parent_pid=(\d+)') {
        return [int]$Matches[1]
    }
    return $null
}

function Resolve-WorkOsBackendSpawnWorkerOwnershipFromParent {
    param(
        [object] $Node,
        [object[]] $ProcessNodes
    )
    if ($Node.Ownership -ne 'ambiguous' -or $Node.Role -ne 'uvicorn_spawn_worker') {
        return $Node
    }
    $parentPid = Get-WorkOsSpawnWorkerParentProcessIdFromCommandLine -CommandLine $Node.CommandLine
    if (-not $parentPid) { return $Node }
    $parentNode = @($ProcessNodes | Where-Object { $_.ProcessId -eq $parentPid })[0]
    if ($parentNode -and $parentNode.Ownership -eq 'same_worktree') {
        $Node.Ownership = 'same_worktree'
        $Node.WorktreePath = $parentNode.WorktreePath
        $Node.Evidence += 'spawn_worker_inherits_proven_parent'
    }
    return $Node
}

function Get-WorkOsSpawnChildProcesses {
    param([int] $ParentProcessId)

    $children = @()
    $filterParent = [string]$ParentProcessId
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    foreach ($proc in $all) {
        $cmd = $proc.CommandLine
        if (-not $cmd) { continue }
        if ($cmd -match "spawn_main\(parent_pid=$filterParent\b") {
            $children += [PSCustomObject]@{
                ProcessId = [int]$proc.ProcessId
                ParentProcessId = [int]$proc.ParentProcessId
                CommandLine = $cmd
                ExecutablePath = (Get-WorkOsProcessExecutablePath -ProcessId ([int]$proc.ProcessId))
            }
        }
    }
    return $children
}

function Get-WorkOsOrphanSpawnWorkersForGhostParent {
    param([int] $GhostParentProcessId)

    return @(Get-WorkOsSpawnChildProcesses -ParentProcessId $GhostParentProcessId)
}

function Test-WorkOsUvicornCommandLine {
    param(
        [string] $CommandLine,
        [int] $ExpectedPort
    )
    if (-not $CommandLine) { return $false }
    $cmdLower = $CommandLine.ToLowerInvariant()
    if ($cmdLower -notmatch 'uvicorn') { return $false }
    if ($cmdLower -notmatch 'main:app') { return $false }
    if ($cmdLower -notmatch "--port\s+$ExpectedPort\b") { return $false }
    return $true
}

function Test-WorkOsSpawnWorkerCommandLine {
    param([string] $CommandLine)
    if (-not $CommandLine) { return $false }
    return ($CommandLine -match 'spawn_main\(parent_pid=\d+')
}

function Get-WorkOsBackendProcessOwnership {
    param(
        [int] $ProcessId,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsBackendPort)
    )

    $backendDir = Join-Path $ProjectRoot "backend"
    $expectedVenvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    $expectedVenvPythonNorm = ($expectedVenvPython -replace '\\', '/').ToLowerInvariant()
    $rootNorm = ($ProjectRoot -replace '\\', '/').ToLowerInvariant()

    $cmd = Get-WorkOsProcessCommandLine -ProcessId $ProcessId
    $exe = Get-WorkOsProcessExecutablePath -ProcessId $ProcessId
    $alive = $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)

    $result = [PSCustomObject]@{
        ProcessId = $ProcessId
        Alive = $alive
        CommandLine = $cmd
        ExecutablePath = $exe
        Role = "unknown"
        Ownership = "ambiguous"
        WorktreePath = $null
        Evidence = @()
    }

    if (Test-WorkOsSpawnWorkerCommandLine -CommandLine $cmd) {
        $result.Role = "uvicorn_spawn_worker"
        if ($exe -and (Test-WorkOsPathUnderProjectRoot -CandidatePath $exe -ProjectRoot $ProjectRoot)) {
            $result.Ownership = "same_worktree"
            $result.WorktreePath = $ProjectRoot
            $result.Evidence += "spawn_worker_executable_under_project_root"
            return $result
        }
        if ($exe) {
            $exeNorm = ($exe -replace '\\', '/').ToLowerInvariant()
            if ($exeNorm -match '\\backend\\\.venv\\scripts\\python\.exe$') {
                $idx = $exeNorm.IndexOf('/backend/.venv/scripts/python.exe')
                if ($idx -gt 0) {
                    $candidateRoot = $exeNorm.Substring(0, $idx)
                    if ($candidateRoot -ne $rootNorm) {
                        $result.Ownership = "other_worktree"
                        $result.WorktreePath = $candidateRoot -replace '/', '\'
                        $result.Evidence += "spawn_worker_other_worktree_venv"
                        return $result
                    }
                }
            }
        }
        $result.Ownership = "ambiguous"
        $result.Evidence += "spawn_worker_missing_worktree_proof"
        if (Test-WorkOsBackendProcessParentLineageProof -ProcessId $ProcessId -ProjectRoot $ProjectRoot) {
            $result.Ownership = "same_worktree"
            $result.WorktreePath = $ProjectRoot
            $result.Evidence += "parent_lineage_project_venv"
        }
        return $result
    }

    if (Test-WorkOsUvicornCommandLine -CommandLine $cmd -ExpectedPort $ExpectedPort) {
        $result.Role = "uvicorn_reloader"
        if ($exe -and (Test-WorkOsPathUnderProjectRoot -CandidatePath $exe -ProjectRoot $ProjectRoot)) {
            $result.Ownership = "same_worktree"
            $result.WorktreePath = $ProjectRoot
            $result.Evidence += "reloader_executable_under_project_root"
            return $result
        }
        if ($exe) {
            $exeNorm = ($exe -replace '\\', '/').ToLowerInvariant()
            if ($exeNorm -eq $expectedVenvPythonNorm -or $exeNorm -match [regex]::Escape($rootNorm)) {
                $result.Ownership = "same_worktree"
                $result.WorktreePath = $ProjectRoot
                $result.Evidence += "reloader_expected_venv_or_root"
                return $result
            }
            if ($exeNorm -match '\\backend\\\.venv\\scripts\\python\.exe$') {
                $idx = $exeNorm.IndexOf('/backend/.venv/scripts/python.exe')
                if ($idx -gt 0) {
                    $candidateRoot = $exeNorm.Substring(0, $idx)
                    if ($candidateRoot -ne $rootNorm) {
                        $result.Ownership = "other_worktree"
                        $result.WorktreePath = $candidateRoot -replace '/', '\'
                        $result.Evidence += "reloader_other_worktree_venv"
                        return $result
                    }
                }
            }
        }
        $result.Ownership = "ambiguous"
        $result.Evidence += "uvicorn_reloader_missing_worktree_proof"
        if (Test-WorkOsBackendCommandLineReferencesProjectVenv -CommandLine $cmd -ProjectRoot $ProjectRoot) {
            $result.Ownership = "same_worktree"
            $result.WorktreePath = $ProjectRoot
            $result.Evidence += "reloader_command_line_project_venv"
            return $result
        }
        if (Test-WorkOsBackendProcessParentLineageProof -ProcessId $ProcessId -ProjectRoot $ProjectRoot) {
            $result.Ownership = "same_worktree"
            $result.WorktreePath = $ProjectRoot
            $result.Evidence += "parent_lineage_project_venv"
        }
        return $result
    }

    if ($cmd -and $cmd -match 'uvicorn') {
        $result.Role = "uvicorn_other"
        $result.Ownership = "foreign_process"
        $result.Evidence += "uvicorn_not_canonical_main_app"
        return $result
    }

    $result.Role = "non_workos"
    $result.Ownership = "foreign_process"
    $result.Evidence += "not_uvicorn_workos_backend"
    return $result
}

function Get-WorkOsBackendProcessTreeSnapshot {
    param(
        [int] $Port,
        [string] $ProjectRoot,
        [int] $ExpectedPort = $(Get-WorkOsBackendPort)
    )

    $listeners = @(Get-WorkOsBackendPortListeners -Port $Port)
    $processNodes = @()
    $ghostParents = @()
    $resolvedPids = @{}

    foreach ($listener in $listeners) {
        $listenerPid = [int]$listener.OwningProcess
        if (-not $listener.ProcessAlive) {
            $ghostParents += [PSCustomObject]@{
                GhostParentProcessId = $listenerPid
                Listener = $listener
                OrphanWorkers = @(Get-WorkOsOrphanSpawnWorkersForGhostParent -GhostParentProcessId $listenerPid)
            }
            foreach ($worker in $ghostParents[-1].OrphanWorkers) {
                if (-not $resolvedPids.ContainsKey($worker.ProcessId)) {
                    $resolvedPids[$worker.ProcessId] = $true
                    $processNodes += Get-WorkOsBackendProcessOwnership -ProcessId $worker.ProcessId -ProjectRoot $ProjectRoot -ExpectedPort $ExpectedPort
                }
            }
            continue
        }

        if (-not $resolvedPids.ContainsKey($listenerPid)) {
            $resolvedPids[$listenerPid] = $true
            $processNodes += Get-WorkOsBackendProcessOwnership -ProcessId $listenerPid -ProjectRoot $ProjectRoot -ExpectedPort $ExpectedPort
            $children = @(Get-WorkOsSpawnChildProcesses -ParentProcessId $listenerPid)
            foreach ($child in $children) {
                if (-not $resolvedPids.ContainsKey($child.ProcessId)) {
                    $resolvedPids[$child.ProcessId] = $true
                    $processNodes += Get-WorkOsBackendProcessOwnership -ProcessId $child.ProcessId -ProjectRoot $ProjectRoot -ExpectedPort $ExpectedPort
                }
            }
        }
    }

    for ($i = 0; $i -lt $processNodes.Count; $i++) {
        $processNodes[$i] = Resolve-WorkOsBackendSpawnWorkerOwnershipFromParent -Node $processNodes[$i] -ProcessNodes $processNodes
    }

    return [PSCustomObject]@{
        Listeners = $listeners
        ListenerCount = $listeners.Count
        GhostParents = $ghostParents
        ProcessNodes = $processNodes
        ResolvedProcessIds = @($resolvedPids.Keys)
    }
}

function Test-WorkOsBackendHttpHealth {
    param(
        [string] $BaseUrl = $(Get-WorkOsBackendUrl),
        [int] $TimeoutSec = 3
    )
    try {
        $r = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec $TimeoutSec
        return [PSCustomObject]@{
            Ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
            StatusCode = $r.StatusCode
            Error = $null
        }
    } catch {
        return [PSCustomObject]@{
            Ok = $false
            StatusCode = $null
            Error = $_.Exception.Message
        }
    }
}

function Test-WorkOsBackendOpenApiRoutes {
    param(
        [string] $BaseUrl = $(Get-WorkOsBackendUrl),
        [object] $Manifest,
        [int] $MaxAttempts = $script:WorkOsFreshnessDefaultOpenApiRetries,
        [int] $DelayMs = $script:WorkOsFreshnessDefaultOpenApiRetryDelayMs
    )

    if (-not $Manifest -or -not $Manifest.Valid) {
        return [PSCustomObject]@{
            Ok = $false
            ParseOk = $false
            MissingPaths = @()
            PresentPaths = @()
            Error = if ($Manifest) { $Manifest.Error } else { "manifest_unavailable" }
            Message = if ($Manifest) { $Manifest.Message } else { "Manifest unavailable" }
            Attempts = 0
        }
    }

    $required = @($Manifest.RequiredPaths)
    $lastError = $null
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $schema = Invoke-RestMethod -Uri "$BaseUrl/openapi.json" -TimeoutSec 5
            $paths = @($schema.paths.PSObject.Properties | ForEach-Object { $_.Name })
            $missing = @($required | Where-Object { $paths -notcontains $_ })
            return [PSCustomObject]@{
                Ok = ($missing.Count -eq 0)
                ParseOk = $true
                MissingPaths = $missing
                PresentPaths = @($required | Where-Object { $paths -contains $_ })
                Error = if ($missing.Count -gt 0) { "canonical_routes_missing" } else { $null }
                Message = if ($missing.Count -gt 0) { "Missing canonical OpenAPI paths: $($missing -join ', ')" } else { $null }
                Attempts = $attempt
            }
        } catch {
            $lastError = $_.Exception.Message
            if ($attempt -lt $MaxAttempts) {
                Start-Sleep -Milliseconds $DelayMs
            }
        }
    }

    return [PSCustomObject]@{
        Ok = $false
        ParseOk = $false
        MissingPaths = $required
        PresentPaths = @()
        Error = "openapi_failed"
        Message = "OpenAPI fetch/parse failed after $MaxAttempts attempts: $lastError"
        Attempts = $MaxAttempts
    }
}

function Get-WorkOsBackendFreshnessClassification {
    param(
        [string] $ProjectRoot,
        [int] $Port = $(Get-WorkOsBackendPort),
        [string] $BaseUrl = $(Get-WorkOsBackendUrl),
        [string] $ScriptsRoot = $PSScriptRoot
    )

    $manifest = Get-WorkOsCanonicalOpenApiManifest -ScriptsRoot $ScriptsRoot
    $tree = Get-WorkOsBackendProcessTreeSnapshot -Port $Port -ProjectRoot $ProjectRoot -ExpectedPort $Port
    $health = $null
    $openapi = $null

    $evaluation = [PSCustomObject]@{
        Classification = "ambiguous_process_tree"
        RecommendedAction = "block"
        Ready = $false
        Manifest = $manifest
        ListenerCount = $tree.ListenerCount
        Listeners = $tree.Listeners
        GhostParents = $tree.GhostParents
        ProcessNodes = $tree.ProcessNodes
        Health = $null
        OpenApi = $null
        MissingPaths = @()
        OwnershipSummary = @()
        StopProcessIds = @()
        Diagnostics = @()
    }

    if (-not $manifest.Valid) {
        $evaluation.Classification = if ($manifest.Error -eq "manifest_empty") { "canonical_routes_missing" } else { "openapi_failed" }
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += $manifest.Message
        return $evaluation
    }

    if ($tree.ListenerCount -eq 0) {
        $evaluation.Classification = "backend_absent"
        $evaluation.RecommendedAction = "start"
        $evaluation.Diagnostics += "No listener on port $Port"
        return $evaluation
    }

    $ownerships = @($tree.ProcessNodes | ForEach-Object { $_.Ownership })
    $evaluation.OwnershipSummary = @($ownerships | Select-Object -Unique)

    if ($ownerships -contains "foreign_process") {
        $evaluation.Classification = "foreign_process"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Foreign process detected on port $Port"
        return $evaluation
    }

    if ($ownerships -contains "other_worktree") {
        $evaluation.Classification = "other_worktree"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Backend process belongs to another worktree"
        return $evaluation
    }

    if ($tree.ProcessNodes.Count -eq 0) {
        $evaluation.Classification = "ambiguous_process_tree"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Listeners present but no process nodes could be resolved"
        return $evaluation
    }

    if ($ownerships -contains "ambiguous") {
        $evaluation.Classification = "ambiguous_process_tree"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Unable to prove process ownership for all listeners"
        return $evaluation
    }

    $distinctSameWorktreeRoots = @(
        $tree.ProcessNodes |
            Where-Object { $_.Ownership -eq "same_worktree" -and $_.WorktreePath } |
            ForEach-Object { $_.WorktreePath } |
            Select-Object -Unique
    )
    if ($distinctSameWorktreeRoots.Count -gt 1) {
        $evaluation.Classification = "ambiguous_process_tree"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Multiple same-worktree roots detected"
        return $evaluation
    }

    $hasMixedOwnership = (
        ($ownerships -contains "same_worktree") -and
        (($ownerships | Where-Object { $_ -ne "same_worktree" }).Count -gt 0)
    )
    if ($hasMixedOwnership) {
        $evaluation.Classification = "multiple_listeners"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += "Multiple listeners with mixed process ownership"
        return $evaluation
    }

    if ($tree.ListenerCount -gt 1 -and $ownerships -notcontains "same_worktree") {
        $allUvicornTree = (
            ($tree.ProcessNodes.Count -gt 0) -and
            (@($tree.ProcessNodes | Where-Object {
                $_.Role -notin @('uvicorn_reloader', 'uvicorn_spawn_worker')
            }).Count -eq 0) -and
            -not ($ownerships -contains 'foreign_process') -and
            -not ($ownerships -contains 'other_worktree')
        )
        if (-not $allUvicornTree) {
            $evaluation.Classification = "multiple_listeners"
            $evaluation.RecommendedAction = "block"
            $evaluation.Diagnostics += "Multiple listeners without proven same-worktree ownership"
            return $evaluation
        }
    }

    $health = Test-WorkOsBackendHttpHealth -BaseUrl $BaseUrl
    $evaluation.Health = $health
    if (-not $health.Ok) {
        $evaluation.Classification = "health_failed"
        $canStopStale = ($ownerships -contains "same_worktree")
        $evaluation.RecommendedAction = if ($canStopStale) { "controlled_stop" } else { "block" }
        $evaluation.Diagnostics += "Health probe failed: $($health.Error)"
        if ($evaluation.RecommendedAction -eq "controlled_stop") {
            $evaluation.StopProcessIds = @(Get-WorkOsBackendStopTargetProcessIds -Tree $tree)
        }
        return $evaluation
    }

    $openapi = Test-WorkOsBackendOpenApiRoutes -BaseUrl $BaseUrl -Manifest $manifest
    $evaluation.OpenApi = $openapi
    $evaluation.MissingPaths = @($openapi.MissingPaths)

    if (-not $openapi.ParseOk) {
        $evaluation.Classification = "openapi_failed"
        $evaluation.RecommendedAction = "block"
        $evaluation.Diagnostics += $openapi.Message
        return $evaluation
    }

    if (-not $openapi.Ok) {
        $evaluation.Classification = "canonical_routes_missing"
        if ($ownerships -contains "same_worktree") {
            $evaluation.RecommendedAction = "controlled_stop"
            $evaluation.StopProcessIds = @(Get-WorkOsBackendStopTargetProcessIds -Tree $tree)
        } else {
            $evaluation.RecommendedAction = "block"
        }
        $evaluation.Diagnostics += $openapi.Message
        return $evaluation
    }

    if ($ownerships -contains "same_worktree") {
        $evaluation.Classification = "current_and_ready"
        $evaluation.RecommendedAction = "reuse"
        $evaluation.Ready = $true
        $evaluation.Diagnostics += "Backend fresh: health OK, canonical OpenAPI routes present, proven same-worktree ownership"
        return $evaluation
    }

    $evaluation.Classification = "ambiguous_process_tree"
    $evaluation.RecommendedAction = "block"
    $evaluation.Diagnostics += "Health and OpenAPI passed but same-worktree ownership is not proven"
    return $evaluation
}

function Get-WorkOsBackendStopTargetProcessIds {
    param([object] $Tree)

    $targets = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($node in $Tree.ProcessNodes) {
        if (-not $node.Alive) { continue }
        if ($node.Ownership -eq 'foreign_process' -or $node.Ownership -eq 'other_worktree') { continue }
        if ($node.Ownership -eq 'same_worktree') {
            [void]$targets.Add([int]$node.ProcessId)
        }
    }
    foreach ($ghost in $Tree.GhostParents) {
        foreach ($worker in $ghost.OrphanWorkers) {
            $node = @($Tree.ProcessNodes | Where-Object { $_.ProcessId -eq $worker.ProcessId })[0]
            if ($node -and $node.Ownership -eq 'same_worktree' -and $node.Alive) {
                [void]$targets.Add([int]$worker.ProcessId)
            }
        }
        if ($ghost.GhostParentProcessId -gt 0) {
            $parentNode = @($Tree.ProcessNodes | Where-Object { $_.ProcessId -eq $ghost.GhostParentProcessId })[0]
            if ($parentNode -and $parentNode.Ownership -eq 'same_worktree' -and $parentNode.Alive) {
                [void]$targets.Add([int]$ghost.GhostParentProcessId)
            }
        }
    }
    foreach ($listener in $Tree.Listeners) {
        if (-not $listener.ProcessAlive) { continue }
        $listenerNode = @($Tree.ProcessNodes | Where-Object { $_.ProcessId -eq $listener.OwningProcess })[0]
        if ($listenerNode -and $listenerNode.Ownership -eq 'same_worktree') {
            [void]$targets.Add([int]$listener.OwningProcess)
            foreach ($child in @(Get-WorkOsSpawnChildProcesses -ParentProcessId ([int]$listener.OwningProcess))) {
                $childNode = @($Tree.ProcessNodes | Where-Object { $_.ProcessId -eq $child.ProcessId })[0]
                if ($childNode -and $childNode.Ownership -eq 'same_worktree') {
                    [void]$targets.Add([int]$child.ProcessId)
                }
            }
        }
    }
    return @($targets | Sort-Object)
}

function Stop-WorkOsBackendProcessTreeControlled {
    param(
        [object] $Tree,
        [int[]] $ProcessIds,
        [int] $Port,
        [int] $MaxReleaseAttempts = $script:WorkOsFreshnessDefaultPortReleaseAttempts,
        [int] $ReleaseDelayMs = $script:WorkOsFreshnessDefaultPortReleaseDelayMs
    )

    $ordered = @()
    $spawnWorkers = @()
    $reloaders = @()
    foreach ($targetPid in $ProcessIds) {
        $cmd = Get-WorkOsProcessCommandLine -ProcessId $targetPid
        if (Test-WorkOsSpawnWorkerCommandLine -CommandLine $cmd) {
            $spawnWorkers += $targetPid
        } else {
            $reloaders += $targetPid
        }
    }
    $ordered = @($spawnWorkers + $reloaders)

    $stopped = @()
    foreach ($targetPid in $ordered) {
        try {
            Stop-Process -Id $targetPid -Force -ErrorAction Stop
            $stopped += $targetPid
        } catch {
            # Process may already be gone (ghost parent); continue with evidence.
        }
    }

    for ($i = 1; $i -le $MaxReleaseAttempts; $i++) {
        Start-Sleep -Milliseconds $ReleaseDelayMs
        $remaining = @(Get-WorkOsBackendPortListeners -Port $Port)
        if ($remaining.Count -eq 0) {
            return [PSCustomObject]@{
                StoppedProcessIds = $stopped
                PortReleased = $true
                RemainingListeners = @()
            }
        }
    }

    return [PSCustomObject]@{
        StoppedProcessIds = $stopped
        PortReleased = $false
        RemainingListeners = @(Get-WorkOsBackendPortListeners -Port $Port)
    }
}

function Write-WorkOsBackendFreshnessDiagnostics {
    param([object] $Evaluation)

    Write-Host ""
    Write-Host "=== Backend freshness diagnostics ===" -ForegroundColor Yellow
    Write-Host ("  classification     = {0}" -f $Evaluation.Classification)
    Write-Host ("  recommended_action = {0}" -f $Evaluation.RecommendedAction)
    Write-Host ("  ready              = {0}" -f $Evaluation.Ready)
    Write-Host ("  listener_count     = {0}" -f $Evaluation.ListenerCount)
    if ($Evaluation.Manifest) {
        Write-Host ("  manifest_version   = {0}" -f $Evaluation.Manifest.ManifestVersion)
        Write-Host ("  manifest_path      = {0}" -f $Evaluation.Manifest.ManifestPath)
    }
    if ($Evaluation.Health) {
        Write-Host ("  health_ok          = {0}" -f $Evaluation.Health.Ok)
        if ($Evaluation.Health.Error) {
            Write-Host ("  health_error       = {0}" -f $Evaluation.Health.Error)
        }
    }
    if ($Evaluation.OpenApi) {
        Write-Host ("  openapi_ok         = {0}" -f $Evaluation.OpenApi.Ok)
        Write-Host ("  openapi_parse_ok   = {0}" -f $Evaluation.OpenApi.ParseOk)
        if ($Evaluation.MissingPaths.Count -gt 0) {
            Write-Host ("  missing_paths      = {0}" -f ($Evaluation.MissingPaths -join ", "))
        }
        if ($Evaluation.OpenApi.Message) {
            Write-Host ("  openapi_message    = {0}" -f $Evaluation.OpenApi.Message)
        }
    }
    if ($Evaluation.OwnershipSummary.Count -gt 0) {
        Write-Host ("  ownership_summary  = {0}" -f ($Evaluation.OwnershipSummary -join ", "))
    }
    foreach ($listener in @($Evaluation.Listeners)) {
        Write-Host ("  listener_pid       = {0} alive={1}" -f $listener.OwningProcess, $listener.ProcessAlive)
        if ($listener.CommandLine) {
            Write-Host ("  listener_cmd       = {0}" -f $listener.CommandLine)
        }
    }
    foreach ($node in @($Evaluation.ProcessNodes)) {
        Write-Host ("  process_pid        = {0} role={1} ownership={2}" -f $node.ProcessId, $node.Role, $node.Ownership)
        if ($node.WorktreePath) {
            Write-Host ("  process_worktree   = {0}" -f $node.WorktreePath)
        }
    }
    foreach ($line in @($Evaluation.Diagnostics)) {
        Write-Host ("  note               = {0}" -f $line)
    }
    Write-Host ""
}

function Test-WorkOsBackendDevReady {
    param(
        [string] $ProjectRoot,
        [string] $ScriptsRoot = $PSScriptRoot
    )

    $evaluation = Get-WorkOsBackendFreshnessClassification -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot
    return $evaluation.Ready
}

function Test-WorkOsBackendDevReadyEvaluation {
    param(
        [string] $ProjectRoot,
        [string] $ScriptsRoot = $PSScriptRoot
    )

    return Get-WorkOsBackendFreshnessClassification -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot
}
