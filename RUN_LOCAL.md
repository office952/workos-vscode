# Run WorkOS local

## 1. Install frontend

Use the canonical frontend package under `frontend/`.

```powershell
cd frontend
pnpm install
```

## 2. Install backend

Use Python 3.11+ and the backend virtual environment.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -r requirements-dev.txt
```

## 3. Configure env

Choose one of these approaches:

```powershell
copy ..\.env.development.example ..\.env
copy .env.example .env
```

Notes:

- `backend/.env.example` is the backend-native example.
- root `.env.development.example` is a safe local preview template.
- `VITE_ENABLE_DEV_AUTH=true` is only for local preview.
- `frontend/src/lib/config.ts` uses a dev fallback to `http://127.0.0.1:8001` if no explicit frontend API base is provided.

## 4. Prepare database

### Use the included local DB

The runnable local DB included in this export is `backend/dev.db`.

### Regenerate from migrations + seeds

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed_sync_all
.\.venv\Scripts\python.exe -m seeds.seed_intake_v6_unified_pricing
```

## 5. Start backend

### Windows helper

```powershell
cd ..
.\scripts\dev-backend.ps1
```

### Direct launch

```powershell
cd backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
$env:DEBUG='true'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## 6. Start frontend

```powershell
cd frontend
pnpm run dev
```

If you want to use the frontend's dev-only direct API fallback, run the backend on `8001` instead of `8000`.

## 7. Open app

```text
Frontend: http://127.0.0.1:3000
Backend health: http://127.0.0.1:8000/health
Pricing: http://127.0.0.1:3000/inventory/pricing
Intake V6 operator: http://127.0.0.1:3000/intake-v6/operator
```

## 8. Test Intake V6

Focused frontend tests:

```powershell
cd frontend
pnpm exec vitest run src/lib/intakeV6/intakeV6OperatorRoutes.test.ts src/lib/intakeV6/intakeV6ClientSvgImport.test.ts
```

Focused backend V6 test:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_order_snapshot_payload.py -q
```

## 9. Known local constraints

- Frontend production build passes.
- Backend import, startup, and `/health` pass with local env vars.
- Global frontend typecheck is not clean at export time.
- Intake V2, V4, V5, and V6 routes are all still present in the app.
- V6 exists, but some V6 modules still depend conceptually on V4-era UI and naming.