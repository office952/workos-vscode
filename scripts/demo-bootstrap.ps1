# Wipe-and-rebuild WorkOS Atoms demo SQLite DB + synthetic seed.
# NEVER touches backend/dev.db.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_workos-python.ps1"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$DemoDir = Join-Path $BackendDir "demo"
$DemoDbPath = Join-Path $DemoDir "workos_demo.db"
$Forbidden = Join-Path $BackendDir "dev.db"

if (-not (Test-Path $DemoDir)) {
    New-Item -ItemType Directory -Path $DemoDir | Out-Null
}

$demoResolved = [System.IO.Path]::GetFullPath($DemoDbPath)
$forbiddenResolved = [System.IO.Path]::GetFullPath($Forbidden)
if ($demoResolved -eq $forbiddenResolved) {
    Write-Error "Refusing bootstrap: demo path equals dev.db"
}
if ([System.IO.Path]::GetFileName($demoResolved).ToLowerInvariant() -eq "dev.db") {
    Write-Error "Refusing bootstrap: basename is dev.db"
}

$DatabaseUrl = "sqlite+aiosqlite:///" + ($demoResolved -replace "\\", "/")
$env:APP_ENV = "development"
$env:ENVIRONMENT = "development"
$env:DATABASE_URL = $DatabaseUrl
$env:JWT_SECRET_KEY = "local-dev-secret-not-for-production"

$venvPython = Get-WorkOsBackendVenvPython -BackendDir $BackendDir

Write-Host "=== WorkOS Atoms demo bootstrap ===" -ForegroundColor Cyan
Write-Host ("  Demo DB = {0}" -f $demoResolved)
Write-Host ("  Forbidden (must not touch) = {0}" -f $forbiddenResolved)

# Guard via Python (cwd = backend so `demo` package imports)
Push-Location $BackendDir
try {
    & $venvPython -c "from demo.db_guard import assert_safe_demo_database_url; import os; p=assert_safe_demo_database_url(os.environ['DATABASE_URL']); print('guard_ok', p)"
    if ($LASTEXITCODE -ne 0) { throw "demo db guard failed" }
} finally {
    Pop-Location
}

# Wipe generated demo DB (+ sqlite sidecars)
foreach ($suffix in @("", "-wal", "-shm", "-journal")) {
    $p = $demoResolved + $suffix
    if (Test-Path -LiteralPath $p) {
        Remove-Item -LiteralPath $p -Force
        Write-Host ("  wiped {0}" -f $p) -ForegroundColor DarkGray
    }
}

Write-Host "Running alembic upgrade head ..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    & $venvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "alembic upgrade failed" }
} finally {
    Pop-Location
}

Write-Host "Running seed_atoms_demo_v1 ..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    & $venvPython -m scripts.seed_atoms_demo_v1
    if ($LASTEXITCODE -ne 0) { throw "seed_atoms_demo_v1 failed" }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $demoResolved)) {
    Write-Error "Demo DB was not created: $demoResolved"
}
if (Test-Path -LiteralPath $forbiddenResolved) {
    Write-Host "Note: backend/dev.db exists locally and was NOT used by this bootstrap." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== Demo bootstrap READY ===" -ForegroundColor Green
Write-Host ("  DB = {0}" -f $demoResolved)
Write-Host "  Next: .\scripts\demo-start.ps1"
Write-Host ""
exit 0
