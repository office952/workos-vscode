# WorkOS — Local Installation (Windows)

Instructions for running WorkOS from this export on a Windows machine.

## 1. Requirements

| Requirement | Expected version (from repo) |
|-------------|------------------------------|
| **Python** | **3.11+** (`scripts/start-dev.ps1` comment; `RUN_LOCAL.md` uses `py -3.11`) |
| **Node.js** | **20+** (`scripts/start-dev.ps1` comment) |
| **pnpm** | **8.10.0** (`packageManager` in `frontend/package.json`; or `npx pnpm@8.10.0`) |
| **PowerShell** | 5.1+ (for `scripts/dev.ps1`, `scripts/start-dev.ps1`) |
| **Git** | Optional (not required to run; needed only if you re-clone) |
| **SQLite dev DB** | Included at `backend/dev.db` |

## 2. Unzip

Extract the ZIP to a path **without spaces** if possible, for example:

```text
C:\workos\workos_full_export\
```

Use the folder that contains `backend/`, `frontend/`, `scripts/`, and this file as the **export root**.

## 3. Backend setup

```powershell
cd <export-root>\backend
python -m venv .venv
# Or: py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -r requirements-dev.txt
```

The repo uses `backend/requirements.txt` (runtime) and `backend/requirements-dev.txt` (pytest/dev tools). No root `pyproject.toml` for app install.

## 4. Frontend setup

The canonical frontend package is under `frontend/` (not the root `package.json`, which is a legacy duplicate).

```powershell
cd <export-root>\frontend
pnpm install
# Or without global pnpm:
npx --yes pnpm@8.10.0 install
```

## 5. Environment variables

**Recommended local values** (placeholders only — no production secrets):

### Backend (PowerShell session or set by dev scripts)

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
$env:DEBUG='true'
$env:ALLOWED_ORIGINS='http://localhost:3000,http://127.0.0.1:3000'
```

When starting from `backend/`, `DATABASE_URL` resolves to `backend/dev.db`.

### Frontend

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
$env:VITE_ENABLE_DEV_AUTH='true'
```

**Optional:** copy templates instead of manual export:

```powershell
copy <export-root>\.env.development.example <export-root>\.env
copy <export-root>\backend\.env.example <export-root>\backend\.env
```

Note: `scripts/dev.ps1` and `scripts/start-dev.ps1` **inject env vars** and do not require `.env` for basic local start.

## 6. Start app

### Primary method — full stack (recommended)

```powershell
cd <export-root>
.\scripts\dev.ps1
```

Equivalent via root `package.json`:

```powershell
cd <export-root>
pnpm run dev:stack
```

Alternative full-stack launcher:

```powershell
.\scripts\start-dev.ps1
```

### Backend only

```powershell
cd <export-root>
.\scripts\dev-backend.ps1
```

### Fallback — backend manual

```powershell
cd <export-root>\backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
$env:DEBUG='true'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Fallback — frontend manual

```powershell
cd <export-root>\frontend
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
$env:VITE_ENABLE_DEV_AUTH='true'
pnpm run dev
```

Frontend dev server: **http://127.0.0.1:3000** (Vite proxies `/api` to backend :8000).

## 7. Health checks

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing
```

## 8. Database

- **Included:** `backend/dev.db` (canonical local SQLite used by `scripts/dev.ps1`).
- **Usage:** `DATABASE_URL=sqlite+aiosqlite:///./dev.db` when cwd is `backend/`.
- **Excluded from ZIP:** 24 backup/forensic DB files — see `database_candidates/EXCLUDED_DB_FILES.txt`.
- **Do not** run reset, seed, or migration destructive steps without **owner GO**.
- Local dev boot may use `Base.metadata.create_all`; Alembic under `backend/alembic/` is for staged schema evolution.

## 9. Known blocked / non-canonical features

| Item | Status |
|------|--------|
| POST materialize | **Blocked** (DEC-009) |
| Execution sessions | **Blocked** — do not create |
| Employee Mobile | **Frozen / final-final** |
| Legacy `/price` + CostEngine minutes-as-price | **Not canonical** for V2 commercial path |
| Step 12 cleanup | **Not done** |

See `docs/architecture/realignment/` and `AGENTS.md` for protected areas (CostEngine, pricing, snapshots, status lifecycle).
