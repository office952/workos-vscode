# WorkOS Atoms — Reproducible Demo Environment

**Status:** V1 demo tooling for UI/UX audit  
**Product scope:** Letters-only (`WORKOS_V1_PRODUCT_SET = LETTERS_ONLY`)  
**Baseline:** finalized WorkOS V1 (`FINALIZED_FOR_AGREED_SCOPE`)

## Purpose

Give Atoms (or any auditor) the **real** WorkOS frontend + backend with a **synthetic** dataset — without Owner `backend/dev.db` and without real PII.

Do **not** invent backend behavior. Use this demo DB + live APIs.

## Bootstrap (Windows PowerShell)

```powershell
cd C:\w\psiso   # or fresh clone of office952/workos-vscode @ feat/f7i-owner-rate-activation
# install deps once: backend\.venv + frontend pnpm as usual

.\scripts\demo-bootstrap.ps1
.\scripts\demo-start.ps1
```

- Bootstrap **wipe-and-rebuilds** `backend/demo/workos_demo.db` only.
- Hard-fails if the target path is `backend/dev.db`.
- Does **not** commit the SQLite file (`*.db` gitignored).
- If Owner/local stack already owns `:8000`/`:3000` on `dev.db`, `demo-start` refuses reuse. Either ask Owner to stop (`opreste`), or use isolated ports:

```powershell
$env:BACKEND_PORT='8010'
$env:VITE_PORT='3010'
$env:VITE_API_BASE_URL='http://127.0.0.1:8010'
.\scripts\demo-start.ps1
```

## Auth

Development-bound only:

- Frontend: `VITE_ENABLE_DEV_AUTH=true` (set by demo-start)
- API: `Authorization: Bearer __DEV_BYPASS_TOKEN__` when `APP_ENV=development`
- Synthetic admin: `dev@localhost` / Dev Admin (or bypass without DB user)

Never enable this pattern in production.

## Important DEMO identities

| Entity | Stable id / code |
|--------|------------------|
| Intake complete | `DEMO-INTAKE-LETTERS-001` · id `d0e10001-0000-4000-8000-000000000001` |
| Intake draft | `DEMO-INTAKE-DRAFT-001` · id `d0e10002-0000-4000-8000-000000000002` |
| Clients | `DEMO-CLIENT-001` … `004` (names Demo Client Alpha…) |
| Employees | Demo Operator CNC / Demo Assembler / Demo Finisher |
| Quote | code forced to `DEMO-QUOTE-EUR-001` (EUR Letters totals from real CPP) |
| Order | code forced to `DEMO-ORDER-001` |

Latest seed machine summary: `backend/demo/last_seed_summary.json` (local, after bootstrap).

## Routes to open

| Route | Notes |
|-------|--------|
| `/dashboard` | Live KPIs from demo DB |
| `/intake` | List includes demo intakes |
| `/intake-v6/d0e10001-0000-4000-8000-000000000001/operator` | Complete Letters |
| `/intake-v6/d0e10002-0000-4000-8000-000000000002/operator` | Draft / incomplete |
| `/product-system/products` | Letters template visible |
| `/inventory/pricing` | Canonical registry rates |
| `/quotes` · `/quotes/1` | EUR demo quote (id from summary) |
| `/orders` · `/orders/1` | Locked order from quote |
| `/execution` · `/execution/1` | EP + assignment + session |
| `/execution/machine-runs` | Registry machines (synthetic names) |
| `/modules` · `/governance` | Natural from code |
| Profitability | Order execution result / profitability-actual for order `1` |

Exact numeric quote/order ids are in `last_seed_summary.json` after bootstrap (stable `1` on fresh wipe).

## What is synthetic

- All client / employee / contact names and `@example.invalid` emails  
- Demo resource display names (`Demo CNC 4020`, …)  
- Artwork: in-repo golden Gradi fixture extract (not Owner Desktop paths)  
- Material stock top-up for one Oracal line so actuals can record  

## What is real

- Product System / ProductDefinition / Aggregate  
- CPP commercial rules + seeded registry prices  
- Quote Snapshot V2 · Order · ExecutionPlan · controlled session · material actuals · profitability read model  

## Limitations

- Not a clone of Owner `dev.db`  
- Labor money finalize may still be optional on the demo path (session minutes are seeded)  
- MachineRun cost remains N/A for V1  
- If `:8000` already serves Owner `dev.db`, `demo-start` refuses reuse until the stack is stopped  

## Reset

```powershell
.\scripts\demo-bootstrap.ps1
```

Wipe-and-rebuild only the demo DB. Owner `backend/dev.db` is untouched.

## Atoms instruction (copy)

> This is the real WorkOS frontend and backend. Bootstrap with `.\scripts\demo-bootstrap.ps1`, start with `.\scripts\demo-start.ps1`, use the DEMO-* dataset. Do not invent API or pricing behavior. Do not use or request `backend/dev.db`.
