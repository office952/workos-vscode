# WorkOS — Environment Notes (Export)

## Local environment variables

These are the variables used by `scripts/dev.ps1`, `scripts/start-dev.ps1`, and `scripts/dev-backend.ps1`:

| Variable | Local value | Notes |
|----------|-------------|-------|
| `APP_ENV` | `development` | Required for dev mode |
| `ENVIRONMENT` | `development` | Same |
| `DATABASE_URL` | `sqlite+aiosqlite:///<absolute-or-relative-path>/backend/dev.db` | Scripts resolve to `backend/dev.db` |
| `JWT_SECRET_KEY` | `local-dev-secret-not-for-production` | Placeholder only |
| `DEBUG` | `true` | Verbose dev logging |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | CORS for Vite |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Frontend → backend |
| `VITE_ENABLE_DEV_AUTH` | `true` | Local dev auth bypass (never production) |

Unset in local scripts: `DEPLOYMENT_ENVIRONMENT`.

## Secrets NOT included

This export does **not** ship:

- Production or staging `.env` files with real credentials
- `JWT_SECRET_KEY` production values
- SmartBill, Stripe, OIDC client secrets
- AWS / Lambda deployment keys
- Any API keys from operator integrations

If your source checkout had a local `.env`, it was **not** copied (gitignored / not in export list). Use:

- `<export-root>/.env.example`
- `<export-root>/.env.development.example`
- `<export-root>/backend/.env.example`

## Creating local `.env` (optional)

```powershell
copy <export-root>\backend\.env.example <export-root>\backend\.env
# Edit only if you need OIDC or non-default paths
```

**Important:** `backend/.env` is **not** auto-loaded by uvicorn alone. Prefer `scripts/dev.ps1` / `scripts/dev-backend.ps1`, which inject vars into the process.

Root `.env.development.example` uses:

```text
DATABASE_URL=sqlite+aiosqlite:///./backend/dev.db
```

when running from repo root context.

## SQLite dev database

- **Path:** `backend/dev.db`
- **URL (from backend cwd):** `sqlite+aiosqlite:///./dev.db`
- **Engine:** SQLAlchemy + aiosqlite (async)
- **State:** snapshot of local dev at export time; may contain fixture data (e.g. order 88002, plan id=2 per recent audits)

24 backup/forensic DB files existed in source but were **excluded** from export ZIPs (patterns `dev.backup-*`, `dev.FORENSIC-*`; local inventory folder removed in repo cleanup 2026-07-16).

## Dev vs production

| Aspect | Local dev (this export) | Production |
|--------|-------------------------|------------|
| DB | SQLite file | PostgreSQL / managed DB (typical) |
| Auth | Dev auth flag / optional OIDC | Real OIDC / SSO |
| Secrets | Placeholders | Secure vault / env injection |
| Migrations | Often `create_all` locally; Alembic for staged deploy | Controlled Alembic pipeline |
| Materialize | Blocked by policy | Owner-gated rollout |

## Warning

**Do not deploy this ZIP as production** without:

- Security review of env and auth
- Proper secret management
- Database migration strategy
- Removal of dev-only flags (`VITE_ENABLE_DEV_AUTH`, debug endpoints)
- Owner sign-off on commercial/pricing/snapshot boundaries

This archive is for **backup, transfer, and local developer restore** only.
