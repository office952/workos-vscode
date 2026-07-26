# Shared Python resolution for WorkOS PowerShell helpers.
# Dot-source from dev-backend.ps1, test-backend.ps1, start-dev.ps1

function Resolve-WorkOsHostPython {
    if ($env:WORKOS_PYTHON) {
        if (Test-Path $env:WORKOS_PYTHON) {
            return $env:WORKOS_PYTHON
        }
        Write-Error "WORKOS_PYTHON is set but not found: $($env:WORKOS_PYTHON)"
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return (Get-Command python).Source
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $launcherPython = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($launcherPython -and (Test-Path $launcherPython.Trim())) {
                return $launcherPython.Trim()
            }
        } catch {
            # fall through to error below
        }
    }

    Write-Error "Python not found. Set WORKOS_PYTHON or install Python 3.12 / add python to PATH."
}

function Get-WorkOsBackendVenvPython {
    param([string] $BackendDir)

    $venvDir = Join-Path $BackendDir ".venv"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"

    if (Test-Path $venvPython) {
        return $venvPython
    }

    $hostPython = Resolve-WorkOsHostPython
    & $hostPython -m venv $venvDir

    if (-not (Test-Path $venvPython)) {
        Write-Error "Failed to create backend virtualenv at $venvDir"
    }

    return $venvPython
}

function Install-WorkOsBackendRequirements {
    param(
        [string] $BackendDir,
        [switch] $IncludeDev
    )

    $pip = Join-Path $BackendDir ".venv\Scripts\pip.exe"
    & $pip install -q -r (Join-Path $BackendDir "requirements.txt")

    if ($IncludeDev) {
        $devReq = Join-Path $BackendDir "requirements-dev.txt"
        if (Test-Path $devReq) {
            & $pip install -q -r $devReq
        }
    }
}

function Set-WorkOsJwtEnv {
    if (-not $env:JWT_SECRET_KEY) {
        $env:JWT_SECRET_KEY = "local-dev-secret-not-for-production"
    }
    if (-not $env:JWT_ALGORITHM) {
        $env:JWT_ALGORITHM = "HS256"
    }
    if (-not $env:JWT_EXPIRE_MINUTES) {
        $env:JWT_EXPIRE_MINUTES = "60"
    }
}
